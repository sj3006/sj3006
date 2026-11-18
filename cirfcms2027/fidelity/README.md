# Twin fidelity for fault diagnosis

How accurate must a digital twin be before the faults it diagnoses can be
trusted, and is that the same accuracy that validation against healthy builds
measures?

| file | what it is |
|---|---|
| `ROADMAP.md` | the plan: question, theorems, study design, work packages |
| `LABNOTEBOOK.md` | dated record of everything done, including wrong turns |
| `FINDINGS.md` | results, once there are any |
| `literature.md` | references, each checked before it is cited |

Code, as it is written, will be listed here with what each module does and how
to run it. Everything is reproducible from the repository: no result in this
directory depends on a file outside it except the forward model in `../src` and
the certificate machinery in `../certificate`.

## Running

```
cd cirfcms2027/fidelity
python3.13 verify.py        # every claim checked; exits non-zero on failure
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
