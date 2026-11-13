# Certifying Safe Operating Regions under Monotone Failure Modes

*Draft v1, 2026-11-13 (supersedes draft.md). Working draft for ICML 2027.
Theorems are drafts that need independent checking; citations need
verification. Numbers marked TBD come from runs in progress.*

## Abstract

Many systems are configured by a few continuous knobs, and each knob setting
can fail in more than one way: a language model sampled at low temperature
degenerates into repetition and at high temperature into incoherence; a
laser powder bed fusion process at low energy leaves unmelted powder and at
high energy drills keyhole pores. Practitioners need the *safe operating
region*: the settings where every failure mode is rare. Estimating each
failure rate requires trials at that very setting (generations to judge,
coupons to build), so the cost of evaluating a configuration grid grows with
its area. We study **certifying a safe region with a family-wise guarantee
when every configuration needs its own trials**, exploiting the one piece
of structure these systems share: each failure mode is monotone in known
directions. We give (i) the **cone rule**, a closed-testing procedure with
betting e-processes that is valid at any stopping time and under any
adaptive choice of trials, and reduces under monotonicity to two cumulative
sums; (ii) a **search algorithm** for the fixed-confidence version that
stops on its own once the target region is certified; (iii) **lower bounds**
showing that with the ordering the cost is governed by the region's
*edge*, without it by its *area*, and **upper bounds** within logarithmic
factors of the ordered bound. On sampling settings of a language model
(TBD), on additive-manufacturing process windows and on a two-drug
combination screen, the method needs [TBD] fewer trials than adaptive
testing without the ordering and [TBD] fewer than evaluating every setting
with a Learn-then-Test style full grid, with no unsafe setting certified in
any run, while a Gaussian-process level-set baseline certifies unsafe
settings in 7.5-100% of runs unless it certifies almost nothing.

## 1. Introduction

**Motivating example.** A team deploying a language model must pick
sampling settings (temperature, top-p). Too low, and outputs repeat
themselves; too high, and they stop making sense. They want a region of
settings where, with 95% confidence, both failure rates are below 10%, so
any setting in it is safe to ship. Each setting's failure rates can only be
estimated by generating outputs at that setting and judging them, which is
expensive at scale. The same pattern appears in process qualification for
additive manufacturing (laser power x scan speed; lack of fusion vs.
keyholing), in dose finding for drug combinations (toxicity vs. lack of
response), and in operating envelopes of controllers and robots.

**What we ask for.** A certified region C with
P(C contains a setting where some failure rate is >= its tolerance) <= alpha,
valid when the experimenter looks at results after every batch and stops
whenever they like, and valid however the next trials are chosen, including
by an imperfect model or simulator.

**Why existing tools fall short.**
- *Risk control for configurations* (Learn-then-Test, Angelopoulos et al.;
  Pareto Testing, Laufer-Goldshtein et al. 2023; Conformal Language
  Modeling, Quach et al. 2024; MultiRisk 2025) evaluates every candidate
  configuration on a shared calibration set. When evaluating a
  configuration means fresh trials at it, that costs the full grid.
- *Adaptive multiple testing with bandits* (Jamieson & Jain 2018; Xu, Wang
  & Ramdas 2021) samples adaptively but treats configurations as unrelated.
- *Monotone thresholding bandits* (Garivier, Menard & Rossi 2017; Cheshire,
  Menard & Carpentier 2020) use order in one dimension, for one constraint,
  without anytime validity.
- *Safe Bayesian optimization and GP level-set estimation* (Sui et al. 2015;
  Gotovos et al. 2013; Losalka & Scarlett 2023, 2024) rely on the GP model
  being right; we show their certificates fail when it is not (Section 6).

**Structure.** In all these systems each failure mode is monotone in known
directions (repetition falls with temperature, incoherence rises with it).
So the null hypotheses "setting x is unsafe for mode m" are logically
related: if x is unsafe, so is everything riskier than x.

**Contributions.**
1. *Problem.* Certification of a safe region under per-mode partial orders
   when each configuration needs its own trials, in a fixed-budget and a
   fixed-confidence version (Section 2).
2. *Testing.* The cone rule: closed testing with weighted e-values, which
   under monotonicity is a cumulative sum; valid at every time under
   arbitrary adaptive sampling; spreading and pooling built in (Section 3).
3. *Allocation.* For a fixed budget, build trials at the riskiest
   uncertified settings of a slightly shrunken target (the lower bound's
   binding constraints). For fixed confidence, a galloping/bisection search
   along the ordering with a two-sided probe that never stalls near a
   threshold (Section 4).
4. *Theory.* Lower bounds with and without the ordering (edge vs. area);
   an oracle upper bound by Wald's identity; an upper bound for the search
   within O(log n) and multiple-testing factors of the ordered lower bound
   (Section 5).
5. *Experiments.* A language model's sampling settings, additive
   manufacturing (a physics-based Rosenthal melt-pool model and a synthetic
   window), and a drug-combination screen (Section 6).

## 2. Problem

Configurations form a grid X (here two axes, n_1 x n_2). There are M
failure modes. A trial at x yields Y in {0,1}^M, i.i.d. given x (modes may be
dependent). The failure rate is p_m(x) = E Y_m; x is safe if
p_m(x) < eps_m for all m, and the safe region is W.

**Assumption A (monotone failure modes).** For each m there is a known
product order ⪯_m on X such that x ⪯_m y implies p_m(y) <= p_m(x)
("y is at least as safe as x for mode m").

**Protocol.** Trials are requested in batches; each batch is chosen from all
data so far and any side information (a simulator, a cheaper model, a pilot
study) before its outcomes are seen.

**Fixed budget.** Output certified sets C_t with
P(C_t ⊆ W for all t) >= 1 - alpha, and make C_t large.

**Fixed confidence.** For a target slack q < 1 and
T = {x : p_m(x) <= q eps_m for all m}, stop at a time tau with a certified
set C such that validity holds and P(tau < inf, T ⊆ C) >= 1 - beta.
Settings with rates between q eps and eps may be certified or not.

## 3. Testing: the cone rule

*Per-configuration evidence.* For each (m, x), a betting e-process
K_{m,x}(t) = prod over trials s at x of (1 + lam_s (eps_m - Y_{s,m})), with
lam_s chosen before trial s. Under H_{m,x}: p_m(x) >= eps_m it is a
nonnegative supermartingale. We bet with a hedge: half a plug-in bet seeded
by side information, half a mixture of eight fixed bets.

*The rule.* Fix weights w_{m,x} >= 0, sum <= 1, before the trials. Certify x
for mode m once

    S_m(x, t) = sum over y at least as risky as x of w_{m,y} K_{m,y}(t) >= 1/alpha,

and certify x if certified for every mode.

**Theorem 1 (validity).** Under Assumption A, for any allocation and any
stopping time, P(some unsafe (m, x) is ever certified) <= alpha.
*Proof.* The unsafe pairs D are closed toward risk, so a false
certification of x makes S_m(x) <= sum_{(m,y) in D} w K, a nonnegative
supermartingale starting at most 1; Ville's inequality. ∎

This is closed testing (Marcus, Peritz & Gabriel 1976) with the weighted
e-value intersection test (Vovk & Wang 2021); monotonicity makes the
smallest admissible intersection a cone, so the closure is a cumulative sum.

*Weights.* Certifying x with weight w costs about ln(1/(alpha w)) / KL(p || eps)
trials; weights should sit on likely edge points. We use the frequency with
which a setting is an edge point under perturbed side information (logit
shifts), mixed 50/50 with uniform weights.

## 4. Allocation

**Fixed budget: edge rule.** Estimate the target with slack (all estimated
rates below 0.7 eps); for each mode, run trials at its riskiest uncertified
settings, several per batch, cheapest first; re-check uncertified settings
whose lower confidence bound still admits membership.

**Fixed confidence: search.** Per mode and row, run a two-sided probe at
one setting at a time: certify it (cone rule), or reject "p <= q eps" with
a defect-betting e-process at level beta/(MN). A certificate spreads to
safer settings, a rejection to riskier ones. Start at the edge found in an
adjacent row (or the side information's predicted edge), gallop until the
edge is bracketed, then bisect. Stop when every row is decided.

## 5. Theory

Let L = (1 - beta) ln(1/alpha) - ln 2.

**Theorem 2 (lower bounds).** (a) With the ordering, any
(alpha, beta)-correct procedure needs at least L * LP(T) trials to
certify T, where the LP's binding constraints are T's riskiest points for
each mode (at most min(n_1, n_2) per mode), plus, in the fixed-confidence
problem, L * sum over the settings just outside T of
min(1/KL(p || eps), 1/KL(p || q eps)). (b) Without the ordering, every
setting must be resolved individually, a sum over the whole grid.

**Theorem 3 (oracle upper bound).** Building trials only at a cover of T
costs at most sum over the cover of (ln(16/(alpha w)) + b)/g(p) in
expectation (Wald's identity), with g within 5% of KL(p || eps) for rates
between 0.5% and 4% at eps = 5%.

**Theorem 4 (search).** The search is (alpha, beta)-correct, and its
expected cost is at most sum over (mode, row) of P_{m,j} C*, with
P_{m,j} = O(log(1 + d_{m,j})) probes for a starting point d positions from
the edge, and C* the largest two-sided probe cost, which is finite because
q < 1.

**Corollary.** On an n x n grid the ordered bounds involve O(M n) settings
and the unordered bound O(n^2); the search is within O(log n) and the
multiple-testing factor ln(MN/alpha)/L of the ordered lower bound.

## 6. Experiments

**Applications.**
- *Language model sampling.* SmolLM2-135M; 12 temperatures (0.2-2.0) x 12
  top-p values (0.5-1.0); prompts from WikiText-2; degenerate = more than
  20% of 4-grams repeated, incoherent = mean token NLL above 3.5 nats;
  eps = 10% for both. Ground truth from 160 generations per setting
  (monotone fit); side information = a pilot of 16 generations per setting
  (counted in the budget). [TBD]
- *Additive manufacturing.* A Rosenthal melt-pool model of 316L with
  Tang et al. lack-of-fusion, King et al. keyhole and length/width balling
  criteria; a synthetic window with controllable simulator error.
- *Drug combination screen.* Toxicity and non-response surfaces with a
  synergy term; Bliss independence as side information.

**Fixed budget** (from draft v0, all at 24x24 unless stated). Trials to
certify 70% of the safe region: ours vs. no ordering 5.0x fewer (synthetic
window), 1.5-1.7x (Rosenthal 316L), 1.3x (drug screen). Scaling to 48x48:
9.1x (synthetic) and 2.2x (Rosenthal) fewer than no ordering; 26x and 42x
fewer than a full grid with Bonferroni. Language model: [TBD].

**Fixed confidence** (synthetic window, good side information; the search
stops on its own and certified the full target in 23 of 24 runs; the
exception hit a probe time-out). Lower bounds from the corrected joint
program (appendix, Theorem 2):

| grid | search | ordered lower bound | ratio | no ordering | unordered bound |
|---|---|---|---|---|---|
| 8x8 | 14.2k | 3.4k | 4.2 | 21.9k | 4.5k |
| 16x16 | 50.3k | 8.8k | 5.7 | 100.0k | 18.7k |
| 32x32 | 165.6k | 19.4k | 8.5 | 457.7k | 77.0k |
| 48x48 | 334.6k | 24.8k | 13.5 | not run | 174.4k |

Both methods pay a similar multiple-testing price over their own bound
(per-setting 4.8-5.9x); the search's extra growth is the O(log n) probe
factor. Language model: [TBD].

**Validity.** Worst case (every setting at the tolerance): 0-2.75%
false certification across configurations at alpha = 5% (400 runs each);
no unsafe setting certified in any efficiency run.

**Model-based baseline.** GP level-set certification certifies an unsafe
setting in 40-100% of runs at beta = 2 and still 7.5-20% at beta = 4,
where it certifies at most 69% (drug screen) and typically under 25% of
the region; ours: 0% and 54-84%. Language model: [TBD].

**Ablations.** The ordering and the allocation rule matter most (no
ordering +69 to +213%; greedy allocation +63 to +94%); weights, pooling and
bet seeding give smaller gains; a fixed maximum bet fails when relevant
rates are near the tolerance.

**When monotonicity fails.** A pocket of unsafe settings inside the region
is certified by spreading in 75-92% of runs; an audit re-testing every
certified setting (about 1.2x the budget) catches gross violations (96-100%)
but rarely mild ones (4-9%).

## 7. Related work

(As in draft v0, plus: Conformal Language Modeling (Quach et al. 2024),
MultiRisk (2025) and conformal certification of LLM outputs (2026) for
risk control of generation settings with a shared calibration set; Celeus
(2026) and adaptive auditing with e-values (2026) for anytime-valid LLM
evaluation of a single system.)

## 8. Limitations

Assumption A is load-bearing (Section 6); thin regions gain less at coarse
resolution; the multiple-testing factor dominates the gap to the lower
bound; the language-model study uses a small model and automatic judges;
the manufacturing studies are simulated with placeholder calibrations.
