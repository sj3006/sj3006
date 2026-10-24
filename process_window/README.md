# Certified process windows

Research code for an ICML 2027 submission: anytime-valid certification of
manufacturing process windows, using the physics ordering of failure modes
and a simulator that guides testing without affecting validity.

Independent of the LIME/RUL work elsewhere in this repo.

Start with:

1. `ROADMAP.md`: the 10-week trajectory, milestones and open questions.
2. `notes/01_betting_and_ville.md`: the core tool, in plain terms.
3. `notes/02_problem_statement.md`: formal setup and the validity proof (draft).

## Layout

```
pwcert/
  eprocess.py     betting e-processes for "defect rate < eps" (one setting)
  certify.py      grid certifier: chains, fixed-sequence testing, spreading
  synthetic.py    toy LPBF ground truth and simulators (placeholders)
experiments/
  exp01_single_setting.py   validity and power for one setting
  exp02_grid.py             validity (worst case) and certified area vs coupons
results/          CSVs, plots and logs written by the experiments
tests/            unit tests (validity checks included)
notes/            study notes and proofs
```

## Running

From this directory:

```bash
pip install -r requirements.txt
python3 -m pytest -q tests                      # ~10 s
python3 experiments/exp01_single_setting.py     # ~1 min
python3 experiments/exp02_grid.py --quick       # ~5 min smoke test
python3 experiments/exp02_grid.py               # ~40 min full run
```

## Current status

See the log at the bottom of `ROADMAP.md`. The ground truth and simulators
in `synthetic.py` are toy placeholders with physically sensible monotone
directions; they will be replaced in Phase 2.
