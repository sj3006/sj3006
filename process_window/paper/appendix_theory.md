# Appendix: theory (consolidated)

*Draft for checking (revised 2026-11-13: Theorem 2 is now one joint
program; the earlier sum of two terms double-counted). Collects the results of notes 2, 5, 6, 7 and 9 in one
notation. Steps marked **[check]** are the ones a careful reader should
verify first.*

## A.1 Setup

- Configurations: a finite grid X = [n_1] x [n_2], N = n_1 n_2. Failure
  modes m = 1..M. For each m a product order ⪯_m on X: x ⪯_m y iff
  (y_1 - x_1) s_{m,1} >= 0 and (y_2 - x_2) s_{m,2} >= 0 for signs
  s_m in {-1, +1}^2 ("y is at least as safe as x").
- Trial t = 1, 2, ... is run at configuration x_t and yields
  Y_t in {0,1}^M. Given the past and x_t = x, Y_t ~ P_x, independently of
  the past; p_m(x) = P_x(Y_m = 1).
- Filtration F_t = sigma(x_1, Y_1, ..., x_t, Y_t, U), where U is any
  independent side information (simulator output, pilot data, internal
  randomization). The allocation x_t is F_{t-1}-measurable (trials in a
  batch are chosen before any of them is observed; processing them one at a
  time in a fixed order keeps this property).
- **Assumption A.** x ⪯_m y implies p_m(y) <= p_m(x), for every m.
- Safe set W = {x : p_m(x) < eps_m for all m}. Target with slack q in (0,1):
  T = {x : p_m(x) <= q eps_m for all m}.

## A.2 Per-configuration e-processes

For (m, x) and a predictable bet sequence lam_t in [0, c/(1-eps_m)], c < 1,
define K_{m,x}(0) = 1 and

    K_{m,x}(t) = K_{m,x}(t-1) * (1 + lam_t (eps_m - Y_{t,m}))  if x_t = x,
                 K_{m,x}(t-1)                                  otherwise.

**Lemma 1.** If p_m(x) >= eps_m, then K_{m,x} is a nonnegative
supermartingale with respect to (F_t).
*Proof.* Nonnegativity: 1 + lam (eps - 1) >= 1 - c > 0. On {x_t = x},
E[K(t) | F_{t-1}] = K(t-1)(1 + lam_t (eps - p_m(x))) <= K(t-1), since lam_t
and x_t are F_{t-1}-measurable and Y_t's conditional law given F_{t-1}
and x_t = x is P_x. On {x_t != x}, K(t) = K(t-1). ∎

A fixed-weight average of such processes (the hedge: half a plug-in bet,
half eight fixed bets with weight 1/16 each) is again a nonnegative
supermartingale under the same null.

Similarly, the **rejection process** R_{m,x}(t), multiplying by
(1 + mu_t (Y_{t,m} - q eps_m)) with mu_t in [0, 1/(q eps_m)), is a
nonnegative supermartingale whenever p_m(x) <= q eps_m.

**Ville's inequality.** For a nonnegative supermartingale Z with Z_0 <= z,
P(sup_t Z_t >= 1/a) <= a z.

## A.3 Validity of the cone rule (Theorem 1)

Weights w_{m,x} >= 0 are F_0-measurable with sum_{m,x} w_{m,x} <= 1. Let
C_m(x) = {y : y ⪯_m x} (the riskier cone, including x). Certify (m, x) at
the first t with S_m(x, t) = sum_{y in C_m(x)} w_{m,y} K_{m,y}(t) >= 1/alpha.

**Theorem 1.** Under Assumption A,
P(there exist t and (m, x) with p_m(x) >= eps_m certified by time t) <= alpha.

*Proof.* Let D = {(m, y) : p_m(y) >= eps_m}. **[check]** Under A, if
(m, x) is in D and y ⪯_m x then p_m(y) >= p_m(x) >= eps_m, so
{m} x C_m(x) ⊆ D. Define E(t) = sum_{(m,y) in D} w_{m,y} K_{m,y}(t). By
Lemma 1 each term is a nonnegative supermartingale, hence so is E, with
E(0) = sum_D w <= 1. A false certification of (m, x) in D at time t means
1/alpha <= S_m(x, t) <= E(t). By Ville, P(sup_t E(t) >= 1/alpha) <= alpha. ∎

Remarks. (i) Nothing about the allocation is used beyond predictability.
(ii) Certification is sticky; the bound covers "ever certified".
(iii) With w uniform, S_m(x) >= max_{y in C_m(x)} w K_y, so the cone rule
certifies everything Bonferroni + spreading certifies.
(iv) **[check]** Interpretation as closed testing: for any family I of
nulls the intersection test sum_{i in I} w_i K_i is an e-process under
H_I; under A the only intersections that can be true are riskier-closed
sets, and the smallest such set containing (m, x) is {m} x C_m(x).

## A.4 Correctness of the search (fixed confidence)

The search (Section 4 of the paper) certifies with the cone rule and
rejects (m, x) when R_{m,x} >= M N / beta. A rejection of (m, x) also marks
every y ⪯_m x as rejected for m; a configuration rejected for some mode is
not searched for the other modes. It stops when every configuration is, for
every mode, certified, rejected, or excluded.

**Theorem 6.** Under Assumption A the search is (alpha, beta)-correct:
validity at level alpha and P(tau < inf, T ⊆ C) >= 1 - beta.

*Proof.* Validity: Theorem 1. Completeness: let G = {no (m, x) with
p_m(x) <= q eps_m is rejected directly}. By Lemma 1 (rejection version),
Ville and a union bound over M N pairs, P(G^c) <= beta. **[check]** On G,
no x in T is ever rejected or excluded: a spread rejection of x for m comes
from some direct rejection at y with x ⪯_m y, but p_m(y) <= p_m(x) <=
q eps_m, contradicting G; exclusion through another mode m' is the same
argument for m'. Termination: every probe ends a.s. (if p < eps the cone
statistic at the probe has positive expected log-growth under the hedge's
best fixed bet, so it crosses 1/alpha a.s.; if p > q eps the rejection
process does), each probe decides at least one configuration, and X is
finite. So on G, tau < inf and every x in T is certified. ∎

## A.5 Expected certification and rejection times

**Lemma 2 (Wald).** Let Z_k = sum_{i<=k} xi_i with xi_i i.i.d., bounded,
E xi = g > 0, and tau = min{k : Z_k >= c}. Then E tau <= (c + b)/g, where
b = ess sup xi.
*Proof.* E tau < inf for positive drift with bounded increments; Wald's
identity E Z_tau = g E tau; Z_tau <= c + b. ∎

**Corollary 1.** At a configuration with rate p < eps and weight w, sampled
exclusively, the cone rule certifies it within an expected

    ( ln(16 / (alpha w)) + ln(1 + lam* eps) ) / g_c(p)

trials, g_c(p) = max over the fixed bets lam_j of
E ln(1 + lam_j (eps - Y)). (The hedge holds each fixed bet with weight 1/16,
and S_m(x) >= w K_x.) Likewise rejection at p > q eps within
(ln(5 M N / beta) + b')/g_r(p).

Numerically (eps = 5%, cap 0.8): KL(p || eps) / g_c(p) = 1.00-1.05 for
p in [0.5%, 4%], 1.24 at p = 0.

## A.6 Upper bounds

**Theorem 3 (oracle, fixed budget).** If trials are run only at a cover F
(for each m, a set of configurations safe for m whose safer cones contain
T), one at a time until certified, the expected number of trials until T is
certified is at most sum over (m, z) in F of the Corollary 1 bound, plus
B per (m, z) when certification is checked once per batch of size B.

**Theorem 4 (search).** Let C(p) = min(T_c(p), T_r(p)) with T_c, T_r the
two Corollary 1 bounds (infinite outside p < eps, p > q eps respectively),
and C* = max_p C(p) < inf (since q < 1). The expected cost of the search is
at most sum over (m, j) of P_{m,j} (C* + B), where P_{m,j} <=
2 ceil(log2(d_{m,j} + 1)) + 2 is the number of probes in row j for mode m and
d_{m,j} the distance from the first probe to the edge.
*Proof sketch.* **[check]** Galloping brackets the edge in
ceil(log2(d + 1)) + 1 probes and bisection closes the bracket in at most as
many; probes elsewhere only decide configurations earlier. A probe's
duration is the minimum of a certification and a rejection passage time,
whose expectation is at most the smaller of the two bounds (Lemma 2), hence
at most C(p) <= C*. Overshoot: at most B per probe. Probes for different
modes at one configuration share trials, which only reduces cost. ∎

## A.7 Lower bounds

**Transportation lemma** (Kaufmann, Cappe & Garivier 2016, Lemma 1; for
procedures that may not stop under the alternative use the
general-event version, Garivier, Menard & Stoltz 2019). **[check: which
version is needed and its exact conditions]** For instances nu, nu', a
stopping time tau and an event E in F_tau,
sum_x E_nu[N_x(tau)] KL(nu_x, nu'_x) >= kl(P_nu(E), P_nu'(E)).
We use kl(a, b) >= a ln(1/b) - ln 2.

Restrict to instances with independent modes (a lower bound on a subclass
is a lower bound). Let K_1 = kl(1 - beta, alpha) (2.65 at
alpha = beta = 0.05; the cruder L = (1 - beta) ln(1/alpha) - ln 2 = 2.15 is
also valid). For an event E with pi = P_nu(E), write

    f(pi) = kl(pi, 1 - beta) if pi < 1 - beta, else 0,
    g(pi) = kl(pi, alpha)    if pi > alpha,    else 0.

If P_nu'(E) <= alpha the transportation lemma gives at least g(pi); if
P_nu'(E) >= 1 - beta it gives at least f(pi) (kl(pi, .) is decreasing below
pi and increasing above it).

**Using the lemma when the procedure may not stop.** If E_nu[tau] = inf
there is nothing to prove. Otherwise tau < inf nu-a.s.; on F_tau the
restriction of P_nu is absolutely continuous with respect to that of P_nu'
(arms are mutually absolutely continuous and P_nu(tau = inf) = 0), with
density the likelihood ratio at tau, whose nu-expectation of the log is
sum_x E_nu[N_x(tau)] KL(nu_x, nu'_x) by Wald's identity. The data-processing
inequality for KL applied to the indicator of E gives the lemma. Nothing
requires tau < inf under nu'. **[check]**

**Theorem 2 (lower bound, fixed confidence).** Any (alpha, beta)-correct
procedure has E[tau] >= OPT, the value of

    minimize sum_y n_y  over n >= 0, subject to
    (i)  for each m and each riskiest point t of T (for ⪯_m):
             sum_{y ⪯_m t, p_m(y) < eps_m} n_y KL(p_m(y) || eps_m) >= K_1;
    (ii) for each m and each boundary point z (z is outside T only because
         of mode m, and every setting strictly safer than z for m is in T
         for m), with
             A_z = n_z KL(p_m(z) || q eps_m),
             B_z = sum_{y ⪯_m z, p_m(y) < eps_m} n_y KL(p_m(y) || eps_m):
         (A_z, B_z) in R = {(A, B) : A >= f(pi), B >= g(pi) for some pi}.

R is convex (its lower-left boundary is B = g(f^{-1}(A)), an increasing
convex function of a decreasing convex function), so this is a convex
program; replacing R by finitely many supporting half-planes
w A + (1 - w) B >= c(w) = min_pi [w f(pi) + (1 - w) g(pi)] gives an LP whose
value is a valid (slightly smaller) bound. That is what `pwcert/bounds.py`
computes. If p_m(z) >= eps_m then B_z = 0 and pi <= alpha, so
A_z >= kl(alpha, 1 - beta).

*Proof.* (i) For each m and t, define nu' by p'_m(y) = max(p_m(y),
eps_m + eta) for y ⪯_m t, everything else unchanged. **nu' satisfies A**:
the riskier cone of t is riskier-closed (y1 ⪯ y2 ⪯ t implies y1 ⪯ t), and
for y1 ⪯ y2: both in the cone, max(p(y2), c) <= max(p(y1), c); y1 in, y2
out, p'(y2) = p(y2) <= p(y1) <= p'(y1); y2 in forces y1 in. In nu', t is
unsafe, so P_nu'(T ⊆ C) <= alpha, while P_nu(tau < inf, T ⊆ C) >= 1 - beta;
apply the lemma with E = {tau < inf, T ⊆ C}, then let eta -> 0.
(ii) Lowering alternative: set p''_m(z) = q eps_m, everything else
unchanged. This keeps A, because every setting strictly safer than z has
p_m <= q eps_m and every riskier one has p_m >= p_m(z) > q eps_m. In nu'',
z is in T, so P_nu''(z in C) >= 1 - beta: the lemma with E = {z in C} gives
A_z >= f(pi), pi = P_nu(z in C). Raising alternative: as in (i) with t
replaced by z; z is unsafe in it, so P(z in C) <= alpha there, and the lemma
gives B_z >= g(pi) for the same pi. ∎

**Why one joint program.** An earlier version added the value of (i) to a
separate sum of boundary terms. That double-counts: trials just outside T
appear in both (i) (if their rate is below eps) and (ii). The joint program
counts each trial once. On the synthetic window this lowers the bound at
48x48 from 40.4k to 24.8k.

**Theorem 2c (without the ordering).** If the procedure must be correct on
all instances, alternatives may change a single configuration, so each
configuration is resolved on its own and the bound is a sum over X: for
x in T, K_1 / min_m KL(p_m(x) || eps_m); for x outside T and safe,
min_pi max(f(pi) / R_x, g(pi) / C_x) with R_x = sum over modes with
p_m > q eps_m of KL(p_m || q eps_m) and C_x = min_m KL(p_m || eps_m); for x
unsafe, kl(alpha, 1 - beta) / R_x.

## A.8 Corollary (edge vs. area)

Theorem 2 involves O(M min(n_1, n_2)) configurations; Theorem 2c involves
all N. Theorem 4 matches Theorem 2 up to: the probe count O(log n) (O(1)
per row in practice with neighbour warm starts), the ratio
C* / C(p_boundary), and the multiple-testing factor
ln(16 M N / (alpha w)) / K_1. The last factor is the price of a
family-wise guarantee over MN hypotheses with a single-hypothesis lower
bound; whether a ln N term is necessary here is open (in unstructured
pure exploration such terms are known to be necessary in moderate
confidence regimes; Simchowitz, Jamieson & Recht 2017). **[open]**

## A.9 Checklist for the reader

1. Lemma 1's filtration argument with batched allocation.
2. Theorem 1's inclusion {m} x C_m(x) ⊆ D under A, and the closed-testing
   interpretation.
3. Theorem 6's claim that no target configuration is rejected by spreading
   or exclusion on G.
4. The transportation lemma when tau may be infinite under the
   alternative (argument above).
5. Both alternatives of Theorem 2 keep A, and the LP sharing across modes
   (a trial at y serves all modes).
6. Convexity of R and the supporting half-planes (replaces the earlier,
   incorrect claim that the certification and boundary terms add).
7. Theorem 4's probe count with spreading from other rows, and the
   min-of-two-stopping-times bound.
