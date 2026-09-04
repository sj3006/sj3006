# Number-by-number audit of `Tolu_Revamped_V10.pdf`

Every quantitative claim in the manuscript, checked against an independent
re-run of the pipeline on `Full_Dataset.xlsx`.

Legend: **MATCH** exact or within rounding · **CLOSE** same conclusion,
different value · **MISMATCH** not reproducible · **INCONSISTENT** the paper
contradicts itself

---

## 1. Dataset — Table 2(b)

| Quantity | Paper | Re-run | Status |
|---|---|---|---|
| Total aircraft engines | 218 | 218 | **MATCH** |
| Total operational cycles | 45,918 | 45,918 | **MATCH** |
| Min engine lifetime | 128 cycles (engine 76) | 128 (engine 76) | **MATCH** |
| Max engine lifetime | 357 cycles (engine 5) | 357 (engine 5) | **MATCH** |
| Mean engine lifetime | 210.63 cycles | 210.63 | **MATCH** |
| σ engine lifetime | 43.50 cycles | 43.50 (ddof=0) / 43.60 (ddof=1) | **MATCH** |
| RUL range | 0 – 356 cycles | 0 – 356 | **MATCH** |
| Training set size | 36,734 (80%) | 36,734 | **MATCH** |
| Test set size | 9,184 (20%) | 9,184 | **MATCH** |

σ is the population standard deviation (`ddof=0`). `pandas` `.std()` defaults to
the sample s.d. and returns 43.60. State which you used, or switch to 43.60.

⚠ **INCONSISTENT** — §4.1.2 says "the RUL labels in the C-MAPSS test set span
from **0 to 350** cycles", but Table 2(b) says **0 – 356**. The test-set range
is 0 – 356 (I checked). The derived figure "35.33 cycles ≈ 10.1% of the
operational range" uses 350; with the correct 356 it is **9.9%**.

---

## 2. GBRM — Table 5

| Metric | Paper | Re-run | Status |
|---|---|---|---|
| MSE | 1248.52 cycles² | 1248.5248 | **MATCH** |
| RMSE | 35.33 cycles | 35.3345 | **MATCH** |
| MAE | 26.96 cycles | 26.9557 | **MATCH** |
| R² | 0.733 | 0.7331 | **MATCH** |
| RMSE/MAE ratio | ≈1.31 | 1.3108 | **MATCH** |

Hyperparameters stated in §4.1 (`loss='squared_error'`, `v=0.1`,
`n_estimators=100`, `max_depth=3`, `min_samples_split=2`, `min_samples_leaf=1`,
`max_features=None`) are exactly scikit-learn's defaults and exactly what the
notebook instantiates. Reproduced to the digit across two scikit-learn minor
versions.

**The entire model-performance section is solid.** Nothing to fix here.

---

## 3. Test instance #10 — §4.2

| Quantity | Paper | Re-run | Status |
|---|---|---|---|
| GBRM predicted RUL | 175.54 cycles | 175.5442 | **MATCH** |
| Local fidelity R²_local (single run) | 0.848 | 0.836 – 0.845 across seeds | **CLOSE** |
| Perturbations per explanation | n = 5000 | 5000 (LIME default) | **MATCH** |
| Features retained | k = 8 | 8 | **MATCH** |

The instance's *actual* RUL is 226 cycles against a prediction of 175.54 — a
50-cycle error. §4.2 calls it "a mid-life engine cycle ... representative of
typical operation", which is fair, but the residual is 1.4× the RMSE. If a
reviewer checks, better to say so than to be caught describing an
above-average-error instance as representative.

---

## 4. LIME stability — Tables 6 and 7

This is where the paper breaks down. **Three different sets of numbers are in
play and no two agree.**

Protocol as stated in §4.3: instance #10, top-k = 8, five runs seeded
`s_i = 17i + 3` for `i = 1…5`, i.e. seeds **20, 37, 54, 71, 88**, all other LIME
hyperparameters fixed.

| Metric (Table 7) | Paper reports | Table 6 implies | My re-run (stated seeds) |
|---|---|---|---|
| Mean pairwise Jaccard, J̄ | **0.636** | **0.7067** | **0.8000** |
| Mean pairwise Spearman, ρ̄ | **1.000** | **0.9929** | **0.9857** |
| Mean local fidelity R²_local | 0.843 | — | 0.8408 |
| Total unique features ever in top-8 | **14** | **11** | **11** |
| Features in top-8 in all 5 runs | **6** | **6** | **7** |
| Features appearing in fewer than 5 runs | **8** | **5** | **4** |
| Number of pairwise comparisons | 10 | 10 | 10 |

### 4.1 Table 7 is internally consistent — with an experiment that is not Table 6

Table 7's numbers do hang together. Five runs × 8 slots = 40; six core features
occupy 30; if the eight unstable features share the remaining 10 slots with two
appearing twice and six appearing once, then exactly 2 of the 10 pairs share a
seventh feature:

```
2 pairs with |A_i ∩ A_j| = 7  ->  J = 7/9 = 0.7778
8 pairs with |A_i ∩ A_j| = 6  ->  J = 6/10 = 0.6000
mean = 0.6356  ->  rounds to the reported 0.636
```

So Table 7 is arithmetically sound. The problem is that **Table 6 does not
describe that experiment.**

### 4.2 What Table 6 actually contains

Transcribing the printed ranks:

| Run | Top-8, in rank order |
|---|---|
| 1 | Time, S15, S11, S4, S13, S3, S14, S8 |
| 2 | Time, S15, S11, S4, S13, S3, S7, S12 |
| 3 | Time, S15, S11, S4, S13, S7, S3, S14 |
| 4 | Time, S15, S11, S4, S13, S3, S2, S7 |
| 5 | Time, S15, S11, S4, S13, S3, S2, S8 |

Each run does have exactly 8 features, so the table is well-formed. But its
union is **{Time, S15, S11, S4, S13, S3, S2, S7, S8, S12, S14} = 11 features**,
not 14, and only **5** of them appear in fewer than all five runs, not 8. The
ten pairwise Jaccard values are `0.6, 0.778, 0.6, 0.778, 0.778, 0.778, 0.6,
0.778, 0.6, 0.778`, averaging **0.7067**.

Table 6 and Table 7 cannot both be describing the same five runs.

### 4.3 The prose names features that are not in Table 6

§4.3 states the unstable features are "Sensors 2, 7, 9, 12, 17, 18, 19, and
Operational Setting 3" — eight features, consistent with Table 7's count of 8.
But Table 6 contains **Sensors 2, 7, 8, 12, 14**:

* named in the prose, absent from Table 6: **Sensors 9, 17, 18, 19, Operational Setting 3**
* present in Table 6, missing from the prose: **Sensors 8, 14**

Three sources, three different answers.

### 4.4 "Mean Spearman is exactly 1.000" is contradicted by Table 6

§4.3 argues: "the mean Spearman rank correlation is exactly 1.000. That is,
whenever two runs agree that a given feature is in the top-8, they also agree on
its precise rank."

Two paragraphs later the same section says: "Rank 6 is occupied by sensor 3 in
4 runs and by sensor 7 in 1 run." Both cannot be true. In Table 6, run 3 places
S7 at rank 6 and S3 at rank 7, while runs 2 and 4 place them the other way
round, and S3 and S7 are both in the intersection for those pairs:

| pair | intersection size q | ρ (Eq. 16) |
|---|---|---|
| runs 2 vs 3 | 7 | **0.9643** |
| runs 3 vs 4 | 7 | **0.9643** |
| other 8 pairs | 6–7 | 1.0000 |

Mean = **0.9929**, not 1.000. Small numerically, but it falsifies the
membership-vs-order dichotomy that §4.3 builds its interpretation on, and it is
the kind of thing a referee checks with a pencil.

### 4.5 A structural problem with Eq. (16)

Spearman is computed **on the intersection only**, re-ranked 1…q. That metric is
close to guaranteed to return ≈1 on this data, for a reason unrelated to LIME's
stability: the features that survive into both top-8 sets are overwhelmingly the
high-SNR ones, whose ordering is stable by construction. The paper's own §4.3
says as much — ranks 1–5 are 100% stable — so restricting to the intersection
discards precisely the features whose order is in doubt.

The metric is therefore near-vacuous as evidence, and reporting it as "exactly
1.000" invites the objection that it was guaranteed in advance. Two fixes,
either acceptable:

* compute Spearman over **all p = 25 features** using untruncated weight
  vectors (`num_features=25`), which is what my `stability_metrics.py` does — I
  get **ρ̄ = 0.849** for single-run LIME, a number with actual resolution; or
* keep the intersection version but report it as a *diagnostic* alongside q,
  and stop drawing the "instability is membership, not order" conclusion from
  it.

---

## 5. WA-LIME — Table 8

| Metric | Paper | My re-run (paper's protocol) | Status |
|---|---|---|---|
| Mean pairwise Jaccard, J̄ | 0.778 | 0.7185 | **CLOSE** |
| Features in top-8 in all runs | 7 of 10 | 6 of 10 | **CLOSE** |
| Total unique features in any top-8 | 10 | 10 | **MATCH** |
| Boundary-fluctuating features | 3 | 4 | **CLOSE** |
| Convergence iterations (3 runs) | 4, 12, 6 | 4, 3, 5 | **CLOSE** |

Table 8's WA-LIME column is internally consistent: three runs of 8 features
sharing a common 7 gives union 10, three boundary features, and pairwise
J = 7/9 = 0.7778 for all three pairs. That checks out.

### 5.1 The relative-gain figure is quoted three ways

0.778 / 0.636 = 1.2233, i.e. **+22.3%**.

* Abstract: "a 22.3% relative gain" ✔
* §4.4 prose: "a 22.3% relative increase" ✔
* Table 8 "Change" column: **+22.4%** ✘
* §5 opening line: "A **22.4%** stability gain" ✘

Pick one. 22.3% is the correct rounding.

### 5.2 The Sensor-7 narrative does not survive re-running

§4.4 and the Conclusion both lean on this: "Sensor 7, which appears in only one
of the five LIME runs (rank 6 in run 5 only), appears in all three WA-LIME
runs... aggregation can correct individual-run omissions."

Two problems:

1. **Table 6 already contradicts it.** Table 6 shows Sensor 7 in runs **2, 3
   and 4** — three of five, at ranks 7, 6 and 8 — and *not* in run 5. The
   parenthetical "rank 6 in run 5 only" matches no row of the paper's own table.
2. **In my re-run with the stated seeds, Sensor 7 appears in all five LIME
   runs.** There is no omission for WA-LIME to correct.

§5 escalates this into an operational claim — that the HPC discharge stage is
"flagged for inspection with considerable certainty, whereas under standard LIME
it would have appeared in roughly one in five reports". That "one in five" rests
entirely on the disputed parenthetical. I would drop this narrative unless it
survives a clean re-run.

### 5.3 The comparison is underpowered

LIME's J̄ is estimated from 5 runs (10 pairs) and WA-LIME's from 3 runs
(3 pairs). With 3 pairs and 8-element sets, J̄ can only take a few discrete
values, and the difference between 0.636 and 0.778 is roughly one feature
swapping in two pairs. Section 6 below quantifies how much of the headline gap
is sampling noise.

### 5.4 A well-powered comparison on the paper's own instance

Repeating the LIME-vs-WA-LIME comparison on instance #10 with R = 100 runs per
method (4,950 pairs rather than 3 or 10), using untruncated weight vectors:

| method | Jaccard@8 | Spearman (all 25 features) | perturbations |
|---|---|---|---|
| LIME, 1× budget (n = 5,000) | 0.8201 | 0.8609 | 5,000 |
| **WA-LIME, B = 5 (5× budget)** | **0.9367** | **0.9351** | 25,000 |
| LIME, 5× budget (n = 25,000) | **0.9434** | **0.9507** | 25,000 |

**WA-LIME does work.** Against a single LIME call it lifts Jaccard@8 from 0.820
to 0.937 and Spearman from 0.861 to 0.935. The paper's qualitative claim is
real, and this is a much stronger way to demonstrate it than 5-vs-3 runs.

**But it does not beat the compute-matched baseline.** Simply raising
`num_samples` from 5,000 to 25,000 — one LIME call, no aggregation, no wrapper —
reaches 0.9434 / 0.9507, edging out WA-LIME on both metrics at identical cost.
This holds on the paper's own instance, and I found the same on a separate
10-instance study.

This is the objection most likely to sink the paper in review, because the
baseline is obvious and cheap to run. §7 of `VERIFICATION_REPORT.md` sets out
the options; the most promising is that aggregating over *resampled backgrounds*
targets a variance component that extra perturbations cannot touch, which would
give WA-LIME a defensible niche. That claim would need its own experiment.

Note on `k`: LIME's `num_features` is not a display truncation — it selects
features and then **refits the surrogate on that subset**, so top-8-of-8 and
top-8-of-25 are different quantities. Under the paper's `k = 8` protocol the
true J̄ is 0.7409; untruncated it is 0.8201. Both are correct for their
respective protocols; the paper should say which it used.

---

## 6. How much of this is sampling noise?

The obvious rejoinder to "I got 0.800 and you got 0.636" is that both are
estimates from 5 runs. So I measured the sampling distribution directly: 250
independent seeded LIME runs on instance #10, then 2,000 resamples of 5 runs
each, recomputing J̄ exactly as Eq. (15) prescribes.

| Statistic of J̄ (5 runs, 10 pairs) | Value |
|---|---|
| mean | 0.7420 |
| standard deviation | 0.0503 |
| min … max over 2,000 resamples | 0.6356 … 0.9111 |
| 5th percentile | 0.6711 |
| 25th percentile | 0.7067 |
| median | 0.7289 |
| 75th percentile | 0.7778 |
| 95th percentile | 0.8267 |

**Best estimate of LIME's true J̄ on instance #10, from all 31,125 pairs:
0.7409 ± 0.1144.**

Where the three candidate values sit in that distribution:

| Value | Source | Percentile |
|---|---|---|
| **0.636** | Table 7 (the paper's headline) | **0.75th** — the minimum of 2,000 resamples |
| 0.7067 | Table 6's implied value | 29th — unremarkable |
| 0.8000 | my re-run with the stated seeds | ~80th |

This is the fair reading, and it cuts both ways.

**In the paper's favour:** 0.636 is *attainable*. It is not fabricated, and a
5-run estimate genuinely can land there. My 0.800 is no more "correct" than the
paper's 0.636 — both are single draws from a distribution with σ ≈ 0.05.

**Against:** 0.636 is the single most pessimistic estimate of LIME's stability
that 5 runs can produce — it sits below 99.25% of resamples. The headline
comparison therefore contrasts a tail-minimum estimate of LIME against a
point estimate of WA-LIME, which inflates the gap. Since the true value is
0.741, the honest baseline is roughly **0.74, not 0.636**, and against 0.74 the
reported WA-LIME value of 0.778 is a **+5% gain, not +22.3%**.

A reviewer who re-runs the five seeds will get something near 0.74–0.80 and will
ask why the paper reports 0.636. There is a clean answer available: report J̄
with a confidence interval over many more runs. It costs minutes of compute —
LIME on this model takes ~0.02 s per explanation — and it converts the weakest
claim in the paper into a defensible one.

### 6.1 Feature-presence rates over 250 runs

Useful for rewriting §4.3, and it settles which features are genuinely unstable:

| Feature | Appears in top-8 |
|---|---|
| time, S3, S4, S11, S13, S15 | 250/250 (100%) |
| sensor 7 | 170/250 (68.0%) |
| sensor 2 | 89/250 (35.6%) |
| sensor 17 | 81/250 (32.4%) |
| sensor 9 | 42/250 (16.8%) |
| sensor 8 | 38/250 (15.2%) |
| sensor 14 | 36/250 (14.4%) |
| sensor 19 | 18/250 (7.2%) |
| sensor 18 | 14/250 (5.6%) |
| sensor 12 | 5/250 (2.0%) |
| sensor 21 | 4/250 (1.6%) |
| sensor 16 | 3/250 (1.2%) |
| **operational setting 3** | **0/250 (0%)** |

Two consequences:

* The **six-feature stable core is confirmed** — time, S15, S11, S4, S13, S3 are
  in the top-8 of every one of 250 runs. That part of §4.3 is solid, and the
  bimodal-stability interpretation is well supported.
* **Operational Setting 3 never appears in 250 runs**, so its inclusion in
  §4.3's list of unstable features is an error. 17 features appear at least
  once across 250 runs, so Table 7's union of 14 across just 5 runs is high but
  not impossible.
* **Sensor 7 appears in 68% of runs**, not 20%. This is the quantitative form of
  the §5.2 problem: the "roughly one in five reports" claim in §5 is off by more
  than a factor of three.

---

## 7. Editorial issues

* **An unresolved author note is still in the PDF**, immediately under Fig. 18
  on p. 23: *"(Can consider adding a statement on the increase of Spearman Rank
  Correlation/point to the results section for the same)"*. Remove before
  submission.
* **Broken cross-references.** §4.4 says "In Figure 12, each curve plots the
  Jaccard index between the top-8 sets at successive iterations" — that is
  **Figure 18**; Figure 12 is the third LIME iteration. §4.4 and §5 both cite
  "Section 3.3" for the five-run instability test and the bimodal finding; both
  are in **Section 4.3**.
* **Garbled sentence in the abstract**: "...increases the number of features
  retained in every run from 6 to 7 of the top-8 set, and features that enter or
  leave the top-𝑘 set across runs." The final clause has lost its verb —
  presumably "and reduces the number of features that enter or leave...".
* **§4.2 ranking claim**: "Since time is a constant factor, the most important
  feature can be tagged as sensor measurement 15, and the least important as
  sensor measurement 19." Sensor 19 does not appear in any of the five runs in
  Table 6, so this sentence refers to the Figure 9 explanation only. Worth
  making explicit.
* **Ranking rule**: §3.6 says the top-k is ranked by |β_r · x̃_r| (coefficient ×
  scaled feature value). The notebook ranks by |β_r| alone, which is what LIME's
  `as_list()` returns. Both give the same top-6 here, but they are different
  quantities and the paper should describe the one the code computes. I checked
  both — see §4 table (the Jaccard results are identical, Spearman differs
  slightly: 0.9857 by |β| vs 0.9976 by |β·x̃|).
