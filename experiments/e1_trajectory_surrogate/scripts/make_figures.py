"""Figures of E1 (results/figures/*.png), from the saved predictions and metrics.

    python scripts/make_figures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from e1.data import SETS, load_all, read_config  # noqa: E402
from e1.evaluate import TrajectoryConformal  # noqa: E402
from e1.train import RES, load_preds  # noqa: E402

# validated categorical slots (light surface), fixed order; chrome per the palette
C = {"lstm": "#2a78d6", "mlp": "#eb6834", "xgb": "#1baf7a", "ridge": "#eda100"}
INK, INK2, MUTED, GRID, AXIS, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
LABEL = {"lstm": "LSTM (memory)", "mlp": "MLP (no memory)", "xgb": "XGBoost (per step)",
         "ridge": "Ridge (per step)", "mean": "Training mean"}
SETNAME = {"test": "Held-out reservoirs\n(in distribution)",
           "shift_lowk": "Lower permeability\n10–30 mD",
           "shift_shutin": "Earlier shut-in\n3.75 yr",
           "shift_openbc": "Open outer\nboundary"}
OUT = RES / "figures"


def plain_log(axis, ticks):
    """Log axis with plain-number tick labels at the given values."""
    axis.set_major_locator(FixedLocator(ticks))
    axis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    axis.set_minor_formatter(NullFormatter())


SHORT = {"test": "In distribution (test)", "shift_lowk": "Lower permeability",
         "shift_shutin": "Earlier shut-in", "shift_openbc": "Open outer boundary"}


def style():
    plt.rcParams.update({
        "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
        "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": AXIS,
        "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
        "axes.titlecolor": INK, "axes.titlesize": 9.5, "axes.titleweight": "bold",
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "lines.linewidth": 2, "savefig.dpi": 200})


def subset(sets, key):
    if key == "test":
        s = sets["id_study"]
        m = s.partition == "test"
        return s.subset(m), "id_study", m
    s = sets[key]
    return s, key, np.ones(len(s.y), bool)


def ensemble(preds, n, mask):
    a = np.stack([p[n][mask] for p in preds.values()])
    return a.mean(0), a.std(0, ddof=1)


def fig_trajectories(sets, ev, cfg):
    preds = {s: load_preds("lstm", s) for s in cfg["training"]["seeds"]}
    ids = sets["id_study"]
    cal = ids.partition == "calib"
    mu_c, sd_c = ensemble(preds, "id_study", cal)
    tc = TrajectoryConformal(cfg["uncertainty"]["alpha"],
                             cfg["uncertainty"]["score_floor_fraction"]).fit(
        mu_c, sd_c, ids.y[cal], ids.realisation_id[cal], "scenario")
    fig, ax = plt.subplots(2, 4, figsize=(11, 5.2), sharex=True)
    t = np.concatenate([[0.0], ids.t_years])
    for c, key in enumerate(SETNAME):
        s, n, m = subset(sets, key)
        mu, sd = ensemble(preds, n, m)
        err = np.sqrt(np.mean((mu[..., 0] - s.y[..., 0]) ** 2, axis=1))
        i = int(np.argsort(err)[len(err) // 2])          # the median-error case
        for r, (j, unit) in enumerate([(0, "MPa"), (1, "m")]):
            a = ax[r, c]
            lo, hi = tc.band(mu[i:i + 1], sd[i:i + 1], j)
            a.fill_between(t, np.r_[0, lo[0]], np.r_[0, hi[0]], color=C["lstm"], alpha=0.18,
                           lw=0, label="90 % conformal band")
            a.plot(t, np.r_[0, s.y[i, :, j]], color=INK, lw=2, label="Simulator")
            a.plot(t, np.r_[0, mu[i, :, j]], color=C["lstm"], lw=2, ls=(0, (4, 2)),
                   label="LSTM ensemble mean")
            shut = 3.75 if key == "shift_shutin" else 5.0
            a.axvline(shut, color=MUTED, lw=0.8)
            if r == 0:
                a.set_title(SHORT[key], loc="left")
                a.text(shut + 0.15, a.get_ylim()[1] * 0.95, "shut-in", color=MUTED,
                       va="top", fontsize=8)
            if c == 0:
                a.set_ylabel(["Bottom-hole pressure\nbuild-up (MPa)",
                              "Radius holding 95 %\nof the CO₂ (m)"][r])
            if r == 1:
                a.set_xlabel("Time since injection start (years)")
    ax[0, 0].legend(loc="lower right", fontsize=7.5)
    fig.suptitle("Typical predicted trajectories (median-error case of each test set)",
                 x=0.01, ha="left", color=INK, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "fig1_trajectories.png")
    plt.close(fig)


def fig_models(acc, ev):
    order = ["mean", "ridge", "xgb_nophys", "xgb", "mlp_nophys", "mlp",
             "lstm_nophys", "lstm_h16", "lstm", "lstm_h128x2"]
    names = {"mean": "Training mean", "ridge": "Ridge, per step", "xgb": "XGBoost, per step",
             "xgb_nophys": "XGBoost, per step  [no cumulative inputs]",
             "mlp": "MLP, per step", "mlp_nophys": "MLP, per step  [no cumulative inputs]",
             "lstm": "LSTM 64", "lstm_nophys": "LSTM 64  [no cumulative inputs]",
             "lstm_h16": "LSTM 16", "lstm_h128x2": "LSTM 128 × 2 layers"}
    fam = lambda m: "lstm" if m.startswith("lstm") else ("mlp" if m.startswith("mlp") else (  # noqa: E731
        "xgb" if m.startswith("xgb") else ("ridge" if m == "ridge" else "mean")))
    d = acc[(acc.set == "test") & (acc.phase == "all")]
    order = [m for m in order if m in set(d.model)]
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.4), sharey=True)
    for k, (tgt, unit, xmax) in enumerate([("dp_bh_MPa", "MPa", None), ("r95_m", "m", None)]):
        a = ax[k]
        for y, m in enumerate(order):
            r = d[(d.model == m) & (d.target == tgt)].iloc[0]
            col = C.get(fam(m), MUTED)
            hollow = "nophys" in m
            a.errorbar(r["mean"], y, xerr=r["std"], fmt="o", ms=7, color=col,
                       mfc=SURF if hollow else col, mew=2, capsize=3, lw=1.2)
            a.text((r["mean"] + r["std"]) * 1.06, y, f"{r['mean']:.3g}", va="center",
                   fontsize=7.5, color=INK2)
        a.set_xscale("log")
        plain_log(a.xaxis, [0.5, 1, 2, 4] if k == 0 else [10, 20, 50, 100])
        a.set_xlabel(f"RMSE over all 40 steps ({unit}), log scale")
        a.set_title(["Bottom-hole pressure build-up", "Plume radius r95"][k], loc="left")
    ax[0].set_yticks(range(len(order)))
    ax[0].set_yticklabels([names[m] for m in order])
    ax[0].invert_yaxis()
    fig.text(0.01, 0.01, "220 test scenarios from 55 held-out reservoirs. Points: mean over 5 seeds "
             "(1 for ridge and mean); bars: ±1 s.d. across seeds. Hollow: inputs without cumulative "
             "injected mass.", fontsize=7.5, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / "fig2_model_comparison.png")
    plt.close(fig)


def fig_shift(acc):
    models = ["mean", "ridge", "xgb", "mlp", "lstm"]
    d = acc[(acc.target == "dp_bh_MPa") & (acc.phase == "all")]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    keys = list(SETNAME)
    off = np.linspace(-0.28, 0.28, len(models))
    for i, m in enumerate(models):
        for y, key in enumerate(keys):
            r = d[(d.model == m) & (d.set == key)]
            if r.empty:
                continue
            r = r.iloc[0]
            ax.errorbar(r["mean"], y + off[i], xerr=r["std"], fmt="o", ms=6,
                        color=C.get(m, MUTED), capsize=2, lw=1, label=LABEL[m] if y == 0 else None)
    ax.set_xscale("log")
    plain_log(ax.xaxis, [0.5, 1, 2, 4, 6])
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels([SETNAME[k] for k in keys])
    ax.invert_yaxis()
    ax.set_xlabel("RMSE of bottom-hole pressure build-up over all 40 steps (MPa), log scale")
    ax.set_title("Accuracy under one-factor shifts (mean ± s.d. over seeds)", loc="left")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_shifts.png")
    plt.close(fig)


def fig_coverage(ev):
    u = ev["uncertainty"]
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.0))
    keys = list(SETNAME)
    a = ax[0]
    for j, (tgt, col, lab) in enumerate([("dp_bh_MPa", C["lstm"], "Pressure build-up"),
                                         ("r95_m", C["mlp"], "Plume radius r95")]):
        for y, key in enumerate(keys):
            c = u["conformal_scenario"][key][tgt]
            lo, hi = c["ci95"]
            yy = y + (-0.12 if j == 0 else 0.12)
            a.plot([lo, hi], [yy, yy], color=col, lw=1.5)
            a.plot(c["coverage"], yy, "o", color=col, ms=7, label=lab if y == 0 else None)
    a.axvline(0.9, color=INK2, lw=1)
    a.text(0.905, -0.45, "target 0.90", color=INK2, fontsize=8)
    a.set_yticks(range(len(keys)))
    a.set_yticklabels([SETNAME[k] for k in keys])
    a.invert_yaxis()
    a.set_xlim(-0.02, 1.02)
    a.set_xlabel("Share of scenarios whose WHOLE 10-year trajectory\nlies inside the band (95 % Clopper–Pearson interval)")
    a.set_title("Conformal whole-trajectory bands", loc="left")
    a.legend(loc="upper left", fontsize=8)
    b = ax[1]
    t = 0.25 * np.arange(1, 41)
    b.plot(t, u["conformal_scenario"]["test"]["dp_bh_MPa"]["per_step"], color=C["lstm"],
           label="Conformal band (calibrated)")
    b.plot(t, u["gaussian_ensemble"]["test"]["dp_bh_MPa"]["per_step"], color=C["mlp"],
           label="Ensemble mean ± 1.645 s.d. (uncalibrated)")
    b.axhline(0.9, color=INK2, lw=1)
    b.set_ylim(0, 1.02)
    b.set_xlabel("Time since injection start (years)")
    b.set_ylabel("Share of test scenarios covered")
    b.set_title("Per-step coverage, pressure build-up (test)", loc="left")
    b.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_coverage.png")
    plt.close(fig)


def fig_peak(sets, cfg):
    ref = pd.read_csv(HERE / "data/processed/scalar_reference.csv").set_index("scenario_id")
    preds = {s: load_preds("lstm", s) for s in cfg["training"]["seeds"]}
    fig, ax = plt.subplots(1, 2, figsize=(9.5, 4.3))
    for k, key in enumerate(["test", "shift_lowk"]):
        s, n, m = subset(sets, key)
        mu, _ = ensemble(preds, n, m)
        r = ref[ref.set == n].loc[s.scenario_id]
        true = s.y[..., 0].max(1)
        a = ax[k]
        a.scatter(true, r.svr_dp_max_MPa, s=14, color=C["mlp"], alpha=0.8, lw=0,
                  label="Published scalar SVR (MSc)")
        a.scatter(true, mu[..., 0].max(1), s=14, color=C["lstm"], alpha=0.8, lw=0,
                  label="LSTM ensemble, max over trajectory")
        lim = [true.min() * 0.6, true.max() * 1.6]
        a.plot(lim, lim, color=INK2, lw=1)
        a.set_xscale("log"); a.set_yscale("log")
        a.set_xlim(lim); a.set_ylim(lim)
        for axis in (a.xaxis, a.yaxis):
            plain_log(axis, [0.5, 1, 2, 5, 10, 20, 50])
        r_l = np.sqrt(np.mean((mu[..., 0].max(1) - true) ** 2))
        r_s = np.sqrt(np.mean((r.svr_dp_max_MPa.to_numpy() - true) ** 2))
        a.text(0.97, 0.04, f"RMSE  LSTM {r_l:.2f} MPa\nRMSE  SVR  {r_s:.2f} MPa\nn = {len(true)}",
               transform=a.transAxes, ha="right", va="bottom", fontsize=8, color=INK2)
        a.set_xlabel("Simulated peak build-up at the 40 report times (MPa)")
        a.set_ylabel("Predicted peak build-up (MPa)")
        a.set_title(SHORT[key], loc="left")
    ax[0].legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig5_peak_vs_scalar.png")
    plt.close(fig)


def fig_learning_curve(acc_lc):
    if acc_lc is None:
        return
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for m in ("xgb", "lstm"):
        d = acc_lc[acc_lc.model == m].sort_values("n")
        ax.errorbar(d.n, d["mean"], yerr=d["std"], color=C[m], marker="o", ms=6, capsize=3,
                    label=LABEL[m])
        ax.text(d.n.iloc[-1] * 1.05, d["mean"].iloc[-1], LABEL[m].split(" (")[0],
                color=INK2, va="center", fontsize=8)
    ax.set_xscale("log"); ax.set_yscale("log")
    plain_log(ax.xaxis, [12, 25, 50, 99])
    plain_log(ax.yaxis, [0.6, 0.7, 0.8, 1.0, 1.2, 1.4])
    ax.set_xlabel("Reservoirs used for fitting (4 schedules each)")
    ax.set_ylabel("Test RMSE, pressure build-up (MPa)")
    ax.set_title("Learning curve on the 55 held-out reservoirs", loc="left")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig6_learning_curve.png")
    plt.close(fig)


def main():
    style()
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = read_config()
    sets = load_all()
    ev = json.loads((RES / "metrics/evaluation.json").read_text())
    acc = pd.read_csv(RES / "metrics/accuracy_summary.csv")
    lc = RES / "metrics/learning_curve.csv"
    fig_trajectories(sets, ev, cfg)
    fig_models(acc, ev)
    fig_shift(acc)
    fig_coverage(ev)
    fig_peak(sets, cfg)
    fig_learning_curve(pd.read_csv(lc) if lc.exists() else None)
    print("figures:", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
