# Running the checks on your own machine

Everything is plain Python. No notebook, no GPU, no network access once the
packages are installed.

---

## 1. Get the code and the data

```bash
git clone -b claude/verify-paper-code-3pvywe https://github.com/sj3006/sj3006.git
cd sj3006
```

Put **`Full_Dataset.xlsx`** in the project root (it is not in the repo). If you
keep it elsewhere:

```bash
export AIRCRAFT_XLSX=/path/to/Full_Dataset.xlsx
```

## 2. Install the packages

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**If `pip install lime` fails** with `AttributeError: install_layout` — this is
a `setuptools >= 70` incompatibility in lime 0.2.0.1's `setup.py`, not a problem
with your setup, and it is what I hit here. The library's runtime code is fine;
only its build step breaks. Run:

```bash
./install_lime.sh
```

which drops the package directory into site-packages directly. Alternatively,
`pip install "setuptools<70"` first, then retry pip.

## 3. Run

```bash
./run_all.sh quick     # the 7 fast checks, ~10 minutes total
./run_all.sh           # everything, ~2 hours (6 more, LIME-heavy)
```

Each script also runs standalone from any directory:

```bash
python3 scripts/paper_audit.py
```

Output is printed and also written to `results/<name>.log`.

---

## Do they depend on each other?

**No. Every script is independent and can be run alone, in any order.**

Each one reads only two things: the Excel file, and a trained GBRM it gets from
`_common.get_model()`. No script reads any other script's output.

`get_model()` caches the model to `results/model.joblib` purely to save refitting
(~40 s) on every run. If the cache is absent, whichever script you run builds it.
It is seeded (`random_state=0`) so it is byte-identical no matter which script
builds it first — order genuinely does not matter. Delete the file any time to
force a rebuild.

The four files some scripts *write* (`rankwise.json`, `snr.json`,
`agg_notebook.npy`, `ctx.joblib`) are outputs for you to inspect. Nothing reads
them back.

One deliberate exception: `repro_gbrm.py` fits the notebook's **unseeded**
`GradientBoostingRegressor()` rather than using the shared cache, because
demonstrating that the paper's exact figures fall out of the untouched default
is the whole point of that script. It does not touch the cache.

---

## What each file checks

### Fast — run these first (~10 min total)

| Script | Time | Checks |
|---|---|---|
| `scripts/table6_audit.py` | instant | **Needs no data.** Recomputes Table 7 from the ranks printed in Table 6. Produces J̄ = 0.7067, ρ̄ = 0.9929, union 11 — against the reported 0.636 / 1.000 / 14. Also lists the prose/table feature mismatches. |
| `scripts/repro_gbrm.py` | ~1 min | RUL construction, the 80/20 split, and the GBRM. Should print MSE 1248.5247554117, R² 0.7331471443. Caches the model to `results/model.joblib` for the other scripts. |
| `scripts/diagnostics.py` | ~3 min | Split leakage (all 218 engines on both sides), sensitivity to the split seed, and the `time` feature's 0.866 importance. |
| `scripts/paper_audit.py` | ~2 min | Every printed number: Table 2(b), Table 5, instance #10's prediction, then the five seeded LIME runs (`17i+3`) against Table 7. |
| `scripts/lime_verify.py` | ~1 min | That `local_exp[1]` is the sign-correct key, and reproduces notebook cells 32 and 35. |
| `scripts/agg_issues.py` | ~2 min | The three WA-LIME aggregation issues: `np.abs()` discarding direction, sign stability, and truncation shrinkage. |
| `scripts/walime_audit.py` | ~2 min | Table 7's internal arithmetic, then the §4.4 WA-LIME convergence protocol against Table 8. |

### Long — the statistical studies (~2 h total)

| Script | Time | Checks |
|---|---|---|
| `scripts/stability_study.py` | ~25 min | Jaccard and Spearman for LIME vs WA-LIME at B = 3/5/10/20, 10 instances, 30 reps each. Also the truncated-vs-untruncated comparison. |
| `scripts/compute_matched.py` | ~15 min | **The most important one.** Plain LIME at 25,000 perturbations against WA-LIME B=5 at the same budget. |
| `scripts/seed_distribution.py` | ~10 min | 250 LIME runs, then 2,000 resamples of 5, to locate the reported 0.636 in the sampling distribution. |
| `scripts/true_effect.py` | ~20 min | Well-powered LIME vs WA-LIME vs compute-matched LIME on instance #10 (R = 100). |
| `scripts/rankwise.py` | ~10 min | Rank-position occupancy over 200 runs, LIME and WA-LIME. Writes `results/rankwise.json`. |
| `scripts/snr.py` | ~10 min | Per-feature signal-to-noise, mean rank, rank variance. Writes `results/snr.json`. |

### Library, not a check

`stability_metrics.py` (project root) is the Jaccard + Spearman implementation
to drop into your own notebook — the piece missing from
`full_aircraft_XAI.ipynb`:

```python
from stability_metrics import run_stability_study
run_stability_study(gb_regressor, X_train, X_test, instance_ids=[10], R=30, B=5)
```

`scripts/_common.py` is shared setup (dataset path, column normalisation,
cached model). Not a check — don't run it directly.

---

## Two things worth knowing before you run

**Runtimes assume LIME takes ~0.02 s per explanation**, which is what it costs
against this GBRM on a normal laptop. If yours is slower, the long scripts scale
linearly — every one has an `R = ...` constant near the bottom you can lower to
get a faster, noisier answer.

**The long scripts are unseeded by design.** They measure sampling variability,
so your numbers will differ from mine in the third decimal. What should
reproduce is the *ordering* and the size of the gaps — e.g. compute-matched LIME
at or above WA-LIME, and ranks 1–5 at 100%. The fast scripts are deterministic
and should match my logs exactly; `results/*.log` in the repo are mine to
compare against.
