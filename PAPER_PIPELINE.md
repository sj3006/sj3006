# Generating the paper's numbers from scratch

This is a **separate pipeline** from `scripts/`. The 13 scripts in `scripts/`
audit the existing draft — they print "paper says X, we got Y". Useful for
checking the old version, wrong for producing new numbers.

`paper/` produces the numbers themselves, with the methodological fixes built
in. Whatever it prints is what goes in the manuscript.

---

## The five files you run

```bash
pip install -r requirements.txt     # ./install_lime.sh if lime fails to build
# put Full_Dataset.xlsx in the project root, or set AIRCRAFT_XLSX

./paper/run_paper.sh                # runs all five stages in order
```

| Stage | Produces | Paper section |
|---|---|---|
| `paper/01_dataset.py` | `t01_dataset.csv`, `t01_sensors.csv` | Dataset table, sensor overview |
| `paper/02_model.py` | `t02_model.csv` | Model performance table |
| `paper/03_explanations.py` | `t03_single_explanation.csv`, `t03_walime_explanation.csv` | Explanation figures, local fidelity |
| `paper/04_stability.py` | `t04_stability.csv`, `t04_stability_per_instance.csv` | **The headline result** |
| `paper/05_rank_snr.py` | `t05_rank_occupancy.csv`, `t05_rank_pooled.csv`, `t05_feature_snr.csv` | Rank-stability and SNR tables |

Everything lands in `paper_outputs/` as CSV (tables) plus JSON (metadata) plus a
`.log` per stage. Stages run in order because 02–05 all rebuild the same seeded
model; each is still runnable on its own.

`paper/config.py` holds every knob. `paper/_lib.py` is the shared machinery —
data, model, explanation engines, metrics. Neither is run directly.

---

## Set config.py before you run anything

The run is only as defensible as these values, and the paper's Methods section
should quote them.

```python
SPLIT       = "random"    # or "grouped"
N_INSTANCES = 8           # instances explained, stratified across the RUL range
R_REPEATS   = 50          # repetitions per method per instance
B_AGG       = 5           # WA-LIME aggregation depth
B_SWEEP     = (2,3,5,10,20)
R_RANK      = 100
RUN_COMPUTE_MATCHED = True
```

For the final submission run set `R_REPEATS = 100`. Everything is seeded, so
the same config reproduces the same numbers exactly.

---

## What this pipeline does differently, and why

Each of these is a decision a reviewer can challenge, so each is worth a
sentence in the Methods section.

**Eight instances, not one.** A single explained instance is an anecdote. The
instances are drawn stratified across the RUL range, so the stability result is
a property of the model rather than of one lucky mid-life cycle. Stage 04
reports pooled means with the spread across instances, and
`t04_stability_per_instance.csv` has the per-instance breakdown.

**R = 50 repetitions, not 5.** Five runs give 10 pairs and a standard deviation
around 0.05 on mean Jaccard — wide enough that the estimate lands almost
anywhere. Fifty runs give 1,225 pairs per instance. Stage 04 also reports a
bootstrap interval resampled over *runs* (not pairs, which are dependent).

**Untruncated explanations.** LIME's `num_features` does feature selection and
then *refits the surrogate on that subset*, so asking for 8 features changes the
model being explained, not just what is shown. Every metric is computed on the
full 25-feature weight vector; truncation happens only for display.

**Spearman over all features, not the intersection.** Computing it on the
intersection of two top-k sets nearly guarantees ≈1: the surviving features are
the high-SNR ones whose order is stable by construction, so the statistic throws
away exactly the features whose ordering is in doubt.

**A compute-matched control.** WA-LIME with B=5 spends five times the
perturbation budget of one LIME call. Stage 04 therefore also runs plain LIME
with `num_samples = B × 5000` and prints an explicit verdict comparing the two.
Without this, a reviewer cannot tell aggregation from extra sampling — and it is
the first baseline they will ask for.

**Both splits reported.** Stage 02 evaluates the row-level split (conventional,
comparable to prior CMAPSS work) *and* the engine-grouped split (no engine on
both sides). Report both; the grouped number is the defensible one.

**Signed weights kept.** Stage 03 reports the WA-LIME explanation as both mean
|w| (for ranking) and mean signed w (for direction). Averaging only magnitudes
loses whether a sensor pushes predicted RUL up or down, which is the actionable
content for a maintenance engineer.

---

## Reading stage 04's verdict

Stage 04 ends by comparing WA-LIME against the compute-matched baseline and
printing one of three verdicts. **Read it before writing the abstract.**

If WA-LIME does not beat plain LIME at equal budget, the claim "aggregation
stabilises explanations" is not supported as stated, and the honest options are
to re-frame the contribution (simplicity, or the budget/stability curve from
`B_SWEEP`) or to find a regime where aggregation genuinely wins. The candidate
is robustness to *background* choice — aggregating over resampled backgrounds
targets a variance component that raising `num_samples` cannot touch. That would
need its own experiment; the pipeline does not currently run it.

Do not delete the compute-matched row from the results table because it is
inconvenient. It is one line of CSV and its absence is more conspicuous than its
presence.
