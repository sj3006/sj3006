# Rank-position analysis

The paper's §4.3 makes a **rank-position** claim, distinct from the set-membership
claim the Jaccard index measures:

> "Reading the table by rank position rather than by feature, the top five rank
> positions are 100% stable... Rank 6 is occupied by sensor 3 in 4 runs and by
> sensor 7 in 1 run. Ranks 7 and 8, however, are completely unstable, with five
> different features appearing at rank 7 across the five runs and five different
> features at rank 8."

This is the paper's most interesting finding, and it **largely holds up**. Below
it is re-measured with 200 runs instead of 5.

---

## 1. What Table 6 actually shows, rank by rank

| Rank | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Distinct |
|---|---|---|---|---|---|---|
| 1 | Time | Time | Time | Time | Time | 1 |
| 2 | S15 | S15 | S15 | S15 | S15 | 1 |
| 3 | S11 | S11 | S11 | S11 | S11 | 1 |
| 4 | S4 | S4 | S4 | S4 | S4 | 1 |
| 5 | S13 | S13 | S13 | S13 | S13 | 1 |
| 6 | S3 | S3 | **S7** | S3 | S3 | 2 |
| 7 | S14 | S7 | S3 | S2 | S2 | **4** |
| 8 | S8 | S12 | S14 | S7 | S8 | **4** |

Ranks 1–5 and rank 6 match the prose exactly. **Ranks 7 and 8 do not:** the prose
says "five different features" at each, but rank 7 holds four distinct features
(S2 repeats in runs 4 and 5) and rank 8 holds four (S8 repeats in runs 1 and 5).

Fix: "four different features at rank 7 and four at rank 8", or re-run and
regenerate.

---

## 2. Rank occupancy over 200 runs

Instance #10, top-k = 8, the paper's protocol, 200 independent seeds.
*Share* is how often the modal feature holds that rank; *distinct* is how many
different features ever occupy it.

### LIME

| Rank | Modal feature | Share | Distinct | Normalised entropy | Mean \|w\| |
|---|---|---|---|---|---|
| 1 | time | 100.0% | 1 | 0.000 | 43.00 |
| 2 | S15 | 100.0% | 1 | 0.000 | 16.36 |
| 3 | S11 | 100.0% | 1 | 0.000 | 12.08 |
| 4 | S4 | 100.0% | 1 | 0.000 | 7.46 |
| 5 | S13 | 100.0% | 1 | 0.000 | 4.85 |
| 6 | S3 | 87.0% | 2 | 0.120 | 2.47 |
| 7 | S7 | 48.5% | 10 | 0.473 | 1.76 |
| 8 | S17 | 23.0% | 9 | 0.600 | 0.97 |

Full occupancy (features holding each rank in >2% of runs):

| Rank | Occupancy |
|---|---|
| 1–5 | time / S15 / S11 / S4 / S13, each 100% |
| 6 | S3 87%, S7 13% |
| 7 | S7 48%, S2 18%, S3 13%, S17 10%, S9 7% |
| 8 | S17 23%, S2 18%, S8 16%, S14 15%, S9 13%, S19 9%, S18 6% |

**The paper's claim is confirmed at 40× the sample size.** Ranks 1–5 never move
in 200 runs. Rank 6 is 87% S3 / 13% S7 — the paper's 5-run estimate of 80%/20%
was almost exactly right. Ranks 7–8 are the unstable tail.

One nuance worth adding to the paper: rank 7 is not *uniformly* random — S7 holds
it in nearly half of runs. "Completely unstable" overstates it slightly. Rank 8,
with 9 distinct occupants and a 23% mode, genuinely is close to arbitrary.

### WA-LIME (B = 5)

| Rank | Modal feature | Share | Distinct | Normalised entropy | Mean \|w\| |
|---|---|---|---|---|---|
| 1 | time | 100.0% | 1 | 0.000 | 42.97 |
| 2 | S15 | 100.0% | 1 | 0.000 | 16.36 |
| 3 | S11 | 100.0% | 1 | 0.000 | 12.06 |
| 4 | S4 | 100.0% | 1 | 0.000 | 7.46 |
| 5 | S13 | 100.0% | 1 | 0.000 | 4.87 |
| 6 | S3 | **100.0%** | 1 | 0.000 | 2.39 |
| 7 | S7 | **88.0%** | 4 | 0.145 | 1.42 |
| 8 | S2 | **50.0%** | 8 | 0.427 | 0.61 |

### Side by side

| Rank | LIME modal share | LIME distinct | WA-LIME modal share | WA-LIME distinct |
|---|---|---|---|---|
| 1 | 100.0% | 1 | 100.0% | 1 |
| 2 | 100.0% | 1 | 100.0% | 1 |
| 3 | 100.0% | 1 | 100.0% | 1 |
| 4 | 100.0% | 1 | 100.0% | 1 |
| 5 | 100.0% | 1 | 100.0% | 1 |
| 6 | 87.0% | 2 | **100.0%** | **1** |
| 7 | 48.5% | 10 | **88.0%** | **4** |
| 8 | 23.0% | 9 | **50.0%** | **8** |

**This is the strongest evidence in favour of WA-LIME that I found.** The entire
gain is concentrated exactly where the paper's Eq. (22) predicts it should be —
in the low-rank tail. Ranks 1–5 were already perfect and cannot improve; rank 6
goes to fully deterministic; rank 7 nearly doubles its modal share; rank 8
doubles.

This table is a better headline than the Jaccard number, because it shows *where*
the improvement happens rather than averaging it away. I would put it in the
paper in place of, or alongside, Table 8.

---

## 3. Why the ranks behave this way — the SNR cliff

§3.7 models each run as a noisy estimate, `β̂ = β* + ε`, and argues that rank
stability follows the signal-to-noise ratio. The paper asserts this but never
measures it. It is straightforward to check, and **the model is confirmed
cleanly.**

200 untruncated runs (`num_features=25`), instance #10:

| # | Feature | Mean w | sd \|w\| | SNR | Mean rank | Rank sd | In top-8 |
|---|---|---|---|---|---|---|---|
| 1 | time | −42.924 | 0.387 | 110.9 | 1.00 | 0.00 | 100.0% |
| 2 | S15 | −16.367 | 0.303 | 54.0 | 2.00 | 0.00 | 100.0% |
| 3 | S11 | −12.072 | 0.310 | 38.9 | 3.00 | 0.00 | 100.0% |
| 4 | S4 | −7.452 | 0.303 | 24.6 | 4.00 | 0.00 | 100.0% |
| 5 | S13 | −4.869 | 0.314 | 15.5 | 5.00 | 0.00 | 100.0% |
| 6 | S3 | −2.384 | 0.332 | 7.2 | 6.18 | 0.41 | 100.0% |
| 7 | S7 | +1.987 | 0.321 | 6.2 | 6.96 | 0.61 | 98.0% |
| 8 | S21 | +1.373 | 0.280 | 4.9 | 9.01 | 1.44 | 45.5% |
| 9 | S2 | −1.127 | 0.310 | 3.6 | 10.47 | 2.19 | 17.0% |
| 10 | S12 | +1.086 | 0.331 | 3.3 | 10.80 | 2.47 | 14.5% |
| 11 | S16 | −1.002 | 0.323 | 3.1 | 11.34 | 2.60 | 13.0% |
| 12 | S20 | +0.920 | 0.326 | 2.8 | 11.94 | 2.76 | 8.5% |
| 13 | S17 | −0.749 | 0.305 | 2.5 | 13.65 | 3.10 | 2.5% |
| 14 | S6 | −0.594 | 0.316 | 1.9 | 15.45 | 3.86 | 1.0% |
| 15 | S9 | −0.584 | 0.293 | 2.0 | 15.44 | 3.48 | 0.0% |
| 16 | S8 | +0.347 | 0.302 | 1.2 | 18.30 | 3.96 | 0.0% |
| 17 | S14 | +0.279 | 0.326 | 0.9 | 18.53 | 3.81 | 0.0% |
| 18 | OS2 | +0.130 | 0.326 | 0.4 | 19.76 | 3.53 | 0.0% |
| 19 | S19 | −0.118 | 0.339 | 0.3 | 19.90 | 3.62 | 0.0% |
| 20 | S18 | −0.086 | 0.312 | 0.3 | 20.29 | 3.52 | 0.0% |
| 21 | S10 | −0.054 | 0.294 | 0.2 | 20.41 | 3.03 | 0.0% |
| 22 | S5 | −0.030 | 0.302 | 0.1 | 20.38 | 3.32 | 0.0% |
| 23 | OS3 | −0.023 | 0.311 | 0.1 | 20.18 | 3.25 | 0.0% |
| 24 | OS1 | +0.022 | 0.288 | 0.1 | 20.64 | 3.33 | 0.0% |
| 25 | S1 | −0.009 | 0.303 | 0.0 | 20.39 | 3.22 | 0.0% |

### Two findings the paper should use

**1. The noise floor is constant.** `sd|w|` sits between **0.280 and 0.387 for
every one of the 25 features**, independent of the coefficient's magnitude. This
is precisely the homoscedastic `ε` the paper's Eq. (17) assumes — and it is an
empirical result, not an assumption. It is worth reporting: it validates the
variance-reduction identity the whole framework rests on.

**2. Rank stability tracks SNR, and the cliff is sharp.**

| Band | Mean SNR | Median rank sd |
|---|---|---|
| ranks 1–5 (stable core) | 48.8 | 0.00 |
| rank 6 (S3) | 7.2 | 0.41 |
| ranks 7–8 (boundary) | 5.5 | 1.02 |
| outside top-8 | 1.3 | 3.32 |

Rank variance is exactly zero above SNR ≈ 15, small between SNR 5 and 7, and
grows sharply below SNR ≈ 5. That is the bimodal pattern §4.3 describes,
quantified.

### A protocol artifact worth fixing

**S21 is the true rank-8/9 boundary feature** — SNR 4.9, mean rank 9.01, in the
top-8 in 45.5% of untruncated runs. But under the paper's `num_features=8`
protocol, S21 essentially never surfaces (1.6% over 250 runs) and never appears
in Table 6.

The cause is the truncation issue: `num_features=8` makes LIME select features
and then **refit the surrogate on that subset**, which changes which features
appear at the boundary. Under the paper's protocol rank 8 is reported as S17 /
S2 / S8 / S14; untruncated, the real contenders are S21, S2, S12, S16.

So the paper's rank-8 row does not identify the feature that genuinely sits at
the top-8 boundary. Running each base explanation with `num_features=25` and
truncating only for display fixes it.

---

## 4. Data files

| File | Contents |
|---|---|
| `results/rank_occupancy.csv` | Per-rank modal feature, share, distinct count, entropy, mean weight — both methods |
| `results/rank_occupancy_full.csv` | Full occupancy distribution: every feature that holds every rank, with its share |
| `results/feature_snr.csv` | Per-feature mean weight, noise sd, SNR, mean rank, rank sd, top-8 rate |
| `results/rankwise.log` · `results/snr.log` | Raw output |
| `scripts/rankwise.py` · `scripts/snr.py` | Reproduce both |
