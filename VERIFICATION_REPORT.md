# Verification of `full_aircraft_XAI.ipynb`

Independent re-run of the notebook against `Full_Dataset.xlsx` (45,918 rows,
218 engines, C-MAPSS-style turbofan data), checking the GBRM, the LIME
implementation, the WA-LIME weight aggregation, and the Jaccard / Spearman
stability metrics.

Environment used for the re-run: Python 3.11, scikit-learn 1.9.0, lime 0.2.0.1
(the notebook was executed under Python 3.9 / scikit-learn 1.6.1).

---

## Summary

| Item | Verdict |
|---|---|
| RUL construction | Correct; reproduces the shipped `RUL` column exactly |
| GBRM metrics (MSE 1248.5248, R² 0.7331) | **Reproduced to all printed digits** |
| `local_exp[1]` indexing in cell 35 | **Correct** (a common false alarm — see §3.1) |
| WA-LIME aggregation arithmetic | Correct as a mean; three design issues (§4) |
| Jaccard Index | **Not implemented anywhere in the notebook** |
| Spearman correlation | **Not implemented anywhere in the notebook** |
| WA-LIME > LIME at equal compute | **Not supported** — see §5.1 |
| Train/test split | Leaks engine trajectories across the split (§2.2) |
| `time` feature | Structurally tied to the target; dominates the explanation (§2.3) |

Nothing in the notebook is *wrong arithmetic*. The problems are protocol
problems, the two headline stability metrics are not there at all, and — most
seriously — once they are computed under a compute-matched comparison, the
central claim that WA-LIME is more stable than LIME does not hold (§5.1).

---

## 1. Data and RUL construction

The supplied `Full_Dataset.xlsx` is the *post-processing export* referred to
in cell 19, not the raw input the notebook reads (`FullAircraftEngineData.xlsx`).
Columns are renamed to title case and `RUL` is already present.

Verified against cell 15's definition:

```
RUL_i = max(time within engine) - time_i
```

* `RUL == last(time) - time` per engine: **True** for all 45,918 rows
* `RUL == max(time) - time` per engine: **True** (so the `.iloc[-1]` in cell 15
  is safe here — the data happens to be sorted by time within each engine)
* every engine reaches `RUL == 0`: **True**
* 218 engines, no missing values

**Minor robustness note.** Cell 15 uses `Aircraft_engine['time'].iloc[-1]`,
which is positional. It is correct only because this file is already sorted.
`groupby('unit number')['time'].transform('max')` is order-independent and would
be safer to state in the paper.

---

## 2. GBRM (Gradient Boosting Regressor)

### 2.1 Reproduction — exact

Re-running cells 21–25 (drop `unit number`, 25 features = `time` + 3
operational settings + 21 sensors, `train_test_split(test_size=0.2,
random_state=42)`, `GradientBoostingRegressor()` with all defaults):

```
MSE = 1248.5247554117    (notebook: 1248.5247554117475)
R²  = 0.7331471443       (notebook: 0.7331471442860311)
```

Exact match across two scikit-learn minor versions. Despite `random_state`
being unset, default GBR (`subsample=1.0`, `max_features=None`) makes no
material use of the RNG, so five unseeded refits gave an MSE range of 0.0000.
**The result is reproducible.** Still worth pinning `random_state=0` explicitly
in the paper's released code so a reader does not have to derive that argument.

Useful context to report alongside R²: RMSE = **35.33 cycles**, against a test
target standard deviation of 68.40 cycles.

### 2.2 The split leaks engine trajectories

`train_test_split` shuffles **rows**, not engines. Consequence:

```
engines appearing in BOTH train and test: 218 / 218
```

Every test row has near-neighbour cycles from the same engine in the training
set, and RUL varies smoothly along a trajectory, so the model can interpolate
rather than generalise to an unseen engine. Under a proper engine-grouped split
(`GroupShuffleSplit` on `unit number`):

```
grouped split : MSE = 1334.64, R² = 0.7249
notebook split: MSE = 1248.52, R² = 0.7331
```

The optimism is **~0.008 R²** — real but small. That is a good outcome for the
paper: the headline number survives the stricter protocol. I would report the
grouped-split number as the primary result and the random-split number as a
secondary, because reviewers in prognostics look for exactly this.

Sensitivity to the split seed, for reference (GBR seeded, five split seeds):
R² = 0.7254 – 0.7331, mean 0.7284, sd 0.0027. The notebook's `random_state=42`
happens to be the most favourable of the five. Reporting mean ± sd over seeds
would be more defensible than a single number quoted to 16 digits.

### 2.3 `time` is structurally tied to the target

`RUL = T_max - time`, and `time` is retained as a feature. Its GBR importance is
**0.866** of the total. Removing it drops R² from 0.733 to 0.604.

This is not strictly leakage — `T_max` is not observable at inference, so the
model still has to infer it from the sensors — but it means the top XAI finding
("`time` is the most important feature", weight 42.7 versus 16.1 for the
runner-up) is close to a restatement of the target definition rather than a
prognostic insight. If the paper's contribution is the *explanation*, the
sensor-only ranking is the more interesting artifact and should at minimum
appear alongside it.

---

## 3. LIME

### 3.1 `explanation.local_exp[1]` is correct

This looks like an off-by-one — in `lime_tabular.explain_instance` the
regression branch sets `labels = [0]`, so one expects key 0. But eleven lines
later:

```python
if self.mode == "regression":
    ret_exp.intercept[1]  = ret_exp.intercept[0]
    ret_exp.local_exp[1]  = [x for x in ret_exp.local_exp[0]]
    ret_exp.local_exp[0]  = [(i, -1 * j) for i, j in ret_exp.local_exp[1]]
```

Key 1 receives the original weights and key 0 is overwritten with their
negation. `Explanation.dummy_label == 1`, so `as_list()` and
`show_in_notebook()` both read key 1. Confirmed empirically:

* `local_exp` keys present: `[0, 1]`
* `local_exp[0] == -local_exp[1]`: True
* `as_list()` agrees with `local_exp[1]`: True

**Cell 35 is right, and the aggregated weights are consistent with the
explanations plotted in cells 30/32.** Had it used key 0, `np.abs()` would have
hidden the error anyway — but the code as written is correct. Worth a sentence
in the paper, since a reviewer may raise it.

### 3.2 Cell 32 does not isolate LIME's instability

The cell is labelled "Proof of LIME's instability". What it varies per
iteration is the **background dataset**: it bootstraps 100 training rows and
rebuilds the explainer. So the observed variation is

> LIME perturbation sampling **+** background resampling **+** a 100-row
> background that is a poor estimate of the feature distribution

confounded together. LIME's intrinsic instability is the first term only. I
measured them separately over 30 repetitions × 10 instances:

| protocol | Jaccard@8 | Spearman |
|---|---|---|
| full training background (LIME sampling only) | 0.855 | 0.849 |
| bootstrap-100 background (notebook cell 32) | 0.852 | 0.835 |

The two are within noise, so cell 32's conclusion happens to hold — but it is
not established by the experiment as designed. Re-running with the full
background and no fixed seed is the clean demonstration, and it is a one-line
change.

**Naming.** `num_samples = 100` is the size of the bootstrapped background set.
LIME's own `num_samples` (perturbations drawn for the surrogate fit) is left at
its default of **5000**. Two different quantities under one name — if the paper
says "100 samples" anywhere, it is describing the wrong thing.

### 3.3 Smaller points

* Cell 30 passes `data_row` (a `pandas.Series`); cell 32 passes `data_row.values`.
  Both work, but the inconsistency produces the sklearn feature-name warnings
  visible in the outputs. Use `.values` in both.
* No seeds anywhere in the LIME path (`np.random.choice`, and
  `LimeTabularExplainer(random_state=...)` unset), so cells 32/35/37/38 are not
  reproducible run to run. This matters more than for the GBRM: my re-run of
  cell 35 gave `time` 42.27 / s15 16.40 / s11 12.11 against the notebook's
  42.68 / 16.15 / 12.06. Same ranking, weights differing by 1–10%. For a paper
  that quotes aggregated weights, seed them.
* `discretize_continuous=False` is a defensible choice (weights are then per-unit
  effects on standardised features) but should be stated, since it changes how
  the weights must be read.

---

## 4. WA-LIME (cell 35)

The arithmetic is a correct mean: `+= np.abs(w) / len(explanations)` over 5
explanations. I reproduced the aggregation and the ranking. Three design issues.

### 4.1 `np.abs()` destroys the direction of the explanation

A single explanation for `X_test.iloc[10]`:

```
time                    -43.1185   decreases predicted RUL
sensor measurement 15   -17.0259   decreases predicted RUL
sensor measurement 11   -11.9535   decreases predicted RUL
sensor measurement 4     -7.5301   decreases predicted RUL
```

After aggregation the bar charts in cells 37/38 show magnitude only. For a
prognostics paper the direction is the actionable content — "which sensor
readings are pulling this engine's remaining life *down*" is the question a
maintenance engineer asks.

I checked whether sign instability forces the use of `abs()`. Over 20
repetitions, the sign is perfectly stable for every feature that ranks in the
top 8; the 10 features with unstable signs are all near-zero-weight ones
(operational settings 1–3, sensors 1, 5, 8, …) whose sign is noise regardless.
**So signed averaging is safe for exactly the features the paper reports.**
Recommendation: aggregate the signed mean for the plot, and keep the mean of
`|w|` as the ranking key if you prefer — report both.

### 4.2 Truncating each base explanation to 8 features biases the aggregate

`num_features=8` means each run contributes only its top 8; features outside it
are implicitly counted as 0 and still divided by 5. So the aggregate is

> mean over runs of ( |w_j| if j in that run's top-8 else 0 )

a *shrunk* mean, not the mean of |w_j|. Features that are strong but
inconsistently selected are penalised twice. Measured against an untruncated
run (`num_features=25`):

| feature | agg (top-8, notebook) | agg (all 25) | shrinkage |
|---|---|---|---|
| time | 42.2198 | 42.1884 | 0% |
| sensor measurement 15 | 16.6370 | 16.6311 | 0% |
| sensor measurement 11 | 12.1431 | 12.1634 | 0% |
| sensor measurement 4 | 7.7366 | 7.7212 | 0% |
| sensor measurement 13 | 5.2556 | 5.2741 | 0% |
| sensor measurement 3 | 2.3907 | 2.3755 | −1% |
| sensor measurement 7 | 1.3004 | 2.1313 | **39%** |
| sensor measurement 21 | 0.0000 | 1.4581 | **100%** |
| sensor measurement 12 | 0.6826 | 1.3166 | **48%** |
| sensor measurement 2 | 0.2771 | 0.9932 | **72%** |

The top ~6 are unaffected, so the headline ranking stands. But everything from
rank 7 down in the notebook's published chart — including `sensor measurement
21` reported as exactly 0.0 — is an artifact of the truncation, not a property
of the model. Fix: request all 25 features in each base explanation and truncate
only for display.

### 4.3 The method should not be called S-LIME

Cells 33–35 are titled "Applying S-LIME". S-LIME (Zhou et al., KDD 2021) is a
specific algorithm that uses hypothesis testing and the central limit theorem to
choose the number of perturbations needed for a stable LASSO feature selection.
Averaging weights over repeated runs is a different method. Calling it WA-LIME,
as you do, is right; the notebook headings need to follow. A reviewer familiar
with the S-LIME paper will otherwise read the section as a misattribution.

---

## 5. Jaccard Index and Spearman correlation

**Neither is implemented in the notebook.** There is no `jaccard`, no
`spearman`, no `scipy.stats` import in any of the 39 cells. If the paper reports
these numbers, they came from code that is not in this file.

I implemented both (`stability_metrics.py`). Protocol: run each method R times
independently on the same instance, then take the mean over all R(R−1)/2 pairs
of runs — that is what explanation stability means. Jaccard on the top-k feature
*sets*; Spearman on the full 25-feature *ranking* by |weight|.

R = 30 repetitions, 10 test instances (including the notebook's `X_test.iloc[10]`):

| method | Jaccard@5 | Jaccard@8 | Jaccard@10 | Spearman |
|---|---|---|---|---|
| LIME, single run, full background | 1.000 ± 0.000 | 0.855 ± 0.108 | 0.790 ± 0.105 | 0.8492 ± 0.0500 |
| LIME, single run, bootstrap-100 background (cell 32) | 1.000 ± 0.000 | 0.852 ± 0.115 | 0.782 ± 0.105 | 0.8354 ± 0.0569 |
| WA-LIME, B = 3 | 1.000 ± 0.000 | 0.920 ± 0.101 | 0.848 ± 0.095 | 0.9050 ± 0.0331 |
| **WA-LIME, B = 5 (the notebook's setting)** | 1.000 ± 0.000 | **0.958 ± 0.077** | **0.870 ± 0.091** | **0.9229 ± 0.0266** |
| WA-LIME, B = 10 | 1.000 ± 0.000 | 0.978 ± 0.050 | 0.900 ± 0.088 | 0.9410 ± 0.0211 |
| WA-LIME, B = 20 | 1.000 ± 0.000 | 0.994 ± 0.015 | 0.912 ± 0.083 | 0.9505 ± 0.0181 |

### Reading these numbers

* **WA-LIME does improve stability**, and monotonically in B. The notebook's
  qualitative claim holds.
* **Jaccard@5 is 1.000 for every method** — useless as a discriminator. `time`
  and the four top sensors dominate so heavily that the top-5 set never changes,
  even for single-run LIME. If the paper reports Jaccard at a small k and gets
  a perfect score, that is a property of this dataset, not evidence for the
  method. Report **k = 8 or 10**, or report Spearman, which has resolution
  across the whole range.
* **Spearman is the more informative metric here** and shows the clearest
  separation.
### 5.1 The compute-matched baseline — please read this before submitting

WA-LIME with B = 5 draws five times as many perturbations as a single LIME call
(5 × 5,000 = 25,000 against 5,000). The comparison above is therefore not
compute-matched, and some of the gain is simply more sampling. I ran the missing
baseline: plain LIME with `num_samples=25000`, one run, no aggregation.

R = 20 repetitions, 5 test instances:

| method | Jaccard@8 | Jaccard@10 | Spearman | perturbations |
|---|---|---|---|---|
| LIME, `num_samples=5000` (1×) | 0.854 | 0.776 | 0.8514 | 5,000 |
| **LIME, `num_samples=25000` (5×)** | **0.984** | 0.844 | **0.9400** | 25,000 |
| WA-LIME, B = 5 × 5,000 (5×) | 0.927 | **0.857** | 0.9253 | 25,000 |

**At equal compute, plain LIME is at least as stable as WA-LIME** — better on
Jaccard@8 (0.984 vs 0.927) and on Spearman (0.9400 vs 0.9253), marginally worse
on Jaccard@10 (0.844 vs 0.857).

The implication is direct: the stability improvement reported in the notebook is
substantially attributable to the fivefold increase in perturbation sampling,
not to the weight aggregation itself. A reviewer who runs this baseline — and it
is an obvious one to ask for — will reach the same conclusion. As it stands, the
paper's central claim is not supported by a controlled comparison.

This does not mean WA-LIME is worthless. It means the paper needs to either:

* **re-frame the claim** as "aggregation reaches a given stability at a given
  budget", and show the budget/stability curve for both methods (LIME at
  5k/10k/25k/50k against WA-LIME at B = 1/2/5/10), so the reader can see whether
  aggregation is ever on the efficient frontier; or
* **find a regime where aggregation genuinely wins** — the plausible candidate
  is robustness to background choice, since aggregating over resampled
  backgrounds targets a different variance component than raising
  `num_samples` does, and it is the one thing extra perturbations cannot fix; or
* **drop the stability-superiority claim** and present WA-LIME as a simpler,
  more interpretable way to spend a larger budget.

I would not submit without addressing this. Everything else in this report is a
tidy-up; this one goes to the contribution.

---

## 6. Recommended changes, in priority order

1. **Add the Jaccard / Spearman evaluation** — it is the paper's evidence and it
   is absent from the code. Use `stability_metrics.py`.
2. **Resolve the compute-matched baseline result** (§5.1). At equal perturbation
   budget, plain LIME matches or beats WA-LIME. This undercuts the paper's main
   claim as currently stated and must be addressed, not omitted.
3. **Seed everything** in the LIME path so the reported aggregated weights are
   reproducible.
4. **Report the engine-grouped split** as the primary GBRM result (§2.2).
5. **Stop truncating base explanations to 8 features** before aggregating (§4.2).
6. **Keep the sign** in the aggregation, or report signed and magnitude side by
   side (§4.1).
7. **Rename S-LIME → WA-LIME** in the notebook headings (§4.3).
8. Discuss `time`'s structural relationship to RUL, and show the sensor-only
   explanation ranking (§2.3).
9. Note in the text that `local_exp[1]` is deliberate and correct (§3.1).
