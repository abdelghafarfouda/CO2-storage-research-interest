"""Simulate the shifted test sets of experiment E1 with the SubsurfaceML simulator.

Each set changes ONE factor relative to the study data the models are trained
on (the paired shift design of Notebook 02 §5):

``shift_lowk``    new reservoirs with median permeability 10-30 mD, below the
                  30-1000 mD training range (geology shift); schedules are
                  drawn by the study's own procedure.
``shift_shutin``  the 55 TEST reservoirs with their own four schedules, but
                  the fourth injection period set to zero rate, so injection
                  stops at 3.75 years instead of 5 years (operating shift).
``shift_openbc``  the 55 TEST reservoirs with their own four schedules, but a
                  constant-pressure outer boundary instead of the sealed one
                  (boundary shift).
``repro_check``   8 TEST scenarios re-simulated unchanged, to confirm that the
                  current code and environment reproduce the stored study data.

Requires a checkout of abdelghafarfouda/manchester-msc-projects with the
``subsurfaceml`` package installed from it (see the experiment README).

    python scripts/generate_shift_sets.py --msc-repo ../../../manchester-msc-projects
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

HERE = Path(__file__).resolve().parents[1]
SUB = Path("advanced-subsurface-modelling/SubsurfaceML")
REAL_FIELDS = ["k_median_mD", "V_DP", "phi_mean", "h_total_m", "r_e_m", "n_g",
               "n_a", "krg0", "S_ar", "mu_g_cP", "rho_g"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo: Path, *args) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, check=True).stdout.strip()


def realisation_from_row(row):
    from subsurfaceml.scenarios import Realisation
    return Realisation(realisation_id=int(row.realisation_id), seed=int(row.seed),
                       **{k: float(getattr(row, k)) for k in REAL_FIELDS})


def run_one(cfg, r, sched):
    from subsurfaceml.scenarios import run_scenario
    t0 = time.perf_counter()
    out = run_scenario(cfg, r, sched)
    out["elapsed_s"] = time.perf_counter() - t0
    return out


def simulate(cfg, jobs, n_jobs):
    res = Parallel(n_jobs=n_jobs, batch_size=1)(
        delayed(run_one)(cfg, r, s) for r, s in jobs)
    rows, series, failed = [], [], []
    for x in res:
        if x["status"] == "ok":
            rows.append(x["row"])
            series.append(x["series"])
        else:
            failed.append({k: x[k] for k in ("scenario_id", "error", "error_type")})
    return (pd.DataFrame(rows), pd.concat(series, ignore_index=True)
            if series else pd.DataFrame(), pd.DataFrame(failed))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--msc-repo", required=True, type=Path)
    ap.add_argument("--sets", nargs="+",
                    default=["repro_check", "shift_lowk", "shift_shutin", "shift_openbc"])
    ap.add_argument("--n-jobs", type=int, default=-1)
    a = ap.parse_args()

    from subsurfaceml.config import load_config, provenance
    from subsurfaceml.scenarios import (make_schedule, sample_realisations,
                                        sample_schedules)

    spec = json.loads((HERE / "config.json").read_text())
    gen = spec["shift_sets"]
    msc = a.msc_repo.resolve()
    study = msc / SUB / "results/study"
    for name, want in spec["source_data"]["sha256"].items():
        got = sha256(study / name)
        if got != want:
            raise SystemExit(f"{name}: sha256 {got} differs from the pinned {want}")
    src_tree = git(msc, "rev-parse", f"HEAD:{SUB}/src")
    if src_tree != spec["source_data"]["subsurfaceml_src_tree"]:
        raise SystemExit(f"SubsurfaceML src tree {src_tree} differs from the pinned "
                         f"{spec['source_data']['subsurfaceml_src_tree']}")

    sc = pd.read_csv(study / "data/scenarios.csv")
    summ = json.loads((study / "metrics/summary.json").read_text())
    test_ids = set(summ["ml"]["split"]["test_ids"])
    test_rows = sc[sc.realisation_id.isin(test_ids)].sort_values("scenario_id")

    out_root = HERE / "data/raw"
    for name in a.sets:
        cfg = load_config(msc / SUB / "config/study.yaml")
        jobs, note = [], ""
        if name == "repro_check":
            pick = test_rows.iloc[:: max(1, len(test_rows) // gen["repro_check"]["n"])]
            pick = pick.iloc[: gen["repro_check"]["n"]]
            for row in pick.itertuples():
                r = realisation_from_row(row)
                rates = [row.q1_kg_s, row.q2_kg_s, row.q3_kg_s, row.q4_kg_s]
                jobs.append((r, make_schedule(cfg, r, rates, int(row.schedule_id))))
            note = "unchanged TEST scenarios, re-simulated"
        elif name == "shift_lowk":
            g = gen["shift_lowk"]
            cfg.scenarios.k_median_mD = tuple(g["k_median_mD"])
            cfg.scenarios.n_realisations = g["n_realisations"]
            cfg.scenarios.seed = g["seed"]
            for r in sample_realisations(cfg):
                r.realisation_id += g["realisation_id_offset"]
                for s in sample_schedules(cfg, r):
                    jobs.append((r, s))
            note = f"new reservoirs, k_median {g['k_median_mD']} mD (training: 30-1000 mD)"
        elif name in ("shift_shutin", "shift_openbc"):
            if name == "shift_openbc":
                cfg.solver.outer_bc = "constant_pressure"
            for row in test_rows.itertuples():
                r = realisation_from_row(row)
                rates = [row.q1_kg_s, row.q2_kg_s, row.q3_kg_s, row.q4_kg_s]
                if name == "shift_shutin":
                    rates[-1] = 0.0
                jobs.append((r, make_schedule(cfg, r, rates, int(row.schedule_id))))
            note = ("TEST reservoirs and schedules, injection stopped at 3.75 yr"
                    if name == "shift_shutin" else
                    "TEST reservoirs and schedules, constant-pressure outer boundary")
        else:
            raise SystemExit(f"unknown set {name}")

        t0 = time.perf_counter()
        print(f"[{name}] {len(jobs)} simulations ({note})", flush=True)
        df, ts, failed = simulate(cfg, jobs, a.n_jobs)
        wall = time.perf_counter() - t0
        d = out_root / name
        d.mkdir(parents=True, exist_ok=True)
        df.to_csv(d / "scenarios.csv", index=False)
        ts.to_csv(d / "timeseries.csv", index=False)
        failed.to_csv(d / "failed_runs.csv", index=False)
        prov = {"set": name, "description": note, "n_requested": len(jobs),
                "n_success": int(len(df)), "n_failed": int(len(failed)),
                "wall_time_s": wall, "outer_bc": cfg.solver.outer_bc,
                "msc_repo_commit": git(msc, "rev-parse", "HEAD"),
                "subsurfaceml_src_tree": src_tree,
                "environment": provenance(),
                "files_sha256": {f: sha256(d / f) for f in
                                 ("scenarios.csv", "timeseries.csv")}}
        (d / "provenance.json").write_text(json.dumps(prov, indent=2, default=str))
        print(f"[{name}] {len(df)} ok, {len(failed)} failed, {wall:.0f} s", flush=True)

        if name == "repro_check":
            ref = pd.read_csv(study / "data/timeseries.csv")
            ref = ref[ref.scenario_id.isin(ts.scenario_id)].sort_values(["scenario_id", "t_s"])
            new = ts.sort_values(["scenario_id", "t_s"])
            cols = ["dp_bh_Pa", "r_plume_m95_m", "mass_in_place_kg"]
            a_ = ref[cols].to_numpy(float); b_ = new[cols].to_numpy(float)
            rel = np.abs(a_ - b_) / np.maximum(np.abs(a_), 1.0)
            prov["max_rel_diff_vs_stored"] = {c: float(rel[:, i].max())
                                              for i, c in enumerate(cols)}
            (d / "provenance.json").write_text(json.dumps(prov, indent=2, default=str))
            print("[repro_check] max relative difference vs stored:",
                  prov["max_rel_diff_vs_stored"], flush=True)


if __name__ == "__main__":
    main()
