# Likely reviewer questions and our answers

For the rebuttal. Each answer is short and points to the evidence. Numbers
are from the current paper (main.tex) and the result files. "We can run"
items are cheap on CPU unless marked GPU.

## Assumptions

**1. Monotonicity is strong. What if it fails?**
The guarantee needs it, and we say so (Assumption A, Limitations, Impact
Statement). Evidence that it holds where we use it:
- Language models: no setting deviates from the monotone fit at the 1%
  level (exact binomial test) on either grid or on the second model; 1 of
  264 neighbouring pairs is reversed by more than 2 SE (8 of 1012 on the
  23x23 grid). Files: results/lm/lm_monotone_check*.csv.
- Manufacturing: in published 316L melt-pool data (11 single-track
  studies, MeltpoolNet), depth and width grow with power and shrink with
  speed in every study; 5 of 942 neighbouring pairs reverse by more than
  2 SE. File: results/final/am_monotone_check.csv.
- When it fails: a pocket of unsafe settings inside the safe region is
  certified by spreading in 75-92% of runs; an audit flags gross
  violations (96-100%) but rarely mild ones (4-9%). Section 6, "When
  monotonicity fails"; results/final/violation.csv.
We can add: a pre-registered audit budget recommendation (it is a
parameter of the audit already).

**2. Trials are not independent in practice (builds on one plate, prompts).**
True for plates, and now tested (Section 6 "Correlated trials", Appendix B,
`experiments/plate_effects.py`, `results/final/plate_effects_*.csv`). With a
beta-binomial plate effect, feeding trials one by one breaks validity:
- worst case (every setting at the tolerance, 8x8, plates of 16): 0.75% at
  intra-plate correlation 0.05, 23% at 0.2;
- one setting with 24 trials per plate: 17% at 0.05, 57% at 0.2.

Two fixes are valid for any correlation, and neither erred in any run:
- one outcome per setting per plate (the plate's failure fraction). It
  costs 19x more trials, because the edge rule stacks trials of one
  setting on a plate.
- a plate-aware edge rule (one trial per setting per plate). It costs
  2.4x more trials and plates than the independent case.

A plate is worth one to two independent trials of a setting, however many
it holds. That is the price of not knowing the correlation; with a known
bound on it one could do better (future work). For language models the
prompts are drawn independently at random, so generations are i.i.d. given
the setting.

**3. Knobs are continuous; you certify a grid.**
New remark in Section 2 ("Between grid points"): with monotone rates, a
cell is covered once each mode's riskiest corner is certified, on the same
event, at no extra cost.

**4. Why FWER and not FDR?**
A certificate is a safety claim: one unsafe setting in the set is a
failure of the whole certificate. FDR would allow a fixed fraction of
unsafe settings, which a qualification engineer cannot use.

## Baselines

**5. A tuned GP or Bayesian optimizer does as well.**
Partly true, and the paper says it. BEAM-style active search at confidence
parameter 4 and lengthscale 0.1 erred in 1 of 40 runs on each simulated
problem and 1 of 20 on the language model, covering 66-94% (ours 54-90%).
But with lengthscale 0.3 the same setting errs in 35-42.5% of runs on two
problems, and nothing in the data says which tuning is safe. One error in
40 runs only bounds the error rate by 13%. In the all-at-tolerance worst
case the GPs rarely err (0-1.25% for BEAM-style); their failures come from
sharp transitions the kernel smooths over. Our guarantee does not depend
on the surface's shape. Files: results/final/gp_baseline*.csv,
gp_validity.csv, results/lm/lm_gp*.csv.

**6. SafeOpt has guarantees.**
Under a known RKHS-norm bound and a correct kernel. Our safe-expansion
baseline (SafeOpt / M-SafeUCB style, with the ordering) either stalls at
its seed (0.7-3.7% of the region) or, at the longest lengthscales,
certifies an unsafe setting in every run.

**7. Learn-then-Test already uses monotonicity.**
Along one axis, on a fixed grid, with a fixed sample per setting. Ours is
19-26x cheaper than full-grid fixed-sequence testing at 48x48, and 3.1x
(12x12) to 8.1x (23x23) cheaper on the language model. The gap grows with
resolution, as the edge-vs-area bounds predict.

## Experiments

**8. The language-model failures are proxies (repetition, own NLL).**
They are standard (seq-rep-n from Welleck et al. 2020; NLL), and the gains
hold over seven alternative definitions (thresholds and tolerances; 70
runs, no false certificate). A task-level failure (format errors, an LLM
judge) is tier C in COMPUTE_PLAN.md.

**9. The models are small.**
135M, 0.5B and 1.5B, all measured (Tables 1-2). Across the three, the gain
over no ordering at half the safe region is 1.6-2.1x (2.1-3.0x at 70%),
and the safe region grows slightly with size (78, 86, 88 of 144
settings). 7B models from three families are tier A in COMPUTE_PLAN.md
(about 10 GPU-hours). The method's cost does not depend on model size;
only measuring the reference surface does.

**10. Benchmark runs resample a fitted surface instead of querying the model.**
The live run queries SmolLM2 directly: 8.0k generations certified 64 of
78 safe settings and no unsafe one, in line with the 65 certified on
average by surface runs at the same budget. More live runs (other seeds,
other models) are cheap on CPU for the small models and part of tier A on
a GPU.

**11. Few runs per configuration (5-8).**
Medians of costs that vary little between runs (the per-run costs are in
the CSVs). Validity uses 400 runs per configuration, GP baselines 40.
More runs are cheap on CPU if a reviewer asks.

**12. The manufacturing results are simulated.**
Yes. No public data set repeats builds at each setting, so failure rates
cannot be measured from the literature; published process maps give one
observation per setting. We use published measurements where they are
informative (the monotonicity check) and show the gains do not depend on
the placeholder calibration (absorptivity and thresholds moved by 10-20%:
still 1.4-2.5x cheaper than no ordering, 14-62x cheaper than full-grid
fixed-sequence testing).

## Theory

**13. The search is 9-15x above the lower bound.**
The gap is the multiple-testing factor (about 5 at 32x32, paid equally by
the per-setting test against its own bound: 4.5-5.9x) and the O(log n)
probe factor. Closing it needs a better multiple-testing scheme for the
search; we tried weight mixes and probe rules without gain (ROADMAP
2026-11-14).

**14. Condition (T) on the bets.**
Checked numerically for every tolerance we use (5-50%); it fails only
below about 2%, where adding a smaller rejection bet restores it.

**15. Novelty against closed testing / e-values.**
The cone rule is closed testing with betting e-processes, and the paper
says so. What is new: it reduces to two cumulative sums under
monotonicity (so it is fast); it stays valid under adaptive allocation
and side information; and the edge-vs-area lower bounds explain the
gains. The search is near-optimal up to the stated factors.

## Practical

**16. How much compute does the method itself need?**
Negligible: two cumulative sums per mode per batch. The cost is the trials.

**17. What if the side information is wrong?**
It affects only cost, never validity. Validity with adversarial side
information (predicting 0.1% or 1% everywhere) is 0-2.75% at alpha 5%
(400 runs). With optimistic side information the search needs 215k trials
at 32x32 against 458k without the ordering.
