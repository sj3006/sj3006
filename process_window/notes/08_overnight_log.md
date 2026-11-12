# Note 8: overnight research log (2026-11-12)

What was tried, in order, what worked, and what didn't. Numbers are from
runs committed in this branch; see `results/final/` and the commit messages.

## Iteration 1: replace chains with closed testing (worked)

**Idea.** The chain-based certifier (notes 2-4) had grown four structures
(chains, one-point chains, hybrid, budget families) and an open problem
(passing budget between chains with e-processes). Closed testing with the
weighted-sum e-value collapses all of it: certify k when the weighted
wealth in k's riskier cone reaches 1/alpha. Validity is three lines via
Ville (notes/06, Theorem 5).

**Result.** About as efficient as the hybrid on the "certify all of T"
goal (within run-to-run noise of about 10%), clearly better on the
"certify as much of the window as possible" goal (toy 24x24, 70% of the
window: 37.7k vs 43.1k coupons), far simpler, and the open budget-passing
problem disappears. Evidence pooling (cone vs max) adds about 8%.

## Iteration 2: where should the weights go? (partly worked)

- Band weights around the simulator's predicted edge: good with a good
  simulator, poor with an optimistic one (weight lands on unsafe settings).
- **Ensemble weights**: probability of being an edge point under perturbed
  simulators (logit shifts, sigma = 1), averaged over slightly wider
  targets, mixed 50/50 with uniform. Robust default: +17% better than
  uniform with a good simulator, never much worse with a bad one.
- Why gains are modest: certification needs ln(1/(alpha w)) nats; better
  weights save about 1 nat out of ~9.6. The dominant cost is the KL rate
  near the edge, which no testing rule can change.

## Iteration 3: bet cap (didn't help)

Raising the bet cap (0.8 -> 0.95) helps only perfectly clean settings and
hurts near-threshold ones, which dominate cost. Kept 0.8. Side result: the
hedge e-process is within ~12% of the KL-optimal evidence rate at a 2.5%
defect rate, so the per-setting test is near-optimal.

## Iteration 4: no simulator (fixed after two failures)

1. Flat prior: the frontier rule never tried unexplored settings (their
   estimated certification rate is exactly zero), and a single setting at
   4.9% (just under eps) absorbed 40,642 coupons. **Fix: optimism** in
   allocation (rate estimate minus one standard error). Toy 16x16 without a
   simulator: 50% of the window in ~19k coupons instead of never.
2. Pilot plate (4 coupons on every other setting): first version predicted
   an empty window because a single setting with 0/4 defects still gets a
   smoothed estimate above 5%. **Fix: pool raw counts through a monotone
   (isotonic) fit**, then use that as the simulator. Predicts 129-141 of
   140 window settings for 256 coupons. Pilot data never enter the tests.

## Iteration 5: a second application (worked)

Two-drug combination screen (toxicity rising in both doses, non-response
falling), Bliss-independence simulator ignoring the interaction. Same
partial-order structure; ours needs 1.5x fewer replicates for half the
window and is the only adaptive method to reach 70%.

## Iteration 6: rigorous upper bound (worked)

Wald's identity for each fixed bet inside the hedge gives E[tau] <=
(ln(16/(alpha w)) + b)/g per setting, so the oracle upper bound
(Theorem 3a, notes/07) is now a proof, not a sketch. Betting price KL/g is
1.00-1.05 at rates 0.5-4%.

## Iteration 7: when monotonicity fails (honest limitation, plus a tool)

A pocket of unsafe settings inside the window gets certified by spreading
in 75-92% of runs. Built an audit (defect-betting e-process on certified
settings). First version used a single large bet with *negative drift* at
15% rates and caught nothing; fixed with a mixture of bets. A full audit
(about 1.2x the certification budget) catches gross violations (15%) in
96-100% of runs, mild ones (8%) in 4-9%, never flags a safe setting.

## Iteration 8: consolidated benchmark (worked, with one negative result)

- Validity: all <= 2.75% at alpha = 5% (400 worst-case runs per row).
- Toy window: cost grows ~n^1.35 vs ~n^2.07 without the ordering;
  4.6x fewer coupons than unstructured and 10.7x fewer than grid DoE at
  48x48.
- **Negative:** on the Rosenthal 316L model the window is a thin diagonal
  band; ours is at parity with unstructured adaptive testing at 12-24.
  The area/edge ratio of that band is only 1.2-2.1 at those sizes (vs
  5-8 for the toy window); it grows to 4.2 at 48x48, so the theory
  predicts gains appear at finer grids (being tested).

## Iteration 9: the allocation rule was the weak link (big win)

An ablation showed the edge rule (aim at rates below 0.7 eps; build at the
riskiest uncertified settings of the estimated target, several coupons per
setting per plate) halving the cost of certifying half the window compared
with the greedy "frontier" rule I had used as default. Checked on four
scenarios at 24x24 (coupons to 70% of the window):

| scenario | frontier | edge, aim 0.7 eps |
|---|---|---|
| toy, good simulator | 37.5k | 15.1k |
| toy, optimistic simulator | 44.4k | 26.2k |
| Rosenthal 316L (thin band) | 60.0k | 25.5k |
| two-drug screen | 84.4k | 63.7k |

Aiming at the full window (no slack) is much worse: it chases settings
whose rates are barely below eps. Edge allocation also helps the
unstructured baseline, so both get it (fair comparison). With both on
their best rule, ours wins on every scenario, including the thin band
(1.8x at 70%), which turns iteration 8's negative result into a positive
one. The earlier parity came from the allocation rule, not the structure.
Frontier-based results are archived in `results/final/frontier_v1/`.

## Final numbers (edge allocation for every adaptive method)

- Validity: worst-case false-certification rates 0-2.75% at alpha = 5%
  (400 runs per row); no unsafe setting certified in any efficiency run.
- 24x24, coupons to 70% of the window, ours vs no ordering: toy 5.0x
  (optimistic simulator 3.3x), Rosenthal 316L band 1.5-1.7x, drug screen
  1.3x. Grid DoE never reaches 25% of an LPBF window in the same budget.
- Scaling to 48x48 (50% of the window): toy 9.1x fewer than no ordering
  and 26x fewer than grid DoE; Rosenthal band 2.2x and 42x. The band starts
  at parity at 12x12 and pulls ahead as predicted from its area/edge ratio.
- GP level-set baseline: certifies an unsafe setting in 7.5-100% of runs
  unless tuned so conservatively that it certifies at most 8% of the
  window; ours: 0 errors, 54-84% of the window at the same budget.
- Open problem, now quantified: on the strict "every setting of the
  target" goal, our cost relative to the ordered lower bound grows from
  5.7x (8x8) to 12.9x (32x32), driven by learning where the target ends.

## What I would do next

1. Get Amit's answers (process, outcome type, replicates, window shape).
   Window shape decides how large the practical gain is.
2. If real windows are thin bands: test physics-derived coordinates (for
   example lack-of-fusion index vs keyhole index), where the window becomes
   closer to a rectangle. Needs a monotonicity argument in those
   coordinates.
3. Learned-allocation theorem (3b) with slack.
4. Independent check of all proofs (notes 2, 5, 6, 7).
