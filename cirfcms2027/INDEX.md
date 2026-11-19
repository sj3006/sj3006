# Index of the LPBF diagnosability work

Three linked papers live in this directory. All of it is on the branch
`claude/lucid-feynman-bqpmqw` of `sj3006/sj3006` until merged.

| directory | paper | state |
|---|---|---|
| `overleaf/`, `src/`, `repro/`, `paper/` | **Conference paper** (Procedia CIRP): which process faults a coaxial monitoring suite can distinguish, and why build context separates them | submitted version in `overleaf/`; every number reproduced by `repro/check.py` |
| `certificate/` | **Certificate paper** (journal): what a monitoring agent is entitled to conclude; a hypothesis test returning the set of admissible causes | complete draft in `certificate/paper/` except the language-model results, which await an API decision; `certificate/verify.py` 32/32, `certificate/claims.py` 76/76 |
| `fidelity/` | **Fidelity paper** (journal): how accurate a digital twin must be for diagnosis, and why validation on healthy builds does not measure it | first full draft (`fidelity/paper/paper.pdf`); results in `fidelity/FINDINGS.md`, log in `fidelity/LABNOTEBOOK.md` |

## Where to start

- To see what each paper claims: `certificate/FINDINGS.md`, `fidelity/FINDINGS.md`,
  and `README.md` here for the conference paper.
- To check that the code still reproduces the papers: run `repro/check.py`,
  `certificate/verify.py`, `certificate/claims.py`, `fidelity/verify.py`.
- To see the reasoning behind decisions taken without the authors:
  `fidelity/LABNOTEBOOK.md`.

Python 3.13 with numpy, scipy and matplotlib. LaTeX with the `elsarticle` class
for the papers.
