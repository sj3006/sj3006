# Verification of `full_aircraft_XAI.ipynb`

Independent re-run and audit of the LIME / WA-LIME explainability pipeline for
turbofan RUL prediction, for academic paper submission.

## Contents

| File | Purpose |
|---|---|
| `PAPER_NUMBER_AUDIT.md` | Every number in `Tolu_Revamped_V10.pdf` vs the re-run |
| `RANKWISE_ANALYSIS.md` | Rank-position occupancy and per-feature SNR |
| `audit.html` | Presentable version of the audit (published artifact) |
| `VERIFICATION_REPORT.md` | Full findings: GBRM, LIME, WA-LIME, Jaccard, Spearman |
| `stability_metrics.py` | Jaccard Index + Spearman correlation implementation (missing from the notebook) |
| `scripts/repro_gbrm.py` | Exact reproduction of the reported MSE / R² |
| `scripts/diagnostics.py` | Split-leakage, seed-sensitivity and `time`-feature checks |
| `scripts/lime_verify.py` | `local_exp[1]` semantics and cell-32 / cell-35 reproduction |
| `scripts/agg_issues.py` | The three WA-LIME aggregation design issues |
| `scripts/stability_study.py` | LIME vs WA-LIME stability across B |
| `scripts/compute_matched.py` | Compute-matched LIME baseline |
| `scripts/paper_audit.py` | Re-runs the paper's stated protocol (seeds 17i+3) |
| `scripts/table6_audit.py` | Recomputes Table 7 from Table 6's printed ranks |
| `scripts/walime_audit.py` | WA-LIME convergence protocol from §4.4 |
| `scripts/seed_distribution.py` | Sampling distribution of the 5-run Jaccard |
| `scripts/true_effect.py` | Well-powered LIME vs WA-LIME on instance #10 |
| `scripts/rankwise.py` | Rank-position occupancy, LIME vs WA-LIME, 200 runs |
| `scripts/snr.py` | Per-feature signal-to-noise and rank variance |
| `results/*.csv` | Rank occupancy and per-feature SNR as data |
| `results/` | Raw logs and JSON output from the runs above |

## Headline result

Every deterministic number in the paper reproduces **exactly**: MSE 1248.52,
RMSE 35.33, MAE 26.96, R² 0.733, all nine Table 2(b) descriptives, and the
175.54-cycle prediction for test instance #10.

The explanation-stability numbers do not. Table 7 reports a mean pairwise
Jaccard of 0.636; Table 6's own printed ranks imply 0.707; the paper's stated
seeds give 0.800; the true value over 31,125 pairs is 0.741. The reported 0.636
sits at the 0.75th percentile of what five runs can produce.

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
