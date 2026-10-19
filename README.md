# Reliable CO₂ Storage Forecasting and Monitoring

**[Read the research proposal →](docs/RESEARCH_PROPOSAL.md)** · [Pilot protocol](docs/PILOT_PROTOCOL.md) · [Entry notebook](notebooks/00_research_overview.ipynb)

## Supervisor overview

**Question.** How reliably can we forecast reservoir pressure and CO₂ plume behaviour during injection and after shut-in, and can pressure and seismic observations reveal incorrect modelling assumptions?

**Why it matters.** In closed and semi-closed formations, pressure build-up often limits how much CO₂ can be stored (Zhou et al., 2008). Whether overpressure stays or dissipates after shut-in depends on the outer hydraulic boundary, an uncertain assumption. A forecast that is wrong about it can still look precise. Three decisions depend on these forecasts:

- **Case A, storage assessment:** the largest rate and duration within an assumed pressure limit;
- **Case B, operational decisions:** ranking injection schedules;
- **Case C, monitoring and model checking:** whether observations agree with the model, or reveal a wrong assumption.

**Approach.** One workflow serves all three cases. A verified reference simulator produces trajectories, with its numerical and model-form errors measured. Fast forecasters, from material balance to hybrid physics–machine-learning models, predict whole trajectories with uncertainty bands calibrated by reservoir. Synthetic pressure observations, and later seismic observations, are tested against those bands to detect a deliberately wrong assumption at a stated false-alarm rate. Computational mathematics, statistics, machine learning, deep learning and seismic methods each enter where the workflow needs them.

**What already exists.**

- **Verified result** (peak pressure build-up only, layered model): in the 2026 [SubsurfaceML project](https://github.com/abdelghafarfouda/manchester-msc-projects/tree/68e532f/advanced-subsurface-modelling/SubsurfaceML) (merge commit `68e532f`), a verified radial CO₂–brine simulator and a hybrid surrogate predict **peak** build-up with 0.31 MPa RMSE on 100 reservoirs generated after the design was frozen. This does not show accuracy for whole trajectories or plume behaviour.
- **Illustrative demonstrations:** four supporting notebooks show the methods on toy problems: reference checks, fair evaluation design, an **untrained** surrogate architecture and seismic detectability.
- **Planned experiment:** everything else, including the first pilot.

**First pilot (planned, not run).** Does post-shut-in pressure reveal that a forecast wrongly assumes a sealed outer boundary? Each reservoir is simulated sealed and with an open boundary. Material-balance, statistical and hybrid forecasters are compared, with whole-trajectory bands calibrated on 100 fresh reservoirs, and detection power and false-alarm rate are measured on 100 further reservoirs generated after the protocol is frozen ([protocol](docs/PILOT_PROTOCOL.md)).

**Proposed contribution.** A reproducible, protocol-frozen benchmark of forecast reliability through injection and shut-in, and of the calibrated detectability of a wrong boundary assumption, compared with classical material-balance and well-test baselines. Novelty is not assumed. It will be established by a literature review and by those comparisons (proposal §12).

**Main limitations.** Synthetic data only, with no field validation. The first reference model is radial and layered, with no gravity, dissolution or trapping, so its plume results describe that model only. Pressure limits used in examples are assumptions, not validated safety criteria.

**Where to start.** Read the [proposal](docs/RESEARCH_PROPOSAL.md) (§1 is a one-paragraph summary, and §13 lists every piece of evidence with its status), then open [`notebooks/00_research_overview.ipynb`](notebooks/00_research_overview.ipynb).

---

## Status labels

Every claim in this repository carries one of three labels.

| Label | Meaning |
|---|---|
| **Verified result** | Obtained under a protocol frozen before the test data existed. The only verified results the proposal uses are in SubsurfaceML. |
| **Illustrative demonstration** | Runs here in seconds on a textbook problem, toy data or an untrained network. It shows how a method or check works; its numbers are not findings. |
| **Planned experiment** | Proposed research; not done yet. |

Notebook sections marked *Background* summarise the author's earlier work that a demonstration builds on. They are context, not results.

## Repository contents

| File | Purpose | Status |
|---|---|---|
| [`docs/RESEARCH_PROPOSAL.md`](docs/RESEARCH_PROPOSAL.md) | The complete research proposal (consolidated draft, October 2026) | — |
| [`docs/PILOT_PROTOCOL.md`](docs/PILOT_PROTOCOL.md) | Reproducible protocol for the first pilot, ready to be frozen | Planned experiment |
| [`notebooks/00_research_overview.ipynb`](notebooks/00_research_overview.ipynb) | Entry point: question, workflow, evidence and planned pilot. Reads repository files only | — |

**Supporting method notebooks.** Each shows one part of the workflow on small examples, followed by how that part will be evaluated in the research.

| Notebook | Role in the workflow | Status |
|---|---|---|
| [01 · Checking the reference simulation](notebooks/01_reference_simulation_checks.ipynb) | Known answers for pressure build-up and fall-off, grid refinement and Richardson extrapolation, a mass-balance check that first catches a seeded defect. Measures the reference error (`e_num`) | Illustrative demonstration |
| [02 · Fair evaluation and a boundary alarm](notebooks/02_fair_evaluation_and_boundary_alarm.ipynb) | Splits by reservoir realisation, a paired shift design, matched tuning budgets, and a pressure alarm for a wrong boundary with its threshold set on separate cases (image-well model) | Illustrative demonstration |
| [03 · Untrained surrogate architecture](notebooks/03_untrained_surrogate_architecture_demo.ipynb) | A recurrent U-Net with **random weights**: shapes, bounds, an inventory-total constraint, and two checks that expose its outputs as physically inconsistent. The design correction is documented, not implemented. Deferred in the proposal | Illustrative demonstration (**untrained**) |
| [04 · Seismic detectability](notebooks/04_seismic_detectability.ipynb) | Gassmann substitution, thin-layer synthetics, tuning and time shift, singular values: what time-lapse seismic can and cannot resolve | Illustrative demonstration |

The notebooks refer to work-package labels WP1–WP4 and other labels from an earlier proposal draft. [Appendix B of the proposal](docs/RESEARCH_PROPOSAL.md#appendix-b-labels-used-in-the-notebooks) maps them.

## Earlier exploratory work

An exploratory pilot of trajectory surrogates (E1) was built on an older SubsurfaceML baseline and test split. It is archived unmerged at commit [`411db4f`](https://github.com/abdelghafarfouda/CO2-storage-research-interest/commit/411db4f42efc2e9319e4709dd10b62d056e7f950), and its numbers are not used as results. The first pilot is anchored to SubsurfaceML `68e532f` instead (proposal §8.2).

## How to run

```bash
git clone https://github.com/abdelghafarfouda/co2-storage-research-interest.git
cd co2-storage-research-interest
python -m venv .venv
source .venv/bin/activate            # on Windows: .venv\Scripts\activate
pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu   # optional: the much smaller CPU-only PyTorch
pip install -r requirements.txt
jupyter lab                          # then open notebooks/00_research_overview.ipynb
```

Notebook 00 uses only the Python standard library and runs in about a second. Notebooks 01–04 run on a CPU in under a minute together. Their random seeds are fixed (mostly 42), so the printed numbers repeat. Only Notebook 03 needs PyTorch. Notebooks 01–04 were last run from a clean kernel with Python 3.11.15 and the package versions in `requirements.txt`. Later edits changed only their text, not their code or outputs. No simulation, training or pilot experiment is run by anything in this repository.

## Key references

Full lists are in the [proposal](docs/RESEARCH_PROPOSAL.md#references) and at the end of each notebook.

- Zhou, Q., Birkholzer, J. T., Tsang, C.-F. & Rutqvist, J. (2008). A method for quick assessment of CO₂ storage capacity in closed and semi-closed saline formations. *International Journal of Greenhouse Gas Control* 2(4), 626–639.
- Nordbotten, J. M., Fernø, M. A., Flemisch, B., Kovscek, A. R. & Lie, K.-A. (2024). The 11th Society of Petroleum Engineers Comparative Solution Project: problem definition. *SPE Journal* 29(5), 2507–2524.
- Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J. & Wasserman, L. (2018). Distribution-free predictive inference for regression. *Journal of the American Statistical Association* 113(523), 1094–1111.
- Horne, R. N. (1995). *Modern Well Test Analysis: A Computer-Aided Approach*, 2nd edition. Petroway.
- Grude, S., Landrø, M. & Osdal, B. (2013). Time-lapse pressure–saturation discrimination for CO₂ storage at the Snøhvit field. *International Journal of Greenhouse Gas Control* 19, 369–378.

## Author and attribution

- **Author.** Abdelghafar Fouda. The verified result above comes from SubsurfaceML (*Surrogate-Assisted Screening of CO₂ Injection Schedules with Simulator Verification*), one of the author's [Personal Computational Projects — 2026](https://github.com/abdelghafarfouda/manchester-msc-projects), informed by the MSc module CHEN60482 *Advanced Subsurface Modelling* (University of Manchester); see [its README](https://github.com/abdelghafarfouda/manchester-msc-projects/blob/main/advanced-subsurface-modelling/SubsurfaceML/README.md).
- **Earlier work.** The notebooks' *Background* sections summarise the author's own earlier exercises, practicals and implementations from MSc study; that earlier work is not reproduced here.
- External methods, software and data are credited where used.

## Reuse status

No open-source licence has been granted for this repository. Third-party software remains under its own licences. SubsurfaceML, in a separate repository, is MIT-licensed.
