# Note 9: the fixed-confidence problem and a near-optimal search algorithm

Status: **draft proofs, need independent checking.** Prerequisites: notes 5,
6, 7. Code: `pwcert/search.py`; experiment: `experiments/exp_search.py`.

## 1. Two problems, not one

- **Fixed budget:** given N coupons, certify as much of the window as
  possible. The edge allocation rule (note 8, iteration 9) is our answer;
  it has no stopping rule and no completeness guarantee.
- **Fixed confidence** (this note): certify the whole target and *know
  you're done*. This is the standard pure-exploration formulation in the
  bandit literature (fixed-confidence thresholding / level-set
  identification), and it is the formulation in which an ICML theory
  result is expected.

## 2. Problem statement

Grid X = rows x positions (n_V rows of n_P settings), modes m = 1..M,
Assumption A (each mode monotone along known product-order directions).
Target slack 0 < q < 1:

    T = { x : p_m(x) <= q eps_m for all m }.

Settings with q eps_m < p_m(x) < eps_m for all m may be certified or not
(slack). A procedure outputs a certified set C at a stopping time tau.

**Definition ((alpha, beta)-correct).** For every instance satisfying A:
1. *validity:* P(C contains a setting with p_m >= eps_m for some m) <= alpha;
2. *completeness:* P(tau < infinity and T ⊆ C) >= 1 - beta.

## 3. The algorithm (SearchCertifier, timeout disabled)

Per (mode m, row j), the row is a chain ordered safest to riskiest for m.

**Two-sided probe at setting x for mode m.** Build coupons at x until
- CERTIFY: the cone rule certifies x for m (note 6), or
- REJECT: the defect-betting e-process for "p_m(x) <= q eps_m" (a mixture
  of 5 fixed bets, each lam (Y - q eps) with lam < 1/(q eps)) reaches
  M N / beta.

**Spreading.** A certificate certifies everything safer (cone rule). A
rejection rejects everything riskier (if p_m(x) > q eps then every riskier
y has p_m(y) >= p_m(x) > q eps). A setting rejected for any mode is outside
T and is not searched for the other modes.

**Search per (m, j).** First probe at the simulator's predicted edge (or
the middle), then gallop toward the side the outcome points to (steps 1,
2, 4, ...) until bracketed, then bisect the undecided positions.

**Stop** when every row is decided for every mode (each position certified,
rejected, or excluded).

## 4. Theorem 6 (correctness)

**Theorem 6.** Under Assumption A, the procedure is (alpha, beta)-correct,
for any simulator.

*Proof.* Validity: certificates come only from the cone rule; Theorem 5
(note 6) applies for any allocation and stopping time.

Completeness. Let G be the event that no (m, x) with p_m(x) <= q eps_m is
ever rejected directly. Each reject e-process is a nonnegative
supermartingale under p_m(x) <= q eps_m (same argument as note 1 with the
roles of defects and good coupons swapped), so by Ville and a union bound
over the M N pairs, P(G) >= 1 - beta.

On G, no target setting is ever rejected, directly or by spreading: if
x in T were rejected by spreading from some safer y (x riskier than y),
then p_m(y) <= p_m(x) <= q eps, so y would be a direct wrong rejection,
excluded by G. Likewise x is never excluded through another mode. So
when the procedure stops (every position decided), every x in T is
certified for every mode.

It remains to show tau < infinity on G almost surely: every probe ends,
because if p <= q eps < eps certification happens a.s. (positive drift,
note 7), and if p > q eps rejection happens a.s.; the number of probes is
finite (each decides at least one position). ∎

## 5. Theorem 7 (upper bound)

Per-probe cost. For a probe at a setting with rate p (mode m), weight w:

    T_c(p) = ( ln(16 / (alpha w)) + b ) / g_c(p)      if p < eps   (else inf)
    T_r(p) = ( ln(5 M N / beta) + b' ) / g_r(p)       if p > q eps (else inf)
    C(p)   = min( T_c(p), T_r(p) ),

where g_c is the best growth rate of the certification bets (note 7) and
g_r that of the rejection bets (both within a few percent of
KL(p || eps) and KL(p || q eps) respectively), and b, b' are overshoot
terms. By Wald's identity (note 7) the expected probe length is at most
C(p), since a probe ends at the first of two stopping times. **C(p) is
finite for every p** because q < 1: below eps certification is finite,
above q eps rejection is finite, and the two ranges overlap. Let
C* = max over p of C(p).

**Theorem 7.** The expected number of coupons until the procedure stops is
at most

    sum over (m, j) of  P_{m,j} * C*   +   B * (number of probes),

where P_{m,j} <= 2 ceil(log2(d_{m,j} + 1)) + 2 is the number of probes in
row j for mode m, d_{m,j} the distance (in positions) between the first
probe and the true edge, and B the coupons per probe per plate. With no
simulator d <= n_P, so the total is O(M n_V log(n_P) C*).

*Proof sketch.* Galloping finds a bracket in at most ceil(log2(d+1)) + 1
probes and bisection closes it in at most as many more. Probes from other
rows and modes only decide positions earlier (spreading), never later.
Each probe's expected length is at most C* by Wald (the coupon stream at a
setting is i.i.d. and the probe's stopping time is the minimum of two
passage times). Sum over probes; add up to B coupons of overshoot per
probe because decisions are checked once per plate. ∎

*What remains to make rigorous:* (i) probes for different modes at the same
setting share coupons, which only helps, but the accounting should be
explicit; (ii) the rows-riskiest-first concurrency and timeouts in the code
are heuristics outside the theorem (timeouts trade completeness for cost;
the theorem is for timeout disabled).

## 6. Theorem 8 (lower bounds, refined)

Let L = (1 - beta) ln(1/alpha) - ln 2 (as in note 5; using the
(alpha, beta) pair, the transportation lemma gives kl(1 - beta, alpha) on
the certification side and kl(1 - beta, beta) on the completeness side).

**(a) With the ordering.** Any (alpha, beta)-correct procedure uses at least

    L * LP(T)  +  L' * sum over z in B of min( 1 / KL(p(z) || eps), 1 / KL(p(z) || q eps) )

coupons in expectation, where LP(T) is the certification LP of note 5
(binding constraints at T's riskiest points) and B is the set of
(mode, setting) pairs that are *just outside* the target: the safest
settings with p_m > q eps that are inside the target for every other mode.
*Why the second term:* for z in B, consider the alternative where p_m(z) is
lowered to just below q eps (and nothing else changes; monotonicity is
kept because every setting safer than z has p_m <= q eps). In the
alternative z is in T and must be certified with probability 1 - beta; in
the real instance certifying z is possible only if p(z) < eps. So the
procedure must either certify z (cost >= L / KL(p || eps)) or tell the two
instances apart (cost >= L' / KL(p || q eps)).

**(b) Without the ordering.** Every setting must be resolved on its own:

    L * sum over x of [ x in T ? max_m 1/KL(p_m(x) || eps)
                                 : min(certify-all cost, min over m with p_m > q eps of 1/KL(p_m || q eps)) ].

**Consequence.** With the ordering, both terms of (a) involve only the
edge of T and the boundary just outside it, at most O(M n) points on an
n x n grid. Without it, (b) involves every setting. Theorems 7 and 8a
match up to:
- an O(log n) factor (binary search; O(log d) with a simulator whose edge
  is off by d positions);
- the ratio C* / C(p_boundary) between the worst-case and the actual probe
  costs;
- log factors ln(M N / alpha) / L from multiple testing.

## 7. Evidence (`results/final/fixed_confidence*.csv`, 4 runs per size)

Toy LPBF window, good simulator; the search stops on its own and was
complete in every run:

| grid | search | lower bound (8a) | ratio | no ordering | lower bound (8b) |
|---|---|---|---|---|---|
| 8x8 | 14.2k | 3.5k | 4.0 | 21.9k | 4.4k |
| 12x12 | 27.2k | 6.7k | 4.1 | 46.1k | 9.9k |
| 16x16 | 50.3k | 13.1k | 3.8 | 100.0k | 19.9k |
| 24x24 | 101.5k | 20.3k | 5.0 | 238.5k | 40.7k |
| 32x32 | 165.6k | 32.8k | 5.1 | n/a | 75.8k |
| 48x48 | 334.6k | 40.4k | 8.3 | n/a | 169.0k |

The ratio grows slowly (4 -> 8 over a 6x larger grid), consistent with the
O(log n) factor; the unordered lower bound grows about twice as fast as
the ordered one, and the per-setting method's cost with it. Optimistic
simulator, 32x32: search 214.8k vs 458.0k without the ordering.

**Where the remaining gap is.** Starting each row's search at the edge
found in an adjacent row (`warm_start="both"`, now the default) cuts probes
substantially (32x32: 179 -> 142 with a good simulator, 258 -> 148 with an
optimistic one) but total coupons only slightly (0% and -9%). At 32x32
the search uses about 142 probes for 88 lower-bound points (1.6x), so the
search itself is close to tight. Most of the ratio to the lower bound is
the multiple-testing price per decision: ln(16 M N / (alpha w)) is about
13.8 nats against L = 2.15 in the single-hypothesis lower bound, a factor
of about 6. That price is shared by every method that certifies many
settings with a family-wise guarantee.

## 8. Open points

1. Probes per row are already close to O(1) with neighbour warm starts on
   smooth windows; proving it needs an assumption on how fast the edge can
   move between rows (a Lipschitz-type condition on the staircase).
2. Replace C* by an instance-dependent quantity (probes concentrate near
   the edge, where costs are C(p) for p near q eps, not the worst case).
3. Make the Theorem 7 accounting for shared coupons and plates explicit.
