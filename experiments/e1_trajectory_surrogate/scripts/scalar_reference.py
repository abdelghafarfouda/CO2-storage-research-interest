"""Predictions of the published SubsurfaceML scalar surrogates on the E1 sets.

The SVR peak-pressure model and the elastic-net plume-radius model of the MSc
study run (results/study/models, loaded and hash-verified by subsurfaceml's own
loader) are applied to every scenario of the in-distribution and shifted
sets, so the trajectory models can be compared with them on the same cases.

    python scripts/scalar_reference.py --msc-repo ../../../manchester-msc-projects
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
SUB = Path("advanced-subsurface-modelling/SubsurfaceML")
REAL_FIELDS = ["k_median_mD", "V_DP", "phi_mean", "h_total_m", "r_e_m", "n_g",
               "n_a", "krg0", "S_ar", "mu_g_cP", "rho_g"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--msc-repo", required=True, type=Path)
    a = ap.parse_args()
    from subsurfaceml.config import load_config
    from subsurfaceml.predict import Predictor
    from subsurfaceml.scenarios import Realisation

    msc = a.msc_repo.resolve()
    cfg = load_config(msc / SUB / "config/study.yaml")
    pred = Predictor(cfg)                               # verifies hashes and versions
    sources = {"id_study": msc / SUB / "results/study/data/scenarios.csv"}
    for n in ("shift_lowk", "shift_shutin", "shift_openbc"):
        sources[n] = HERE / "data/raw" / n / "scenarios.csv"
    out = []
    for name, path in sources.items():
        sc = pd.read_csv(path)
        for row in sc.itertuples():
            r = Realisation(realisation_id=int(row.realisation_id), seed=int(row.seed),
                            **{k: float(getattr(row, k)) for k in REAL_FIELDS})
            rates = np.array([[row.q1_kg_s, row.q2_kg_s, row.q3_kg_s, row.q4_kg_s]])
            p = pred.predict(r, rates)
            dp, rp = p["dp_bh_max_MPa"], p["r_plume_m95_m"]
            out.append({"set": name, "scenario_id": row.scenario_id,
                        "dp_bh_max_MPa_true": row.dp_bh_max_Pa / 1e6,
                        "svr_dp_max_MPa": float(dp["pred"][0]),
                        "svr_band_low_MPa": float(dp["band_low"][0]),
                        "svr_band_high_MPa": float(dp["band_high"][0]),
                        "r95_final_m_true": row.r_plume_m95_m,
                        "enet_r95_m": float(rp["pred"][0]),
                        "enet_band_low_m": float(rp["band_low"][0]),
                        "enet_band_high_m": float(rp["band_high"][0])})
        print(name, len(sc))
    df = pd.DataFrame(out)
    dest = HERE / "data/processed/scalar_reference.csv"
    df.to_csv(dest, index=False)
    (dest.with_suffix(".json")).write_text(json.dumps({
        "models": pred.manifest["selected_models"],
        "model_files_sha256": {k: v["sha256"] for k, v in pred.manifest["files"].items()},
        "msc_config": "config/study.yaml"}, indent=2))


if __name__ == "__main__":
    main()
