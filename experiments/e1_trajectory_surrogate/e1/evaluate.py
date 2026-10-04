"""Metrics, paired comparisons and uncertainty evaluation for E1."""
from __future__ import annotations

import math

import numpy as np
from scipy import stats

INJ = slice(0, 20)      # steps 1-20: t <= 5 yr (training schedules inject until 5 yr)
POST = slice(20, 40)    # steps 21-40: 5 < t <= 10 yr
PHASES = {"all": slice(0, 40), "t<=5yr": INJ, "t>5yr": POST}


def rmse(pred, y, j: int, steps=slice(0, 40)) -> float:
    return float(np.sqrt(np.mean((pred[:, steps, j] - y[:, steps, j]) ** 2)))


def scenario_mse(pred, y, j: int, steps=slice(0, 40)) -> np.ndarray:
    return np.mean((pred[:, steps, j] - y[:, steps, j]) ** 2, axis=1)


def peak_error(pred, y) -> np.ndarray:
    """Predicted minus simulated maximum of dp_bh over the report times [MPa]."""
    return pred[..., 0].max(1) - y[..., 0].max(1)


def reservoir_bootstrap(mse_a, mse_b, groups, n_boot: int, seed: int) -> dict:
    """95 % interval of RMSE_a - RMSE_b, resampling whole reservoirs (the unit
    of exchangeability: the four schedules of a reservoir share its geology)."""
    g = np.asarray(groups)
    uniq = np.unique(g)
    idx = [np.flatnonzero(g == u) for u in uniq]
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_boot)
    for b in range(n_boot):
        pick = np.concatenate([idx[i] for i in rng.integers(0, len(uniq), len(uniq))])
        diffs[b] = math.sqrt(mse_a[pick].mean()) - math.sqrt(mse_b[pick].mean())
    point = math.sqrt(mse_a.mean()) - math.sqrt(mse_b.mean())
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {"diff": point, "ci95": [float(lo), float(hi)],
            "excludes_zero": bool(lo > 0 or hi < 0)}


def conformal_quantile(scores, alpha: float) -> float:
    """Split-conformal quantile: the ceil((n+1)(1-alpha))-th smallest score."""
    s = np.sort(np.asarray(scores, float))
    k = math.ceil((len(s) + 1) * (1 - alpha))
    return float("inf") if k > len(s) else float(s[k - 1])


def clopper_pearson(x: int, n: int, level: float = 0.95) -> list[float]:
    a = (1 - level) / 2
    lo = 0.0 if x == 0 else stats.beta.ppf(a, x, n - x + 1)
    hi = 1.0 if x == n else stats.beta.ppf(1 - a, x + 1, n - x)
    return [float(lo), float(hi)]


def auroc(neg, pos) -> float:
    """P(score of a shifted case > score of an in-distribution case)."""
    neg, pos = np.asarray(neg), np.asarray(pos)
    u = stats.mannwhitneyu(pos, neg, alternative="two-sided").statistic
    return float(u / (len(pos) * len(neg)))


class TrajectoryConformal:
    """Simultaneous (whole-trajectory) band from a deep ensemble.

    Score of a trajectory = max over steps of |y - mu| / (sigma + floor), the
    ensemble spread sigma making the band wider where the members disagree.
    Calibrated on held-out calibration reservoirs, one score per scenario
    (``unit='scenario'``) or the maximum over a reservoir's scenarios
    (``unit='reservoir'``, valid when reservoirs are exchangeable)."""

    def __init__(self, alpha: float, floor_fraction: float):
        self.alpha, self.ff = alpha, floor_fraction

    def _scores(self, mu, sd, y, j):
        return np.max(np.abs(y[..., j] - mu[..., j]) / (sd[..., j] + self.floor[j]), axis=1)

    def fit(self, mu, sd, y, groups, unit: str = "scenario"):
        self.floor = [self.ff * float(np.median(sd[..., j])) for j in range(2)]
        self.unit = unit
        self.q, self.n_cal = [], 0
        for j in range(2):
            s = self._scores(mu, sd, y, j)
            if unit == "reservoir":
                s = np.array([s[groups == g].max() for g in np.unique(groups)])
            self.q.append(conformal_quantile(s, self.alpha))
            self.n_cal = len(s)
        return self

    def band(self, mu, sd, j):
        w = self.q[j] * (sd[..., j] + self.floor[j])
        return mu[..., j] - w, mu[..., j] + w

    def coverage(self, mu, sd, y, groups, j) -> dict:
        lo, hi = self.band(mu, sd, j)
        inside = (y[..., j] >= lo) & (y[..., j] <= hi)
        whole = inside.all(axis=1)
        if self.unit == "reservoir":
            units = np.array([whole[groups == g].all() for g in np.unique(groups)])
        else:
            units = whole
        x, n = int(units.sum()), len(units)
        return {"covered": x, "n": n, "coverage": x / n, "ci95": clopper_pearson(x, n),
                "per_step": inside.mean(0).tolist(),
                "mean_width": {p: float(np.mean((hi - lo)[:, s])) for p, s in PHASES.items()}}


def gaussian_ensemble_coverage(mu, sd, y, j, z: float = 1.6449) -> dict:
    """Coverage of the uncalibrated band mu +/- z sigma (90 % if Gaussian)."""
    inside = np.abs(y[..., j] - mu[..., j]) <= z * sd[..., j]
    whole = inside.all(1)
    return {"whole_trajectory": float(whole.mean()),
            "ci95": clopper_pearson(int(whole.sum()), len(whole)),
            "per_step_mean": float(inside.mean()), "per_step": inside.mean(0).tolist()}
