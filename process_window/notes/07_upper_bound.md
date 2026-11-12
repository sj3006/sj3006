# Note 7: the upper bound (Theorem 3), with a rigorous oracle part

Status: **draft, needs independent checking.** Prerequisites: notes 1, 5, 6.

## 1. What we can now prove, and what stays a conjecture

- **Theorem 3a (oracle allocation): rigorous.** If you knew which settings to
  test (a cover of the target), the expected number of coupons is bounded by a
  sum of per-setting stopping times, each controlled by Wald's identity.
- **Theorem 3b (learned allocation, with slack): conjecture with a sketch.**
  Adds the cost of learning where the target ends (note 6, section 5).

Together with the lower bounds (note 5), 3a shows the testing machinery is
within explicit factors of optimal. The gap between 3a and practice is the
learning term, which experiments quantify.

## 2. One setting: expected time to certify

Fix one (mode, setting) pair with true rate p < eps, weight w in the cone
rule, and coupons arriving i.i.d. there. Ignore help from other settings in
the cone (that only speeds certification up).

The cone rule certifies it once w K(t) >= 1/alpha, where K is the hedge
e-process: half agrapa, half an equal-weight mixture of 8 fixed bets
lambda_1..lambda_8 (note 1, section 5). So

    K(t) >= (1/16) K^{(lambda_j)}(t)   for every j,

and the setting is certified no later than the first time some fixed-bet
log-wealth

    Y_j(t) = sum_{s <= t} ln(1 + lambda_j (eps - Y_s))

reaches c = ln(16 / (alpha w)).

**Lemma (Wald).** For a fixed bet lambda with drift
g(lambda) = E ln(1 + lambda (eps - Y)) > 0, the first-passage time tau of the
random walk above level c satisfies

    E[tau]  <=  (c + b) / g(lambda),   b = ln(1 + lambda eps).

*Proof.* The increments are i.i.d. and bounded, with mean g > 0, so E[tau] is
finite and Wald's identity gives E[Y(tau)] = g E[tau]. At the passage time,
Y(tau) <= c + b, because the last step overshoots by at most the largest
possible increment, ln(1 + lambda eps) (a good coupon). ∎

**Corollary.** The expected coupons to certify the setting are at most

    min over j of  ( ln(16 / (alpha w)) + ln(1 + lambda_j eps) ) / g(lambda_j).

Write g_Lambda(p) = max_j g(lambda_j). The best possible rate for any test of
p >= eps against this p is KL(p || eps) (note 1), and g_Lambda(p) <= KL(p || eps).
With our bet grid and cap 0.8 (eps = 0.05):

| p | KL(p || eps) | g_Lambda(p) | ratio |
|---|---|---|---|
| 0.000 | 0.0513 | 0.0412 | 1.24 (the cap binds) |
| 0.010 | 0.0247 | 0.0247 | 1.00 |
| 0.025 | 0.0080 | 0.0078 | 1.03 |
| 0.040 | 0.0011 | 0.0011 | 1.05 |

So the fixed-bet grid loses at most 5% of the optimal evidence rate at the
settings that dominate the cost (rates near the target edge).

## 3. Theorem 3a (oracle allocation)

Let T be a target inside the window. For each mode m, let F_m be a set of
settings, all safe for m, whose safer cones cover T (a cover; the cheapest
covers sit on T's edge, note 5). Allocation: build coupons at one cover
point at a time until it is certified for its mode, then move to the next.

**Theorem 3a.** The expected number of coupons until T is certified (for
every mode) is at most

    sum over m, sum over z in F_m of
        ( ln(16 / (alpha w_{m,z})) + ln(1 + lambda* eps_m) ) / g_Lambda(p_m(z)),

where lambda* is the largest bet in the grid.

*Proof.* Certifying z for mode m makes every setting in z's safer cone
certified for m (spreading is built into the cone rule, note 6). The covers
F_m therefore certify T for every mode once all their points are certified.
The coupons spent are the sum, over (m, z), of the coupons spent while z was
being worked on, and each is at most the stopping time in section 2 (other
modes' coupons at the same setting only add evidence). Take expectations
and apply the corollary. ∎

**With uniform weights** w = 1/(M N), the log term is ln(16 M N / alpha), the
Bonferroni price. **With ensemble weights** concentrated on likely edge
points it approaches ln(16 |E| / alpha), where |E| <= M n on an n x n grid
(edge-size lemma).

## 4. How 3a and the lower bound fit together

Theorem 4a (note 5): any alpha-valid procedure needs at least
L * LP_A(T) coupons, with L = (1 - beta) ln(1/alpha) - ln 2 and the LP's
binding constraints at T's edge points. Taking F_m = edge_m(T) in 3a, the
ratio upper / lower is at most the product of

1. **testing price:** max_z ln(16 / (alpha w_z)) / L (about 5 for uniform
   weights on a 16x16 grid with three modes; less with ensemble weights);
2. **betting price:** max_z KL(p_z || eps) / g_Lambda(p_z) (1.00-1.05 for
   rates between 0.5% and 4%; 1.24 only for perfectly clean settings);
3. **sharing price:** sum_z 1/KL(p_z || eps) / LP_A(T), between 1 and the
   number of edge points, measured at about 1.2 on the toy grids.

None of these grows like the target's area. Both bounds scale with the
number of edge points, at most M n, which is the boundary. Against the
unordered lower bound (Theorem 4b), which sums over every target point,
the speed-up from the ordering is about |T| / (number of edge points),
times log factors.

## 5. Theorem 3b (learned allocation, with slack), conjecture

Same as note 6, section 5: add a membership-learning term for settings with
rates between q eps and q' eps on T's risky side, each costing about
ln(M N / beta) / ((q' - q) eps)^2 coupons. Needed for a proof:

1. a time-uniform confidence sequence for each setting's rate (for example
   the betting confidence sequences of Waudby-Smith & Ramdas 2024), to bound
   how long a wrongly classified setting stays wrong;
2. an argument that the optimistic re-check reaches every T point that was
   wrongly excluded;
3. the observation that coupons at a setting serve all modes.

Measured: on toy grids up to 32x32, the learned edge rule spends on the
necessary edge points about as much as the oracle; the excess goes to
settings just outside T (note 4, section 4b).

## 6. Check yourself

1. Why is Y(tau) <= c + ln(1 + lambda eps) and not just Y(tau) = c?
2. Why does evidence from other settings in z's cone only help?
3. In Theorem 3a, why is it enough that the covers' safer cones contain T,
   when the window needs T certified for every mode at once?
