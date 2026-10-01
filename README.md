# CO₂ storage: predicting pressure and plume migration, and what monitoring can confirm

I want to study how reservoir pressure and CO₂ movement change during injection and after it stops, and how monitoring can help us check our predictions.

These four notebooks show how I would approach that question using computational mathematics, data science and machine learning, deep learning, and seismic methods. Each notebook uses small worked examples to explain a method, test it, and show where it could help with the engineering problem.

The examples support a research proposal. The deep-learning model is untrained, and the full simulation, training and monitoring studies are proposed future work.

This repository adapts my own work in computational mathematics, data science and machine learning, deep learning, and seismic to a CO₂ storage research question. External methods, software, datasets and any specifically identified supplied material are credited where used.

The notebooks are saved with their outputs, so they can be read on GitHub without installing anything. To run them yourself, see [How to run](#how-to-run).

## The four notebooks

The formal question of my PhD research proposal (draft v0.6.3) is:

> **How reliably can reservoir pressure and CO₂ plume migration be predicted through injection and after shut-in, and what can pressure and seismic monitoring confirm about those predictions?**

Reservoir engineering and physical modelling are the core: pressure build-up and fall-off, a CO₂ inventory that must add up, and the physics of what gauges and time-lapse seismic can see. Each area answers one step of the question and measures one term of an *error budget*: the separate sources of error, each measured on the same quantities.

| Area | Notebook | Engineering question | Method | Error-budget term |
|---|---|---|---|---|
| Computational Mathematics | [01](notebooks/01_computational_mathematics_reference_checks.ipynb) · WP1 | Is the reference simulation right, and how wrong is it? | Verification: known answers, grid refinement and a mass balance | `e_num`, `e_mf` |
| Data Science and Machine Learning | [02](notebooks/02_data_science_fair_tests.ipynb) · WP2 | Are the tests of a fast model fair, and how much geological uncertainty must a forecast resolve? | Test design: splits by realisation, paired shift cases, matched tuning budgets | `u_geo` |
| Deep Learning | [03](notebooks/03_deep_learning_surrogate.ipynb) · WP3 | Can a fast network (a *surrogate*) replace the simulator, and how is that judged? | An untrained recurrent U-Net with built-in physical constraints; tests of accuracy and coverage | `e_sur` |
| Seismic | [04](notebooks/04_seismic_monitoring_sensitivity.ipynb) · WP4 | What can time-lapse seismic see of a CO₂ layer? | Rock physics, synthetic traces and singular values | `e_obs` |

## What is here, and what is not

Each notebook opens with a short introduction to its question, method and purpose. Then come (1) my work in that area; (2) how it is adapted to the CO₂ problem; (3) the worked examples, which run in seconds, each followed by how to read its result and what it means for the PhD; (4) how the work package will be evaluated, with the detailed rules; (5) assumptions and what has to change; and (6) a short status line with references. Each part carries one of four labels:

| Label | Meaning |
|---|---|
| **My work** | My own earlier work: implementations, completed exercises, analysis and explanations |
| **Proposed adaptation** | What I plan to do in the PhD. Not done yet |
| **Implemented example** | New code written for this repository, run on a textbook or toy problem, or on an untrained network |
| **Evaluated result** | A tested research result. **There are none yet** |

The examples illustrate methods and checks. No reservoir simulation has been run for this project, and the numbers come from toy inputs, so they are not research findings. My original notebooks are not reproduced here; the four notebooks are new adaptations of that work.

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

Values in square brackets are placeholders to be set with a supervisor before any results exist.

## How to run

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
