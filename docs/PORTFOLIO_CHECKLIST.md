# Portfolio improvement checklist

This file tracks the criticisms of the two portfolio repositories and what has
been done about each:

* **MSc** = [manchester-msc-projects](https://github.com/abdelghafarfouda/manchester-msc-projects)
  (the original MSc projects);
* **RI** = this repository (research interest; new work after the MSc).

An item is ticked only when the evidence named next to it is in a repository.
Status words: **Resolved** (evidence in place), **Partly** (some evidence, gap
stated), **Open** (not started), **Blocked** (needs an input named in the row).
New extensions are kept apart from the original MSc work: they live in
`experiments/` of this repository (or are labelled as extensions where they
must sit next to MSc code), and each states what is new.

Last updated: 2026-10-04 (Milestone 1).

## 1. Deep learning

- [x] **D1. One genuine trained-and-evaluated deep-learning experiment on CO₂
  simulation data**, with reservoir-level splits, baselines, multiple seeds,
  held-out accuracy, uncertainty, an out-of-distribution test, controlled
  comparisons of model complexity, and saved data spec, configuration,
  checkpoints, logs, metrics, figures and commands. — **Resolved as a pilot
  (Milestone 1):** [`experiments/e1_trajectory_surrogate`](../experiments/e1_trajectory_surrogate).
  It covers 880 + 600 simulations, the published reservoir split, 5 models ×
  5 seeds, size and input ablations, a learning curve, conformal
  whole-trajectory bands and three shifted test sets, with 11 tests. Broader
  validation (repeated splits, a reference simulator with gravity) is still
  open and stated in its README.
- [ ] **D2. Spatial (field) surrogate** building on the ConvLSTM / U-Net of
  Notebook 03, trained on saturation and pressure fields. — **Open.** The
  stored study data hold only time series and a final saturation profile;
  fields must be re-simulated.

## 2. SubsurfaceML (MSc)

- [ ] **S1. Investigate the error-band coverage** (83–91 % measured against a
  90 % target). — **Open.** Coverage is reported in the MSc README, not
  investigated.
- [ ] **S2. Investigate the schedule-screening failure** on the 40 mD
  reservoir. — **Open.** The failure is reported in the MSc README, not
  analysed.
- [ ] **S3. Test generalisation beyond the training distribution.** —
  **Partly.** E1 applies the published SVR to three shifted sets. Its peak
  RMSE rises from 1.24 MPa to 4.15 MPa at 10–30 mD and to 6.34 MPa with an
  open boundary, and its P5–P95 band then covers 47 % and 1 % of cases. The
  MSc pipeline itself does not yet run such tests.
- [ ] **S4. Extend scalar predictions toward trajectories or fields.** —
  **Partly.** Trajectories are done in E1 (pressure and plume radius over
  40 steps, peak accuracy equal to the scalar SVR); fields remain open (D2).
- [ ] **S5. Missing physics: gravity, capillary pressure, dissolution,
  vertical crossflow**, through verified extensions or comparison with a
  reference simulator. — **Open.** A reference simulator (OPM Flow or MRST)
  is not installed in the current environment; availability to be checked.

## 3. Flash surrogate (MSc)

- [ ] **F1. Reproduce the current results.** — **Partly.** The MSc README
  records a publication check by the author (§7); an independent re-run in
  this programme is still to be done.
- [ ] **F2. Investigate why the physics loss worsens extrapolation.** — **Open.**
- [ ] **F3. Accuracy and computational cost against the numerical solver.** —
  **Partly.** One timing comparison is reported (bisection about 30 ms vs a
  forward pass of 10–24 ms on 12,000 states); no accuracy–cost study.

## 4. Heat conduction (MSc)

- [ ] **H1. A focused scientific extension beyond the coursework exercise.** — **Open.**
- [ ] **H2. Automate the meaningful verification checks.** — **Partly.**
  `run_project.py` runs six checks and exits with status 1 on failure; they are
  not yet run by a test suite or CI.

## 5. Missing evidence

- [ ] **E1. MRST work, the "Gardner" work, the MSc dissertation and other
  CV-linked work.** — **Blocked:** none of these is in either repository.
  Needed from the author: the files (code, reports or notebooks) for each
  item, and the CV text that names them, so each claim can be matched to
  evidence. Nothing will be recreated in their place.

## 6. Skills and reproducibility

- [ ] **K1. Runnable evidence for each skill claimed.** — **Open.** Needs the
  CV skill list (see E1).
- [ ] **K2. Maintainability of the large pipeline** (`SubsurfaceML/src/subsurfaceml/pipeline.py`,
  904 lines). — **Open.**
- [ ] **K3. Tested continuous integration.** — **Open.** Neither repository has
  a CI workflow.
- [ ] **K4. Docker support where appropriate.** — **Open.** No Dockerfile in
  either repository.

## 7. Research interests (RI)

- [ ] **R1. One focused research question connecting computational
  mathematics, machine learning, deep learning and data science.** — **Partly.**
  The README states one question with four work packages; the link between
  them is not yet shown by results.
- [ ] **R2. Replace toy demonstrations with evaluated experiments,
  progressively.** — **Partly.** E1 is the first evaluated experiment (WP2
  and WP3 designs on simulations); the four notebooks are still toy
  demonstrations.
- [ ] **R3. Self-contained explanation connected to verified portfolio
  findings.** — **Open.**

## 8. Presentation

- [ ] **P1. Readable plots with units.** — **Partly.** The six E1 figures
  carry units and direct labels, use a colour-blind-checked palette and were
  inspected after rendering; the existing MSc figures are not yet reviewed.
- [ ] **P2. Concise explanations.** — **Partly:** opening summaries added in
  the open README pull requests (MSc #1, RI #2).
- [ ] **P3. Licensing.** — **Partly.** The three MSc projects are MIT
  licensed; this repository has no licence, which is the author's decision.
- [ ] **P4. Safe repository housekeeping.** — **Open.** Recorded SubsurfaceML
  run files contain absolute machine paths (`/home/claude/work/...`,
  `D:/...`); they are provenance records, so they will be documented rather
  than rewritten.
- [x] **P5. Accurate contribution statements and source credits.** —
  **Resolved in the open README pull requests** (MSc #1, RI #2), awaiting merge.
- [ ] **P6. Distinguish new extensions and results from the original MSc
  work.** — **Partly.** New work goes in `experiments/` of this repository.
  E1 has a "what is new" table and its own contribution statement (produced
  with an AI coding assistant at the author's request). Extensions inside
  the MSc repository are not yet labelled, because none exist yet.

## 9. Research output

- [ ] **O1. Short paper draft around the strongest supported finding**, with
  methods, comparisons, uncertainty, limitations and reproducibility links. —
  **Open**, after the experiments.

## Milestone log

| Milestone | Date | Pull request | Items moved |
|---|---|---|---|
| 0. README review (contribution statements, summaries, split wording) | 2026-10-04 | MSc #1, RI #2 | P2, P5 |
| 1. E1 deep-learning pilot | 2026-10-04 | RI #2 (same branch) | D1 resolved; S3, S4, R2, P1, P6 partly |
