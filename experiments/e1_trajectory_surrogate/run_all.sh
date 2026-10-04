#!/usr/bin/env bash
# Experiment E1, end to end. Run from this folder. MSC is a checkout of
# https://github.com/abdelghafarfouda/manchester-msc-projects at the commit
# pinned in config.json, with the SubsurfaceML package installed from it.
set -euo pipefail
MSC=${MSC:-../../../manchester-msc-projects}
if [[ "${REGENERATE_DATA:-0}" == "1" ]]; then
  python scripts/generate_shift_sets.py --msc-repo "$MSC"   # ~5 min on 4 cores
  python scripts/build_dataset.py --msc-repo "$MSC"
  python scripts/scalar_reference.py --msc-repo "$MSC"
fi
python scripts/run_training.py          # ~3 min on 4 cores (72 runs incl. learning curve)
python scripts/evaluate.py              # ~1 min
python scripts/make_figures.py
python -m pytest tests -q
