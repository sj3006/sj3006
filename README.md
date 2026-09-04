# Verification of `full_aircraft_XAI.ipynb`

Independent re-run and audit of the LIME / WA-LIME explainability pipeline for
turbofan RUL prediction, for academic paper submission.

## Contents

| File | Purpose |
|---|---|
| `VERIFICATION_REPORT.md` | Full findings: GBRM, LIME, WA-LIME, Jaccard, Spearman |
| `stability_metrics.py` | Jaccard Index + Spearman correlation implementation (missing from the notebook) |
| `scripts/repro_gbrm.py` | Exact reproduction of the reported MSE / R² |
| `scripts/diagnostics.py` | Split-leakage, seed-sensitivity and `time`-feature checks |
| `scripts/lime_verify.py` | `local_exp[1]` semantics and cell-32 / cell-35 reproduction |
| `scripts/agg_issues.py` | The three WA-LIME aggregation design issues |
| `scripts/stability_study.py` | LIME vs WA-LIME stability across B |
| `scripts/compute_matched.py` | Compute-matched LIME baseline |
| `results/` | Raw logs and JSON output from the runs above |

## Headline result

The reported GBRM metrics reproduce **exactly** (MSE 1248.5247554117,
R² 0.7331471443). The LIME and WA-LIME code is arithmetically correct,
including the `local_exp[1]` indexing that commonly looks like a bug.

The Jaccard Index and Spearman correlation are **not implemented anywhere in
the notebook** — `stability_metrics.py` supplies them.

See `VERIFICATION_REPORT.md` for the full analysis and a prioritised list of
recommended changes.

## Reproducing

```bash
pip install pandas numpy scipy scikit-learn openpyxl matplotlib lime
python scripts/repro_gbrm.py       # writes results/model.joblib
python scripts/stability_study.py
```

`lime==0.2.0.1` does not build under recent setuptools; install it by copying
the `lime/` package directory out of the sdist if `pip install lime` fails.
