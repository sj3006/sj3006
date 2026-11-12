# Certifying Process Windows with Ordered Physics: Anytime-Valid, Simulator-Guided Discovery of Safe Operating Regions

*Draft v0, 2026-11-12. Working draft for an ICML 2027 submission. Theorems are
drafts and need independent checking; citations need verification against
the original papers.*

## Abstract

Before a manufacturing process is qualified, engineers must find its
*process window*: the settings (for laser powder bed fusion, laser power and
scan speed) at which every defect mode occurs below a tolerated rate. Today
windows are drawn from a fitted model or a full-factorial experiment, and
nothing guarantees they contain only good settings. We study **certifying a
feasible region** when every candidate setting needs its own costly
experiments, and give a procedure whose output region contains an unsafe
setting with probability at most alpha, at any stopping time, under any
adaptive choice of where to experiment, and for any simulator used to guide
it. The procedure combines betting e-processes per setting with a **cone
rule**: closed testing with weighted e-values, which under the monotone
structure of physical failure modes (lack of fusion falls with energy input,
keyholing rises with it) reduces to two cumulative sums. We prove matching
lower and upper bounds showing that, with the ordering, the cost of
certification is governed by the *edge* of the target region (at most
M n settings on an n x n grid with M failure modes), whereas any method
that ignores it must pay for the region's *area*. Across a toy LPBF window,
a Rosenthal melt-pool model of 316L and a two-drug combination screen, the
method needs 1.3-5x fewer experiments than the same adaptive tests without
the ordering at 24x24 resolution (2.2-9x at 48x48) and 26-42x fewer than
full-factorial practice at 48x48, with no false certification in any run,
while a Gaussian-process level-set baseline either certifies unsafe
settings in 7.5-100% of runs or certifies at most 8% of the window.

## 1. Introduction

**The problem.** Qualifying an additive manufacturing process (for example
under NASA-STD-6030) starts with a defined set of process parameters. For
laser powder bed fusion (LPBF), defects come in distinct modes: lack of
fusion at low energy input, keyhole porosity at high energy density, balling
when melt tracks become unstable. A *process window* is the set of settings
where each mode occurs rarely enough. It is usually found by building a
grid of test coupons, fitting a model, and drawing the region where the
model predicts few defects. Two things go wrong. The fitted region carries
no guarantee: near its boundary, defect rates are close to the tolerance and
a few coupons cannot distinguish 3% from 6%. And the grid is expensive: a
full factorial with enough coupons per setting to certify a 5% rate at 95%
confidence needs 59 defect-free coupons per setting even in the best case
(the success-run rule).

**What we ask for.** A region R of settings such that

    P( R contains a setting where some defect rate is >= its tolerance ) <= alpha,

that remains valid if experimenters look at the data after every build plate
and stop whenever they like, and that is valid regardless of how a simulator
(an analytical melt-pool model, a fitted surrogate) is used to decide where
to build next.

**Why this is not covered by existing tools.**
- Risk-control methods for ML configurations (Learn-then-Test, Pareto
  Testing) assume a single shared calibration set on which every candidate
  configuration can be evaluated for free. Here each setting requires its
  own physical experiments.
- Adaptive multiple testing with bandits (Jamieson & Jain 2018; Xu, Wang &
  Ramdas 2021) handles adaptive sampling but treats settings as unrelated.
- Monotone thresholding bandits (Garivier, Menard & Rossi 2017; Cheshire,
  Menard & Carpentier 2020) exploit order in one dimension, without anytime
  validity or multiple modes.
- Safe Bayesian optimization with monotonicity (Losalka & Scarlett 2023,
  2024) gives guarantees under Gaussian-process assumptions that are hard
  to verify.
- Sim-to-real certification by betting (Chen & Weng 2026) certifies a single
  performance number, not a region.

**The structure we exploit.** Each defect mode is monotone in a known
direction: lack of fusion becomes rarer with more power and less speed,
keyholing the reverse. This is physics every process engineer knows, and it
makes the null hypotheses "setting x is unsafe for mode m" *logically
related*: if x is unsafe, so is every setting riskier than x.

**Contributions.**
1. *Problem.* We formalize certification of a multi-dimensional feasible
   region under per-mode partial orders when each configuration requires
   its own experiments (Section 2).
2. *Method.* The cone rule (Section 3): certify a setting when the weighted
   betting wealth in its riskier cone reaches 1/alpha. It is closed testing
   with e-values specialized to logically related nulls, costs two
   cumulative sums per update, and has spreading and evidence pooling built
   in. A simulator enters only through fixed weights and the allocation rule,
   so a wrong simulator can cost efficiency but never validity. Without a
   simulator, a pilot plate and a monotone fit learn one.
3. *Theory* (Section 4). Validity at any stopping time (Theorem 1). A lower
   bound for any valid method with the ordering, governed by the target's
   edge points (at most M n), and one without the ordering, governed by its
   area (Theorems 2a, 2b). An oracle upper bound matching the ordered lower
   bound up to explicit testing, betting and sharing factors (Theorem 3).
4. *Experiments* (Section 5). A Rosenthal melt-pool model of 316L LPBF with
   standard defect criteria, a toy LPBF window with controllable simulator
   error, and a two-drug combination screen with a Bliss-independence
   simulator.

## 2. Problem setup

**Settings and modes.** A finite grid X of settings (here n_P x n_V), and
failure modes m = 1..M. A coupon built at x yields outcomes
Y = (Y_1, ..., Y_M) in [0, 1]^M, drawn i.i.d. from P_x (modes may be
dependent). The defect rate is p_m(x) = E Y_m, and x is safe for m if
p_m(x) < eps_m. The window is W = {x : p_m(x) < eps_m for all m}.

**Ordering (Assumption A).** For each mode there is a known partial order
on X, written x ⪯_m y ("y is at least as safe as x for m"), such that
x ⪯_m y implies p_m(y) <= p_m(x). On the (power, speed) grid each order is a
product order with mode-specific directions. In our Rosenthal model the
directions are measured, not assumed: lack of fusion (safer: more power,
less speed), keyhole (safer: less power, more speed), balling (safer: less
power, less speed).

**Protocol.** Coupons are built on plates; the settings on a plate are
chosen from all data so far (and any simulator) before the plate is
inspected. After any plate the experimenter may stop.

**Goal.** Output certified regions R_t with
P(R_t ⊆ W for all t) >= 1 - alpha, and make R_t large quickly.

## 3. Method

**Per-setting evidence.** For each (m, x), a betting e-process for
H_{m,x}: p_m(x) >= eps_m,

    K_{m,x}(t) = prod over coupons s at x of (1 + lambda_s (eps_m - Y_{s,m})),

with bets lambda_s >= 0 chosen before the coupon is inspected and capped so
wealth stays positive. Under H_{m,x}, K is a nonnegative supermartingale.
We use a hedge: half a plug-in bet (aGRAPA; Waudby-Smith & Ramdas 2024)
seeded with the simulator's prediction, half an equal mixture of eight fixed
bets. The success-run rule is the special case of the largest fixed bet
with no defects.

**Cone rule.** Fixed weights w_{m,x} >= 0 with sum <= 1. Let C_m(k) be the
settings at least as risky as k for mode m. Certify k for m at the first t
with

    S_m(k, t) = sum_{x in C_m(k)} w_{m,x} K_{m,x}(t)  >=  1 / alpha,

and output R_t = settings certified for every mode. S_m is computed for all
k at once by two cumulative sums along the risk directions.

**Weights from a simulator.** Certifying an edge setting with weight w costs
about ln(1/(alpha w)) / KL(p || eps) coupons, so weights should sit on likely
edge points. We perturb the simulator's predictions (independent logit
shifts per mode, standard deviation sigma = 1), compute the target's edge
points in each perturbed world, and use the frequency with which each setting
is an edge point, mixed 50/50 with uniform weights. The uniform half caps
the loss from a wrong simulator at ln 2 nats per certification.

**Allocation (edge rule).** Estimate a target region, the settings whose
estimated rates are all below q' eps with a slack q' < 1 (we use 0.7). For
each mode, build at the riskiest uncertified settings of that region, which
are exactly the binding constraints of the lower bound (Theorem 2a), filling
a plate with each setting's expected remaining coupons, cheapest first. When
the estimated region is covered, re-check uncertified settings whose lower
confidence bound still admits membership (optimism), and stop spending on
settings that are confidently unsafe. Aiming slightly inside the window
matters: aiming at q' = 1 chases settings whose rates are barely below eps,
whose certification cost blows up like 1/KL. A greedy alternative
("frontier": most new certified area per expected coupon) is 1.3-2.5x
worse in our experiments (ablation, Section 5).

**No simulator.** A pilot plate (4 coupons on every other setting in each
direction) and a 2D isotonic fit of pooled counts give a monotone
"learned simulator" used for weights and allocation. Pilot coupons are
counted in all budgets and never enter the tests.

## 4. Theory

**Theorem 1 (validity).** Under Assumption A, with weights fixed before the
test data, predictable bets and plate-wise predictable allocation,
P(some unsafe (m, x) is ever certified) <= alpha.

*Proof.* The truly unsafe pairs D form a set closed toward risk. A false
certification of k makes C_m(k) ⊆ D, so sum_{(m,x) in D} w K >= S_m(k)
>= 1/alpha. That sum is a nonnegative supermartingale starting at most 1;
Ville's inequality bounds the probability that it ever reaches 1/alpha. ∎

This is closed testing (Marcus, Peritz & Gabriel 1976) with the weighted
e-value intersection test (Vovk & Wang 2021), whose shortcut under the
ordering is the cone sum; no explicit budget passing is needed.

**Theorem 2a (lower bound with the ordering).** Any procedure that is
alpha-valid on monotone instances and certifies a target T ⊆ W with
probability 1 - beta uses, in expectation, at least L * LP(T) coupons,
L = (1 - beta) ln(1/alpha) - ln 2, where LP(T) minimizes sum_y n_y subject
to, for each mode m and each ⪯_m-minimal point z of T,
sum over safe y ⪯_m z of n_y KL(p_m(y) || eps_m) >= 1.
At most min(n_P, n_V) points of T are minimal per mode.

**Theorem 2b (lower bound without the ordering).** Any procedure valid on
all instances needs at least L sum_{z in T} max_m 1/KL(p_m(z) || eps_m).

*Proofs* use the transportation lemma (Kaufmann, Cappe & Garivier 2016)
with alternatives that raise rates to just above eps_m on z and everything
riskier (2a, staying monotone) or on z alone (2b).

**Theorem 3 (upper bound, oracle allocation).** If coupons are built only
at a cover F_m of T for each mode, the expected number of coupons is at most
sum_m sum_{z in F_m} (ln(16 / (alpha w_{m,z})) + b) / g(p_m(z)), where
g <= KL is the best growth rate in the bet grid and b <= ln(1 + eps).
*Proof:* Wald's identity for each fixed bet inside the hedge.

**Corollary (boundary, not area).** With the cover at T's edge, the upper
and lower bounds in Theorems 2a and 3 differ by a testing factor
ln(16/(alpha w))/L, a betting factor KL/g (1.00-1.05 at rates 0.5-4%), and a
sharing factor (about 1.2 measured). Neither bound grows with T's area,
while Theorem 2b does. The achievable speed-up from the ordering is about
|T| / |edge(T)|.

**Open: learned allocation.** With estimated rates, allocation pays an
extra cost for learning where T ends, which we bound only heuristically
(it depends on the slack between the target q and the allowed region q').

## 5. Experiments

**Scenarios.**
- *Toy LPBF window* (logistic defect rates in energy density, P/sqrt(v), v/P),
  with good (thresholds shifted ~0.5 logit) and optimistic (~3 logits)
  simulators.
- *Rosenthal 316L model*: Rosenthal melt pool with Tang et al. (2017)
  lack-of-fusion overlap, King et al. (2014) normalized-enthalpy keyhole and
  length/width balling criteria (placeholder calibrations); the simulator
  has misspecified absorptivity and criterion thresholds.
- *Two-drug screen*: toxicity (rising in both doses) and non-response
  (falling), with a synergy term; the simulator is Bliss independence.

**Methods.** Ours; ours without a simulator (pilot plate); the same
adaptive betting tests without the ordering (Bonferroni weights, same
allocation, same simulator prior); without the ordering and without a
simulator; and current practice (full factorial, exact binomial
Clopper-Pearson bounds, Bonferroni). alpha = 0.05, eps = 5% per LPBF mode
(30% toxicity, 50% non-response for the drug screen).

All methods below use edge allocation aimed at rates below 0.7 eps, which
is the best rule for both our method and the unordered baseline (ablation).

**Validity** (`results/final/validity_edge.csv`, `validity.csv`). Worst
case: every setting has every defect rate exactly at its tolerance, so any
certification is an error. 400 runs per row, 8x8 grids, 4,000 coupons per
run, edge allocation (frontier allocation gives the same picture).

| scenario | simulator | cone rule (ours) | Bonferroni + spreading | no ordering |
|---|---|---|---|---|
| toy LPBF | good | 0.25% | 0.25% | 0.00% |
| toy LPBF | adversarial | 0.00% | 0.00% | 0.00% |
| drug screen | good | 1.25% | 1.00% | 0.25% |
| drug screen | adversarial | 2.75% | 1.50% | 1.50% |

All rates are below alpha = 5%. In every efficiency run below (over 30
million simulated coupons in total), our method never certified an unsafe
setting.

**Certified area vs budget** (`fig_curves.png`; 24x24 grids, 8 runs per
method, budget 115,200 coupons, resolution 2,880). Coupons (thousands) to
certify 50% / 70% of the true window:

| scenario | ours | ours, no simulator | no ordering | no ordering, no sim. | grid DoE |
|---|---|---|---|---|---|
| toy LPBF, good simulator | **11.5 / 17.3** | 11.5 / 20.2 | 60.5 / 86.4 | 74.9 / 103.7 | not reached |
| toy LPBF, optimistic simulator | 23.0 / 28.8 | **11.5 / 20.2** | 66.2 / 95.0 | 74.9 / 103.7 | not reached |
| Rosenthal 316L, good simulator | **14.4 / 25.9** | 17.3 / 37.4 | 23.0 / 43.2 | 28.8 / 49.0 | not reached |
| Rosenthal 316L, optimistic sim. | 20.2 / **31.7** | **17.3** / 37.4 | 25.9 / 46.1 | 28.8 / 49.0 | not reached |
| two-drug screen, Bliss simulator | **28.8 / 72.0** | 34.6 / 80.6 | 43.2 / 95.0 | 49.0 / 106.6 | 25% at 109k |

At 70% of the window, ours needs 5.0x fewer coupons than the same tests
without the ordering on the toy window (3.3x with an optimistic simulator),
1.5-1.7x fewer on the thin Rosenthal band and 1.3x fewer on the drug
screen. A pilot plate without any simulator does about as well as a good
simulator and *better than a badly optimistic one*. Full-factorial practice
does not reach a quarter of any LPBF window within this budget.

**Scaling** (`fig_scaling.png`; coupons to certify 50% of the window,
median of 5 runs):

| grid | toy: ours | toy: no ordering | toy: grid DoE | 316L: ours | 316L: no ordering | 316L: grid DoE |
|---|---|---|---|---|---|---|
| 8x8 | 2.6k | 4.9k | 17.5k | | | |
| 12x12 | 3.8k | 12.3k | 39.5k | 4.8k | 4.1k | 69k |
| 16x16 | 7.6k | 24.6k | 77.1k | 5.3k | 7.7k | 135k |
| 24x24 | 10.8k | 61.1k | 173k | 13.0k | 21.1k | 367k |
| 32x32 | 16.6k | 116k | 339k | 19.5k | 38.0k | 653k |
| 48x48 | 29.6k | 270k | 763k | 42.5k | 93.5k | 1,772k |

Fitted exponents (cost ~ n^k over the range): toy window, ours 1.36, no
ordering 2.24, grid DoE 2.10; Rosenthal band, ours 1.58, no ordering 2.26,
grid DoE 2.34. At 48x48 ours needs 9.1x (toy) and 2.2x (Rosenthal) fewer
coupons than the same tests without the ordering, and 26x and 42x fewer
than grid DoE. The gap grows with resolution as predicted. The thin band
starts at parity (12x12, where its area/edge ratio is 1.2) and pulls ahead
as the ratio grows (4.2 at 48x48).

**Certifying every setting of a target** (`fig_bounds.png`; target: all
rates <= eps/2, toy window, median of 3 runs):

| grid | target size | edge points | lower bound, ordered | lower bound, unordered | ours | no ordering |
|---|---|---|---|---|---|---|
| 8x8 | 28 | 13 | 987 | 1,787 | 5.6k | 9.7k |
| 12x12 | 69 | 18 | 2,142 | 5,050 | 11.1k | 30.7k |
| 16x16 | 122 | 24 | 2,902 | 8,572 | 19.0k | 58.2k |
| 24x24 | 287 | 34 | 6,158 | 21,901 | 55.3k | 159.5k |
| 32x32 | 513 | 45 | 8,821 | 39,026 | 114.2k | not within 307k |

The two lower bounds separate as predicted (edge vs area). Ours needs
1.7-3.1x fewer coupons than the unordered method, but its ratio to the ordered lower bound
grows from 5.7 to 12.9: on this strict goal, learning where the target ends
costs more as the grid gets finer (Section 4, open problem; with an oracle
allocation the cost tracks the upper bound of Theorem 3, note 4).

**Ablations** (16x16, coupons to certify 50% of the window, median of 8
runs; `ablation_*.csv`):

| variant | toy, good sim. | toy, optimistic sim. | drug screen |
|---|---|---|---|
| ours | 7.8k | 10.0k | 10.4k |
| greedy frontier allocation | +94% | +90% | +63% |
| edge allocation aimed at the full window (no slack) | +91% | +173% | +29% |
| no ordering | +213% | +157% | +69% |
| uniform weights | +6% | +18% | +25% |
| Bonferroni + spreading (no pooling) | -7% | 0% | +19% |
| no simulator prior in bets | +24% | -3% | +41% |
| fixed maximum bet instead of hedge | -16% | +26% | never reaches 50% |

The ordering and the allocation rule matter most. Weights and evidence
pooling give smaller, mostly positive effects. The fixed maximum bet is
cheaper when clean settings dominate but fails outright when the relevant
rates are near the tolerance (drug screen), which is why we hedge.

**Model-based baseline** (`gp_baseline.csv`; GP level-set certification,
certify where mean + beta * sd < eps, RBF kernel, binomial noise; 16x16,
40 runs per row, budget 15,360 coupons):

| scenario | GP, beta = 2 | GP, beta = 3 | GP, beta = 4 | ours |
|---|---|---|---|---|
| toy LPBF | 80-100% / 90-98% | 2.5-60% / 0-89% | 0-20% / 0-51% | **0% / 84%** |
| Rosenthal 316L | 40-100% / 51-87% | 2.5-15% / 2-44% | 0-7.5% / 0-25% | **0% / 75%** |
| drug screen | 92-98% / 90-94% | 38-53% / 61-78% | 7.5-15% / 29-69% | **0% / 54%** |

Entries: share of runs that certified at least one unsafe setting / share
of the window correctly certified, over lengthscales 0.1, 0.2, 0.3. With
beta = 2, the GP certifies an unsafe setting in nearly every run. The only
GP settings with error rates at or below 5% certify at most 8% of the window.
The GP's guarantee requires a correctly specified model, and defect rates
with sharp transitions are not one.

**When monotonicity fails** (`violation.csv`; 16x16 toy window with a
pocket of unsafe settings inside it, 60 runs per row):

| pocket | certified by spreading | caught by a full audit | false audit flags |
|---|---|---|---|
| 1 setting at 15% | 77% of runs | 96% | 0 |
| 2x2 settings at 15% | 90% | 100% | 0 |
| 1 setting at 8% | 75% | 4% | 0 |
| 2x2 settings at 8% | 92% | 9% | 0 |

Assumption A is load-bearing. An audit that re-tests every certified
setting with a defect-betting e-process (up to 300 coupons each, about
1.2x the certification budget) catches gross violations and rarely catches
mild ones.

## 6. Related work

*Anytime-valid inference and e-values:* Ville (1939); Shafer (2021);
Ramdas, Grunwald, Vovk & Shafer (2023); Vovk & Wang (2021); Wang & Ramdas
(2022); Waudby-Smith & Ramdas (2024). *Multiple testing with structure:*
closed testing (Marcus, Peritz & Gabriel 1976), sequential rejection
(Goeman & Solari 2010), graphical procedures (Bretz et al. 2009), closure
for monotone bi-factorial dose designs (Hellmich & Lehmacher). *Adaptive
testing and bandits:* Jamieson & Jain (2018); Xu, Wang & Ramdas (2021);
thresholding bandits (Locatelli, Gutzeit & Carpentier 2016) and their
monotone versions (Garivier, Menard & Rossi 2017; Cheshire, Menard &
Carpentier 2020); lower bounds (Garivier & Kaufmann 2016; Kaufmann, Cappe &
Garivier 2016); multi-fidelity best-arm identification (Poiani et al. 2022,
2024). *Risk control for configurations:* Learn-then-Test (Angelopoulos et
al.); Pareto Testing (Laufer-Goldshtein et al. 2023). *Using predictions in
tests:* prediction-powered inference and e-values (Angelopoulos et al. 2023;
Csillag et al. 2025); active statistical inference (Zrnic & Candes 2024);
sim-to-real betting (Chen & Weng 2026). *Safe exploration and level sets:*
SafeOpt (Sui et al. 2015); monotone safe BO (Losalka & Scarlett 2023,
2024); level-set estimation (Gotovos et al. 2013; Mason et al. 2022).
*Applications:* AM process mapping and qualification (process-map reviews;
BEAM, Doppa group 2026; NASA-STD-6030); dose finding for combinations
(partial-order CRM, Wages et al.).

## 7. Limitations

- **Assumption A must hold.** If a mode is not monotone (for example
  spatter at extreme power), the guarantee can fail there. A sequential
  test of monotonicity should accompany the method; we have not built it.
- **Thin windows.** When the window is a sliver at the chosen resolution
  (area close to its edge length), the ordering helps little: on the
  Rosenthal band the two methods are at parity at 12x12, and the gain
  appears only as the grid gets finer.
- **No simulator.** The pilot-learned simulator recovers much, not all, of
  the benefit of a good simulator.
- **Learned allocation** is not covered by a theorem, and on the strict
  goal of certifying every point of a target its cost relative to the
  ordered lower bound grows with resolution (5.7x at 8x8 to 12.9x at
  32x32), driven by learning which settings belong to the target.
- **Real data.** All experiments are simulated; the defect criteria are
  placeholder calibrations. A real LPBF campaign is the next step.
- **Grid, not continuum.** Certificates extend to a continuous box under
  Assumption A (each certified point certifies its safer orthant), but
  allocation is on a grid.

## Reproducibility

All code is in `process_window/` of this repository: `pwcert/cone.py`
(method), `pwcert/eprocess.py` (betting e-processes), `pwcert/physics.py`,
`pwcert/dose.py`, `pwcert/pilot.py`, and `experiments/final.py` (every
number and figure in Section 5).
