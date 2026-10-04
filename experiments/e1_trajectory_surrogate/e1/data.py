"""Sequence dataset for E1.

One sample is one simulated scenario (reservoir realisation + injection
schedule) as a 40-step sequence, t_k = 0.25 k years, k = 1..40 (10 years:
5 years of injection in four 1.25-year periods, then shut-in).

Inputs are quantities known BEFORE simulating:

* static (16): the sampled reservoir description and closed-form summaries of
  it (the same quantities the SubsurfaceML scalar surrogates use, minus every
  schedule descriptor, so the schedule enters only through the per-step
  inputs);
* dynamic, per step: the rate in effect during step k and the time t_k, and
  in the ``full`` feature set also quantities that integrate the rate history
  (cumulative mass, a closed-box material-balance pressure estimate and a
  volumetric plume-radius estimate).  The ``no_cumulative`` set drops those,
  so a model without memory cannot know how much CO2 has been injected.

Targets, per step: bottom-hole pressure build-up dp_bh [MPa] and the radius
holding 95 % of the CO2 mass r95 [m].
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
YEAR = 365.25 * 86400.0
MD = 9.869233e-16            # m^2 per mD
MPA = 1e6
# constants of subsurfaceml.scenarios.reference_rate (closed-form, no simulator output)
MU_BRINE = 6.0e-4            # Pa s
C_T = 9.0e-10                # 1/Pa, rock + brine
R_W = 0.15                   # m

STATIC = ["log10_k_mD", "V_DP", "phi_mean", "h_total_m", "r_e_m", "n_g", "n_a",
          "krg0", "S_ar", "mu_g_cP", "rho_g", "V_DP_layers", "log10_q_ref",
          "log10_pv", "log10_kh", "log10_mobility_ratio"]
DYN_ALL = ["q_over_qref", "q_scaled", "injecting", "t_frac", "dp_flow_MPa",
           "cum_mass_scaled", "dp_tank_MPa", "log_r_vol"]
FEATURE_SETS = {
    "full": DYN_ALL,
    "no_cumulative": ["q_over_qref", "q_scaled", "injecting", "t_frac", "dp_flow_MPa"],
}
TARGETS = ["dp_bh_MPa", "r95_m"]
SETS = ["id_study", "shift_lowk", "shift_shutin", "shift_openbc"]


@dataclass
class SeqSet:
    """Raw (unscaled) arrays of one scenario set."""
    name: str
    scenario_id: np.ndarray      # (N,)
    realisation_id: np.ndarray   # (N,)
    static: np.ndarray           # (N, S)
    dyn: np.ndarray              # (N, T, D) in DYN_ALL order
    y: np.ndarray                # (N, T, 2) physical units
    t_years: np.ndarray          # (T,)
    partition: np.ndarray        # (N,) str: fit / val / calib / test / shift

    def subset(self, mask) -> "SeqSet":
        return SeqSet(self.name, self.scenario_id[mask], self.realisation_id[mask],
                      self.static[mask], self.dyn[mask], self.y[mask],
                      self.t_years, self.partition[mask])


def static_frame(sc: pd.DataFrame) -> pd.DataFrame:
    k = sc.k_median_mD.to_numpy(float)
    pv = np.pi * sc.r_e_m ** 2 * sc.h_total_m * sc.phi_mean
    return pd.DataFrame({
        "log10_k_mD": np.log10(k), "V_DP": sc.V_DP, "phi_mean": sc.phi_mean,
        "h_total_m": sc.h_total_m, "r_e_m": sc.r_e_m, "n_g": sc.n_g, "n_a": sc.n_a,
        "krg0": sc.krg0, "S_ar": sc.S_ar, "mu_g_cP": sc.mu_g_cP, "rho_g": sc.rho_g,
        "V_DP_layers": sc.V_DP_layers, "log10_q_ref": np.log10(sc.q_ref_kg_s),
        "log10_pv": np.log10(pv), "log10_kh": np.log10(k * sc.h_total_m),
        "log10_mobility_ratio": np.log10(sc.endpoint_mobility_ratio),
    })[STATIC]


def dynamic_array(sc: pd.DataFrame, q: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Per-step inputs. ``q[i, k]`` is the rate during (t_{k-1}, t_k]."""
    dt = np.diff(np.concatenate([[0.0], t])) * YEAR                 # s
    M = np.cumsum(q * dt[None, :], axis=1)                          # kg
    rho = sc.rho_g.to_numpy(float)[:, None]
    h = sc.h_total_m.to_numpy(float)[:, None]
    phi = sc.phi_mean.to_numpy(float)[:, None]
    re = sc.r_e_m.to_numpy(float)[:, None]
    k = sc.k_median_mD.to_numpy(float)[:, None] * MD
    qref = sc.q_ref_kg_s.to_numpy(float)[:, None]
    vp = np.pi * re ** 2 * h * phi
    dp_tank = M / (rho * C_T * vp) / MPA
    dp_flow = q * MU_BRINE * np.log(re / R_W) / (2 * np.pi * k * h * rho) / MPA
    r_vol = np.sqrt(M / (rho * np.pi * h * phi))
    T = len(t)
    feats = {
        "q_over_qref": q / qref,
        "q_scaled": q / 10.0,
        "injecting": (q > 0).astype(float),
        "t_frac": np.broadcast_to(t / 10.0, (len(sc), T)),
        "dp_flow_MPa": dp_flow,
        "cum_mass_scaled": M / 1e9,
        "dp_tank_MPa": dp_tank,
        "log_r_vol": np.log1p(r_vol / 10.0),
    }
    return np.stack([feats[c] for c in DYN_ALL], axis=-1)


def build_set(name: str, sc: pd.DataFrame, ts: pd.DataFrame,
              partition_of: dict | None = None) -> SeqSet:
    sc = sc[sc.status == "ok"].sort_values("scenario_id").reset_index(drop=True)
    ts = ts.sort_values(["scenario_id", "t_s"])
    n_t = ts.groupby("scenario_id").size()
    if not (n_t == 41).all():
        raise ValueError(f"{name}: every scenario needs 41 report times")
    ts = ts[ts.t_s > 0]                                             # drop t = 0
    piv = {c: ts.pivot(index="scenario_id", columns="t_s", values=c)
           .loc[sc.scenario_id].to_numpy(float)
           for c in ("q_kg_s", "dp_bh_Pa", "r_plume_m95_m")}
    t = np.sort(ts.t_s.unique()) / YEAR
    if not np.allclose(t, 0.25 * np.arange(1, 41)):
        raise ValueError(f"{name}: unexpected report times")
    y = np.stack([piv["dp_bh_Pa"] / MPA, piv["r_plume_m95_m"]], axis=-1)
    part = (np.array([partition_of[int(r)] for r in sc.realisation_id])
            if partition_of is not None else np.full(len(sc), "shift"))
    return SeqSet(name, sc.scenario_id.to_numpy(str), sc.realisation_id.to_numpy(int),
                  static_frame(sc).to_numpy(float), dynamic_array(sc, piv["q_kg_s"], t),
                  y, t, part)


def save_set(s: SeqSet, path: Path) -> None:
    np.savez_compressed(path, name=s.name, scenario_id=s.scenario_id,
                        realisation_id=s.realisation_id, static=s.static, dyn=s.dyn,
                        y=s.y, t_years=s.t_years, partition=s.partition,
                        static_names=np.array(STATIC), dyn_names=np.array(DYN_ALL),
                        target_names=np.array(TARGETS))


def load_set(name: str, root: Path = HERE / "data/processed") -> SeqSet:
    z = np.load(root / f"{name}.npz", allow_pickle=False)
    if list(z["static_names"]) != STATIC or list(z["dyn_names"]) != DYN_ALL:
        raise ValueError(f"{name}.npz was built with a different feature list")
    return SeqSet(str(z["name"]), z["scenario_id"], z["realisation_id"], z["static"],
                  z["dyn"], z["y"], z["t_years"], z["partition"])


def inner_split(train_ids, frac: float, seed: int):
    """Split the training reservoirs into fit / validation (early stopping)."""
    ids = np.array(sorted(train_ids))
    rng = np.random.default_rng(seed)
    val = set(rng.choice(ids, size=int(round(frac * len(ids))), replace=False).tolist())
    return [int(i) for i in ids if i not in val], sorted(int(i) for i in val)


# ---------------------------------------------------------------------------
class Scaler:
    """Feature and target transforms, fitted on the ``fit`` partition only."""

    def __init__(self, feature_set: str):
        self.dyn_idx = [DYN_ALL.index(c) for c in FEATURE_SETS[feature_set]]
        self.feature_set = feature_set

    @staticmethod
    def ty(y):
        """Physical -> transformed targets (log1p keeps both positive scales)."""
        return np.stack([np.log1p(np.clip(y[..., 0], -0.5, None)),
                         np.log1p(np.clip(y[..., 1], 0.0, None) / 10.0)], axis=-1)

    @staticmethod
    def iy(z):
        return np.stack([np.expm1(z[..., 0]), 10.0 * np.expm1(z[..., 1])], axis=-1)

    def fit(self, s: SeqSet) -> "Scaler":
        d = s.dyn[..., self.dyn_idx].reshape(-1, len(self.dyn_idx))
        self.s_mu, self.s_sd = s.static.mean(0), s.static.std(0) + 1e-12
        self.d_mu, self.d_sd = d.mean(0), d.std(0) + 1e-12
        z = self.ty(s.y).reshape(-1, 2)
        self.y_mu, self.y_sd = z.mean(0), z.std(0)
        return self

    def x(self, s: SeqSet) -> np.ndarray:
        """(N, T, S + D) standardised inputs."""
        st = (s.static - self.s_mu) / self.s_sd
        dy = (s.dyn[..., self.dyn_idx] - self.d_mu) / self.d_sd
        st = np.broadcast_to(st[:, None, :], (len(s.static), dy.shape[1], st.shape[1]))
        return np.concatenate([st, dy], axis=-1).astype(np.float32)

    def y(self, s: SeqSet) -> np.ndarray:
        return ((self.ty(s.y) - self.y_mu) / self.y_sd).astype(np.float32)

    def inverse(self, zs: np.ndarray) -> np.ndarray:
        return self.iy(zs * self.y_sd + self.y_mu)

    def state(self) -> dict:
        return {k: getattr(self, k).tolist() for k in
                ("s_mu", "s_sd", "d_mu", "d_sd", "y_mu", "y_sd")} | {
            "feature_set": self.feature_set}


def load_all() -> dict[str, SeqSet]:
    return {n: load_set(n) for n in SETS}


def read_config() -> dict:
    return json.loads((HERE / "config.json").read_text())
