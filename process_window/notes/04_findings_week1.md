# Note 4: what the first experiments taught us, and the revised theory target

Status: working notes. Numbers come from `results/` and from exploratory
runs logged in the commit messages.

## 1. Validity holds everywhere we looked

- One setting (exp01): false-certification rate at the worst-case null
  p = eps stays at or below 5% for every betting strategy, including a lying
  simulator.
- Whole grid, worst case (exp02 part A, 200 runs each): FWER of 0.020,
  0.025, 0.040, 0.030 and 0.000 across five configurations, all below 0.05.
- No run in any efficiency experiment ever certified an unsafe setting.

This is what Theorem 1 predicts. It's the part of the paper we can already
stand behind.

## 2. The simulator matters for where to test, not how much to bet

Seeding the bets with an accurate simulator saved about 6% of coupons for a
single setting (73 vs 78 at p = 0); a pessimistic one cost about 50% more.
Choosing where chains start, and which settings go on each plate, mattered
far more. The method section should present the simulator as a **design
tool for the experiment**, with bet seeding as a minor extra.

## 3. The big one: why chains scale with area, and what doesn't

The first design walked chains one point at a time from the middle of the
window toward its edge. On finer grids its cost grew like the window's
*area* (about 4x per doubling of n), not its boundary.

The reason is physical. Defect rates don't jump at the window edge; they
rise over a transition band of fixed physical width (in power and speed).
Refining the grid puts more points inside the band, and a chain must
certify every one of them in turn. Band points have rates close to eps,
so each one is expensive (cost about ln(1/alpha) / KL(p || eps), note 1).

What spreading really needs is different. One certificate at the riskiest
certifiable setting covers everything safer. So the efficient procedure
certifies a small set of settings along the edge of the region we want and
lets spreading fill in the rest. Two ways to get there:

- **Boundary-start chains.** Start each chain near the predicted edge.
  Excellent with a good simulator; with an optimistic simulator the start
  lands on an unsafe setting and the chain never certifies anything.
- **Spread (one-point chains plus spreading).** Test any setting at
  Bonferroni level alpha / (M N) and let the allocation rule pick the
  settings worth certifying. Pays a log factor, but doesn't depend on
  getting starts right.
- **Hybrid** runs both with half the budget each. Exploratory runs on the
  toy model: 70%-of-window cost at 24x24 was 27k coupons (chains,
  good simulator), 43-45k (spread, either simulator), 64k (chains,
  optimistic simulator), 96k (no ordering). exp03 measures the hybrid.

The allocation rule ("frontier") chooses settings with the most new
predicted-window area per expected coupon:
gain / (remaining log-wealth / KL(p_hat || eps)).

## 4. Revised theory target

The quantity that should govern the cost is a **weighted cover of the target
region**. For a target region T inside the window and each mode m, we must
certify a set of settings F_m whose safe quadrants cover T. Certifying z
costs about ln(1/alpha) / KL(p_m(z) || eps_m) coupons, so define

    C*(T) = sum over modes m of  min over covers F_m of T
                sum_{z in F_m}  1 / KL(p_m(z) || eps_m).

The cheapest covers sit on the edge of T. If T stays a fixed distance
inside the window, its edge has about n grid points on an n x n grid, so
C*(T) grows like n (the boundary), while T has about n^2 points (the area).

**Theorem 3 (upper bound, target).** With the spread structure and an
allocation rule that finds the cheapest cover, the expected number of
coupons to certify T is at most about C*(T) * ln(M N / alpha), plus lower
order terms for learning which settings form the cover.

**Theorem 4 (lower bound, target).** Every procedure that certifies T with
error at most alpha needs at least about C*(T) * ln(1 / alpha) coupons in
expectation. Proof idea: the standard change-of-measure argument for
pure-exploration bandits (Garivier & Kaufmann 2016; Kaufmann, Cappe &
Garivier 2016). For each cover point z, imagine the world where p_m(z) is
nudged just above eps_m. The procedure must behave differently there, which
takes at least ln(1/alpha) / KL coupons at z.

**What we can claim if both hold:** the spread structure is optimal up to a
ln(M N) factor, and the factor separating it from any unstructured method is
area / boundary. That's the ICML-level result. The chains are then an
efficiency improvement on the log factor when the simulator is good, and
the hybrid makes the method robust.

**Caveat to check early:** the "learning which settings form the cover"
term. If it isn't lower order, Theorem 3 needs a different shape. Measuring
how far the frontier rule is from an oracle that knows the true rates is a
good week-2 experiment.

## 4b. Allocation: the lower bound tells you where to test

`experiments/exp05_bounds.py` computes Theorem 4a's lower bound (an LP),
Theorem 4b's, and the oracle upper bound, next to measured costs, for the
target T = {all rates <= eps/2}. Smoke-test numbers (3 runs):

| grid | lower bound, ordering | lower bound, no ordering | oracle upper bound |
|---|---|---|---|
| 8x8 | 987 | 1,787 | 5,142 |
| 12x12 | 2,142 | 5,050 | 11,793 |
| 16x16 | 2,902 | 8,572 | 16,733 |

The ordered bound grows about linearly, the unordered one about
quadratically. The gap between the oracle upper bound and the ordered lower
bound (5.2x at 8x8) is accounted for by the Bonferroni log factor
(ln(M N 16 / alpha) / L, about 5.1) and the bet cap (about 1.24), partly
offset because the LP lets one coupon count toward several edge
constraints (about 1.2x).

Getting the *algorithm* to track the oracle took three fixes, each forced
by a failure:

1. **Greedy "area per coupon" wastes coupons on the interior.** At 16x16 it
   spent 16k coupons on target-interior points, which spreading from the
   edge covers for free. Fix: the **edge rule** samples only the current
   riskiest uncertified points of the estimated target, for each mode.
   These are exactly the binding constraints of Theorem 4a, so the rule
   is the lower bound's own structure used as an algorithm. It also fills
   plates with several coupons per point instead of one each.
2. **A hard cap of 800 coupons per setting** abandoned target points with
   rates near 2%, which need 1,000-1,400. Removed.
3. **Exploration trap.** A safe target point with an unlucky streak looks
   unsafe, stops being sampled, and is never certified. Fixes: futility
   only when *confidently* unsafe (estimate minus 2 standard errors above
   eps), and once the estimated target is covered, **re-check** the
   uncertified points with the lowest lower confidence bound (optimism).

Result, coupons to certify all of T (median of 3):

| grid | oracle allocation / UB | learned allocation / UB |
|---|---|---|
| 8x8 | 0.76 | 1.06 |
| 16x16 | 0.74 | 1.50 |
| 24x24 | 0.81 | 2.18 |

With the oracle, the edge rule sits just under the upper bound at every
size. The learned version's overhead still grows slowly with n. **That
growth is the open "learning term" in Theorem 3**, and it now has a
concrete shape: wasted coupons on points whose estimated membership in T
flips. Candidate remedies for week 2: smaller prior weight, sharing
information across neighbouring settings (monotone smoothing of the
estimates), and confidence-based edge selection.

**Where the learned overhead goes (24x24, one run):**

| category | oracle | learned |
|---|---|---|
| target edge (necessary) | 30,672 | 31,102 |
| target interior | 0 | 7,182 |
| window outside target | 0 | 38,764 |
| unsafe | 0 | 9,832 |

The learned rule certifies the necessary edge points as efficiently as the
oracle. Nearly all the overhead goes to settings just outside the target,
mostly during the re-check phase. That's inherent in the goal, not a bug:
the target's edge points have rates right at q * eps *by definition*, so
deciding which settings are in T is itself a thresholding problem at
q * eps, and finer grids put more settings near that line.

Two negative results: isotonic smoothing of the estimates (`smooth=True`)
did not reliably reduce the overhead; a 2-standard-error re-check rule is
needed for completion but is what spends the extra coupons.

**Consequence for Theorem 3: state it with slack**, as in (eps, delta)-PAC
pure exploration. Guarantee that every setting with rate <= q * eps gets
certified, while allowing spending on settings with rate up to q' * eps
(q < q' < 1). The membership-learning cost then depends on the gap
(q' - q) * eps and can be bounded explicitly. This is also the natural
engineering goal ("certify everything comfortably safe; borderline
settings may be certified too").

On the easier goal of certifying a *fraction* of the window (exp04),
learned allocation already matches the oracle (ratios 0.76-1.08 up to
24x24), so the learning cost only bites when every point of a target must
be certified.

## 5. Physics findings that change modelling choices

- With a Rosenthal melt pool, **balling increases with both power and speed**
  (length/width grows with power at high Peclet number), not decreasing with
  power as first assumed. The code now *measures* monotone directions from
  the ground truth instead of assuming them. Which balling mechanism
  dominates in a real process (Plateau-Rayleigh elongation vs. poor wetting
  at low power) is a question for Amit.
- Literature thresholds (keyhole ~30, balling ~pi) don't transfer to a crude
  Rosenthal pool; `physics.Criteria` uses placeholder calibrations.
- The physics-based window on (power, speed) is a **thin diagonal band**
  along roughly constant energy density, the typical shape of real LPBF
  windows. Thin bands are the hard case for spreading (area close to
  boundary).
- Idea to explore: in physics-derived coordinates (for example
  lack-of-fusion index vs. keyhole index), each mode depends mostly on one
  axis and the window becomes close to a rectangle, where spreading is far
  more powerful. Monotonicity in those coordinates would need justifying.

## 6. Open questions this raised

1. Can the frontier rule provably find the cheapest cover (Theorem 3's
   learning term)?
2. Budget passing between chains with e-processes (note 3, section 4).
3. How sensitive is everything to the transition-band width? (It sets how
   expensive the edge is.)
4. Is the real LPBF window a thin band in (power, speed)? Your data will
   tell.
