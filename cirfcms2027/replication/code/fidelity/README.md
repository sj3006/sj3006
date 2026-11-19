# Twin fidelity for fault diagnosis

How accurate must a digital twin be before the faults it diagnoses can be
trusted, and is that the same accuracy that validation against healthy builds
measures?

| file | what it is |
|---|---|
| `ROADMAP.md` | the plan: question, theorems, study design, work packages |
| `LABNOTEBOOK.md` | dated record of everything done, including wrong turns |
| `FINDINGS.md` | **start here**: the results in plain language |
| `literature.md` | references, each checked before it is cited |
| `paper/paper.tex`, `paper/paper.pdf` | the journal draft (23 pages) |

| module | what it does |
|---|---|
| `theory.py` | the six results (Theorems 1-2, Corollary, Propositions 3-6) with proofs in the docstring |
| `verify.py` | checks every result by simulation; 16 checks |
| `twin.py` | a twin as a frozen record of every quantity the model depends on |
| `twins.py` | the truth (961 grid) and the thirteen twin families; the validation region |
| `study.py` | scores every twin on prediction and diagnosis; writes `_study.json` (about 45 min) |
| `results.py` | summarises the study into `_results.json`, every number the paper quotes |
| `grid_convergence.py`, `floor_check.py` | the instrument-model grid finding and the numerical floor |
| `fig_fidelity.py`, `fig_theory.py`, `fig_region.py` | Figures 1 to 3 |
| `fill_tables.py` | writes the paper's data tables from `_results.json` |
| `claims.py`, `claims_registry.py` | checks every printed number against `_results.json`; 71 claims |
| `sloppy.py` | a local linearised analysis that failed; kept as a recorded negative result | Everything is reproducible from the repository: no result in this
directory depends on a file outside it except the forward model in `../src` and
the certificate machinery in `../certificate`.

## Running

```
cd cirfcms2027/fidelity
python3.13 verify.py                 # theory, 16 checks
PYTHONPATH=../src python3.13 study.py      # the twin study, about 45 min on 4 cores
PYTHONPATH=../src python3.13 grid_convergence.py
PYTHONPATH=../src python3.13 floor_check.py
PYTHONPATH=../src python3.13 results.py    # writes _results.json
python3.13 fill_tables.py && python3.13 fig_fidelity.py && python3.13 fig_theory.py \
    && PYTHONPATH=../src python3.13 fig_region.py
PYTHONPATH=../src python3.13 claims.py     # every printed number; 71 claims
cd paper && pdflatex paper && bibtex paper && pdflatex paper && pdflatex paper
```

Requires `numpy`, `scipy` and `matplotlib`. The forward model is slow enough
(tens of milliseconds a call) that the larger studies cache their results; caches
are not committed and rebuild themselves.

## Relation to the other two papers in this repository

- `../overleaf/`, `../src/`: the conference paper. Diagnosability limits of a
  coaxial suite; the calibrated forward model everything here reuses.
- `../certificate/`: the certificate paper. A statistical test giving the set of
  causes an observation admits. This paper asks how wrong the twin underneath
  that test can be before the test stops being right.
