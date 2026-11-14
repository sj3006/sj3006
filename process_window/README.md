# Certifying safe operating regions under monotone failure modes

Code for the ICML 2027 submission. The paper itself is
`paper/latex/main.tex` (compiled: `paper/latex/main.pdf`); the proofs in
plain text are `paper/appendix_theory.md`.

**The problem.** A system has two knobs (a language model's temperature and
top-p; a laser's power and scan speed; two drug doses). Each setting can fail
in several ways, and each failure rate can only be estimated by running
trials at that setting. We want the set of settings where every failure
rate is below its tolerance, with a 95% guarantee that nothing unsafe is in
the set, using as few trials as possible. The structure we use: each failure
mode gets worse in a known direction (repetition falls with temperature,
incoherence rises with it).

**What is here.**
- The *cone rule*: a closed-testing procedure with betting e-processes. It is
  valid at any stopping time under any adaptive choice of trials, and under
  monotonicity it reduces to two cumulative sums (`pwcert/cone.py`).
- A *search* for the fixed-confidence version that stops on its own once the
  target region is certified (`pwcert/search.py`).
- Instance-dependent *lower bounds*, with and without the ordering
  (`pwcert/bounds.py`).
- Three applications: language-model sampling settings (measured from real
  generations), additive-manufacturing process windows, and a two-drug
  combination screen.

Independent of the LIME/RUL work elsewhere in this repository.

## Layout

```
pwcert/
  eprocess.py     betting e-processes for "failure rate < eps" (hedge of
                  plug-in and fixed bets)
  cone.py         ConeCertifier: cone rule, weights, edge allocation,
                  re-checks, futility; cone_sum (the two cumulative sums)
  search.py       SearchCertifier: fixed-confidence search (galloping and
                  bisection per row, rejection e-processes, time-outs)
  bounds.py       lower bounds: ordered (joint LP, Theorem 2) and unordered
  baselines.py    full grid with Bonferroni; full grid with fixed-sequence
                  testing (Learn-then-Test for a monotone risk)
  gp_baseline.py  GP level-set baseline, optionally with the monotone closure
  synthetic.py    synthetic process window with controllable simulator error
  physics.py      Rosenthal melt-pool model of 316L (lack of fusion,
                  keyhole, balling)
  dose.py         two-drug toxicity / non-response surfaces, Bliss prior
  lm.py           SmolLM2-135M generation and scoring (seq-rep-4, NLL)
  lm_scenario.py  LM benchmark built from the measured surface
  pilot.py        pilot-study simulator for the "no simulator" variants
  certify.py, audit.py   earlier chain certifier and the monotonicity audit
experiments/      one script per table or figure (below)
results/          CSVs, logs and figures written by the experiments
tests/            unit tests, including validity checks
notes/            study notes and earlier proof drafts
```

## Install

```bash
pip install -r requirements.txt          # core: numpy, scipy, matplotlib, pytest
pip install -r requirements-lm.txt       # only for measuring the LM surface
python3 -m pytest -q tests               # 54 tests, about 1 minute
```

Tested with Python 3.13, numpy 2.5, scipy 1.18, matplotlib 3.11, torch 2.15
(CPU), transformers 5.22, datasets 5.2.

## Reproducing the paper

Run from this directory. Times are on 4 CPU cores. The LM benchmark reads
`results/lm/surface_scores.npz`, which is committed, so only the first LM
step needs torch.

| Paper item | Command | Output | Time |
|---|---|---|---|
| LM surface (measured) | `HF_HOME=<cache> python3 experiments/lm_surface.py` | `results/lm/surface_scores.npz` | 1.6 h |
| Figure 1, LM budget curves | `python3 experiments/lm_figure.py` | `results/lm/fig_lm_*.{png,pdf}` | 1 min |
| LM rows of Tables 1-2, LM GP numbers, monotonicity check | `python3 experiments/exp_lm.py --parts budget,confidence,gp,cost,check` | `results/lm/lm_*.csv` | 20 min |
| LM 23x23 surface (nested; reuses the 12x12 settings) | `HF_HOME=<cache> python3 experiments/lm_surface.py --n 23` | `results/lm/surface_scores_23.npz` | 4 h |
| LM 23x23 rows of Tables 1-2 | `python3 experiments/exp_lm.py --parts cost,confidence --surface results/lm/surface_scores_23.npz --pilot-stride 2 --budget 150000` | `results/lm/lm_*_23.csv` | 1 h |
| Live LM run (certifier queries the model) | `HF_HOME=<cache> python3 experiments/lm_live.py` | `results/lm/lm_live_seed0.json` | 40 min |
| Table 1, Figure 2 (scaling) | `python3 experiments/final.py scaling --scen toy-good` and `--scen lpbf-good`, then `final.py gridfst` | `results/final/scaling_*.csv` | several hours |
| Table 2, Figure 3 (fixed confidence) | `python3 experiments/exp_search.py` | `results/final/fixed_confidence*.csv` | several hours |
| Validity (worst case) | `python3 experiments/final.py validity` | `results/final/validity.csv` | 30 min |
| GP baseline | `python3 experiments/final.py gp --n 16` | `results/final/gp_baseline.csv` | 1 h |
| GP baseline with the ordering | `python3 experiments/final.py gp --n 16 --monotone` and `exp_lm.py --parts gpmono` | `results/final/gp_baseline_monotone.csv`, `results/lm/lm_gp_monotone.csv` | 1 h |
| Ablations | `python3 experiments/final.py ablation --scen toy-good` | `results/final/ablation_*.csv` | 1 h |
| Monotonicity violations | `python3 experiments/violation.py` | `results/final/violation.csv` | 30 min |
| Paper figures from the CSVs | `python3 experiments/paper_figs.py` | `paper/latex/figs/*.pdf` | 1 min |

Set `OMP_NUM_THREADS=1` for the benchmark scripts; they are single-threaded
numpy and run faster without thread contention.

## Using the certifier on your own system

```python
import numpy as np
from pwcert.synthetic import Scenario
from pwcert.cone import ConeCertifier

# truth: dict mode -> (n1, n2) array of failure rates (only used to simulate
# trials and to score results; replace run_plate's sampling with real trials);
# directions: dict mode -> (s1, s2), the index steps that make the mode SAFER.
sc = Scenario(knob1, knob2, eps={"a": 0.1, "b": 0.1}, truth=truth, sim=prior,
              directions={"a": (+1, +1), "b": (-1, -1)})
c = ConeCertifier(sc, rule="cone", weights="ensemble", alloc="edge",
                  target_q=0.7, batch=24, rng=np.random.default_rng(0))
c.run(8000)            # trial budget
print(c.window())      # certified settings (boolean grid)
```

`experiments/lm_live.py` shows how to plug in real trials: subclass
`ConeCertifier` and override `run_plate` to run the chosen settings.

## Status

See the log at the bottom of `ROADMAP.md`.
