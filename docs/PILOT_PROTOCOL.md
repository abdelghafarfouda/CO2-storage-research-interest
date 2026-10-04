# Pilot protocol: pressure-based detection of a wrong outer-boundary assumption

**Status: Planned experiment. Draft for freezing; nothing in this protocol has been run.**

This protocol belongs to §8 of the [research proposal](RESEARCH_PROPOSAL.md). It is written so that it can be frozen before any new calibration or test simulation exists. To freeze it: (1) fill in the two seeds and the reference commit in §9, (2) commit and push this file, and (3) record the frozen commit hash in the pilot's results. After the freeze, any change is made as a dated addendum that states whether it was written before or after the affected data existed, as in the SubsurfaceML protocol addendum.

## 1. Question and hypotheses

**Question.** Can post-shut-in pressure observations reveal that a forecast model wrongly assumes a sealed outer boundary, at a controlled false-alarm rate? And how reliable are whole-trajectory pressure forecasts when that assumption holds and when it does not?

Proposal hypotheses tested: **H2** (systematic post-shut-in error under a boundary shift, with no change in the inputs), **H3** (detection at a false-alarm rate of at most 0.05, with power rising with observation duration and diffusion time) and **H4** (in-distribution coverage holds, coverage under shift does not, and band width does not signal it).

## 2. Reference model and controlled mismatch

- **Simulator:** SubsurfaceML layered radial IMPES model at merge commit `68e532f` of [`manchester-msc-projects`](https://github.com/abdelghafarfouda/manchester-msc-projects/tree/68e532f/advanced-subsurface-modelling/SubsurfaceML), or a later descendant whose simulator modules are verified identical. Configuration `config/study.yaml`: four layers, common bottom-hole pressure, 5 years of injection in four rate periods, then 5 years of shut-in. The development prior is used unchanged.
- **Reference case ("assumptions hold"):** `outer_bc: closed`.
- **Controlled mismatch ("wrong assumption"):** the same reservoir and schedule with `outer_bc: constant_pressure`, which holds the outer radius at the initial pressure. Nothing else changes.
- **Forecasters and detectors always assume a sealed boundary.** They see only inputs known before simulating (reservoir description and schedule), as in SubsurfaceML, and the synthetic observations.
- Simulator outputs are model-dependent reference results. They describe the layered model only.

## 3. Quantities

| Quantity | Definition | Notes |
|---|---|---|
| Peak build-up | `dp_bh_max`: maximum bottom-hole overpressure while injecting | Unchanged SubsurfaceML definition |
| Mean overpressure | pore-volume-weighted mean of `p − p_init` over all cells, at shut-in + {0.25, 1, 2, 5} years | New output (§4) |
| Relaxation time t½ | first time after shut-in at which the well-side overpressure falls below `(Δp_ws(t_s) + Δp̄(t_end)) / 2`, where `Δp_ws(t_s)` is the well-side overpressure at shut-in and `Δp̄(t_end)` is the mean overpressure at the last report time | Defined only if `Δp_ws(t_s) − Δp̄(t_end) ≥ 0.05 MPa` and the half level is reached before `t_end`. Otherwise "not defined", counted and reported separately |
| Plume radius r95 | radius holding 95 % of free-phase CO₂, at shut-in and at `t_end` | Layered model only. Grid error about 4 %; model-form error not converged (proposal §5.2) |

Not forecast: dissolved or trapped mass (not modelled), up-dip migration (no dip), and CO₂ outflow. An open boundary does not by itself produce outflow, and zero outflow is not evidence of a defect. Outflow is recorded only as the domain-size flag (above 0.1 % of injected mass).

## 4. Adaptations before predicting trajectories

Each adaptation is implemented in this repository, not in SubsurfaceML, by wrapping the pinned simulator. Each gets a known-answer test before any pilot data are generated.

| # | Adaptation | Known-answer test |
|---|---|---|
| A1 | Record the pore-volume-weighted mean pressure at every report time | Sealed single-phase tank: mean overpressure equals injected mass / (ρ c_t V_p) to solver tolerance |
| A2 | Report monthly for 24 months after shut-in, then quarterly | Re-simulating 8 development cases reproduces the stored quarterly series at the shared times (relative difference below 1e-6) |
| A3 | Use the shut-in pressure diagnostic (`p_bh` during shut-in: the productivity-weighted pressure of a zero-net-rate wellbore; not a physical gauge reading) as the primary synthetic "well-side" observable, an **idealised proxy** for a gauge | In a sealed case it converges to the mean pressure after relaxation. Passing this test is required before the proxy is interpreted as a gauge reading. If it fails, the failure is recorded before calibration data exist, and pressure detection is run only as the separate idealised-observation experiment of §6 |
| A4 | Trajectory version of the SubsurfaceML reduced-order model: pseudo-steady-state tanks evaluated through the piecewise-constant schedule; after shut-in, well-side pressure set to the tank pressure | Reproduces the frozen reduced-order peak on development cases exactly; equals material balance after shut-in in a single-layer sealed tank |
| A5 | Reproduction check of any reused E1 simulation under `68e532f` | Relative difference below 1e-6, or the simulation is regenerated |

## 5. Data roles

| Role | Reservoirs | Boundary variants | Seed | Use |
|---|---|---|---|---|
| Development: training and selection | 220 (SubsurfaceML development set; includes the 55 reservoirs E1 tested on) | sealed and open, × 4 schedules = 1,760 runs | 20260909 (existing) | fitting; grouped 5-fold CV for every design choice; detector development |
| Calibration | 100 fresh | sealed only, × 4 schedules = 400 runs | `SEED_CAL` (new; §9) | conformal bands and alarm thresholds **only**. No forecaster or classifier is fitted on calibration reservoirs |
| Independent test | 100 fresh | sealed and open, × 4 schedules = 800 runs | `SEED_TEST` (new; §9) | scored **once**, after the design and thresholds are frozen |

Rules:

- All splits and folds are by **whole reservoir**. A reservoir's schedules and boundary variants are never separated.
- Test data are generated **after** the protocol and the development-stage design addendum (§8) are pushed. Seeds must differ from every seed used before: 20260909, 20261004 (E1), 20261104, 20261105 and 20261106.
- SubsurfaceML's final-test, shift and calibration-check reservoirs are **not** used as pilot test data. They were already scored or used for calibration there, and their time series are not stored.
- E1's held-out reservoirs now train and are never described as independent test data.
- All model fitting, including the D3 classifier, uses development reservoirs only. Calibration reservoirs set bands and alarm thresholds and nothing else.

## 6. Observations

- **Primary observable: the well-side pressure diagnostic** (A3), monthly for 24 months after shut-in. It is an idealised proxy for a well-side gauge, interpreted as a gauge reading only after it passes A3.
- **Mean pressure** is a forecast quantity, not an observation. A real gauge does not measure it.
- **Separate idealised-observation experiment** (only if A3 fails): detection is repeated with noisy mean pressure as the observation, with the same noise settings, windows and sealed calibration runs. Its results are reported in a separate section, with their own conclusions, which are not statements about gauge measurements.
- **Noise:** independent Gaussian with σ = 0.01 MPa (primary). Sensitivity runs use σ = 0.05 MPa, and σ = 0.01 MPa plus a linear drift of 0.01 MPa per year with random sign. One noise realisation per case is drawn from a fixed seed, and the same realisation is used for the sealed and open variants, so that comparisons are paired.
- **Windows:** the first 3, 6, 12 and 24 months after shut-in.

## 7. Forecasters, baselines and detectors

**Forecasters of the sealed-boundary trajectory** (all trained on sealed development runs only):

| ID | Method | Role |
|---|---|---|
| F0 | Training mean per time step | floor |
| F1 | Material balance for mean overpressure; A4 reduced-order trajectory for well-side pressure | physics baseline |
| F2 | Ridge per time step on known inputs plus cumulative injected mass | simple statistical baseline |
| F3 | Trajectory hybrid: `ln Δp(t) = ln Δp_F1(t) + g(x, t)`, g by gradient boosting | primary candidate |
| F4 *(optional)* | Small LSTM (one layer, 64 units) on the same inputs as F2/F3 | answers only: does memory beat a memoryless per-step model with the same inputs and the same tuning budget? Dropped if the development CV shows no difference by rule R1 |
| Peak reference | SubsurfaceML hybrid, frozen at `68e532f` | the peak forecast must be compared with it on the same test reservoirs. Its verified 0.31 MPa RMSE is a peak result, not a trajectory result |

Every learned method gets the same tuning budget: 20 random-search trials, scored by grouped 5-fold CV on the development reservoirs.

**Whole-trajectory bands.** Normalised score per reservoir, `s = max over schedules and report times of |y − ŷ| / σ̂(x, t)`. Here σ̂ is a scale model fitted on development residuals, and `y` is the noisy observation for observed times and the reference value for forecast quantities. The band is `ŷ ± q·σ̂`, with `q` the ⌈(n+1)(1−α)⌉-th smallest calibration score (n = 100 reservoirs). α = 0.10 for the forecast bands. α = 0.05 for detector D2.

**Detectors** (alarm = statistic above a threshold set on the 100 sealed calibration reservoirs for a false-alarm rate of 0.05):

- **D1 material-balance residual:** mean of `(Δp_MB − Δp_obs)/σ` over the last third of the window.
- **D2 band exceedance:** an alarm if any observation in the window leaves the reservoir-calibrated 95 % band of F3 (or of the best forecaster by development CV).
- **D3 statistical classifier:** logistic regression on the ratios of observed overpressure at the end of the window to that at shut-in and at the window midpoint. It is fitted **only on development reservoirs**, using their sealed and open variants. Its threshold is set on the sealed calibration runs. No calibration reservoir is used to fit it.

## 8. Development stage and design addendum

On development data only, by grouped CV: choose the F3 learner settings, the σ̂ model, whether F4 is kept and the D1 window fraction. Record the choices in a dated **design addendum**, then push it **before** `SEED_TEST` data are generated. Development results may be reported, labelled as development results.

## 9. Freeze record (to be completed at the freeze)

| Item | Value |
|---|---|
| SubsurfaceML reference commit | `68e532f` (or verified descendant: ______) |
| `SEED_CAL` | ______ |
| `SEED_TEST` | ______ |
| Protocol commit hash | ______ |
| Design addendum commit hash | ______ |

## 10. Test-stage outputs (scored once)

1. **Accuracy (sealed test runs):** RMSE and worst under-prediction for each quantity, injection and post-shut-in separately. Paired reservoir-bootstrap intervals (2,000 resamples) for F3 against F1 and F2, and against the frozen SubsurfaceML hybrid for the peak.
2. **Coverage:** the share of test reservoirs whose whole trajectories lie inside the 90 % band, with a Clopper–Pearson interval, for sealed runs (in distribution) and open runs (shift, H4), with mean band width.
3. **Detection:** false-alarm rate (sealed runs) and power (open runs) for D1–D3, by window and noise setting, with Clopper–Pearson intervals. Power is also shown against the dimensionless diffusion time `k t / (φ μ c_t r_e²)`.
4. **Relaxation time:** the share of cases where it is defined, and the error where it is defined.
5. **Confounding:** properties of the sealed reservoirs that raised alarms.
6. **Outcome statement for H2, H3 and H4:** supported, not supported or inconclusive, by the rules of proposal §7.6.

## 11. Pre-declared follow-ups

- **Power of 1 in the first window for every detector:** add graded mismatches (constant-pressure boundary at 2 r_e and 4 r_e) in a new protocol version, with new test seeds.
- **Power near the false-alarm rate:** report the pilot as a negative result for pressure-only detection, and move the question to Stage 2 (pressure plus seismic).
- **A3 fails:** the well-side proxy is not interpreted as a gauge reading. Pressure detection is reported only from the separate idealised-observation experiment of §6, and its conclusions are limited to idealised observations.

## 12. Next stage (not part of this pilot)

- **Gravity model:** vertical-convergence check of the SubsurfaceML r–z model (5, 10 and 20 rows per layer; k_v/k_h 0.01, 0.1 and 1) before it serves as a plume benchmark.
- **Seismic detectability:** the Notebook 04 chain applied to reference saturation maps, and whether seismic adds to pressure.
- **Later extension:** OPM Flow on SPE11-type cases.

## 13. Reproduction

The pilot's code will live in `experiments/pilot_boundary_detection/`. It will contain a pinned environment, one script per stage (`adapt_and_test`, `generate`, `develop`, `calibrate`, `test`), and a manifest of every data file with its SHA-256 and seed. Expected runtime is a few hours on a 4-core CPU (proposal §10). No part of this has been written or run yet.
