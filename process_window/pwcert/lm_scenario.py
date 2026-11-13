"""Language-model scenario built from measured generations.

`results/lm/surface_scores.npz` (from experiments/lm_surface.py) holds, for
each (temperature, top-p) setting, the scores of N generated continuations.
Thresholds turn scores into pass/fail per failure mode; the empirical rates
are then fitted with a monotone (2D isotonic) surface so the benchmark's
ground truth satisfies Assumption A exactly (raw rates from N samples
fluctuate by a few percent between neighbouring settings). Benchmark runs
draw fresh Bernoulli outcomes from that surface.

Axes: axis 0 = temperature (low -> high), axis 1 = top-p (low -> high).
- "degenerate" (repetition) is safer at HIGHER temperature and top-p: (+1, +1)
- "incoherent" (high NLL) is safer at LOWER temperature and top-p: (-1, -1)

Simulators:
- "pilot": a monotone fit from the first `pilot_n` generations per setting
  of a *disjoint* subset of the measurements (a cheap pilot study);
- "none": flat prior.
"""

import os

import numpy as np

from .certify import _isotonic_2d
from .synthetic import Scenario

LM_MODES = ("degenerate", "incoherent")
LM_DIRECTIONS = {"degenerate": (+1, +1), "incoherent": (-1, -1)}
REP_THRESH, NLL_THRESH = 0.2, 3.5
PATH = os.path.join(os.path.dirname(__file__), "..", "results", "lm", "surface_scores.npz")


def _monotone(rates, weights, direction):
    d0, d1 = direction
    f = _isotonic_2d(rates, weights, -d0, -d1, iters=8)
    f = f[::-d0, ::-d1]
    f = np.maximum.accumulate(np.maximum.accumulate(f, axis=0), axis=1)[::-d0, ::-d1]
    return np.clip(f, 1e-4, 1 - 1e-4)


def load_scores(path=PATH):
    z = np.load(path, allow_pickle=True)
    temps, tops = z["temps"], z["tops"]
    nT, nP = len(temps), len(tops)
    scores = [[z[f"{i}_{j}"] for j in range(nP)] for i in range(nT)]
    return temps, tops, scores


def make_lm_scenario(eps=0.10, simulator="pilot", pilot_n=16, path=PATH,
                     rep_thresh=REP_THRESH, nll_thresh=NLL_THRESH):
    temps, tops, scores = load_scores(path)
    nT, nP = len(temps), len(tops)
    fails = {"degenerate": np.zeros((nT, nP)), "incoherent": np.zeros((nT, nP))}
    pil = {"degenerate": np.zeros((nT, nP)), "incoherent": np.zeros((nT, nP))}
    n_main = np.zeros((nT, nP))
    for i in range(nT):
        for j in range(nP):
            s = scores[i][j]
            deg, inc = s[0] > rep_thresh, s[1] > nll_thresh
            # The pilot uses the first pilot_n generations; the truth uses the rest.
            fails["degenerate"][i, j] = deg[pilot_n:].mean()
            fails["incoherent"][i, j] = inc[pilot_n:].mean()
            pil["degenerate"][i, j] = deg[:pilot_n].mean()
            pil["incoherent"][i, j] = inc[:pilot_n].mean()
            n_main[i, j] = len(deg) - pilot_n
    truth = {m: _monotone(fails[m], n_main, LM_DIRECTIONS[m]) for m in LM_MODES}
    eps_d = {m: eps for m in LM_MODES}
    if simulator == "pilot":
        w = np.full((nT, nP), float(pilot_n))
        sim = {m: _monotone(pil[m], w, LM_DIRECTIONS[m]) for m in LM_MODES}
        meta = dict(pilot_coupons=int(pilot_n * nT * nP))
    elif simulator == "none":
        sim = {m: np.full((nT, nP), eps) for m in LM_MODES}
        meta = {}
    else:
        raise ValueError(simulator)
    return Scenario(temps, tops, eps_d, truth, sim, name=f"lm/{simulator}",
                    directions=dict(LM_DIRECTIONS), meta=meta)
