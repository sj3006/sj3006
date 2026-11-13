# Appendix: theory (consolidated)

*Revised 2026-11-13. Theorem 2 is now one joint program; the earlier sum
of two terms double-counted. Second pass the same day: the closed-testing
remark is now Proposition 1 with a proof; termination of the search needs
a growth condition (T) on the fixed bets, now stated (it holds at every
tolerance used in the experiments); time-outs are covered explicitly; the
transportation lemma's conditions are spelled out; and the Theorem 4 proof
says why interleaved probes still see i.i.d. trials. Collects the results
of notes 2, 5, 6, 7 and 9 in one notation. A.9 lists where each
previously flagged step is resolved. The one open question is marked
**[open]**.*

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

*Batches.* Trials in a batch are chosen before any of them is observed and
then processed one at a time in a fixed order. Trial t's setting was fixed
at the start of its batch, so it is F_{t-1}-measurable. Its bet may use the
outcomes of earlier trials in the same batch: the plug-in bet is updated
after each trial, and that is still F_{t-1}-measurable. So the proof
applies as is. The side information U (simulator, pilot data) must be
independent of the trials' outcomes given their settings. That holds when
the pilot is a separate set of trials, as in all our experiments: the LM
pilot uses generations that the benchmark never reuses.

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

*Proof.* Let D = {(m, y) : p_m(y) >= eps_m}, the true nulls. If (m, x) is
in D and y is in C_m(x), then y ⪯_m x: x is at least as safe as y. By A,
p_m(x) <= p_m(y), so p_m(y) >= eps_m. Hence {m} x C_m(x) ⊆ D. Define E(t) = sum_{(m,y) in D} w_{m,y} K_{m,y}(t). By
Lemma 1 each term is a nonnegative supermartingale, hence so is E, with
E(0) = sum_D w <= 1. A false certification of (m, x) in D at time t means
1/alpha <= S_m(x, t) <= E(t). By Ville, P(sup_t E(t) >= 1/alpha) <= alpha. ∎

Remarks. (i) Nothing about the allocation is used beyond predictability.
(ii) Certification is sticky; the bound covers "ever certified".
(iii) With w uniform, S_m(x) >= max_{y in C_m(x)} w K_y, so the cone rule
certifies everything Bonferroni + spreading certifies.
(iv) The cone rule is closed testing; see Proposition 1.

**Proposition 1 (closed testing).** Call a set I ⊆ [M] x X *admissible*
if, for each m, its m-section I_m = {x : (m, x) in I} is riskier-closed
(x in I_m and y ⪯_m x imply y in I_m). For admissible I, test the
intersection null H_I = "every (m, x) in I is unsafe for m" by rejecting
at the first time phi_I(t) = sum_{i in I} w_i K_i(t) >= 1/alpha. Then:
(a) the admissible sets are exactly the possible sets of true nulls under
A; (b) each phi_I is a time-uniform level-alpha test of H_I; (c) closed
testing over the admissible family, with these local tests, rejects
(m, x) at time t if and only if S_m(x, t) >= 1/alpha. So the cone rule is
closed testing with Shaffer-type restricted combinations, and Theorem 1 is
its usual family-wise guarantee, made time-uniform.

*Proof.* (a) Under A the m-section of D is riskier-closed (the argument in
the proof of Theorem 1). Conversely, given an admissible I, put
p_m = eps_m on I_m and p_m = 0 elsewhere. This satisfies A: if x ⪯_m y and
y is in I_m, then x is in I_m. And its set of true nulls is I. (b) Under
H_I each K_i with i in I is a nonnegative supermartingale (Lemma 1), so
phi_I is one too, with phi_I(0) = sum_I w <= 1; apply Ville. (c) Closed
testing rejects (m, x) when every admissible I containing (m, x) is
rejected. phi_I is nondecreasing in I, because every term is nonnegative.
And {m} x C_m(x) is the smallest admissible set containing (m, x): it is
riskier-closed by transitivity, its other sections are empty, and every
riskier-closed set containing x contains C_m(x). So all admissible
I ∋ (m, x) are rejected iff phi_{{m} x C_m(x)} = S_m(x) >= 1/alpha. ∎

## A.4 Correctness of the search (fixed confidence)

The search (Section 4 of the paper) certifies with the cone rule and
rejects (m, x) when R_{m,x} >= M N / beta. A rejection of (m, x) also marks
every y ⪯_m x as rejected for m; a configuration rejected for some mode is
not searched for the other modes. It stops when every configuration is, for
every mode, certified, rejected, or excluded.

**Growth condition (T).** Write g_c(p) = max_j E_p ln(1 + lam_j (eps - Y))
over the hedge's fixed certification bets and g_r(p) = max_k E_p ln(1 +
mu_k (Y - q eps)) over the fixed rejection bets. Condition (T): for every
p in [0, 1], g_c(p) > 0 or g_r(p) > 0. It is a property of the two bet
grids and (eps, q), and it can be checked numerically. For our grids
(certification: fractions 0.05-1 of 0.8/(1 - eps); rejection: fractions
0.025-0.4 of 1/(q eps)) and q = 0.5, min_p max(g_c, g_r) is 1.6e-3, 4.6e-3,
1.6e-2 and 3.4e-2 at eps = 5%, 10%, 30% and 50%: every tolerance in our
experiments. The worst p is near 0.75 eps. (T) fails only for small
tolerances: at eps = 2% no bet grows on p in (0.980, 0.996) eps. Adding a
smaller rejection bet fixes that. Under (T), C* = max_p min(T_c(p), T_r(p))
is finite.

**Theorem 6.** Under Assumption A and (T), the search without time-outs is
(alpha, beta)-correct: validity at level alpha and
P(tau < inf, T ⊆ C) >= 1 - beta. With time-outs, validity still holds,
tau < inf surely, and P(T ⊆ C) >= 1 - beta - P(a probe at some (m, x)
with x in T times out).

*Proof.* Validity: Theorem 1. Completeness: let G = {no (m, x) with
p_m(x) <= q eps_m is rejected directly}. By Lemma 1 (rejection version),
Ville and a union bound over M N pairs (each R_{m,x} starts at 1 and
rejects at M N / beta), P(G^c) <= beta.

*No target configuration is lost on G.* Spreading marks y rejected for m
when some directly rejected z has y ⪯_m z: z is at least as safe as y.
Suppose x in T were rejected for m. Either directly, which contradicts G
because p_m(x) <= q eps_m. Or by spreading from a direct rejection at z
with x ⪯_m z. Then by A, p_m(z) <= p_m(x) <= q eps_m, and (m, z) is a
target pair that was rejected directly, which again contradicts G. A
configuration is *excluded* (not searched for other modes) only when it is
rejected for some mode m'; for x in T that is impossible on G by the same
argument with m' in place of m.

*Termination.* Fix a probe at (m, x) with rate p = p_m(x). By (T), one of
two cases holds. If g_c(p) > 0, the best fixed certification bet's wealth
satisfies (1/n) ln K_j -> g_c(p) > 0 a.s. along the trials at x (strong
law). The cone statistic is at least w_{m,x} (1/16) K_j, so it crosses
1/alpha a.s. If g_r(p) > 0, the same holds for the rejection mixture,
which is at least (1/5) R_k. So each probe ends a.s. Each probe decides at
least one (mode, configuration) pair, and there are M N pairs, so tau < inf
a.s. Hence on G, tau < inf and T ⊆ C.

*Time-outs.* A time-out marks the probe's pair as rejected for the search.
That never certifies anything, so validity is untouched. It caps every
probe's length, so tau < inf surely. The completeness argument above goes
through on G ∩ {no probe at a target pair times out}. ∎

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
and C* = max_p C(p), finite under (T). For the analysed variant below,
the expected cost of the search is at most
(C* + B) (sum over (m, j) of P_{m,j} + (alpha + beta) M N), where
P_{m,j} <= 2 ceil(log2 d_{m,j}) + 2 and d_{m,j} is the distance from the
first probe in row j to the far end of mode m's slack band (Lemma 3).
**Lemma 3 (probes per row).** Fix mode m and a row, ordered safest to
riskiest for m (rates nondecreasing). Let a be the last position with
p_m <= q eps_m and b the first with p_m >= eps_m (the slack band is the
positions strictly between). On the event G ∩ V (no wrong direct rejection,
no wrong certification), a probe at position i can only certify if i < b
and can only reject if i > a; certified positions form a prefix and
rejected ones a suffix. If the first probe is at s and
d = max(b - s, s - a, 1), the row is decided after at most
2 ceil(log2 d) + 2 probes.
*Proof.* Say the first probe certifies (the other case is symmetric).
Galloping probes s + 1, s + 2, s + 4, ...; it cannot certify at or beyond
b, so the first rejection comes after at most ceil(log2 (b - s)) + 1
probes, leaving a bracket with at most 2^(k-1) <= b - s undecided
positions. Each bisection probe at the median of the undecided positions
certifies it (and everything safer) or rejects it (and everything
riskier), so it at least halves them: at most ceil(log2 (b - s)) + 1 more
probes. Positions decided by other rows or modes only shrink the bracket. ∎

**Analysed variant.** For the cost bound, the e-process K_{m,x} (and the
rejection process R_{m,x}) use only the trials run during probes *for mode
m*. Which trials enter is decided before they are seen, so these are still
valid e-processes and Theorems 1 and 6 still apply. The implementation also
lets a trial at x count for every mode, which can only make decisions
earlier in practice but makes the accounting below messier.

*Proof of Theorem 4 (cost), for the analysed variant.* Number the probes
k = 1, 2, ... in the order they start, and let L_k be the trials probe k
uses. Probes run concurrently, so their trials interleave. Use the
standard "reward table" construction: for each pair (m, x), draw in
advance an i.i.d. sequence of outcome vectors from P_x, and let the j-th
trial of a mode-m probe at x read the j-th entry. This has the same law as
the procedure, because each trial's outcome given the past is P_x. In the
analysed variant (m, x) is probed at most once: a probe ends only when its
pair is decided. So the trials probe k sees are the first entries of its
own table, independent of everything before it started, and its
processes start fresh;
the cone statistic is at least w K_{m,x}, so probe k ends no later than the
first of the two passage times of Lemma 2. Hence
E[L_k | start of probe k] <= min(T_c, T_r) + B <= C* + B, the B for checking
once per batch. Whether probe k happens is known when it starts, so

    E[total] = sum_k E[ 1{probe k happens} E[L_k | start] ] <= (C* + B) E[number of probes].

On G ∩ V (probability at least 1 - alpha - beta) Lemma 3 gives at most
sum_{m,j} P_{m,j} probes; off it, at most M N (each probe decides a
(mode, setting) pair). So

    E[total] <= (C* + B) ( sum_{m,j} (2 ceil(log2 d_{m,j}) + 2) + (alpha + beta) M N ).

The second term is the price of the rare runs where an e-process misleads;
it is at most (alpha + beta) times the cost of probing everything. ∎

## A.7 Lower bounds

**Transportation lemma** (Kaufmann, Cappe & Garivier 2016, Lemma 1; for
procedures that may not stop under the alternative use the
general-event version, Garivier, Menard & Stoltz 2019). Conditions used
here: nu_x is absolutely continuous with respect to nu'_x for every x; tau
is a stopping time with E_nu[tau] < inf; E is in F_tau and E ⊆ {tau < inf}.
Then
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
(nu_x ≪ nu'_x for every x, and P_nu(tau = inf) = 0), with density the
likelihood ratio at tau. Its nu-expectation of the log is
sum_x E_nu[N_x(tau)] KL(nu_x, nu'_x) by Wald's identity. The
data-processing inequality for KL, applied to the indicator of E, gives
the lemma. Nothing requires tau < inf under nu'. That matters, because a
correct procedure need not stop on an instance it cannot resolve.
Absolute continuity is needed only in the direction nu ≪ nu'. Raising a
rate from p >= 0 to eps + eta and lowering it from p > q eps to q eps
both keep it, including at p = 0. The events used below,
{tau < inf, T ⊆ C} and {tau < inf, z in C}, are subsets of {tau < inf}
by definition.

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

## A.9 Previously flagged steps and where they are resolved

1. Lemma 1 with batched allocation: the "Batches" paragraph after Lemma 1.
2. Theorem 1's inclusion {m} x C_m(x) ⊆ D: its proof. The closed-testing
   interpretation: Proposition 1.
3. Theorem 6, no target pair lost to spreading or exclusion on G: its
   proof. Termination now assumes (T), which is checked numerically for
   every tolerance used. Time-outs are covered in the statement.
4. The transportation lemma when tau may be infinite under the
   alternative: the conditions and argument in A.7.
5. Both alternatives of Theorem 2 keep A: the proof of Theorem 2. Sharing
   across modes: a trial at y yields all M outcomes, and the alternatives
   change one mode at a time on instances with independent modes, so
   KL(nu_y, nu'_y) = KL_m(y) and the constraint is on the total n_y.
6. Convexity of R: f is decreasing and convex on [0, 1 - beta) and g is
   increasing and convex on (alpha, 1], so the lower boundary
   B = g(f^{-1}(A)) is convex. Validity of the half-planes does not even
   need convexity: w f(pi) + (1 - w) g(pi) >= c(w) for every pi.
7. Lemma 3 with spreading from other rows: decisions made elsewhere only
   shrink the bracket. The conditional-expectation step in Theorem 4: the
   reward-table paragraph in its proof.

Open: whether the ln N in the multiple-testing factor is necessary (A.8).
