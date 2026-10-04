"""Build the E1 sequence datasets (data/processed/*.npz) and the dataset record.

    python scripts/build_dataset.py --msc-repo ../../../manchester-msc-projects

The in-distribution set is the SubsurfaceML study run, read from a checkout of
manchester-msc-projects and checked against the pinned sha256 values in
config.json. Its partitions are the published ones (124 training, 41
calibration and 55 test reservoirs, from metrics/summary.json); the training
reservoirs are further split into fit and validation (early stopping only).
The shifted sets are read from data/raw/ (scripts/generate_shift_sets.py).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from e1.data import build_set, inner_split, save_set, read_config  # noqa: E402

SUB = Path("advanced-subsurface-modelling/SubsurfaceML/results/study")


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--msc-repo", required=True, type=Path)
    a = ap.parse_args()
    cfg = read_config()
    study = a.msc_repo.resolve() / SUB
    for name, want in cfg["source_data"]["sha256"].items():
        if sha256(study / name) != want:
            raise SystemExit(f"{name} does not match the pinned sha256 {want}")

    summ = json.loads((study / "metrics/summary.json").read_text())["ml"]["split"]
    fit, val = inner_split(summ["train_ids"], cfg["data"]["inner_validation_fraction"],
                           cfg["data"]["inner_validation_seed"])
    part = {i: "fit" for i in fit} | {i: "val" for i in val}
    part |= {int(i): "calib" for i in summ["calib_ids"]}
    part |= {int(i): "test" for i in summ["test_ids"]}

    out = HERE / "data/processed"
    out.mkdir(parents=True, exist_ok=True)
    record = {"source": cfg["source_data"], "sets": {}}
    sets = {"id_study": (pd.read_csv(study / "data/scenarios.csv"),
                         pd.read_csv(study / "data/timeseries.csv"), part)}
    for name in ("shift_lowk", "shift_shutin", "shift_openbc"):
        d = HERE / "data/raw" / name
        sets[name] = (pd.read_csv(d / "scenarios.csv"), pd.read_csv(d / "timeseries.csv"), None)

    for name, (sc, ts, p) in sets.items():
        s = build_set(name, sc, ts, p)
        save_set(s, out / f"{name}.npz")
        parts, counts = np.unique(s.partition, return_counts=True)
        record["sets"][name] = {
            "scenarios": int(len(s.scenario_id)),
            "reservoirs": int(len(np.unique(s.realisation_id))),
            "by_partition": {str(k): {"scenarios": int(c), "reservoirs": int(len(
                np.unique(s.realisation_id[s.partition == k])))}
                for k, c in zip(parts, counts)},
            "dp_bh_MPa_range": [float(s.y[..., 0].min()), float(s.y[..., 0].max())],
            "r95_m_range": [float(s.y[..., 1].min()), float(s.y[..., 1].max())],
            "k_median_mD_range": [float(10 ** s.static[:, 0].min()),
                                  float(10 ** s.static[:, 0].max())],
            "npz_sha256": sha256(out / f"{name}.npz"),
        }
        print(name, record["sets"][name]["scenarios"], "scenarios",
              record["sets"][name]["by_partition"])
    (out / "dataset_record.json").write_text(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
