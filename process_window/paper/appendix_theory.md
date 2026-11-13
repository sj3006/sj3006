# Appendix: theory (consolidated)

*Draft for checking. Collects the results of notes 2, 5, 6, 7 and 9 in one
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
is a lower bound). L = (1 - beta) ln(1/alpha) - ln 2.

**Theorem 2a (certification term).** For each m and each z in T, define
nu' by p'_m(y) = max(p_m(y), eps_m + eta) for all y ⪯_m z, everything else
unchanged. **[check]** nu' satisfies A (case analysis in note 5, section 3).
In nu', z is unsafe, so an alpha-valid procedure certifies T with
probability at most alpha; under nu it does with probability >= 1 - beta.
Letting eta -> 0:

    sum over y ⪯_m z with p_m(y) < eps_m of  E[N_y] KL(p_m(y) || eps_m)  >=  L.

Hence E[tau] >= L * LP(T), LP(T) = min sum_y n_y subject to these
constraints for all (m, z). Only the ⪯_m-minimal points of T bind, and
there are at most min(n_1, n_2) of them per mode (an antichain of a product
order on a grid has at most one point per row and per column).

**Theorem 2b (boundary term, fixed confidence).** For each m and each
configuration z just outside T for m (p_m(z) > q eps_m, every
configuration safer than z for m is in T for m, and z is in T for the other
modes), lower p_m(z) to q eps_m - eta. **[check]** This keeps A, because
every configuration safer than z has p_m <= q eps_m. In the alternative z is
in T and must be certified with probability >= 1 - beta. So the procedure
either certifies z (cost >= L / KL(p_m(z) || eps_m), infinite if
p_m(z) >= eps_m) or distinguishes the instances at z (cost >=
L_beta / KL(p_m(z) || q eps_m), L_beta = (1 - beta) ln(1/beta) - ln 2). The
boundary points are distinct from the minimal points of T, so the two terms
add (up to the sharing allowed by the LP).

**Theorem 2c (without the ordering).** If the procedure must be correct on
all instances, perturbations at a single configuration are allowed, so
every configuration contributes its own term: certification for x in T,
the cheaper of certification and rejection otherwise. The bound is a sum
over all of X.

## A.8 Corollary (edge vs. area)

Theorems 2a/2b involve O(M min(n_1, n_2)) configurations; Theorem 2c
involves all N. Theorem 4 matches 2a/2b up to: the probe count O(log n)
(O(1) per row in practice with neighbour warm starts), the ratio
C* / C(p_boundary), and the multiple-testing factor
ln(16 M N / (alpha w)) / L.

## A.9 Checklist for the reader

1. Lemma 1's filtration argument with batched allocation.
2. Theorem 1's inclusion {m} x C_m(x) ⊆ D under A, and the closed-testing
   interpretation.
3. Theorem 6's claim that no target configuration is rejected by spreading
   or exclusion on G.
4. The transportation lemma version (stopping not guaranteed under the
   alternative).
5. Theorem 2a's alternative keeps A (note 5, section 3), and the LP
   sharing across modes (a trial at y serves all modes).
6. Theorem 2b's alternative keeps A, and the claim that the two terms add.
7. Theorem 4's probe count with spreading from other rows, and the
   min-of-two-stopping-times bound.
