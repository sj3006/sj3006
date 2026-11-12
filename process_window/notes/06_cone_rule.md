# Note 6: the cone rule (closed testing with e-processes), and the slack upper bound

Status: **draft, needs independent checking.** Prerequisites: notes 1, 2, 3, 5.
Code: `pwcert/cone.py`.

## 1. Why a new rule

The procedure in notes 2-4 grew by accretion: chains (fixed-sequence
testing), one-point chains (Bonferroni + spreading), a hybrid of the two
with the budget split in half, and an open question about passing budget
between chains with e-processes (note 3, section 4). The cone rule replaces
all of that with one fixed weight table and one inequality, and its validity
proof is three lines.

## 2. The rule

Every (mode, setting) pair i = (m, x) gets:
- a betting e-process K_i(t) for H_i: p_m(x) >= eps_m (note 1), updated by
  every coupon built at x;
- a fixed weight w_i >= 0, chosen before any test data, with sum_i w_i <= 1.

For mode m and setting k, let C_m(k) be k's **riskier cone**: all settings
at least as risky as k for mode m (k included). Define

    S_m(k, t) = sum over x in C_m(k) of w_{m,x} K_{m,x}(t).

**Rule.** Certify k for mode m at the first time S_m(k, t) >= 1/alpha, and
keep it certified. The certified window is the set of settings certified
for every mode.

Two properties come for free:
- *Spreading.* If j is safer than k, C_m(j) contains C_m(k), so
  S_m(j) >= S_m(k). The certified set for each mode is automatically closed
  toward safety.
- *Pooling.* Several riskier settings with moderate evidence can certify k
  together. Bonferroni + spreading ("max" rule) needs one of them to have
  w_x K_x >= 1/alpha alone. Since sum >= max, the cone rule certifies
  everything the max rule does, and possibly more.

## 3. Theorem 5 (validity)

**Theorem 5.** Under Assumption A, if the weights are fixed before the test
data (they may depend on a simulator or on separate pilot data), every
coupon's location is chosen before that coupon is inspected, and bets are
predictable, then

    P( some unsafe (mode, setting) pair is ever certified ) <= alpha.

*Proof.* Let D be the set of truly unsafe pairs (m, x): p_m(x) >= eps_m.
Under A, D is closed toward risk: if (m, x) is in D, so is every (m, y)
with y riskier than x for m. Suppose (m, k) in D is certified at time t.
Then S_m(k, t) >= 1/alpha, and C_m(k) is inside D's slice for mode m, so

    E_D(t) = sum_{(m,x) in D} w_{m,x} K_{m,x}(t)  >=  S_m(k, t)  >=  1/alpha.

Each K_{m,x} with (m, x) in D is a nonnegative supermartingale with respect
to the global filtration (note 2, Theorem 1, step 3), so the fixed-weight
sum E_D is too, starting at E_D(0) = sum_D w <= 1. By Ville's inequality,
P(E_D(t) >= 1/alpha for some t) <= alpha. ∎

*Where A is used:* only to know that k's riskier cone lies in D.
*What can depend on data:* the sampling (allocation) rule and the stopping
time, freely. The weights cannot (they would no longer be fixed in E_D).

**Relation to closed testing.** This is the closed testing procedure (Marcus,
Peritz & Gabriel 1976) whose intersection test for a set I of hypotheses is
the e-value sum_{i in I} w_i K_i, which is valid under any dependence (Vovk
& Wang, "E-values: calibration, combination and applications", Annals of
Statistics 2021, and "Confidence and discoveries with e-values", 2023).
Monotonicity means only riskier-closed sets I can be the true-null set,
and the smallest such set containing k is k's cone. So the closed testing
shortcut is exactly the cone sum, computable with two cumulative sums. Being
closed testing with e-processes, it is valid at every time simultaneously.
That settles the question in note 3, section 4: no explicit budget passing is
needed, because the closure already reuses the weight of hypotheses that are
"logically certified".

## 4. Choosing the weights

Certifying an edge setting x with weight w costs about

    ln(1 / (alpha w)) / KL(p_x || eps)    coupons

(note 1, section 4; the hedge e-process gets within ~12% of this in our
runs). With uniform weights w = 1/(M N) this is the Bonferroni price
ln(M N / alpha). If the target's edge points E were known, putting weight
1/|E| on each would cost ln(|E| / alpha) instead, and |E| <= M n on an n x n
grid (note 5, edge-size lemma). With an uncertain simulator, the natural
compromise is weight proportional to the probability that a setting is an
edge point. `make_weights(kind="ensemble")` estimates it by perturbing the
simulator (independent logit shifts per mode, standard deviation sigma) and
mixes it 50/50 with uniform, so a wrong simulator costs at most ln 2 nats
per certification relative to uniform.

Measured effect (16x16, coupons to certify the whole target {rates <=
eps/2}, 8 runs): ensemble weights beat uniform by 15% with a good
simulator and 5% with an optimistic one, consistent with saving about
1 of roughly 9.6 nats. The rule is about as efficient as the old hybrid
chains (within +/-10%, usually better) while being far simpler.

## 5. Theorem 3 with slack (upper bound), sketch

Fix targets q < q' <= 1. Goal: certify every setting in T = T_q (all rates
<= q eps), while settings with rates up to q' eps may also be certified
(that is allowed and costs nothing in validity).

Allocation (the edge rule with re-check, `alloc="edge"`, target_q = q'):
sample the riskiest uncertified settings of the estimated target; when it
is covered, re-check uncertified settings with the lowest lower confidence
bound, ignoring confidently unsafe ones.

**Claim (sketch).** With probability 1 - beta, the number of coupons until T
is certified is at most

    sum over edge points z of T, per mode, of  ln(1/(alpha w_z)) / g(p_z)        (certification)
  + sum over settings y with q eps < p_y <= q' eps on T's risky side of
        ln(M N / beta) / (q' - q)^2 eps        (membership; Bernstein-type)
  + lower-order terms,

where g is the growth rate of the betting strategy (about KL). The first
term matches the lower bound (Theorem 4a) up to ln(1/w) vs ln(1/alpha) and
g vs KL. The second is the price of not knowing where T ends. It disappears
as q' grows (more slack) and blows up as q' -> q, which is what we measured
(note 4, section 4b: overhead concentrated on settings just outside T).

**What's needed to make this a theorem:**
1. An expected-stopping-time bound for the hedge e-process (Waudby-Smith &
   Ramdas 2024 give growth-rate results; we need the stopping-time form).
2. A confidence-sequence argument that membership errors (a T point
   wrongly excluded, a non-T point wrongly included) get corrected within
   the stated number of coupons. The re-check step is what guarantees the
   first kind is corrected; the futility step bounds the second kind.
3. Accounting for the fact that a coupon at one setting serves all modes.

## 6. Check yourself

1. Why must the weights be fixed before the test data, while the sampling
   rule may depend on the data freely?
2. Show that the cone rule with w uniform certifies at least everything
   Bonferroni + spreading certifies.
3. Suppose the simulator is useless and you put all weight on settings it
   says are edge points. What happens to validity? To power?
4. Why does averaging the ensemble weights with uniform cost at most ln 2
   nats per certification?

(3: validity is unaffected; power is lost wherever the true edge has zero
weight, which is why the uniform floor is there. 4: every weight is at
least half its uniform value.)
