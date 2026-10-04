"""Tests for experiment E1:  python -m pytest tests -q   (from the E1 folder)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from e1 import data, evaluate, models  # noqa: E402

PROCESSED = HERE / "data/processed"
have_data = pytest.mark.skipif(not (PROCESSED / "id_study.npz").exists(),
                               reason="run scripts/build_dataset.py first")


# --- data ------------------------------------------------------------------
def _toy_frame():
    return pd.DataFrame({"k_median_mD": [100.0], "V_DP": [0.5], "phi_mean": [0.2],
                         "h_total_m": [50.0], "r_e_m": [2000.0], "n_g": [2.0],
                         "n_a": [3.0], "krg0": [0.4], "S_ar": [0.25], "mu_g_cP": [0.05],
                         "rho_g": [700.0], "V_DP_layers": [0.3], "q_ref_kg_s": [5.0],
                         "endpoint_mobility_ratio": [5.0]})


def test_cumulative_mass_and_tank_pressure():
    sc = _toy_frame()
    t = 0.25 * np.arange(1, 41)
    q = np.where(t <= 5.0, 4.0, 0.0)[None, :]
    d = data.dynamic_array(sc, q, t)
    col = {c: i for i, c in enumerate(data.DYN_ALL)}
    m_end = 4.0 * 5.0 * data.YEAR
    assert d[0, 19, col["cum_mass_scaled"]] * 1e9 == pytest.approx(m_end, rel=1e-12)
    assert np.all(d[0, 20:, col["cum_mass_scaled"]] == d[0, 19, col["cum_mass_scaled"]])
    vp = np.pi * 2000.0 ** 2 * 50.0 * 0.2
    assert d[0, 19, col["dp_tank_MPa"]] == pytest.approx(
        m_end / (700.0 * data.C_T * vp) / 1e6, rel=1e-12)
    assert np.all(d[0, 20:, col["injecting"]] == 0) and np.all(d[0, :20, col["injecting"]] == 1)


def test_target_transform_round_trip():
    y = np.random.default_rng(0).uniform([0, 0], [30, 2000], size=(5, 40, 2))
    assert np.allclose(data.Scaler.iy(data.Scaler.ty(y)), y)


def test_no_cumulative_set_has_no_history_features():
    assert not {"cum_mass_scaled", "dp_tank_MPa", "log_r_vol"} & set(
        data.FEATURE_SETS["no_cumulative"])


@have_data
def test_partitions_follow_the_published_split():
    s = data.load_set("id_study")
    rec = json.loads((PROCESSED / "dataset_record.json").read_text())["sets"]["id_study"]
    by = {p: set(s.realisation_id[s.partition == p]) for p in np.unique(s.partition)}
    assert {p: len(v) for p, v in by.items()} == {"fit": 99, "val": 25, "calib": 41, "test": 55}
    assert sum((s.partition == p).sum() for p in ("fit", "val")) == 496
    assert (s.partition == "calib").sum() == 164 and (s.partition == "test").sum() == 220
    names = list(by)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert not by[a] & by[b], f"reservoir in both {a} and {b}"
    assert rec["scenarios"] == 880


@have_data
def test_shift_sets_are_paired_with_the_test_scenarios():
    test = data.load_set("id_study")
    test = test.subset(test.partition == "test")
    for name in ("shift_shutin", "shift_openbc"):
        s = data.load_set(name)
        assert list(s.scenario_id) == list(test.scenario_id)
        assert np.allclose(s.static, test.static)
    low = data.load_set("shift_lowk")
    assert 10 ** low.static[:, 0].max() <= 30.0 < 10 ** test.static[:, 0].min() + 1e-9


# --- models ----------------------------------------------------------------
def test_lstm_is_causal_and_mlp_is_local():
    torch.manual_seed(0)
    x = torch.randn(3, 40, 12)
    x2 = x.clone()
    x2[:, 25:, :] += 1.0
    lstm, mlp = models.SeqLSTM(12, 16), models.StepMLP(12, 16, 2)
    with torch.no_grad():
        assert torch.allclose(lstm(x)[:, :25], lstm(x2)[:, :25])
        assert not torch.allclose(lstm(x)[:, 25:], lstm(x2)[:, 25:])
        assert torch.allclose(mlp(x)[:, :25], mlp(x2)[:, :25])


# --- evaluation ------------------------------------------------------------
def test_conformal_quantile_is_the_finite_sample_rank():
    s = np.arange(1, 20)                       # n = 19
    assert evaluate.conformal_quantile(s, 0.1) == 18.0
    assert evaluate.conformal_quantile(np.arange(5), 0.1) == float("inf")


def test_conformal_band_covers_exchangeable_trajectories():
    rng = np.random.default_rng(1)
    cover = []
    for rep in range(200):
        y = rng.normal(size=(300, 40, 2))
        mu, sd = np.zeros_like(y), np.ones_like(y)
        g = np.arange(300)
        tc = evaluate.TrajectoryConformal(0.1, 0.0).fit(mu[:150], sd[:150], y[:150], g[:150])
        cover.append(tc.coverage(mu[150:], sd[150:], y[150:], g[150:], 0)["coverage"])
    assert 0.885 <= np.mean(cover) <= 0.93


def test_clopper_pearson_and_auroc():
    assert evaluate.clopper_pearson(0, 10)[0] == 0.0
    lo, hi = evaluate.clopper_pearson(90, 100)
    assert lo < 0.9 < hi
    assert evaluate.auroc([0, 1, 2], [3, 4]) == 1.0


def test_bootstrap_of_identical_errors_is_zero():
    e = np.random.default_rng(0).uniform(size=40)
    r = evaluate.reservoir_bootstrap(e, e, np.repeat(np.arange(10), 4), 200, 0)
    assert r["diff"] == 0.0 and r["ci95"] == [0.0, 0.0] and not r["excludes_zero"]


# --- reproducibility of the saved results ----------------------------------
@have_data
@pytest.mark.skipif(not (HERE / "results/checkpoints/lstm/seed0.pt").exists(),
                    reason="run scripts/run_training.py first")
def test_saved_lstm_checkpoint_reproduces_saved_predictions():
    ck = torch.load(HERE / "results/checkpoints/lstm/seed0.pt", weights_only=False)
    net = models.build_net(ck["spec"], ck["n_in"])
    net.load_state_dict(ck["state_dict"])
    net.eval()
    sc = data.Scaler(ck["spec"]["features"])
    for k, v in ck["scaler"].items():
        if k != "feature_set":
            setattr(sc, k, np.asarray(v))
    s = data.load_set("id_study")
    with torch.no_grad():
        p = sc.inverse(net(torch.from_numpy(sc.x(s))).numpy())
    saved = np.load(HERE / "results/predictions/lstm/seed0.npz")["id_study"]
    assert np.allclose(p, saved, rtol=1e-4, atol=1e-4)
