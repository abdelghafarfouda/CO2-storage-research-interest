"""Evaluate every trained E1 model: held-out accuracy, controlled comparisons,
uncertainty, shifted sets and the comparison with the scalar surrogates.

    python scripts/evaluate.py

Writes results/metrics/*.json|csv. Figures: scripts/make_figures.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from e1.data import SETS, load_all, read_config  # noqa: E402
from e1.evaluate import (PHASES, TrajectoryConformal, auroc, clopper_pearson,  # noqa: E402
                         gaussian_ensemble_coverage, peak_error, reservoir_bootstrap,
                         rmse, scenario_mse)
from e1.train import RES, load_preds  # noqa: E402

TARGET = {0: "dp_bh_MPa", 1: "r95_m"}
EVAL_SETS = {"test": ("id_study", "test"), "shift_lowk": ("shift_lowk", None),
             "shift_shutin": ("shift_shutin", None), "shift_openbc": ("shift_openbc", None)}


def model_seeds(name: str) -> list[int]:
    d = RES / "predictions" / name
    return sorted(int(p.stem[4:]) for p in d.glob("seed*.npz"))


def select(sets, key):
    name, part = EVAL_SETS[key]
    s = sets[name]
    m = np.ones(len(s.y), bool) if part is None else (s.partition == part)
    return s.subset(m), m


def main() -> None:
    cfg = read_config()
    sets = load_all()
    models = ["mean", "ridge", "xgb", "xgb_nophys", *cfg["models"].keys()]
    models = [m for m in models if (RES / "predictions" / m).exists()]
    preds = {m: {s: load_preds(m, s) for s in model_seeds(m)} for m in models}
    meta = {m: [json.loads((RES / "predictions" / m / f"seed{s}.json").read_text())
                for s in model_seeds(m)] for m in models}
    out = {"n_seeds": {m: len(preds[m]) for m in models}}

    # ---- 1. accuracy, per model x set x target x phase ---------------------
    rows = []
    for key in EVAL_SETS:
        s, mask = select(sets, key)
        for m in models:
            for seed, p in preds[m].items():
                pm = p[EVAL_SETS[key][0]][mask]
                for j, tname in TARGET.items():
                    for ph, sl in PHASES.items():
                        rows.append({"set": key, "model": m, "seed": seed, "target": tname,
                                     "phase": ph, "rmse": rmse(pm, s.y, j, sl)})
                pe = peak_error(pm, s.y)
                rows.append({"set": key, "model": m, "seed": seed, "target": "peak_dp_MPa",
                             "phase": "max", "rmse": float(np.sqrt(np.mean(pe ** 2)))})
    acc = pd.DataFrame(rows)
    acc.to_csv(RES / "metrics/accuracy_by_seed.csv", index=False)
    summ = (acc.groupby(["set", "model", "target", "phase"]).rmse
            .agg(["mean", "std", "count"]).reset_index())
    summ["std"] = summ["std"].fillna(0.0)
    summ.to_csv(RES / "metrics/accuracy_summary.csv", index=False)

    # ---- 2. complexity and cost ---------------------------------------------
    cost = {}
    n_all = sum(len(x.y) for x in sets.values())
    for m in models:
        mm = meta[m]
        cost[m] = {"n_params": mm[0].get("n_params"),
                   "train_seconds_mean": float(np.mean([x.get("train_seconds", 0.0) for x in mm])),
                   "epochs_mean": float(np.mean([x.get("epochs_run", 0) for x in mm]))
                   if "epochs_run" in mm[0] else None,
                   "inference_ms_per_scenario": 1e3 * float(np.mean(
                       [x.get("inference_seconds_all_sets", np.nan) for x in mm])) / n_all
                   if "inference_seconds_all_sets" in mm[0] else None}
    test_sc = pd.read_csv(HERE / "data/processed/scalar_reference.csv")
    out["cost"] = cost

    # ---- 3. paired comparisons on the TEST reservoirs ------------------------
    s, mask = select(sets, "test")
    ev = cfg["evaluation"]

    def mean_mse(m, j, sl=slice(0, 40)):
        return np.mean([scenario_mse(p["id_study"][mask], s.y, j, sl)
                        for p in preds[m].values()], axis=0)
    pairs = [("lstm", "mlp"), ("lstm", "xgb"), ("lstm", "ridge"), ("xgb", "mlp"),
             ("lstm_nophys", "mlp_nophys"), ("lstm_nophys", "xgb_nophys"),
             ("lstm", "lstm_nophys"), ("lstm_h16", "lstm"), ("lstm_h128x2", "lstm")]
    comp = []
    for a, b in pairs:
        if a not in preds or b not in preds:
            continue
        for j, tname in TARGET.items():
            for ph, sl in PHASES.items():
                r = reservoir_bootstrap(mean_mse(a, j, sl), mean_mse(b, j, sl),
                                        s.realisation_id, ev["bootstrap_resamples"],
                                        ev["bootstrap_seed"])
                comp.append({"a": a, "b": b, "target": tname, "phase": ph, **r})
    out["paired_comparisons_test"] = comp

    # ---- 4. uncertainty: deep ensemble + conformal ---------------------------
    uc = cfg["uncertainty"]
    em = uc["ensemble_model"]
    stack = {n: np.stack([p[n] for p in preds[em].values()]) for n in SETS}
    mu = {n: v.mean(0) for n, v in stack.items()}
    sd = {n: v.std(0, ddof=1) for n, v in stack.items()}
    ids = sets["id_study"]
    cal = ids.partition == "calib"
    unc = {"ensemble_model": em, "members": len(preds[em]), "alpha": uc["alpha"]}
    for unit in ("scenario", "reservoir"):
        tc = TrajectoryConformal(uc["alpha"], uc["score_floor_fraction"]).fit(
            mu["id_study"][cal], sd["id_study"][cal], ids.y[cal], ids.realisation_id[cal], unit)
        res = {"q": tc.q, "floor": tc.floor, "n_calibration_units": tc.n_cal}
        for key in EVAL_SETS:
            ss, mk = select(sets, key)
            n = EVAL_SETS[key][0]
            res[key] = {TARGET[j]: tc.coverage(mu[n][mk], sd[n][mk], ss.y, ss.realisation_id, j)
                        for j in TARGET}
        unc[f"conformal_{unit}"] = res
    unc["gaussian_ensemble"] = {}
    for key in EVAL_SETS:
        ss, mk = select(sets, key)
        n = EVAL_SETS[key][0]
        unc["gaussian_ensemble"][key] = {TARGET[j]: gaussian_ensemble_coverage(
            mu[n][mk], sd[n][mk], ss.y, j) for j in TARGET}
    # ensemble-mean accuracy
    unc["ensemble_mean_rmse"] = {}
    for key in EVAL_SETS:
        ss, mk = select(sets, key)
        n = EVAL_SETS[key][0]
        unc["ensemble_mean_rmse"][key] = {TARGET[j]: {ph: rmse(mu[n][mk], ss.y, j, sl)
                                                      for ph, sl in PHASES.items()}
                                          for j in TARGET}
    # does ensemble disagreement flag the shifted sets?
    s_t, m_t = select(sets, "test")
    spread_id = sd["id_study"][m_t][..., 0].mean(1)
    rel_id = (sd["id_study"][m_t][..., 0] / np.maximum(mu["id_study"][m_t][..., 0], 0.1)).mean(1)
    unc["shift_detection_auroc"] = {}
    for key in ("shift_lowk", "shift_shutin", "shift_openbc"):
        n = EVAL_SETS[key][0]
        sp = sd[n][..., 0].mean(1)
        rl = (sd[n][..., 0] / np.maximum(mu[n][..., 0], 0.1)).mean(1)
        unc["shift_detection_auroc"][key] = {
            "mean_dp_spread_MPa": auroc(spread_id, sp),
            "mean_relative_dp_spread": auroc(rel_id, rl),
            "median_spread_MPa": {"test": float(np.median(spread_id)),
                                  key: float(np.median(sp))}}
    out["uncertainty"] = unc

    # ---- 5. shift effects, paired by scenario (same reservoir and schedule) --
    shift = []
    base_s, base_m = select(sets, "test")
    for key in ("shift_shutin", "shift_openbc"):
        sh = sets[EVAL_SETS[key][0]]
        assert list(sh.scenario_id) == list(base_s.scenario_id)
        for m in ("lstm", "mlp", "xgb", "ridge"):
            if m not in preds:
                continue
            for j, tname in TARGET.items():
                e_sh = np.mean([scenario_mse(p[EVAL_SETS[key][0]], sh.y, j) for p in preds[m].values()], 0)
                e_b = np.mean([scenario_mse(p["id_study"][base_m], base_s.y, j)
                               for p in preds[m].values()], 0)
                r = reservoir_bootstrap(e_sh, e_b, base_s.realisation_id,
                                        ev["bootstrap_resamples"], ev["bootstrap_seed"])
                shift.append({"shift": key, "model": m, "target": tname,
                              "rmse_shifted": float(np.sqrt(e_sh.mean())),
                              "rmse_baseline": float(np.sqrt(e_b.mean())), **r})
    out["paired_shift_effects"] = shift

    # ---- 6. scalar surrogate (published SVR / elastic net) on the same cases --
    ref = test_sc.set_index("scenario_id")
    scal = {}
    for key in EVAL_SETS:
        ss, mk = select(sets, key)
        n = EVAL_SETS[key][0]
        r = ref[ref.set == n].loc[ss.scenario_id]
        svr = r.svr_dp_max_MPa.to_numpy()
        true_max = r.dp_bh_max_MPa_true.to_numpy()
        rep_max = ss.y[..., 0].max(1)
        lstm_peak = mu[n][mk][..., 0].max(1)
        lstm_seed_peak = [p[n][mk][..., 0].max(1) for p in preds["lstm"].values()]
        inside = (true_max >= r.svr_band_low_MPa.to_numpy()) & (true_max <= r.svr_band_high_MPa.to_numpy())
        scal[key] = {
            "n": int(len(ss.y)),
            "svr_rmse_vs_simulated_max_MPa": float(np.sqrt(np.mean((svr - true_max) ** 2))),
            "svr_rmse_vs_report_time_max_MPa": float(np.sqrt(np.mean((svr - rep_max) ** 2))),
            "lstm_ensemble_rmse_vs_report_time_max_MPa": float(np.sqrt(np.mean((lstm_peak - rep_max) ** 2))),
            "lstm_single_seed_rmse_vs_report_time_max_MPa": [
                float(np.sqrt(np.mean((x - rep_max) ** 2))) for x in lstm_seed_peak],
            "lstm_ensemble_rmse_vs_simulated_max_MPa": float(np.sqrt(np.mean((lstm_peak - true_max) ** 2))),
            "svr_band_coverage_of_simulated_max": float(inside.mean()),
            "cases_where_report_max_differs_from_simulated_max": int(np.sum(np.abs(true_max - rep_max) > 1e-6)),
            "enet_r95_final_rmse_m": float(np.sqrt(np.mean((r.enet_r95_m.to_numpy() - ss.y[:, -1, 1]) ** 2))),
            "lstm_ensemble_r95_final_rmse_m": float(np.sqrt(np.mean((mu[n][mk][:, -1, 1] - ss.y[:, -1, 1]) ** 2))),
        }
        if key != "shift_openbc":
            e_l = (lstm_peak - rep_max) ** 2
            e_s = (svr - rep_max) ** 2
            scal[key]["paired_lstm_minus_svr_vs_report_max"] = reservoir_bootstrap(
                e_l, e_s, ss.realisation_id, ev["bootstrap_resamples"], ev["bootstrap_seed"])
    out["scalar_surrogate_comparison"] = scal

    # ---- 6b. where the error sits: permeability terciles and worst cases ---
    s_t, m_t = select(sets, "test")
    k = 10 ** s_t.static[:, 0]
    edges = np.quantile(np.unique(k), [1 / 3, 2 / 3])
    terc = np.digitize(k, edges)
    by_k = {}
    for m in ("lstm", "mlp", "xgb", "ridge"):
        if m not in preds:
            continue
        e = mean_mse(m, 0)
        by_k[m] = {f"tercile_{i + 1}": {"k_mD": [float(k[terc == i].min()), float(k[terc == i].max())],
                                         "rmse_dp_MPa": float(np.sqrt(e[terc == i].mean())),
                                         "n": int((terc == i).sum())} for i in range(3)}
        order = np.argsort(e)[::-1]
        by_k[m]["share_of_mse_from_worst_reservoir"] = float(
            e[s_t.realisation_id == s_t.realisation_id[order[0]]].sum() / e.sum())
        by_k[m]["worst_scenario"] = {"scenario_id": str(s_t.scenario_id[order[0]]),
                                     "k_mD": float(k[order[0]]),
                                     "rmse_dp_MPa": float(np.sqrt(e[order[0]])),
                                     "peak_true_MPa": float(s_t.y[order[0], :, 0].max())}
        keep = s_t.realisation_id != s_t.realisation_id[order[0]]
        by_k[m]["rmse_dp_without_worst_reservoir_MPa"] = float(np.sqrt(e[keep].mean()))
        by_k[m]["median_scenario_rmse_dp_MPa"] = float(np.median(np.sqrt(e)))
    out["test_error_structure"] = by_k
    sim_s = pd.read_csv(HERE / "data/raw/shift_shutin/scenarios.csv")
    out["simulator_seconds_per_scenario"] = {
        "note": "single-process wall time of the SubsurfaceML simulator, from the shifted-set runs",
        "median": float(sim_s.wall_time_s.median()), "mean": float(sim_s.wall_time_s.mean())}

    # ---- 7. learning curve (test RMSE against the number of fit reservoirs) --
    lc_rows = []
    for base in cfg["learning_curve"]["models"]:
        runs = {99: base} | {n: f"lc_{base}_n{n}" for n in cfg["learning_curve"]["n_fit_reservoirs"]}
        for n, m in runs.items():
            if not (RES / "predictions" / m).exists():
                continue
            v = [rmse(load_preds(m, sd_)["id_study"][mask], s.y, 0) for sd_ in model_seeds(m)]
            lc_rows.append({"model": base, "n": n, "mean": float(np.mean(v)),
                            "std": float(np.std(v, ddof=1)), "seeds": len(v)})
    if lc_rows:
        pd.DataFrame(lc_rows).to_csv(RES / "metrics/learning_curve.csv", index=False)
        out["learning_curve_test_dp_rmse_MPa"] = lc_rows

    (RES / "metrics/evaluation.json").write_text(json.dumps(out, indent=2))
    # compact table for the README
    keep = summ[(summ.phase.isin(["all", "t<=5yr", "t>5yr", "max"]))]
    keep.to_csv(RES / "metrics/accuracy_table.csv", index=False)
    print(summ[(summ.target == "dp_bh_MPa") & (summ.phase == "all")]
          .pivot(index="model", columns="set", values="mean").round(3))
    print(json.dumps(out["scalar_surrogate_comparison"]["test"], indent=1)[:1500])


if __name__ == "__main__":
    main()
