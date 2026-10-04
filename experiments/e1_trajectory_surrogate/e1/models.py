"""Neural trajectory models and tabular baselines.

Both networks see the same per-step inputs (static reservoir description
repeated at every step, plus the dynamic inputs of the chosen feature set):

* ``SeqLSTM`` carries a memory across steps, so it can integrate the rate
  history itself (it builds on the LSTM cell of Notebook 03 §3, here
  ``torch.nn.LSTM``);
* ``StepMLP`` maps each step independently: no memory, the control.

The tabular baselines treat every (scenario, step) as one row.
"""
from __future__ import annotations

import numpy as np
import torch
from torch import nn


class SeqLSTM(nn.Module):
    def __init__(self, n_in: int, hidden: int = 64, layers: int = 1, n_out: int = 2):
        super().__init__()
        self.inp = nn.Linear(n_in, hidden)
        self.lstm = nn.LSTM(hidden, hidden, num_layers=layers, batch_first=True)
        self.head = nn.Sequential(nn.Linear(hidden, hidden), nn.GELU(),
                                  nn.Linear(hidden, n_out))

    def forward(self, x):                      # x: (B, T, n_in)
        h, _ = self.lstm(torch.tanh(self.inp(x)))
        return self.head(h)


class StepMLP(nn.Module):
    def __init__(self, n_in: int, hidden: int = 128, layers: int = 3, n_out: int = 2):
        super().__init__()
        mods, d = [], n_in
        for _ in range(layers):
            mods += [nn.Linear(d, hidden), nn.GELU()]
            d = hidden
        mods.append(nn.Linear(d, n_out))
        self.net = nn.Sequential(*mods)

    def forward(self, x):
        return self.net(x)


def build_net(spec: dict, n_in: int) -> nn.Module:
    if spec["kind"] == "lstm":
        return SeqLSTM(n_in, spec["hidden"], spec["layers"])
    if spec["kind"] == "mlp":
        return StepMLP(n_in, spec["hidden"], spec["layers"])
    raise ValueError(spec["kind"])


def n_params(m: nn.Module) -> int:
    return int(sum(p.numel() for p in m.parameters() if p.requires_grad))


# ---------------------------------------------------------------------------
def rows(x: np.ndarray) -> np.ndarray:
    """(N, T, F) -> (N*T, F) for the per-step tabular baselines."""
    return x.reshape(-1, x.shape[-1])
