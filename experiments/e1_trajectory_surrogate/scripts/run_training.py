"""Train every E1 model and seed (results/checkpoints, logs, predictions).

    python scripts/run_training.py                 # everything in config.json
    python scripts/run_training.py --only lstm mlp # a subset
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from joblib import Parallel, delayed

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from e1.data import read_config  # noqa: E402
from e1 import train  # noqa: E402


def job(kind, name, spec, seed, tcfg, n_res=None):
    if kind == "nn":
        return train.train_nn(name, spec, seed, tcfg, n_res)
    return train.train_xgb(name, spec, seed, n_res)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--n-jobs", type=int, default=4)
    a = ap.parse_args()
    cfg = read_config()
    want = lambda n: not a.only or n in a.only  # noqa: E731
    t0 = time.perf_counter()
    done = []
    if want("mean"):
        done.append(train.train_mean())
    if want("ridge"):
        done.append(train.train_ridge(cfg["baselines"]["ridge"]["alphas"]))
    jobs = []
    for name, spec in cfg["models"].items():
        if want(name):
            jobs += [("nn", name, spec, s, cfg["training"]) for s in cfg["training"]["seeds"]]
    for name in ("xgb", "xgb_nophys"):
        if want(name):
            jobs += [("xgb", name, cfg["baselines"][name], s, None)
                     for s in cfg["training"]["seeds"]]
    lc = cfg["learning_curve"]
    for base in lc["models"]:
        for n in lc["n_fit_reservoirs"]:
            name = f"lc_{base}_n{n}"
            if not want(name) and not want("learning_curve"):
                continue
            if base in cfg["models"]:
                jobs += [("nn", name, cfg["models"][base], s, cfg["training"], n)
                         for s in cfg["training"]["seeds"]]
            else:
                jobs += [("xgb", name, cfg["baselines"][base], s, None, n)
                         for s in cfg["training"]["seeds"]]
    # longest jobs first
    jobs.sort(key=lambda j: (j[0] != "nn", "lstm" not in j[1]))
    done += Parallel(n_jobs=a.n_jobs, verbose=10)(delayed(job)(*j) for j in jobs)
    out = HERE / "results/metrics"
    out.mkdir(parents=True, exist_ok=True)
    summary = {"wall_seconds": time.perf_counter() - t0, "runs": done}
    tag = "_".join(a.only) if a.only else "all"
    (out / f"training_runs_{tag}.json").write_text(json.dumps(summary, indent=2))
    print(f"trained {len(done)} runs in {summary['wall_seconds']:.0f} s")


if __name__ == "__main__":
    main()
