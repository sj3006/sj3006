# Note 5: how many coupons any valid method needs (Theorem 4), draft

Status: **draft proof, needs independent checking.** Prerequisites: note 1
(KL as the per-coupon evidence rate), note 2 (setup), note 4 (why the cost
should depend on the edge of the target region). Read alongside
Garivier, Menard & Rossi 2017 (Day 5): this is the 2D, multi-mode version
of their monotone lower bound.

## 0. The idea in one paragraph

To certify a setting z, a method has to rule out the possibility that z is
actually unsafe. If z were unsafe, monotonicity would force every setting
riskier than z to be unsafe too, so the "z is unsafe" world differs from
the real one only on z and the settings riskier than it. Evidence that
separates the two worlds can only come from coupons built there, and each
coupon supplies at most KL(p || eps) nats. Collecting ln(1/alpha) nats is
unavoidable. With the physics ordering, only the riskiest points of the
target region generate such constraints, and there are at most n of them
per mode on an n x n grid. Without the ordering, every point of the target
does. That's the area-vs-boundary gap, as a theorem.

## 1. Setting for the lower bound

- Grid X, modes m = 1..M, Bernoulli outcomes with means p_m(x), modes
  independent within a coupon (a lower bound for this sub-class is a lower
  bound in general).
- An **instance** nu is the table of means p_m(x).
- Class A: instances satisfying Assumption A (monotone in the known
  directions). Class U: all instances (no structure).
- A procedure is **alpha-valid on a class** if for every instance in the
  class, P(the final output contains an unsafe setting) <= alpha.
- For an instance nu and a target T inside the true window W(nu), the
  procedure **certifies T with probability 1 - beta** if
  P_nu(T ⊆ output) >= 1 - beta.
- tau = total coupons used, N_y = coupons used at setting y.

Shorthand: k_m(y) = KL(Bernoulli(p_m(y)) || Bernoulli(eps_m)) for
p_m(y) < eps_m. This is the evidence per coupon (note 1, section 4).

## 2. The tool: the transportation lemma

**Lemma (Kaufmann, Cappe & Garivier 2016, Lemma 1).** For two instances
nu, nu', a stopping time tau that is finite almost surely under both, and
any event E decided by time tau,

    sum over settings y of  E_nu[N_y] * KL(nu_y, nu'_y)  >=  kl(P_nu(E), P_nu'(E)),

where nu_y is the distribution of one coupon's outcome vector at y and
kl(a, b) is the KL divergence between Bernoulli(a) and Bernoulli(b).

We use it with E = {T ⊆ output} and the elementary bound
kl(a, b) >= a ln(1/b) - ln 2.

## 3. Alternatives that respect the physics

Fix a mode m and a setting z in T. Let D_m(z) be the settings that are
riskier than or equal to z for mode m *and* safe for m:

    D_m(z) = { y : y ⪯_m z and p_m(y) < eps_m }.

Define the alternative nu' = nu^{(m,z)} by raising mode m to at least
eps_m + eta on everything riskier than or equal to z:

    p'_m(y) = max(p_m(y), eps_m + eta)   if y ⪯_m z,   p'_m(y) = p_m(y) otherwise.

Only settings in D_m(z) actually change once eta is small (unsafe settings
riskier than z already have p_m >= eps_m, and as eta -> 0 any change to
them costs KL -> 0).

**Claim: nu' is still in class A.** Take x ⪯_m y; we need p'_m(y) <= p'_m(x).
- If y ⪯_m z, then x ⪯_m z too, and max(p_m(y), c) <= max(p_m(x), c)
  because p_m(y) <= p_m(x).
- If y is not ⪯_m z but x is: p'_m(y) = p_m(y) <= p_m(x) <= p'_m(x).
- If neither is: nothing changed.

In nu', z is unsafe, so any alpha-valid procedure has P_nu'(T ⊆ output)
<= alpha.

## 4. Theorem 4a (with the physics ordering)

**Theorem 4a.** Let a procedure be alpha-valid on class A and certify T with
probability 1 - beta on an instance nu in class A. Then, for every mode m
and every z in T,

    sum over y in D_m(z) of  E_nu[N_y] * k_m(y)  >=  L,   with L = (1 - beta) ln(1/alpha) - ln 2.

Consequently

    E_nu[tau]  >=  L * LP_A(T),

where LP_A(T) is the value of the linear program

    minimize   sum_y n_y
    subject to sum_{y in D_m(z)} n_y k_m(y) >= 1   for all m and all z in T,
               n >= 0.

*Proof.* Apply the lemma to nu and nu^{(m,z)} with E = {T ⊆ output}. Only
mode m on D_m(z) changes. Since modes are independent within a coupon, the
per-coupon KL at y in D_m(z) is KL(Bern(p_m(y)) || Bern(eps_m + eta)),
which tends to k_m(y) as eta -> 0. So
sum_{y in D_m(z)} E[N_y] KL_eta(y) >= kl(1 - beta, alpha) >= L.
Let eta -> 0. The expected counts n_y = E[N_y] / L are feasible for the LP,
so sum_y E[N_y] >= L * LP_A(T). ∎

**Only the riskiest points of T matter.** If z ⪯_m z' (z' safer), then
D_m(z) ⊆ D_m(z'), so z's constraint implies z''s. The binding constraints
come from the ⪯_m-minimal points of T, call them edge_m(T).

**Lemma (edge size).** On an n_P x n_V grid with a product order, edge_m(T)
has at most min(n_P, n_V) points.
*Proof.* The minimal points form an antichain. Two settings in the same
speed row are comparable (one has more power at the same speed), so an
antichain has at most one point per row; the same holds for columns. ∎

So Theorem 4a has at most M * n binding constraints on an n x n grid, which
is about the length of the region's edge.

## 5. Theorem 4b (without the ordering)

**Theorem 4b.** Let a procedure be alpha-valid on class U and certify T with
probability 1 - beta on an instance nu. Then

    E_nu[tau]  >=  L * sum_{z in T} max_m 1 / k_m(z).

*Proof.* In class U we may change a single setting: let nu' raise p_m(z)
to eps_m + eta and leave everything else alone. The lemma gives
E[N_z] k_m(z) >= L for every m, so E[N_z] >= L max_m 1/k_m(z). Sum over
z in T. ∎

So without the ordering, every point of the target must be sampled
directly: the cost grows with the **area** of T.

## 6. The matching upper bound (Theorem 3), sketch

Take the spread structure (budget alpha/(M N) per hypothesis) and an
allocation that builds coupons only at the edge points edge_m(T), for each
m. Certifying edge point z for mode m makes T's part of z's safe quadrant
certified for m by spreading, and the edge points' quadrants cover T. For
the hedge betting strategy, the expected number of coupons until z's wealth
reaches M N / alpha is about

    ( ln(M N / alpha) + ln 16 ) / g_c(p_m(z)),

where g_c(p) <= k_m(z) is the best growth rate available to a bet capped at
c / (1 - eps) (ln 16 pays for hedging: half the wealth goes to an
8-component mixture, so each component has weight 1/16). So

    E[tau]  <=  sum_m sum_{z in edge_m(T)}  (ln(M N / alpha) + ln 16) / g_c(p_m(z))  +  lower-order terms.

Comparing with Theorem 4a, the method is optimal up to three factors:

1. ln(M N / alpha) / ln(1/alpha), the Bonferroni price (a log factor);
2. k / g_c, the cap on bets (a constant, about 1.25 at the default cap);
3. sum over edge points / LP_A(T), how much one coupon can serve several
   edge constraints at once (between 1 and the number of edge points; to
   characterize).

**Gaps to close before this is a theorem:**
- The stopping-time bound for the hedge e-process needs a citable result
  (Waudby-Smith & Ramdas 2024 have growth-rate results for their betting
  strategies; we need the expected-stopping-time version).
- The sketch assumes the allocation knows the edge points. With a learned
  allocation there is an extra "learning" term. exp04 measures how big it
  is in practice.
- Factor 3 above.

## 7. What this buys the paper

Put together, Theorems 4a, 4b and 3 say:

- With the physics ordering, the cost is governed by about M * n edge
  points: the boundary.
- Without it, by all |T| points of the target: the area.
- Our method gets within log factors of the first.

The ratio |T| / (M n) is the speed-up physics knowledge buys, and no
unstructured method can recover it. That's the ICML-level claim.

## 8. Check yourself

1. Why does the alternative in section 3 raise the rate on everything
   riskier than z, and not just at z? What goes wrong if you only raise
   p_m(z)?
2. In Theorem 4b, why may we change one setting at a time?
3. Draw a 4 x 4 grid, shade a target T, and mark edge_m(T) for lack of
   fusion (safer = more power, less speed). Check the edge-size lemma.
