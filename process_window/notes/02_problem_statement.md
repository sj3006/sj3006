# Note 2: problem statement and Theorem 1 (validity), v0

Status: **draft, needs independent checking** before it goes in a paper.
Read note 1 first. Your Day 6 task is to rewrite section 1 in your own words.

## 1. Setup

**Settings.** A finite grid X of process settings (for now, laser power x
scan speed). Later we extend to a continuous box.

**Failure modes.** m = 1, ..., M (lack of fusion, keyhole, balling).

**Coupons.** Building a coupon at setting x gives an outcome vector
Y = (Y_1, ..., Y_M) in [0, 1]^M (1 = defect of that type). Coupons at x are
independent draws from an unknown distribution P_x. Modes may be dependent
within a coupon (a coupon can have two defect types at once). The defect
rate of mode m at x is p_m(x) = E[Y_m].

**Thresholds.** eps_m in (0, 1). Setting x is safe for mode m if
p_m(x) < eps_m. Write S_m for the set of such settings.

**Process window.** W = S_1 ∩ ... ∩ S_M.

**Physics ordering (Assumption A).** For each mode m there is a known
partial order ⪯_m on X, where "x ⪯_m y" means "y is at least as safe as x
for mode m", and

    x ⪯_m y  implies  p_m(y) <= p_m(x).

On the (power, speed) grid:

| mode | y is at least as safe as x when |
|---|---|
| lack of fusion | power(y) >= power(x) and speed(y) <= speed(x) |
| keyhole | power(y) <= power(x) and speed(y) >= speed(x) |
| balling | power(y) >= power(x) and speed(y) <= speed(x) |

**Consequence.** Under A, each S_m is an *up-set* for ⪯_m: if x is in S_m
and x ⪯_m y, then y is in S_m. (Proof: p_m(y) <= p_m(x) < eps_m.)

**Goal.** Output a set Ŵ of settings with P(Ŵ ⊆ W) >= 1 - alpha, while
building as few coupons as possible, choosing adaptively where to build.

## 2. The procedure (as in `pwcert/certify.py`)

1. **Chains, chosen before any test data.** For each mode m, pick chains
   C_{m,1}, ..., C_{m,K_m}. Each chain is a list of settings
   (x_1, x_2, ...) that gets *less safe* as you go:
   x_{r+1} ⪯_m x_r. Chains may use the simulator, or a pilot plate whose
   coupons are never used in step 2. In the code: one chain per speed row,
   starting at the simulator's best guess and walking toward the risky side
   for that mode.
2. **One e-process per (mode, setting).** Each coupon at x updates the
   betting wealth K^{m,x} for every mode m (note 1). Bets are chosen before
   the coupon is inspected.
3. **Budgets.** Chain C_{m,k} gets error budget alpha_{m,k}, with
   sum over all (m, k) of alpha_{m,k} <= alpha. In the code it's
   Bonferroni: alpha / (total number of chains).
4. **Fixed-sequence rule.** In each chain, only the *current* point may be
   certified for that mode, and only when its wealth reaches
   1/alpha_{m,k}. After that, the chain moves on to its next point not
   already covered by step 5.
5. **Spreading.** If z is certified for mode m, every y with z ⪯_m y is
   marked certified for m. Let Ĉ_m be the set of all such marked settings.
6. **Output.** Ŵ = Ĉ_1 ∩ ... ∩ Ĉ_M. The allocation rule (where to build the
   next plate) may be anything that is decided before that plate's coupons
   are inspected.

## 3. Theorem 1 (validity)

**Theorem 1.** Under Assumption A, with chains chosen independently of the
test data, bets and allocations chosen before the coupons they apply to
are inspected, and sum_{m,k} alpha_{m,k} <= alpha:

    P( Ŵ_t ⊆ W for every time t ) >= 1 - alpha.

"For every time t" means you may stop after any plate, for any reason, and
the guarantee still holds. It holds for any simulator.

### Proof

*Step 1: reduce to "some unsafe point was certified directly."* Suppose at
some time a setting x is in Ŵ but not in W. Then for some mode m, x is in
Ĉ_m but not in S_m. Being in Ĉ_m means x was spread from some directly
certified z with z ⪯_m x. If z were safe for m (z in S_m), then x would be
too, because S_m is an up-set. So z is unsafe for m: an unsafe point was
certified *directly* (in step 4). Call this event E_m.

*Step 2: the first mistake happens at a predictable place.* Fix mode m. For
each chain k, let z*_k be the first point of chain k that is unsafe for m
(if the chain has none, it can never cause E_m). Because chains get less
safe as they go, every point after z*_k is unsafe too, and every point
before it is safe. Note z*_k is a fixed point: it depends only on the chain
(fixed before the test data) and on the unknown truth, not on the data.

Consider the first time tau at which any unsafe point is certified directly
for mode m, in chain k say. Before tau, every certified point was safe, so
everything spread from them was safe as well. So up to tau, chain k only
ever moved past safe points, which means its current point at tau is at
or before z*_k. The point certified at tau is unsafe, so it can only be
z*_k itself. Hence

    E_m  ⊆  union over k of { K^{m, z*_k} reaches 1/alpha_{m,k} at some time }.

*Step 3: Ville.* z*_k is unsafe, so H0 holds there, and its wealth process
is a nonnegative supermartingale starting at 1 (note 1, section 3). This
uses two facts: each coupon's location was decided before the coupon was
inspected, and given its location and the past, the coupon is a fresh
draw from P_{z*_k}. Ville's inequality gives

    P( K^{m, z*_k} ever reaches 1/alpha_{m,k} ) <= alpha_{m,k}.

The wealth was updated by every coupon ever built at z*_k, including ones
built before z*_k became the current point. That's fine because Ville
covers all times at once.

*Step 4: add up.* P(some error at some time) <= sum_m P(E_m)
<= sum_{m,k} alpha_{m,k} <= alpha. ∎

### Things to check in this proof (your Day 5-6 exercise)

1. Where exactly is Assumption A used? (Twice: in step 1 and in "every
   point after z*_k is unsafe" in step 2.)
2. Why must the chains be fixed before the test data? Construct a cheating
   procedure that picks chains after peeking, and show how it breaks step 2.
3. Why is it fine for one coupon to update several modes' wealth at once,
   even though the modes are dependent? (Hint: step 4 is a union bound, and
   union bounds don't care about dependence.)
4. A build plate holds many coupons whose locations were all chosen before
   any of them were inspected. Check that step 3 still goes through if we
   process them one at a time in a fixed order.
5. The futility rule stops a chain. Why can stopping a chain never cause
   an error?

## 4. Corollary (continuous region)

If the grid sits inside a continuous box of settings and Assumption A holds
on the whole box, the same proof shows that the region

    R = ∩_m  ∪_{z certified for m}  { y in the box : z ⪯_m y }

contains no unsafe setting, with probability >= 1 - alpha. So the
certificate covers a continuous region, not only grid points, with no
smoothness assumption. (Spell this out properly in week 2: it's Theorem 2
in the roadmap.)

## 5. What is not proven yet

- **Efficiency.** Nothing above says the method certifies much. That is
  Theorem 3 (upper bound) and Theorem 4 (lower bound), weeks 5-6.
  Working conjecture, from note 1, section 4: the expected number of coupons
  to certify a target subset T of W is about

      sum over points z that must be certified directly
          ln(number of chains / alpha) / KL(p_m(z) || eps_m),

  and the number of such points scales with the boundary of T, not its
  area. Experiment 2 is the first empirical check.
- **Budget passing between chains.** Bonferroni wastes budget on chains
  that finish early. A graphical procedure (Bretz et al. 2009) passes it
  on. We need to prove it keeps Theorem 1 with e-processes and adaptive
  stopping (week 3).
- **Choosing chains from data.** Right now a wrong start point loses a
  whole row. A pilot plate fixes this legally; can we do better without
  splitting data?
- **Assumption A failing.** If physics monotonicity breaks somewhere (for
  example spatter at very high power), the guarantee can fail there. We
  need a sequential check that flags violations (week 3).
