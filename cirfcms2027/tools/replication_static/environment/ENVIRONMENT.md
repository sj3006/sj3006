# Computing environment

## Python

Produced and checked with Python 3.13.18 on Linux x86-64 and the packages pinned
in `requirements.txt`:

    python3 -m venv .venv
    . .venv/bin/activate
    pip install -r environment/requirements.txt

Nothing else is required: no GPU, no licensed solver, no network access, no
external dataset. The forward model generates every signal; the only outside
numbers are the published measurements in `data/input/`, which are written into
the code as constants.

Python 3.10 or later should work. numpy 2.0 or later is required.

## LaTeX, for rebuilding the papers

The papers were built with pdfTeX from TeX Live 2023 and the Elsevier
`elsarticle` class (the conference paper uses the Procedia CIRP layout supplied
with it):

    pdflatex paper && bibtex paper && pdflatex paper && pdflatex paper

The conference paper has its bibliography inline and needs no `bibtex` step.

## Hardware and run time

Measured on a four-core cloud machine with 16 GB of memory.

| task | time |
|---|---|
| `scripts/check_all.sh`, everything checked against shipped data | about 10 min |
| conference paper, full recomputation of 234 numbers | about 4 min |
| conference paper, every analysis stage (`run_all.py`) | about 15 min |
| certificate paper, results from scratch | about 10 min |
| fidelity paper, results from scratch | about 70 min |

The fidelity study runs four worker processes. With `OMP_NUM_THREADS=1` (set by
`scripts/reproduce_fidelity.sh`) each worker uses one core.

## Determinism

Every random draw is seeded. A rerun on the same platform reproduces the
shipped data exactly. On a different processor or library build, summation
order can change the last digits of floating-point results;
`scripts/compare_outputs.py` compares at a relative tolerance of 1e-6 for that
reason, and the claim checks compare at the precision each paper prints.
