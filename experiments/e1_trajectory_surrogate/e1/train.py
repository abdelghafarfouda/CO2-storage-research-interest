"""Training of every model of E1; each run saves a checkpoint, a log and its
predictions (physical units) on every scenario of every set."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from .data import HERE, SETS, Scaler, SeqSet, load_all
from .models import build_net, n_params, rows

RES = HERE / "results"


def _fit_set(sets: dict[str, SeqSet], part: str, n_res: int | None = None) -> SeqSet:
    """Scenarios of one partition; with ``n_res``, only the first ``n_res``
    reservoirs of a fixed permutation (nested subsets for the learning curve)."""
    s = sets["id_study"]
    s = s.subset(s.partition == part)
    if n_res is not None:
        ids = np.random.default_rng(12345).permutation(np.unique(s.realisation_id))
        s = s.subset(np.isin(s.realisation_id, ids[:n_res]))
    return s


def _save_preds(model: str, seed: int, preds: dict, meta: dict) -> None:
    d = RES / "predictions" / model
    d.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(d / f"seed{seed}.npz", **{k: v.astype(np.float32)
                                                   for k, v in preds.items()})
    (d / f"seed{seed}.json").write_text(json.dumps(meta, indent=2))


def train_nn(name: str, spec: dict, seed: int, tcfg: dict, n_res: int | None = None) -> dict:
    import torch
    torch.set_num_threads(tcfg.get("torch_threads", 1))
    torch.manual_seed(seed)
    np.random.seed(seed)
    sets = load_all()
    fit, val = _fit_set(sets, "fit", n_res), _fit_set(sets, "val")
    sc = Scaler(spec["features"]).fit(fit)
    Xf, Yf = torch.from_numpy(sc.x(fit)), torch.from_numpy(sc.y(fit))
    Xv, Yv = torch.from_numpy(sc.x(val)), torch.from_numpy(sc.y(val))
    net = build_net(spec, Xf.shape[-1])
    opt = torch.optim.Adam(net.parameters(), lr=tcfg["lr"],
                           weight_decay=tcfg["weight_decay"])
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=20,
                                                       min_lr=1e-5)
    gen = torch.Generator().manual_seed(seed)
    best, best_state, bad, log = np.inf, None, 0, []
    t0 = time.perf_counter()
    for ep in range(tcfg["max_epochs"]):
        net.train()
        perm = torch.randperm(len(Xf), generator=gen)
        tl = 0.0
        for i in range(0, len(Xf), tcfg["batch_size"]):
            b = perm[i:i + tcfg["batch_size"]]
            opt.zero_grad()
            loss = torch.mean((net(Xf[b]) - Yf[b]) ** 2)
            loss.backward()
            opt.step()
            tl += loss.item() * len(b)
        net.eval()
        with torch.no_grad():
            vl = float(torch.mean((net(Xv) - Yv) ** 2))
        sched.step(vl)
        log.append({"epoch": ep, "train_loss": tl / len(Xf), "val_loss": vl,
                    "lr": opt.param_groups[0]["lr"]})
        if vl < best - 1e-6:
            best, bad = vl, 0
            best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}
        else:
            bad += 1
            if bad >= tcfg["patience"]:
                break
    wall = time.perf_counter() - t0
    net.load_state_dict(best_state)
    net.eval()
    preds = {}
    t1 = time.perf_counter()
    with torch.no_grad():
        for n, s in sets.items():
            preds[n] = sc.inverse(net(torch.from_numpy(sc.x(s))).numpy())
    infer = time.perf_counter() - t1
    ck = RES / "checkpoints" / name
    ck.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": best_state, "spec": spec, "scaler": sc.state(),
                "n_in": int(Xf.shape[-1]), "seed": seed}, ck / f"seed{seed}.pt")
    lg = RES / "logs" / name
    lg.mkdir(parents=True, exist_ok=True)
    (lg / f"seed{seed}.jsonl").write_text("\n".join(json.dumps(r) for r in log) + "\n")
    meta = {"model": name, "seed": seed, "spec": spec, "n_params": n_params(net),
            "n_fit_reservoirs": int(len(np.unique(fit.realisation_id))),
            "epochs_run": len(log), "best_epoch": int(np.argmin([r["val_loss"] for r in log])),
            "best_val_loss": best, "train_seconds": wall,
            "inference_seconds_all_sets": infer,
            "n_scenarios_predicted": int(sum(len(s.y) for s in sets.values()))}
    _save_preds(name, seed, preds, meta)
    return meta


def train_xgb(name: str, spec: dict, seed: int, n_res: int | None = None) -> dict:
    import xgboost as xgb
    sets = load_all()
    fit, val = _fit_set(sets, "fit", n_res), _fit_set(sets, "val")
    sc = Scaler(spec["features"]).fit(fit)
    Xf, Xv = rows(sc.x(fit)), rows(sc.x(val))
    Yf, Yv = sc.y(fit).reshape(-1, 2), sc.y(val).reshape(-1, 2)
    t0 = time.perf_counter()
    boosters, best_it = [], []
    for j in range(2):
        m = xgb.XGBRegressor(n_estimators=spec["n_estimators"],
                             learning_rate=spec["learning_rate"],
                             max_depth=spec["max_depth"], subsample=spec["subsample"],
                             colsample_bytree=spec["colsample_bytree"],
                             early_stopping_rounds=spec["early_stopping_rounds"],
                             random_state=seed, n_jobs=1, tree_method="hist")
        m.fit(Xf, Yf[:, j], eval_set=[(Xv, Yv[:, j])], verbose=False)
        boosters.append(m)
        best_it.append(int(m.best_iteration))
    wall = time.perf_counter() - t0
    preds = {}
    t1 = time.perf_counter()
    for n, s in sets.items():
        X = rows(sc.x(s))
        z = np.stack([b.predict(X) for b in boosters], axis=-1).reshape(len(s.y), -1, 2)
        preds[n] = sc.inverse(z)
    infer = time.perf_counter() - t1
    meta = {"model": name, "seed": seed, "spec": spec, "best_iterations": best_it,
            "n_fit_reservoirs": int(len(np.unique(fit.realisation_id))),
            "train_seconds": wall, "inference_seconds_all_sets": infer}
    _save_preds(name, seed, preds, meta)
    return meta


def train_ridge(alphas) -> dict:
    from sklearn.linear_model import Ridge
    sets = load_all()
    fit, val = _fit_set(sets, "fit"), _fit_set(sets, "val")
    sc = Scaler("full").fit(fit)
    Xf, Xv = rows(sc.x(fit)), rows(sc.x(val))
    Yf, Yv = sc.y(fit).reshape(-1, 2), sc.y(val).reshape(-1, 2)
    scores = {a: float(np.mean((Ridge(alpha=a).fit(Xf, Yf).predict(Xv) - Yv) ** 2))
              for a in alphas}
    a = min(scores, key=scores.get)
    m = Ridge(alpha=a).fit(Xf, Yf)
    preds = {n: sc.inverse(m.predict(rows(sc.x(s))).reshape(len(s.y), -1, 2))
             for n, s in sets.items()}
    meta = {"model": "ridge", "seed": 0, "alpha": a, "val_mse_by_alpha": scores}
    _save_preds("ridge", 0, preds, meta)
    return meta


def train_mean() -> dict:
    sets = load_all()
    mu = _fit_set(sets, "fit").y.mean(0)
    preds = {n: np.broadcast_to(mu, s.y.shape).copy() for n, s in sets.items()}
    meta = {"model": "mean", "seed": 0}
    _save_preds("mean", 0, preds, meta)
    return meta


def load_preds(model: str, seed: int) -> dict:
    z = np.load(RES / "predictions" / model / f"seed{seed}.npz")
    return {k: z[k].astype(float) for k in SETS}
