# CO₂ storage: predicting pressure and plume migration, and what monitoring can confirm

I want to study how reservoir pressure and CO₂ movement change during injection and after it stops (*shut-in*), how reliably both can be predicted, and how monitoring can check those predictions.

This repository supports my PhD research proposal (draft v0.6.3). It contains four Jupyter notebooks, one for each area of my earlier work: computational mathematics, data science and machine learning, deep learning, and seismic. Each notebook shows, on small worked examples, how I would adapt that work to the CO₂ storage question, how I would test it, and where it could help.

**These are illustrations, not research results.** No reservoir simulation has been run for this project, the deep-learning model is untrained, and every number comes from a textbook problem, toy data or random inputs. The simulation, training and monitoring studies themselves are proposed future work. External methods, software, datasets and any specifically identified supplied material are credited where they are used.

## Repository guide

| File | What it contains |
|---|---|
| [`notebooks/01_computational_mathematics_reference_checks.ipynb`](notebooks/01_computational_mathematics_reference_checks.ipynb) | WP1: checking the reference simulation with known answers, grid refinement and a mass balance |
| [`notebooks/02_data_science_fair_tests.ipynb`](notebooks/02_data_science_fair_tests.ipynb) | WP2: fair tests for a fast model, from splits by realisation to an alarm for a wrong boundary |
| [`notebooks/03_deep_learning_surrogate.ipynb`](notebooks/03_deep_learning_surrogate.ipynb) | WP3: an untrained recurrent U-Net surrogate, its built-in constraints, and how its accuracy and coverage would be judged |
| [`notebooks/04_seismic_monitoring_sensitivity.ipynb`](notebooks/04_seismic_monitoring_sensitivity.ipynb) | WP4: what time-lapse seismic can see of a thin CO₂ layer |
| [`requirements.txt`](requirements.txt) | Package versions used for the last clean run of the notebooks |

The notebooks are saved with their outputs, so they can be read on GitHub without installing anything. To run them yourself, see [Viewing and running the notebooks](#viewing-and-running-the-notebooks).

## The research question

The formal question of the proposal is:

> **How reliably can reservoir pressure and CO₂ plume migration be predicted through injection and after shut-in, and what can pressure and seismic monitoring confirm about those predictions?**

The question matters because decisions about a storage site, such as the injection rate and duration that stay within pressure limits, the choice between injection schedules, and whether monitoring can narrow the forecasts or reveal a wrong boundary (Cases A–C below), rest on forecasts of pressure and of where the CO₂ goes. Those forecasts carry errors from several sources: the simulator's numerical error, uncertainty in the geology, the error of any fast model used in place of the simulator, and the assumptions that link monitoring data to the reservoir. The proposal treats these as separate terms of an *error budget*, each measured on the same quantities, so that a claim about prediction or monitoring can say which error dominates.

Reservoir engineering and physical modelling are the core: pressure build-up and fall-off, a CO₂ inventory that must add up, and the physics of what gauges and time-lapse seismic can see. Each notebook takes one step of the question and one term of the error budget:

| Area | Notebook | Engineering question | Method | Error-budget term |
|---|---|---|---|---|
| Computational Mathematics | [01](notebooks/01_computational_mathematics_reference_checks.ipynb) · WP1 | Is the reference simulation right, and how wrong is it? | Verification: known answers, grid refinement and a mass balance | `e_num`, `e_mf` |
| Data Science and Machine Learning | [02](notebooks/02_data_science_fair_tests.ipynb) · WP2 | Are the tests of a fast model fair, and how much geological uncertainty must a forecast resolve? | Test design: splits by realisation, paired shift cases, matched tuning budgets | `u_geo` |
| Deep Learning | [03](notebooks/03_deep_learning_surrogate.ipynb) · WP3 | Can a fast network (a *surrogate*) replace the simulator, and how is that judged? | An untrained recurrent U-Net with built-in physical constraints; tests of accuracy and coverage | `e_sur` |
| Seismic | [04](notebooks/04_seismic_monitoring_sensitivity.ipynb) · WP4 | What can time-lapse seismic see of a CO₂ layer? | Rock physics, synthetic traces and singular values | `e_obs` |

## How the notebooks connect, and the order to read them

The notebooks are meant to be read in order, 01 to 04, because each builds on the one before:

1. **01** checks the *reference*, the detailed simulation that every fast model is compared with. It defines the numerical error `e_num` and introduces the Theis pressure solution, which 02 reuses; it also lists the singular value decomposition among my methods, which 04 uses.
2. **02** designs the tests that a fast model must pass. It reuses the Theis solution from 01 for a gauge alarm that warns of a wrong boundary, and its design of held-out and shifted cases is the one the surrogate is trained and scored on.
3. **03** builds the surrogate and shows why it must be judged against the refined reference of 01, not only against the simulation it learned from, using the paired comparisons of 02.
4. **04** turns to monitoring. It picks up the question left open by the gauge alarm in 02 (what can seismic add?) and uses the SVD from 01 to ask what the data can and cannot separate.

The terms used throughout (decision quantities P1–P4 and M1–M3, rules R1–R5, usefulness tests U1–U4 and Cases A–C) are listed under [Key terms and rules from the proposal](#key-terms-and-rules-from-the-proposal). It may help to skim that section first and return to it as needed.

Each notebook has the same structure: a short introduction; (1) my work in that area; (2) how it is adapted to the CO₂ problem; (3) the worked examples, each followed by how to read its result and what it means for the PhD; (4) how the work package will be evaluated; (5) assumptions and what has to change; and (6) a short status line with references. Each part carries one of four labels:

| Label | Meaning |
|---|---|
| **My work** | My own earlier work: implementations, completed exercises, analysis and explanations |
| **Proposed adaptation** | What I plan to do in the PhD. Not done yet |
| **Implemented example** | New code written for this repository, run on a textbook or toy problem, or on an untrained network |
| **Evaluated result** | A tested research result. **There are none yet** |

My original notebooks are not reproduced here; the four notebooks are new adaptations of that work.

## Main observations from the worked examples

These come from the implemented examples. They show what each check is for and where I expect the real problem to be hard; the sizes of the effects come from toy inputs and say nothing yet about a real storage site.

- **01, pressure after shut-in.** In the single-phase Theis example, the fall-off in an open aquifer follows the same Horner line for all three compressibilities (0.0726 MPa 20 years after shut-in), while in a closed box the average overpressure stays at its material-balance level (3.0 MPa for c<sub>t</sub> = 10⁻⁹ 1/Pa). In this example the boundary decides whether pressure falls after shut-in.
- **01, convergence.** On a 1D front, the mid-point (c = 0.5) is within 0.001 of the exact position on every grid, but a threshold edge (c = 0.02), like a plume footprint, converges with an observed order of only about 0.6–0.7. The grid-convergence index still brackets the exact answer. A two-measure mass balance agrees to round-off and catches a seeded 0.2 % inflow error.
- **02, splits.** Random row splits give a test error less than half that of splits by realisation (RMSE 1.54 against 3.43), because rows of one realisation share their geology. Testing across shut-in raises the error again (5.33 against 2.16).
- **02, comparisons.** At the same tuning budget, ridge regression is worse than two tree ensembles by a paired bootstrap, but most of its disadvantage comes from a single test realisation (mean difference +0.75, or +0.30 without it).
- **02, alarm.** A gauge alarm for a sealing fault, with its threshold set for 0.90 precision on calibration cases, reaches 0.84 on separate test cases (95 % interval 0.72–0.92) and detects only about half of the faults more than 2.5 km away.
- **03, built-in constraints.** For any weights, the untrained network keeps saturation between 0 and 1, makes the CO₂ inventory add up to the injected mass, and gives zero outflow for a closed boundary. A controlled check shows that the boundary input reaches every cell of its maps. Another check shows what the design does *not* guarantee: with random weights, cumulative outflow falls after shut-in.
- **03, choice of reference.** In a toy with a known discretisation error, a surrogate looks better than a physics estimate against the reference it learned from (RMSE 0.30 against 1.03) but worse against the exact answer (0.85 against 0.61).
- **03, coverage.** Bands calibrated row by row reach 0.895 average coverage but contain only 0.716 of whole trajectories. Bands calibrated on whole trajectories contain 0.901, at about 1.35 times the width.
- **04, rock physics.** A 30 % drop in P-wave velocity means a CO₂ saturation of 0.1–0.2 with uniform mixing but 0.5–0.8 with patchy mixing.
- **04, identifiability.** The RMS amplitude change peaks near 10 m of CO₂ layer (tuning), while the time shift keeps growing (0.486 ms per metre). For a 4 m layer the smallest scaled singular value is below 1, so to first order the two measurements cannot see the saturation, or the trade-off between thickness and saturation, across the prior range.

## Limitations

- **No simulation and no training.** No reservoir simulation has been run, and the network is untrained. Only its shapes and built-in constraints are checked, and its response to the boundary input comes from random weights.
- **Simplified physics.** The pressure examples are single-phase (the Theis solution, and an image well for one straight fault), and the front is 1D advection–diffusion. None of them is two-phase CO₂ flow with gravity, capillary pressure and dissolution, so they test parts of the method, not the whole.
- **Toy data.** The ensemble in 02 and the errors and residuals in 03 are generated in the notebooks, with known structure. In 03, calibration and test cases come from the same distribution, which real shut-in and boundary shifts would break.
- **Simplified seismic.** The traces are 1D, at normal incidence, with no noise in the traces themselves. The rock values are illustrative and not calibrated to a well, uniform mixing is assumed in §§4–5, pressure does not change the rock, and the sensitivity analysis is local.
- **Placeholders.** Values in square brackets, such as tolerances and set sizes, are placeholders to be set with a supervisor before any results exist.
- **The proposal is not included.** References to proposal sections (§) and to hypotheses H1–H5 point to the proposal itself.

Each notebook ends with its own, more detailed list of assumptions and what has to change: 01 §6, 02 §10, 03 §11 and 04 §7.

## From my work to evaluation

Where each method appears, as notebook section and cell id. Cell ids are stored in the notebook files but are not shown when a notebook is displayed; to find a cell such as `nb03-s6-known`, go to its section, or search the raw `.ipynb` file for the id.

| Area | Method from my work | Engineering use | Notebook section · cell | How it is evaluated |
|---|---|---|---|---|
| Computational Mathematics | Exact solutions as checks | Theis build-up and fall-off with superposition; closed-box material balance; Horner line | 01 §3 · `nb01-s3-theis`, `nb01-s3-table`, `nb01-s3-horner` | OPM Flow pressure within a pre-set tolerance of the known answer (01 §5) |
| | Observed order, Richardson extrapolation, grid-convergence index | Refinement of a mid-point and a threshold plume edge | 01 §4.1–4.2 · `nb01-s4-refine`, `nb01-s4-richardson` | Observed order and GCI, or an error bracket; gives `e_num` |
| | Conservation and quadrature | Two-measure mass balance with a seeded 0.2 % inflow error (stand-in for the CO₂ inventory); free-phase CO₂ mass from maps | 01 §4.3 · `nb01-s4-massbalance`; 03 §6 · `nb03-s6-known` | Gap below [1e-6]; every check first catches its seeded defect |
| | SVD and conditioning | What seismic data cannot separate | 04 §5 · `nb04-s5-svd` | Singular values in noise units across the prior range |
| Data Science and ML | Split first; pipelines fitted on training data | Splits by realisation, before and after shut-in | 02 §4 · `nb02-s4-splits` | Test error of each split; only splits by realisation are used |
| | Depth-window and spatial hold-outs | Paired shift design: held-out TEST geologies under baseline and shifted conditions, matched by geology id; an unseen AUDIT set | 02 §5 · `nb02-s5-design`, `nb02-s5-pairs`, `nb02-s5-checks` | Automated checks: unique cases, no geology leakage, a baseline for every shifted case, one factor per pair; AUDIT scored once |
| | Learning curves | Ensemble size by realisation | 02 §6 · `nb02-s6-curve` | Where the curve stops falling |
| | Tuning budgets and ensembles | Baselines at the same budget, compared by paired bootstrap (rule R1) | 02 §7 · `nb02-s7-tuning`, `nb02-s7-paired`, `nb02-s7-check` | 95 % interval of the paired difference |
| | Thresholds for a target precision | Alarm for a wrong boundary (sealing fault) from gauge data | 02 §8 · `nb02-s8-alarm`, `nb02-s8-misses` | Test precision with a Clopper–Pearson interval; recall by fault distance |
| Deep Learning | LSTM cell from its equations | ConvLSTM memory for pressure and plume maps | 03 §3 · `nb03-s3-cell`, `nb03-s3-check` | Shape and range checks |
| | Softmax output | CO₂ inventory that adds up exactly; zero outflow for a closed boundary | 03 §4 · `nb03-s4-layer`, `nb03-s4-test` | Known-answer test |
| | U-Net, rollout, parameter count | Recurrent U-Net surrogate (untrained), with the boundary openness as an input to its maps and series | 03 §5 · `nb03-s5-model`, `nb03-s5-forward`, `nb03-s5-checks`, `nb03-s5-boundary` | Controlled check that changes only the boundary; usefulness tests U1–U4 after training (03 §9) |
| | Seeded training | Deep ensembles and conformal bands over whole trajectories | 03 §7–8 · `nb03-s7-toy`, `nb03-s8-repeat`, `nb03-s8-rule` | Rule R2; trajectory coverage of at least 0.90 |
| Seismic | Impedance, reflection coefficients, Ricker wavelet and convolution; wedge model | Time-lapse synthetics of a thin CO₂ layer; tuning | 04 §4 · `nb04-s4-trace`, `nb04-s4-obs`, `nb04-s4-traces` | Known answer: no CO₂ gives no change; tuning near a quarter wavelength |
| | RMS amplitude attribute; velocity and travel time | Amplitude change and time shift as measurements | 04 §4 · `nb04-s4-obs`, `nb04-s4-plot` | Response per metre of CO₂ against assumed noise |
| | *New for the PhD:* Gassmann rock physics | CO₂ saturation to P-wave velocity, uniform and patchy mixing | 04 §3 · `nb04-s3-mixing`, `nb04-s3-check` | Mixing rules agree for brine only and CO₂ only; the rule is part of `e_obs` |

## Key terms and rules from the proposal

The notebooks explain each term in plain words where it first appears and refer to sections of the proposal, which is not included in this repository. Its main terms and rules are:

- **Decision quantities.** P1 peak bottom-hole pressure during injection; P2 average overpressure at shut-in, +5 and +10 years; P3 overpressure below the caprock and at a distant point; P4 time for overpressure to halve after shut-in; M1 CO₂ mass by state (mobile, immobile, dissolved); M2 plume footprint above a saturation threshold; M3 maximum up-dip migration distance.
- **CO₂ inventory.** `M_inj(t) = M_mob(t) + M_imm(t) + M_diss(t) + M_out(t)`, where `M_out` is cumulative outflow across the model edge (zero for a closed boundary, and wherever the chosen boundary representation lets no CO₂ cross).
- **Error budget.** `u_geo` spread across the geological prior; `e_num = R_h − R∞`, production-grid reference minus refined reference; `e_mf` differences between model levels; `e_sur = S − R_h`, surrogate minus reference; `e_obs` effect of rock-physics and noise choices. `R∞` estimates the converged solution of the model equations, and the surrogate's error against it is `S − R∞ = e_sur + e_num`. This is measured only on refined realisations; elsewhere it is estimated by an error indicator, which is checked on held-out refined realisations and is not a bound.
- **Rules.** R1 a difference between methods is claimed only if a paired 95 % bootstrap interval excludes zero; R2 an advantage seen only against `R_h` and smaller than `|e_num|` is not claimed; R3 a surrogate is fit for a quantity only where the 90th percentile of `|S − R∞|` over refined test realisations is below [0.2] `u_geo`, and a verdict that rests on the indicator, or on a shift without refined cases of that shift, is reported as provisional; R4 model choice is reported as controlling where `e_mf` dominates; R5 every term is reported before and after shut-in.
- **Usefulness tests.** U1 accuracy (R3); U2 added value over the best simpler method at the same tuning budget; U3 lower total cost, training data included, than an equally accurate coarse-grid simulation; U4 the same ranking of operating schedules as the reference.
- **Coverage target.** At least 0.90 of test realisations inside a simultaneous band for their whole post-shut-in trajectory, judged with a 95 % Clopper–Pearson interval.
- **Cases.** A, assessment (rate and duration within pressure limits); B, operation (ranking injection schedules); C, monitoring (which data narrow forecasts, and whether they reveal a wrong boundary).

Values in square brackets are placeholders to be set with a supervisor before any results exist. The section numbers (§) cited in the notebooks refer to the proposal, and so do its hypotheses, whose full statements are given there. The notebooks cite H1 in 01 §4.1, H2 in 03 §5.1 and §11, H4 in 03 §8, and H5 in 04 (introduction, §5 and §6); H3 is not cited.

## Viewing and running the notebooks

### Viewing the saved results

GitHub displays each notebook with its saved text output, equations and figures: open one from the [repository guide](#repository-guide). If GitHub fails to display a notebook, which can happen with larger files, open it through nbviewer instead, for example <https://nbviewer.org/github/abdelghafarfouda/co2-storage-research-interest/blob/main/notebooks/03_deep_learning_surrogate.ipynb>.

### Running them locally

You need Git and Python 3.11 or newer: the pinned versions of NumPy, SciPy, pandas and scikit-learn do not install on older Python.

```bash
git clone https://github.com/abdelghafarfouda/co2-storage-research-interest.git
cd co2-storage-research-interest
python -m venv .venv
source .venv/bin/activate            # on Windows: .venv\Scripts\activate
pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu   # optional: the much smaller CPU-only PyTorch
pip install -r requirements.txt
jupyter lab                          # then open a notebook and run all cells
```

- **Python version.** On macOS and Linux the command may be `python3` rather than `python`. If `python --version` inside the environment shows a version older than 3.11, delete `.venv` and create it again with a newer interpreter, for example `python3.11 -m venv .venv`.
- **CPU-only PyTorch.** The `torch` line is optional. It matters most on Linux, where the default PyTorch from PyPI also installs several gigabytes of GPU (CUDA) libraries. Run it before `pip install -r requirements.txt`: pip then treats the pinned `torch==2.14.0` as already installed.
- **Running a notebook.** In JupyterLab, open a notebook and choose *Kernel → Restart Kernel and Run All Cells*, so that it runs from a clean kernel as it was saved.
- **Checking all four at once.** `jupyter execute notebooks/*.ipynb` runs every notebook from a clean kernel without opening JupyterLab and without changing the saved files. It stops with an error if any cell fails, including the built-in checks (the `assert` statements in Notebooks 02 and 03). On Windows, where the shell does not expand `*`, name the four notebook files instead.

Everything runs on a CPU, and the four notebooks together take under a minute. Random seeds are fixed in the code (mostly 42), so the printed numbers repeat. Only Notebook 03 needs PyTorch.

The notebooks use NumPy, SciPy, pandas, scikit-learn, Matplotlib and PyTorch. They were last run from a clean kernel with Python 3.11.15 and the package versions in `requirements.txt`. Methods, papers and other sources are cited at the end of each notebook.

## How these materials were prepared

This repository adapts my earlier work to a CO₂ storage research question. I used AI tools to help prepare the new notebooks and explanations.

## Licence

No open-source licence has been granted for this repository. Third-party software remains under its own licences.
