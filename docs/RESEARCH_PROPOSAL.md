# Reliable CO₂ Storage Forecasting and Monitoring

**Research proposal: consolidated draft, October 2026.**

> **About this document.** This is a new consolidated draft. It was written from the material in this repository and from the completed SubsurfaceML project (merge commit [`68e532f`](https://github.com/abdelghafarfouda/manchester-msc-projects/tree/68e532f/advanced-subsurface-modelling/SubsurfaceML)). The earlier proposal draft v0.6.3, which the notebooks cited, is not in this repository and was not available when this draft was prepared, so this is not a revision of that text. Where the notebooks use labels from that draft (WP1–WP4, P1–P4, M1–M3, R1–R5, U1–U4), Appendix B maps them to this document.
>
> **Status labels.** Every piece of evidence is marked with one of three labels: **Verified result** (obtained under a protocol frozen before the test data existed), **Illustrative demonstration** (runs on toy data, a textbook solution or an untrained network; not a finding) and **Planned experiment** (not yet done). No experiment proposed here has been run. The settings in this document are **planned settings**. They and the evaluation protocol will be frozen before any new test data are generated or inspected.

## Contents

1. [Summary](#1-summary)
2. [Problem, motivation and research gap](#2-problem-motivation-and-research-gap)
3. [Research question, sub-questions and hypotheses](#3-research-question-sub-questions-and-hypotheses)
4. [One workflow for Cases A, B and C](#4-one-workflow-for-cases-a-b-and-c)
5. [Quantities, models, data and provenance](#5-quantities-models-data-and-provenance)
6. [Methods](#6-methods)
7. [Evaluation](#7-evaluation)
8. [The first pilot](#8-the-first-pilot)
9. [Staged work plan](#9-staged-work-plan)
10. [Feasibility and computing budget](#10-feasibility-and-computing-budget)
11. [Limitations and risks](#11-limitations-and-risks)
12. [Proposed contribution](#12-proposed-contribution)
13. [Existing evidence and its status](#13-existing-evidence-and-its-status)
- [References](#references)
- [Appendix A: Planned settings and their rationale](#appendix-a-planned-settings-and-their-rationale)
- [Appendix B: Labels used in the notebooks](#appendix-b-labels-used-in-the-notebooks)

---

## 1. Summary

**Question.** How reliably can we forecast reservoir pressure and CO₂ plume behaviour during injection and after shut-in, and can pressure and seismic observations reveal incorrect modelling assumptions?

**Why it matters.** Decisions about a storage site rest on forecasts made before most of the observations exist: how much can be injected without exceeding a pressure limit (Case A), which injection schedule to use (Case B), and whether the monitoring data agree with the model on which those decisions were based (Case C). In closed and semi-closed formations, pressure build-up rather than pore volume often limits capacity (Zhou et al., 2008; Birkholzer et al., 2009). The outer hydraulic boundary decides whether overpressure stays in the formation or dissipates after shut-in. This assumption is uncertain, and a forecast that is wrong about it can look precise.

**Approach.** One workflow links the three cases. A verified reference simulator defines the quantities. Fast forecasters, from material balance to hybrid physics–machine-learning models, predict whole trajectories, with uncertainty bands calibrated by reservoir. Synthetic pressure observations, and later seismic observations, are then tested against those bands to detect a deliberately wrong assumption at a controlled false-alarm rate. Each error source is measured separately: discretisation, model form, forecaster and observation model.

**First step.** A small pilot (§8; full protocol in [`PILOT_PROTOCOL.md`](PILOT_PROTOCOL.md)) asks whether post-shut-in pressure reveals a wrong outer-boundary assumption. Forecasts assume a sealed compartment, while the synthetic "truth" has an open outer boundary. The pilot builds on the verified SubsurfaceML simulator and its reservoir-grouped evaluation design. It is a **planned experiment** and has not been run.

**Contribution sought.** The aim is a reproducible, protocol-frozen benchmark of forecast reliability through injection and shut-in, and of the calibrated detectability of a wrong boundary assumption, compared with classical material-balance and well-test baselines (§12). Whether this adds to existing work will be established by a structured literature review and by the comparison with those baselines. Novelty is not assumed.

## 2. Problem, motivation and research gap

### 2.1 The engineering problem

During injection, overpressure builds up near the well and spreads through the formation. After shut-in, the near-well overpressure relaxes. Where it settles depends on the boundary. In a sealed compartment it settles at a level set by material balance, the injected mass over the compressible pore volume. With an open boundary it decays towards the initial pressure. The CO₂ plume keeps moving after shut-in, mainly by buoyancy. Three decisions depend on forecasting these processes:

- **Case A, storage assessment:** the largest rate and duration that keep the forecast pressure below an assumed limit, with stated uncertainty.
- **Case B, operational decisions:** ranking injection schedules by injected mass and pressure margin.
- **Case C, monitoring and model checking:** deciding whether gauge and seismic data are consistent with the forecast model, or whether they reveal a wrong assumption.

### 2.2 What is known

- **Pressure-limited capacity.** Analytical and numerical studies show that boundary conditions and compartment size control pressure build-up and capacity (Zhou et al., 2008; Birkholzer et al., 2009).
- **Boundary detection from pressure.** Pressure-transient analysis has long identified boundaries from the time behaviour of pressure and its derivative (Bourdet et al., 1983; Horne, 1995). Material balance gives the stabilised pressure of a closed system. These classical methods are the baselines any new detector must beat.
- **Surrogate forecasting.** Deep-learning surrogates for multiphase flow and CO₂ storage forecast saturation and pressure maps (Mo et al., 2019; Tang et al., 2020; Wen et al., 2022). They are usually judged by accuracy against the simulator they were trained on, and often on a random split of cases rather than of geological realisations.
- **Calibrated uncertainty.** Split-conformal prediction gives distribution-free coverage for exchangeable data (Vovk et al., 2005; Lei et al., 2018), and it extends to whole functions, here trajectories (Lei et al., 2015). Deep ensembles give a spread with no coverage guarantee (Lakshminarayanan et al., 2017).
- **Model checking.** Comparing observations with a model's predictive distribution is a standard way to test a model (Gelman et al., 1996). Model discrepancy is a recognised part of calibrating computer models (Kennedy and O'Hagan, 2001).
- **Seismic monitoring.** Time-lapse seismic detects CO₂ plumes at Sleipner (Furre et al., 2017). Pressure and saturation effects can be separated only partly (Landrø, 2001; Grude et al., 2013). Thin layers below the tuning thickness are poorly resolved.
- **Benchmarks.** The SPE11 comparative solution project defines CO₂ storage benchmark cases with mobile, immobile and dissolved CO₂ (Nordbotten et al., 2024). OPM Flow is an open-source simulator able to run them (Rasmussen et al., 2021).

### 2.3 The specific gap

The components above exist separately. What appears to be missing, subject to confirmation by the literature review in Stage 0, is an evaluation that does all of the following together:

1. tests forecasts of **whole trajectories through injection and shut-in**, rather than single peak values, on **geological realisations held out from all design choices**;
2. **calibrates uncertainty bands by reservoir** and checks their coverage when one assumption is wrong;
3. measures how well **pressure observations, and later seismic observations, detect** a wrong assumption at a **stated false-alarm rate**, against classical material-balance and well-test baselines;
4. reports the **numerical and model-form error of the reference simulator** beside the forecaster's error, so that no forecast is judged more accurate than its reference can show.

## 3. Research question, sub-questions and hypotheses

**Main question.** How reliably can we forecast reservoir pressure and CO₂ plume behaviour during injection and after shut-in, and can pressure and seismic observations reveal incorrect modelling assumptions?

| Sub-question | What answers it |
|---|---|
| **Q1 Reference.** How large are the discretisation and model-form errors of the reference results for each quantity? | Grid refinement and model-level comparison (§7.1); Notebook 01 shows the methods |
| **Q2 Forecast reliability.** How accurate are fast forecasters, and do their reservoir-calibrated whole-trajectory bands reach nominal coverage, before and after shut-in? | Pilot (§8), Stage 2 |
| **Q3 Detection.** Can post-shut-in pressure reveal a wrong outer-boundary assumption at a controlled false-alarm rate? How does that depend on observation duration, noise and reservoir properties? | Pilot (§8) |
| **Q4 Seismic.** What does time-lapse seismic add to pressure for plume quantities and for detecting wrong assumptions? | Stage 2; Notebook 04 shows the methods |
| **Q5 Decisions.** Do the forecasts and alarms change Case A and B decisions compared with the reference? | Stages 1–3 (§7.5) |

**Hypotheses.** Each is testable with the stated measurement. The SubsurfaceML evidence for H1 concerns the layered model only.

- **H1 (reference error).** Threshold-based plume quantities carry much larger discretisation and model-form error than pressure quantities. *Test:* the refinement and model-level differences of §7.1, per quantity. *Existing evidence (Verified result, layered model):* peak build-up changes by a median 0.06 % under refinement, plume radius r95 by 2.7 %, and adding gravity and crossflow changes r95 by a median +88 % (SubsurfaceML).
- **H2 (boundary shift).** A forecaster trained only on sealed-compartment simulations makes systematic errors in post-shut-in pressure when the true boundary is open. Its inputs do not change, so it cannot flag the shift itself. *Test:* the paired error and band coverage on matched closed and open versions of the same test reservoirs.
- **H3 (pressure detection).** Post-shut-in pressure detects an open outer boundary, when a sealed compartment is assumed, at a false-alarm rate of at most 5 %. Detection power rises with observation duration and with the dimensionless diffusion time of the compartment. *Test:* false-alarm rate and detection power with Clopper–Pearson intervals on independent test reservoirs (§7.4).
- **H4 (calibration under shift).** Whole-trajectory bands calibrated by reservoir reach nominal coverage in distribution. They lose coverage under a boundary or shut-in-time shift, and their width does not signal the loss. *Test:* coverage in distribution and under each shift.
- **H5 (seismic).** Time-lapse seismic constrains the plume footprint, but constrains the saturation and thickness of thin layers only weakly. It adds little to pressure for detecting a wrong hydraulic boundary. *Test:* singular values in noise units and the change in detection power when seismic is added (Stage 2).

A hypothesis that the test does not support is reported as such. A negative result for H3 would itself inform Case C monitoring design.

## 4. One workflow for Cases A, B and C

```
 prior over reservoirs ──► reference simulator ──► verified reference results ──► error budget (e_num, e_mf)
  and operating schedules   (§5.2; checks of §7.1)   (trajectories, maps)                    │
                                                          │                                  ▼
                                                          ▼                    forecasters with whole-trajectory
                                                 training / selection /        bands calibrated by reservoir (§6)
                                                 calibration / test sets                     │
                                                 grouped by reservoir (§7.2)                 │
             ┌───────────────────────────────────────────────────────────────────────────────┤
             ▼                                    ▼                                          ▼
   Case A: assessment                  Case B: operation                       Case C: monitoring and model checking
   largest rate/duration within an     rank schedules; every recommended       synthetic observations vs bands;
   assumed pressure limit, with        schedule confirmed by the reference     alarm at a stated false-alarm rate
   bands                               simulator                               when an assumption is wrong
             ▲                                    ▲                                          │
             └────────────── an alarm withdraws trust in the forecasts used by A and B ◄─────┘
```

The same forecasts and bands serve all three cases. Case C closes the loop: an alarm means the assumptions behind the Case A and B forecasts must be revised before those decisions are relied on. The pilot exercises Case C and the pressure quantities of Case A. Case B builds on the schedule screening already verified in SubsurfaceML for the layered model.

## 5. Quantities, models, data and provenance

### 5.1 Forecast quantities

**Pilot quantities.** These are limited to what the reference model supports:

| Quantity | Definition | Support in the reference model |
|---|---|---|
| **Peak pressure build-up** | maximum bottom-hole overpressure while injecting, tracked at every time step | Direct output (`dp_bh_max`); discretisation error median 0.06 % |
| **Mean reservoir overpressure at set post-shut-in times** | pore-volume-weighted mean overpressure of the compartment at shut-in + {0.25, 1, 2, 5} years | Computable from the pressure field; **not stored yet**, so an output adaptation is needed (§8) |
| **Pressure relaxation time** | time after shut-in for the well-side overpressure to cover half the distance from its shut-in value to its end value (definition in [`PILOT_PROTOCOL.md`](PILOT_PROTOCOL.md) §3) | Defined **only where relaxation occurs**, that is, where the drop exceeds a set minimum and the half level is reached within the record. Otherwise it is reported as not defined |
| **Plume radius** r95 | radius holding 95 % of the free-phase CO₂ | Direct output. **Limitations:** the layered model has no gravity or crossflow; adding them changed r95 by a median +88 %, and this estimate grew with vertical resolution, so it is not converged. r95 therefore describes the layered model only |

**Excluded from the pilot.** Dissolved and residually trapped mass (the reference model includes neither), up-dip migration distance (the reference model is radial with horizontal layers) and CO₂ outflow across the model edge as a forecast target. In a sealed compartment outflow is zero by construction. With an open boundary, CO₂ crosses only if the plume reaches it: in a SubsurfaceML physics check with an open boundary, 6 of 10 runs lost CO₂ across the outer radius and 4 did not. So **an open hydraulic boundary does not automatically produce CO₂ outflow, and zero outflow alone is not evidence of a defect**. Pressure, not outflow, is the pilot's evidence about the boundary.

**Later quantities** (Stage 3, with a reference model that supports them): CO₂ mass by state (mobile, immobile, dissolved; Nordbotten et al., 2024), up-dip migration and overpressure at a distant point or below the caprock. A domain-size flag, set when outflow exceeds 0.1 % of the injected mass, marks a model domain too small for a closed-compartment interpretation. It is a check on the set-up, not a forecast target.

### 5.2 Reference simulators

All simulator outputs are **model-dependent reference results**. They describe the model's equations and assumptions, not a real site.

| Model | Physics | Role | Status |
|---|---|---|---|
| **SubsurfaceML layered simulator** (`68e532f`) | Radial IMPES, two-phase CO₂–brine, four horizontal layers with one common bottom-hole pressure; sealed or constant-pressure outer boundary; no gravity, crossflow, capillary pressure, dissolution or residual trapping | Reference for the pilot's pressure quantities | **Verified result:** 21 verification checks, including bottom-hole pressure against the pseudo-steady-state solution; 107 tests |
| **SubsurfaceML radial–vertical (r–z) model** | Adds gravity and vertical crossflow (assumed k_v/k_h = 0.1); otherwise the same | Model-form error of the layered model; candidate plume benchmark | Reduces to the layered model when both are off. Plume radius **not vertically converged** (median +88 % at 5 rows per layer, +101 % at 10 rows on 8 cases), so it **needs a vertical-convergence check before it can serve as a plume benchmark** (Stage 2) |
| **OPM Flow** on SPE11-type cases | Industrial-grade black-oil/CO₂–brine with dissolution, capillarity and 3D geometry | Later extension (Stage 3) | Not installed or run in this project |

Two details of the layered model matter for observations. During shut-in all completions are closed and there is no wellbore crossflow, so the reported bottom-hole pressure is a **diagnostic**: the productivity-weighted pressure a zero-net-rate open wellbore would take, not a physical gauge reading. And with an open outer boundary, the boundary is held at the initial pressure (a Dirichlet condition) at the compartment radius.

### 5.3 Data and provenance

| Data | Origin | Use in this proposal | Status |
|---|---|---|---|
| SubsurfaceML development set: 220 reservoirs × 4 schedules = 880 cases, with time series (seed 20260909) | `results/study/data/` at `68e532f`; `timeseries.csv` SHA-256 `e939de9f…aabf57` | Pilot training and model selection only | Existing. The file is byte-identical to the one the E1 branch used |
| SubsurfaceML final test (100 reservoirs, seed 20261104), shift (60, seed 20261105), calibration check (41, seed 20261106) | Same commit; scalar outputs only, no stored time series | Not used as pilot test data (§8.2) | Existing; already scored for peak build-up |
| E1 branch data: 600 shifted simulations and 8 re-simulations | Unmerged branch `claude/nice-sagan-y3cic1` of this repository, generated with SubsurfaceML `4bccd29` | Development-stage material at most, after a reproduction check | Not merged (§13) |
| New pilot simulations | To be generated with SubsurfaceML `68e532f`, under seeds recorded in the frozen protocol and never used before | Calibration and independent test (§8) | **Planned experiment** |
| Toy data in Notebooks 01–04 | Generated in the notebooks | Illustration only | Illustrative demonstration |
| Sleipner and Smeaheia public datasets | CO₂ data-sharing releases (access and licence to be confirmed) | Plausibility ranges for priors and rock physics only, not history matching | Planned for Stage 3; not obtained |
| SPE11 case definitions | Nordbotten et al. (2024) | Stage 3 benchmark geometry and physics | Planned |

### 5.4 Main assumptions

- Synthetic data from assumed priors (SubsurfaceML: median permeability 30–1000 mD, log-uniform; initial pressure 15 MPa; 40 m total thickness; 5 years of injection in four rate periods, then 5 years of shut-in).
- In the pilot, the forecaster knows the sampled reservoir description and the schedule (as in SubsurfaceML). This is optimistic. Stage 2 relaxes it.
- Pressure limits used in Case A and B examples, such as 9 MPa, are **modelling assumptions** chosen to make the screening bind. They are **not validated fracture-pressure or caprock criteria**, and no safety threshold is proposed here.
- Observation noise models are simple and planned (Appendix A). They are to be checked against specifications of the gauge type assumed.

## 6. Methods

### 6.1 Baselines

Every candidate is compared with the simplest method that could answer the same question, at the same tuning budget:

| Baseline | Quantities | Notes |
|---|---|---|
| **Training mean** per time step | all trajectories | Floor for any learned method |
| **Material balance** (closed tank: mean overpressure = injected mass / (ρ c_t V_p)) | mean overpressure after shut-in | Exact in the limit of a sealed, slightly compressible system; the natural closed-model forecast |
| **SubsurfaceML reduced-order model** (sealed pseudo-steady-state tank per layer, common bottom-hole pressure) | peak build-up; trajectory during injection after adaptation | Designed for the peak. Using it for trajectories needs adaptation: sequential evaluation through the rate periods, and a post-shut-in relaxation term (§8) |
| **SubsurfaceML hybrid** (reduced-order model × learned correction), frozen at `68e532f` | peak build-up | **Verified result:** 0.31 MPa RMSE on 100 fresh test reservoirs. This is a **peak** result and is not evidence of accuracy for whole trajectories |
| **Ridge regression per time step** on known inputs, including cumulative injected mass | all trajectories | Simple statistical baseline |
| **Classical detection statistics:** material-balance residual of the late post-shut-in pressure; pressure-ratio classifier as in Notebook 02 §8 | boundary detection | Well-test baselines (Bourdet et al., 1983; Horne, 1995) |

### 6.2 Candidate forecasting methods

1. **Trajectory hybrid** *(Planned experiment; primary).* The reduced-order or material-balance trajectory times a learned correction per time step, `ln Δp(t) = ln Δp_phys(t) + g(x, t)`, with g by gradient boosting or ridge. This extends the verified peak hybrid of SubsurfaceML to trajectories.
2. **Small LSTM** *(Planned experiment; secondary, optional).* Included only to answer one question: does sequence memory improve post-shut-in pressure forecasts over a memoryless per-step model that gets the same cumulative-mass inputs and the same tuning budget? Development-stage observations on the unmerged E1 branch suggest it may not. If so, that is a useful negative result and the LSTM is dropped.
3. **Recurrent U-Net for maps** *(deferred).* Notebook 03 shows an untrained architecture of this kind. It is deferred until a stage needs spatial outputs, such as plume maps for seismic forward modelling, and the design correction documented in Notebook 03 §6 has been made: inventories derived consistently from the predicted maps, and nondecreasing cumulative outflow if that output is kept.

### 6.3 Observation models

- **Pressure** *(Pilot).* The primary synthetic observable is the reference model's **well-side pressure diagnostic** (§5.2), sampled monthly after shut-in, plus independent Gaussian noise. A drift term is added in a sensitivity run (Appendix A). The diagnostic is an **idealised proxy** for a well-side gauge. It is interpreted as a gauge reading only after it passes the validation test of protocol A3. **Mean reservoir pressure** is a forecast quantity, not an observation. If A3 fails, detection with noisy mean pressure as the observation is run as a **separate idealised-observation experiment** with its own conclusions, which are not statements about gauge measurements (protocol §6 and §11). Observations are generated from the "truth" simulation, never from the forecaster.
- **Time-lapse seismic** *(Stage 2).* The rock-physics and convolution chain of Notebook 04: Gassmann substitution with uniform or patchy mixing, normal-incidence synthetics, RMS amplitude and time shift, with stated noise. It is applied to saturation maps of the reference model. The pressure sensitivity of the dry rock is added before pressure and saturation effects are interpreted.

### 6.4 Detecting an incorrect assumption

A detector compares observations with what the assumed model predicts. It raises an alarm when the discrepancy exceeds a threshold set on calibration reservoirs for a target false-alarm rate. Three detectors are compared:

- **D1, material-balance residual:** the mean shortfall of observed late overpressure below the closed-tank level, standardised;
- **D2, band exceedance:** an alarm if the observed trajectory leaves the forecaster's whole-trajectory band, calibrated by reservoir on noisy observations at level 1 − α, so that the false-alarm rate is controlled by construction when the assumptions hold;
- **D3, simple statistical classifier:** logistic regression on a few summary features of the post-shut-in pressure (as in Notebook 02 §8). It is fitted **only on development reservoirs**, using their sealed and open variants. Its alarm threshold is set on the sealed calibration reservoirs for the target false-alarm rate.

Later, sequential versions such as CUSUM (Page, 1954) can answer *how soon* a wrong assumption is detected.

### 6.5 What each component delivers

| Component (notebook label) | Output |
|---|---|
| Reference checks (WP1, Notebook 01) | `e_num` and `e_mf` per quantity, before and after shut-in |
| Evaluation design (WP2, Notebook 02) | Reservoir-grouped data roles, geological spread `u_geo`, baseline scores, the detector design |
| Forecasters (WP3, Notebook 03) | `e_sur`, coverage of whole-trajectory bands, and a statement of where each forecaster is fit for use. For any map output, the CO₂ inventory is derived from the maps (Notebook 03 §6 design correction), and any separately predicted inventory term is checked against them, with the mismatch reported |
| Monitoring (WP4, Notebook 04) | `e_obs`, detection power and false-alarm rate per observation design, and a tested map of which data constrain which quantities (H5). A value-of-information comparison of monitoring options for Case C |

## 7. Evaluation

### 7.1 Error budget

Each quantity is reported with separate error terms, measured on the same cases:

- `u_geo`: spread of the quantity across the geological prior (the yardstick);
- `e_num = R_h − R_∞`: production-grid reference minus a refined reference (Richardson extrapolation or the finest level; Roache, 1994);
- `e_mf`: difference between model levels, such as the layered model and the r–z model with gravity;
- `e_sur = S − R_h`: forecaster minus reference;
- `e_obs`: effect of observation-model choices such as noise, drift and rock-physics mixing rule.

The forecaster's error against the converged solution is `S − R_∞ = e_sur + e_num`. It is measured only on refined cases. Elsewhere it is estimated, and any verdict that rests on the estimate is reported as provisional.

### 7.2 Independence and data roles

- Every split and every cross-validation fold is **by whole reservoir**. A reservoir's schedules and boundary variants share its geology and stay together.
- Four roles: **training**, **selection** (grouped cross-validation within the development set), **calibration** (bands and alarm thresholds only; no forecaster or classifier is ever fitted on calibration reservoirs) and **independent test** (scored once).
- **Test reservoirs are generated after the protocol is frozen**, with new seeds recorded in the frozen protocol. No reservoir that was used for training or inspected during design is presented as independent test data.
- Shifts change **one factor at a time** and are **paired** with unshifted versions of the same reservoir and schedule (Notebook 02 §5).

### 7.3 Accuracy and uncertainty calibration

- **Accuracy:** RMSE and worst under-prediction per quantity, separately for injection and post-shut-in periods. Comparisons use a paired bootstrap that resamples whole reservoirs (Efron and Tibshirani, 1993).
- **Whole-trajectory bands:** split-conformal with one score per **reservoir**, the largest normalised error over its schedules and report times (Lei et al., 2015, 2018). The band therefore covers a reservoir's whole trajectory, not each point separately.
- **Coverage:** the share of test reservoirs whose whole trajectories lie inside the band, nominal 0.90, with a 95 % Clopper–Pearson interval (Clopper and Pearson, 1934). The target counts as missed only when the whole interval lies below 0.90. Coverage is reported in distribution and under each shift, together with band width.

### 7.4 Detection

- **False-alarm rate:** the share of test reservoirs with correct assumptions that raise an alarm. Target at most 0.05, with a Clopper–Pearson interval.
- **Detection power:** the share of test reservoirs with the wrong assumption that raise an alarm, overall and by observation window (3, 6, 12 and 24 months after shut-in), noise level and dimensionless diffusion time of the compartment.
- **Confounding:** alarms among correct-assumption reservoirs are examined by reservoir property, as in Notebook 02 §8, where low permeability mimicked a fault.

### 7.5 Decision metrics

- **Case A:** agreement of the forecast with the reference on whether a schedule stays within an assumed pressure limit (misses and false exceedances). The limit is an assumption, not a safety criterion.
- **Case B:** whether the forecaster ranks schedules as the reference does, and the injected mass lost relative to the reference's best schedule, with every recommendation confirmed by the reference simulator.
- **Case C:** detection power at the controlled false-alarm rate, and the monitoring duration needed to reach a stated power.

### 7.6 Rules for claims

- **R1:** a difference between methods is claimed only if its paired 95 % bootstrap interval excludes zero.
- **R2:** an advantage seen only against the production-grid reference, and smaller than |`e_num`|, is not claimed.
- **R3:** a forecaster is called fit for a quantity only where the 90th percentile of |S − R_∞| over refined test reservoirs is below 0.2 `u_geo` (planned setting, Appendix A). A verdict that rests on the error estimate, or on a shift without refined cases of that shift, is reported as provisional.
- **R4:** where `e_mf` dominates, model choice is reported as the controlling uncertainty, and further forecaster accuracy is not claimed to matter.
- **R5:** every term is reported before and after shut-in.

## 8. The first pilot

**Status: Planned experiment.** The full, reproducible protocol is [`PILOT_PROTOCOL.md`](PILOT_PROTOCOL.md). It is drafted to be frozen, with a commit hash and seeds, before any new calibration or test simulation is generated.

### 8.1 Question and design

**Can post-shut-in pressure observations reveal that a forecast model wrongly assumes a sealed outer boundary?** The "truth" for each reservoir and schedule is simulated twice with the layered simulator at `68e532f`: once sealed (the assumptions hold) and once with a constant-pressure outer boundary at the same radius (controlled mismatch). The forecasters and detectors always assume a sealed boundary. Both versions share the reservoir, the schedule and the noise realisation, so the effect of the boundary is measured case by case.

### 8.2 Anchoring to SubsurfaceML `68e532f`, and what carries over from E1

The unmerged E1 pilot on branch `claude/nice-sagan-y3cic1` used the earlier SubsurfaceML commit `4bccd29`. It took the published scalar SVR (1.24 MPa peak RMSE) as its baseline and used the earlier 124/41/55 reservoir split. **It is not merged.** At `68e532f`:

- the 55 reservoirs that E1 tested on were inspected while SubsurfaceML was revised, and **are now training reservoirs**. E1's held-out numbers are therefore development-stage results, not independent test results;
- the scalar baseline is now the verified hybrid (0.31 MPa peak RMSE on 100 fresh test reservoirs). E1's comparisons with the old SVR are obsolete;
- the 880 development time series are **byte-identical** (same SHA-256), and the simulator core modules (`impes.py`, `fluids.py`, `grid.py`, `outputs.py`) are unchanged. The scenario-generation and petrophysics modules changed, so any E1-generated simulation must pass a reproduction check under `68e532f` before reuse.

| E1 material | Status for the pilot |
|---|---|
| Development time series (880 cases) | Valid as training and selection data |
| Code (dataset building, models, conformal evaluation) | Usable as starting material after review |
| Qualitative observations: cumulative-mass inputs make memory unnecessary; raw ensemble spread under-covers; an open boundary leaves every input unchanged | Motivate H2 and H4 and the optional LSTM question. They are **not** verified results |
| Held-out accuracy, coverage and shift numbers | **Need a new evaluation** on fresh test reservoirs |
| Shifted sets built on the old test reservoirs (open boundary, earlier shut-in) | Development data at most, since those reservoirs now train |
| Low-permeability shift set (40 reservoirs) | Inspected, so development data at most, after a reproduction check |

### 8.3 Outputs, adaptations and baselines

- **Outputs:** the four pilot quantities of §5.1.
- **Adaptations before any trajectory is forecast:** (a) record the pore-volume-weighted mean pressure at every report time; (b) report monthly for the first two years after shut-in, not only quarterly, so that relaxation is resolved (planned rationale: the diffusion time φμc_t r_e²/k ranges from about a month to a few years across the prior; it will be computed per reservoir before the freeze); (c) adopt the shut-in pressure diagnostic as the primary synthetic observable, an idealised proxy, and validate it against mean pressure in a sealed tank before interpreting it as a gauge reading (protocol A3); (d) extend the reduced-order model to trajectories (§6.1). Each adaptation gets a known-answer test before use.
- **Baselines:** training mean, material balance, the trajectory-adapted reduced-order model, ridge per step, the frozen SubsurfaceML hybrid for the peak, and detectors D1–D3 (§6.4).

### 8.4 Data roles (planned settings; rationale in Appendix A)

| Role | Reservoirs | Simulations | Source |
|---|---|---|---|
| Training and selection (grouped 5-fold CV) | 220 | 880 sealed, re-run with the new outputs (they must reproduce the stored series) + 880 open | SubsurfaceML development prior and seed 20260909 |
| Calibration (bands and alarm thresholds only; nothing is fitted on it) | 100 | 400 sealed | new seed, fixed at freeze |
| Independent test (scored once) | 100 | 400 sealed + 400 open | new seed, fixed at freeze, generated after the freeze |

Bands and alarm thresholds are calibrated on noisy synthetic observations of the sealed calibration runs, one score per reservoir. Forecasters and the D3 classifier are fitted on development reservoirs only. The test is scored once. Reporting follows §7.3–7.4, with the outcome for each hypothesis stated, including negative outcomes.

### 8.5 Completion criteria

The pilot is complete when the protocol has been frozen and pushed before the new data existed; all adaptations have passed their known-answer tests (if A3 fails, the failure is recorded before calibration data exist, and pressure detection is reported only as the separate idealised-observation experiment); the test has been scored once; every pre-specified metric has been reported with its interval; and the result for H2, H3 and H4 has been stated, whatever it is. A pilot that finds detection trivially easy (every open case detected within a month) or impossible is still complete. §11 gives the follow-up for each case.

## 9. Staged work plan

Durations are indicative and are to be agreed with a supervisor.

| Stage | Content | Deliverables | Completion criteria |
|---|---|---|---|
| **0. Review and freeze** (about 2 months) | Structured literature review: boundary detection from pressure, surrogate forecasting with calibrated uncertainty, CO₂ monitoring design. Confirm or refine the gap (§2.3). Agree planned settings | Review chapter; frozen [`PILOT_PROTOCOL.md`](PILOT_PROTOCOL.md) with commit hash and seeds | Supervisor sign-off; protocol pushed before any new test data exist |
| **1. Pressure pilot** (about 4 months) | §8: adaptations, development experiments, calibration, one-time test | Pilot report with all metrics; code and data with provenance | §8.5 |
| **2. Plume reliability and seismic detectability** (about 6 months) | Vertical-convergence check of the r–z gravity model (rows per layer 5, 10, 20; k_v/k_h sensitivity). If converged, use it as the plume benchmark and measure `e_mf` for plume radius. Seismic detectability of the plume with the Notebook 04 chain; pressure plus seismic detection; uncertain reservoir description in the detector. Decision gate on map outputs, and on the recurrent U-Net with the Notebook 03 design correction | Convergence report; detectability maps (H5); detection with and without seismic; decision note on the U-Net | Convergence demonstrated, or the plume benchmark reported as unconverged with its bracket; H4 and H5 tested |
| **3. Benchmark-scale extension** (about 12 months) | OPM Flow on SPE11-type cases, with verification first. Add dissolved and trapped mass, and up-dip migration, now that the reference supports them. Cases A, B and C at benchmark scale. Public datasets for prior plausibility only | Verified OPM set-up; forecasting and detection results at benchmark scale | Verification checks pass; frozen protocol and one-time test, as in Stage 1 |
| **4. Synthesis** | Thesis chapters, papers, archived code and data | Thesis; released repository | — |

## 10. Feasibility and computing budget

- **Stage 1 runs on a CPU.** The SubsurfaceML full pipeline took 66 minutes on a 4-core virtual machine. That covers more than 1,700 simulations (880 development, 640 fresh test and shift, 215 refinement runs) plus model fitting. The pilot needs about 3,000 simulations of the same model (§8.4), which by extrapolation is a few hours on a similar machine. The estimate will be measured on a sample before the freeze.
- **Existing assets:** a verified simulator with tests and a reservoir-grouped evaluation pipeline (SubsurfaceML); conformal and dataset code on the E1 branch; illustrative checks in Notebooks 01–04.
- **Stage 2:** the r–z model ran 60 simulations in 16 minutes, so a convergence study at up to 20 rows per layer on a few dozen cases is within a workstation budget.
- **Stage 3** needs an OPM Flow installation and probably access to a computing cluster for SPE11-scale ensembles. The size of those ensembles is set by learning curves (Notebook 02 §6) and the available allocation.

## 11. Limitations and risks

**Limitations.**

- All data are synthetic, from assumed priors. There is no field validation, and simulator outputs are model-dependent reference results.
- The pilot's reference model is radial, with horizontal layers and one well. It has no gravity, crossflow, capillary pressure, dissolution, residual trapping or geomechanics. Its plume results describe the layered model only.
- The forecaster knows the true reservoir description in the pilot, which favours detection. Stage 2 removes this.
- A sealed compartment and a constant-pressure boundary are two end-members. Real boundaries are partly open, and faults may be partly sealing.
- Convolutional seismic synthetics give upper bounds on detectability (1D, normal incidence, fixed wavelet).
- Vertical-equilibrium models, which assume CO₂ and brine have already separated vertically, are not used as the reference because that assumption fails early in injection.
- No validated fracture-pressure or caprock criterion is proposed. Pressure limits in examples are assumptions.

**Risks and responses.**

| Risk | Response |
|---|---|
| Detection is trivially easy for the end-member mismatch | Add graded mismatches (boundary at a larger radius, or a boundary transmissibility multiplier) as a pre-declared follow-up |
| Detection fails for low-permeability reservoirs (slow diffusion) | Report power against dimensionless diffusion time; this is itself a monitoring-design result |
| The well-side pressure diagnostic fails its validation (protocol A3) | Do not interpret it as a gauge reading. Run detection with noisy mean pressure as a separate idealised-observation experiment, with separate conclusions that do not describe gauge measurements |
| The r–z model does not converge vertically | Report the plume benchmark as bracketed and unconverged; move plume benchmarking to OPM Flow |
| The literature review finds the gap already filled | Narrow the contribution to what remains open, for example the false-alarm-controlled comparison or the seismic increment |
| Computing for Stage 3 is unavailable | Reduce ensemble sizes guided by learning curves; keep Stages 1–2 self-contained |

## 12. Proposed contribution

The intended contribution is concrete and checkable:

1. **A reproducible benchmark protocol** for forecasting pressure and plume quantities through injection and shut-in. It has reservoir-grouped roles, test data generated after the protocol is frozen, whole-trajectory bands calibrated by reservoir, and an error budget that separates numerical, model-form, forecaster and observation error.
2. **Measured detectability of a wrong boundary assumption** from post-shut-in pressure at a controlled false-alarm rate. Forecast-band detectors are compared with material-balance and well-test baselines, and power is mapped against observation duration, noise and diffusion time.
3. **Measured added value of time-lapse seismic** over pressure for plume quantities and for model checking (Stage 2).
4. **Open code and data** with provenance for every result.

No component (conformal bands, hybrid physics–ML models, pressure-transient analysis, Gassmann substitution) is claimed as new. Whether their combination and the resulting evidence add to existing work will be established by the Stage 0 review and by the baseline comparisons. If a simple baseline matches the learned methods, that will be reported as the finding.

## 13. Existing evidence and its status

| Evidence | Label | Where |
|---|---|---|
| Layered simulator verification (21 checks, 107 tests); peak build-up hybrid with 0.31 MPa RMSE on 100 fresh test reservoirs (published approach retrained: 0.70 MPa; ΔRMSE 95 % CI [−0.63, −0.18]); measured coverage 95 % of cases and 86 % of whole reservoirs at nominal 90 % (not a guarantee; 97 % and 91 % after recalibration on 41 fresh reservoirs); lower-permeability shift RMSE 1.95 MPa; discretisation and model-form errors | **Verified result** (peak build-up only, layered model) | [SubsurfaceML at `68e532f`](https://github.com/abdelghafarfouda/manchester-msc-projects/tree/68e532f/advanced-subsurface-modelling/SubsurfaceML) |
| Known-answer pressure checks, grid refinement, Richardson extrapolation, seeded mass-balance defect | Illustrative demonstration | [Notebook 01](../notebooks/01_reference_simulation_checks.ipynb) |
| Reservoir-grouped splits, paired shift design, matched tuning budgets, boundary alarm on an image-well model | Illustrative demonstration | [Notebook 02](../notebooks/02_fair_evaluation_and_boundary_alarm.ipynb) |
| Untrained recurrent U-Net: shapes, bounds and inventory-total constraint, and two bookkeeping checks that expose its physical inconsistency; toy studies of reference choice and whole-trajectory coverage | Illustrative demonstration (**untrained**; no physical consistency claimed) | [Notebook 03](../notebooks/03_untrained_surrogate_architecture_demo.ipynb) |
| Gassmann substitution, thin-layer synthetics, tuning, singular values | Illustrative demonstration | [Notebook 04](../notebooks/04_seismic_detectability.ipynb) |
| E1 trajectory pilot (unmerged branch) | Development-stage exploration; **not a verified result** (§8.2) | branch `claude/nice-sagan-y3cic1` |
| The pilot of §8 and Stages 2–3 | Planned experiment | [`PILOT_PROTOCOL.md`](PILOT_PROTOCOL.md) |

The 0.31 MPa result concerns **peak** pressure build-up only. It is not evidence of accuracy for complete pressure trajectories, for post-shut-in pressure or for plume quantities.

## References

- Birkholzer, J. T., Zhou, Q. & Tsang, C.-F. (2009). Large-scale impact of CO₂ storage in deep saline aquifers: a sensitivity study on pressure response in stratified systems. *International Journal of Greenhouse Gas Control* 3(2), 181–194.
- Bourdet, D., Whittle, T. M., Douglas, A. A. & Pirard, Y. M. (1983). A new set of type curves simplifies well test analysis. *World Oil* 196(6), 95–106.
- Clopper, C. J. & Pearson, E. S. (1934). The use of confidence or fiducial limits illustrated in the case of the binomial. *Biometrika* 26(4), 404–413.
- Efron, B. & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall.
- Furre, A.-K., Eiken, O., Alnes, H., Vevatne, J. N. & Kiær, A. F. (2017). 20 years of monitoring CO₂-injection at Sleipner. *Energy Procedia* 114, 3916–3926.
- Gassmann, F. (1951). Über die Elastizität poröser Medien. *Vierteljahrsschrift der Naturforschenden Gesellschaft in Zürich* 96, 1–23.
- Gelman, A., Meng, X.-L. & Stern, H. (1996). Posterior predictive assessment of model fitness via realized discrepancies. *Statistica Sinica* 6(4), 733–807.
- Grude, S., Landrø, M. & Osdal, B. (2013). Time-lapse pressure–saturation discrimination for CO₂ storage at the Snøhvit field. *International Journal of Greenhouse Gas Control* 19, 369–378.
- Horne, R. N. (1995). *Modern Well Test Analysis: A Computer-Aided Approach*, 2nd edition. Petroway.
- Kennedy, M. C. & O'Hagan, A. (2001). Bayesian calibration of computer models. *Journal of the Royal Statistical Society: Series B* 63(3), 425–464.
- Lakshminarayanan, B., Pritzel, A. & Blundell, C. (2017). Simple and scalable predictive uncertainty estimation using deep ensembles. *Advances in Neural Information Processing Systems* 30.
- Landrø, M. (2001). Discrimination between pressure and fluid saturation changes from time-lapse seismic data. *Geophysics* 66(3), 836–844.
- Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J. & Wasserman, L. (2018). Distribution-free predictive inference for regression. *Journal of the American Statistical Association* 113(523), 1094–1111.
- Lei, J., Rinaldo, A. & Wasserman, L. (2015). A conformal prediction approach to explore functional data. *Annals of Mathematics and Artificial Intelligence* 74(1), 29–43.
- Mo, S., Zhu, Y., Zabaras, N., Shi, X. & Wu, J. (2019). Deep convolutional encoder–decoder networks for uncertainty quantification of dynamic multiphase flow in heterogeneous media. *Water Resources Research* 55(1), 703–728.
- Nordbotten, J. M., Fernø, M. A., Flemisch, B., Kovscek, A. R. & Lie, K.-A. (2024). The 11th Society of Petroleum Engineers Comparative Solution Project: problem definition. *SPE Journal* 29(5), 2507–2524.
- Page, E. S. (1954). Continuous inspection schemes. *Biometrika* 41(1/2), 100–115.
- Rasmussen, A. F., Sandve, T. H., Bao, K., Lauser, A., Hove, J., Skaflestad, B., Klöfkorn, R., Blatt, M., Rustad, A. B., Sævareid, O., Lie, K.-A. & Thune, A. (2021). The Open Porous Media Flow reservoir simulator. *Computers & Mathematics with Applications* 81, 159–185.
- Roache, P. J. (1994). Perspective: a method for uniform reporting of grid refinement studies. *Journal of Fluids Engineering* 116(3), 405–413.
- Tang, M., Liu, Y. & Durlofsky, L. J. (2020). A deep-learning-based surrogate model for data assimilation in dynamic subsurface flow problems. *Journal of Computational Physics* 413, 109456.
- Vovk, V., Gammerman, A. & Shafer, G. (2005). *Algorithmic Learning in a Random World*. Springer.
- Wen, G., Li, Z., Azizzadenesheli, K., Anandkumar, A. & Benson, S. M. (2022). U-FNO — an enhanced Fourier neural operator-based deep-learning model for multiphase flow. *Advances in Water Resources* 163, 104180.
- Zhou, Q., Birkholzer, J. T., Tsang, C.-F. & Rutqvist, J. (2008). A method for quick assessment of CO₂ storage capacity in closed and semi-closed saline formations. *International Journal of Greenhouse Gas Control* 2(4), 626–639.

Method references for the individual demonstrations are listed at the end of each notebook.

## Appendix A: Planned settings and their rationale

These replace the bracketed placeholders of earlier drafts. They are **planned settings**: they may be revised with a supervisor during Stage 0, and they are then frozen with the protocol before any new calibration or test data are generated or inspected. None is a validated safety threshold.

| Setting | Planned value | Rationale |
|---|---|---|
| Nominal whole-trajectory coverage | 0.90, one score per reservoir | Matches SubsurfaceML. With 100 test reservoirs, the Clopper–Pearson interval around an observed 0.90 is about 0.82–0.95, enough to detect a large loss of coverage |
| Target false-alarm rate | ≤ 0.05 per reservoir | Conventional level. With 100 calibration reservoirs the 95th-percentile threshold rests on about five exceedances. The resulting uncertainty is reported, not hidden |
| Calibration and test sizes | 100 fresh calibration reservoirs × 4 schedules, sealed only; 100 fresh test reservoirs × 4 schedules × 2 boundary variants | Same order as SubsurfaceML's fresh test (100). Affordable on a CPU (§10). Reservoir-level intervals of usable width |
| Fit threshold in R3 | 90th percentile of the error below 0.2 `u_geo` | A forecaster error under one fifth of the geological spread is small beside the uncertainty a decision must already carry. To be reviewed against the decision metrics of §7.5 |
| Gauge noise | σ = 0.01 MPa white Gaussian; sensitivity runs at 0.05 MPa and with drift of 0.01 MPa per year | Order of a permanent downhole gauge's stated accuracy, to be checked against the specification of the gauge type assumed. The larger values stand in for unmodelled effects |
| Observation schedule | monthly for 24 months after shut-in; windows 3, 6, 12 and 24 months | The diffusion time φμc_t r_e²/k ranges from about a month to a few years across the prior, so quarterly sampling under-resolves the faster relaxations |
| Relaxation defined only if | drop from shut-in to end value ≥ 0.05 MPa (5σ) and the half level is reached within the record | Avoids defining a time from noise. Otherwise reported as not defined |
| Mean-pressure times | shut-in + 0.25, 1, 2 and 5 years | Early, intermediate and late relaxation; 5 years is the end of the SubsurfaceML record |
| Ensemble size, if an ensemble is used | 5 members | As in Lakshminarayanan et al. (2017) and E1; ensemble spread is not used for coverage without conformal calibration |
| Mass-balance gap for reference checks | relative 1 × 10⁻⁶ | Far above round-off (SubsurfaceML reaches about 10⁻¹³), far below any physical quantity of interest |
| Domain-size flag | outflow above 0.1 % of injected mass | Marks a domain too small for a closed-compartment reading. It is a set-up check, not a defect test (§5.1) |

## Appendix B: Labels used in the notebooks

The notebooks use labels from the earlier draft. They correspond to this document as follows.

| Notebook label | Meaning here |
|---|---|
| WP1 | Reference checks, `e_num` and `e_mf` (§7.1); Stage 2 convergence work and Stage 3 OPM verification |
| WP2 | Evaluation design and baselines (§7.2, §6.1); the pilot's data roles (§8.4) |
| WP3 | Forecasters and calibrated bands (§6.2, §7.3) |
| WP4 | Observation models and detection (§6.3–6.4, §7.4) |
| P1 peak bottom-hole pressure | Pilot quantity: peak pressure build-up |
| P2 average overpressure at shut-in, +5, +10 years | Pilot quantity: mean reservoir overpressure at shut-in + {0.25, 1, 2, 5} years (the reference record ends 5 years after shut-in) |
| P3 overpressure below the caprock / at a distant point | Later quantity (Stage 3) |
| P4 time for overpressure to halve | Pilot quantity: relaxation time, only where relaxation occurs |
| M1 CO₂ mass by state | Later quantity; excluded from the pilot (no dissolution or trapping in the reference) |
| M2 plume footprint | Pilot quantity: plume radius r95, with its limitations |
| M3 up-dip migration | Later quantity; excluded from the pilot (no dip in the reference) |
| R1–R5 | §7.6 |
| U1–U4 usefulness tests | U1 accuracy (R3); U2 added value over the best simpler method at the same budget (§6.1); U3 lower total cost than an equally accurate coarse simulation (§10); U4 same schedule ranking as the reference (§7.5) |
| Cases A, B, C | §2.1 and §4 |
| Hypotheses H1, H2, H4, H5 | §3. The notebooks' uses are consistent with the statements there; H3 is new in this draft |
