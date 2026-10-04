# Evaluated experiments

Each experiment is self-contained: question, data specification, configuration,
code, checkpoints, logs, metrics, figures, tests and run commands. Each states
what is new and what it takes from earlier work, and separates pilot findings
from broader validation.

| | Experiment | Status | Data | Headline |
|---|---|---|---|---|
| E1 | [Trajectory surrogates for CO₂ injection and shut-in](e1_trajectory_surrogate) | Pilot, completed 2026-10-04 | 880 MSc SubsurfaceML simulations + 600 new shifted ones | LSTM matches the MSc scalar surrogate on peak pressure and adds whole trajectories; memory is not needed once cumulative mass is an input; conformal whole-trajectory bands reach 91 % coverage in distribution, 81 % under a permeability shift and 3 % with an open boundary. |

These experiments are later work than the MSc projects and the notebooks.
Their code, runs and write-ups were produced with an AI coding assistant
(Claude Code) at the author's request.
