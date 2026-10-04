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

- **Verified result** (peak pressure build-up only, layered model): in the completed [SubsurfaceML project](https://github.com/abdelghafarfouda/manchester-msc-projects/tree/68e532f/advanced-subsurface-modelling/SubsurfaceML) (merge commit `68e532f`), a verified radial CO₂–brine simulator and a hybrid surrogate predict **peak** build-up with 0.31 MPa RMSE on 100 reservoirs generated after the design was frozen. This does not show accuracy for whole trajectories or plume behaviour.
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

Notebook sections marked *Background* summarise the owner's earlier work that a demonstration builds on. They are context, not results.

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

## Corrections made in this revision

- An unsourced field-case statement in Notebook 02 §8, a sealing-fault interpretation attributed to Snøhvit, has been removed. No primary source supporting that wording has been checked. The section now states only the physical point that its image-well model demonstrates.
- The 0.31 MPa SubsurfaceML result is described as a **peak** build-up result, not as accuracy for complete trajectories.
- Notebook 03 is labelled as an untrained architecture demonstration. Claims of physical consistency are withdrawn, and the required design correction is documented in its §6: inventories derived consistently from the maps, and nondecreasing cumulative outflow if that output is kept.
- An open hydraulic boundary is no longer treated as implying CO₂ outflow. Zero outflow alone is not evidence of a defect (proposal §5.1).
- The pilot is anchored to SubsurfaceML `68e532f`. The earlier E1 pilot branch, built on an older baseline and test split, is not merged, and its numbers are not used as results (proposal §8.2).

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

Notebook 00 uses only the Python standard library and runs in about a second. Notebooks 01–04 run on a CPU in under a minute together. Their random seeds are fixed (mostly 42), so the printed numbers repeat. Only Notebook 03 needs PyTorch. Notebooks 01–04 were last run from a clean kernel with Python 3.11.15 and the package versions in `requirements.txt`. In this revision only their text changed, not their code or outputs. No simulation, training or pilot experiment is run by anything in this repository.

## Key references

Full lists are in the [proposal](docs/RESEARCH_PROPOSAL.md#references) and at the end of each notebook.

- Zhou, Q., Birkholzer, J. T., Tsang, C.-F. & Rutqvist, J. (2008). A method for quick assessment of CO₂ storage capacity in closed and semi-closed saline formations. *International Journal of Greenhouse Gas Control* 2(4), 626–639.
- Nordbotten, J. M., Fernø, M. A., Flemisch, B., Kovscek, A. R. & Lie, K.-A. (2024). The 11th Society of Petroleum Engineers Comparative Solution Project: problem definition. *SPE Journal* 29(5), 2507–2524.
- Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J. & Wasserman, L. (2018). Distribution-free predictive inference for regression. *Journal of the American Statistical Association* 113(523), 1094–1111.
- Horne, R. N. (1995). *Modern Well Test Analysis: A Computer-Aided Approach*, 2nd edition. Petroway.
- Grude, S., Landrø, M. & Osdal, B. (2013). Time-lapse pressure–saturation discrimination for CO₂ storage at the Snøhvit field. *International Journal of Greenhouse Gas Control* 19, 369–378.

## Contribution and AI assistance

- **Owner.** Abdelghafar Fouda owns this repository and is named as the author of the SubsurfaceML project, which was developed for the MSc module CHEN60482 *Advanced Subsurface Modelling* at the University of Manchester (see its README).
- **Earlier work.** The notebooks' *Background* sections describe the owner's earlier coursework as stated in the notebooks. The original coursework notebooks are not reproduced here.
- **AI assistance.** AI tools were used to prepare the notebooks and their explanations, as the previous version of this README stated. The SubsurfaceML README states that its October 2026 revision was implemented with an AI coding assistant (Claude, Anthropic) at the author's direction. In this revision, the proposal, the pilot protocol, this README, Notebook 00 and the notebook text changes were drafted by Claude Code, an AI coding assistant, at the owner's request, from the repository material and SubsurfaceML. They need the owner's review before they are shared.
- External methods, software and data are credited where used.

## Reuse status and owner decisions

**Reuse status.** No open-source licence has been granted for this repository. Third-party software remains under its own licences. SubsurfaceML, in a separate repository, is MIT-licensed.

**Decisions only the owner can make** (none blocks reading the proposal):

1. Confirm or correct the contribution statement above, in particular which parts of the notebooks are your own work.
2. Decide what to do with the two open pull requests: [abdelghafarfouda/co2-storage-research-interest#1](https://github.com/abdelghafarfouda/co2-storage-research-interest/pull/1), an earlier README revision now superseded, and [abdelghafarfouda/co2-storage-research-interest#2](https://github.com/abdelghafarfouda/co2-storage-research-interest/pull/2), the E1 pilot, which should not be merged as it stands. Both were left unchanged.
3. Agree the planned settings (proposal Appendix A) with a prospective supervisor, then freeze the pilot protocol before any new test data are generated.
4. Optionally, choose a licence if others should be able to reuse the material.
