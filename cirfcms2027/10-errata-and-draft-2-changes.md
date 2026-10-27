# Errata and changes for draft 2

A running list of defects found in the first draft of the paper
(`paper/paper.tex`, 6 pages, two-column Procedia layout) after it was written.

**How this file works.** One entry per defect, newest at the top of its section.
Every entry carries the same five fields:

    WHAT DRAFT 1 SAYS   verbatim, with the paper section and the .tex line
    WHAT IS WRONG       the defect, stated plainly
    EVIDENCE            the measurement that establishes it
    DOES IT CHANGE THE RESULT?   honestly, including "no"
    CHANGE FOR DRAFT 2  the edit to make

Entries are classified:

    [E]  error present in draft 1 - the paper states something untrue or too strong
    [O]  omission in draft 1 - nothing false, but something load-bearing is missing
    [W]  working error - a mistake made during analysis, caught before it reached
         the paper. Logged so it is not repeated, not because draft 1 is wrong.

**Nothing in this file has been applied to the paper yet.**

---

## Status summary

| id | type | one line | changes a result? |
|---|---|---|---|
| E1 | error | "every conclusion invariant" to the conductivity coupling is too strong | **yes, one cell** |
| E2 | error | 11.7 % / 13.0 % is an aggregate that hides the base-case error and a one-sided bias | no |
| E3 | error | the VED correlation coefficients do not reproduce, are grid-dependent, and are mis-framed as a check against external data | no diagnosability result; weakens one validation leg |
| O1 | omission | the operating point the whole analysis linearises about is never stated | no |
| W1 | working | spot size used as the Gaussian sigma instead of a D4-sigma diameter | no |

---

# E1. "Every conclusion invariant to it" is too strong [E]

## What draft 1 says

Section 3.2, `paper.tex` lines 236-238:

> "Its conductivity coupling remains an unmeasured estimate, swept across its
> plausible range in Section 4.5 **with every conclusion invariant to it**."

and Section 4.5, lines 427-429:

> "The unmeasured conductivity coupling leaves the worst angle at 25.83 degrees
> throughout its range..."

## What is wrong

The second sentence is true. The first is not. *Every accumulated-regime*
conclusion is invariant to `layer_to_conductivity`. One **instantaneous** class
assignment is not, and the coupling turns out to be load-bearing in a way the
draft never mentions.

## Evidence

Instantaneous pairwise angles against the coupling `c_k`:

| c_k | power/layer | speed/layer | layer/gas | layer/geometry |
|---|---|---|---|---|
| **0.00** | **0.00** | 7.12 | **0.00** | 61.39 |
| 0.10 | 2.34 | 9.46 | 2.34 | 59.36 |
| 0.25 | 3.09 | **10.21** | 3.09 | 58.71 |
| **0.50 (study value)** | 3.46 | **10.58** | 3.46 | 58.40 |
| 0.75 | 3.60 | 10.72 | 3.61 | 58.27 |
| 1.00 | 3.68 | 10.80 | 3.68 | 58.21 |
| 1.50 | 3.76 | 10.88 | 3.76 | 58.14 |

Enlarged pairwise angles over the same sweep:

| c_k | power/layer | speed/layer | layer/gas | layer/geometry | overall worst | rank | cond |
|---|---|---|---|---|---|---|---|
| 0.00 | 36.26 | 46.57 | 44.48 | 68.59 | **25.83** | 5 | 47 |
| 0.50 | 36.40 | 47.08 | 44.58 | 66.45 | **25.83** | 5 | 30 |
| 1.50 | 36.43 | 47.13 | 44.60 | 66.27 | **25.83** | 5 | 36 |

Two consequences.

**speed/layer crosses the isolability floor inside the swept range.** At the
study value it clears 10 degrees by **0.58 degrees**. Below about c_k = 0.2 it
falls under and becomes class 2. The draft's instantaneous count of "five of ten
pairs in class 1" depends entirely on this one marginal pair: the other four
class-1 pairs are all geometry pairs at 58-68 degrees. At c_k = 0.1 the count is
4/10, not 5/10.

**At c_k = 0 the layer fault becomes exactly confounded with power and gas**,
both reading 0.00 degrees. This is not numerical noise. The layer fault's two
power-side channels nearly cancel - absorptivity -0.230 plus enthalpy +0.186
gives a net -0.044 on the product (absorptivity x power) - so with no
conductivity channel the layer fault acts *only* through the same product that
power and gas act through, and joins their degeneracy exactly.

**The conductivity coupling is therefore the only thing that makes a layer fault
instantaneously distinguishable from a power fault at all**, and it is the one
coupling in the model with no literature behind it.

Why the enlarged regime does not care: the coupling changes the layer
signature's *magnitude* by a factor of 23 (whitened column norm 0.101 at c_k = 0
to 2.326 at c_k = 1.5) but its *direction* by under half a degree across
0.25-1.5. Angles depend only on direction.

| c_k | layer column norm | angle vs c_k = 0.50 |
|---|---|---|
| 0.00 | 0.101 | 3.46 deg |
| 0.25 | 0.472 | 0.37 deg |
| 0.50 | 0.843 | - |
| 1.00 | 1.584 | 0.22 deg |
| 1.50 | 2.326 | 0.30 deg |

## Does it change the result?

**The headline: no.** Power/gas stays at 0.00 degrees (algebraic, nothing to do
with layer couplings). Instantaneous rank stays 3, enlarged rank stays 5. The
enlarged worst pair is **25.83 degrees at every value of the coupling**. The
paper's central contribution - build context dissolves the instantaneous limit -
is untouched, as is the whole accumulated regime where all ten pairs are class 1.

**One secondary number: yes.** The instantaneous class-1 count of 5/10 is
contingent on c_k being above roughly 0.2. It is also sensitive to the floor
convention: speed/layer is at 10.58 degrees, so any floor above that gives 4/10.

## Change for draft 2

1. Replace the Section 3.2 clause. Proposed: *"...swept across its plausible
   range in Section 4.5, with every accumulated-regime conclusion invariant to
   it. In the instantaneous regime it is load-bearing: it is the only channel
   separating a layer fault from a power fault, and speed/layer clears the 10
   degree floor at 10.58 degrees only for couplings above about 0.2."*
2. Add a caveat where the 5/10 instantaneous count is reported (Section 4.6),
   noting that speed/layer clears the floor by 0.58 degrees and that the count
   is 4/10 for a weaker coupling or a slightly higher floor.
3. Name the measurement that would settle it: Liu, Kinzel and Leu (2023),
   lock-in thermography of powder layer thermal diffusivity against thickness.

**Also fix in the code, not the paper:** the `FaultCouplings` docstring in
`src/faults.py` claims conductivity is "by far the weakest of the three layer
effects: isolating each at f = 0.2 moves the melt depth by 3.4 % (absorptivity),
1.6 % (enthalpy) and 0.35 % (conductivity)." Re-measured, those are -3.55 %,
+2.97 % and -1.41 %. Conductivity is four times stronger than documented, and
because the first two nearly cancel it is the **dominant surviving channel**,
not the weakest. The docstring states the opposite of the truth.

---

# E2. 11.7 % / 13.0 % is an aggregate that conceals three things [E]

## What draft 1 says

Section 3.1, `paper.tex` line 205:

> "Four parameters --- effective absorptivity, effective conductivity, heat
> capacity and the keyhole constant --- are fitted to the seven IN718 bare-plate
> single-track cases of the 2022 Additive Manufacturing Benchmark, giving
> **11.7 % error on melt pool width and 13.0 % on depth**."

## What is wrong

The numbers are correctly computed - the fit returns width 11.687 %, depth
13.036 % - but presenting them alone is misleading in three ways.

**(a) It is not the error at the point the paper linearises about.** Those are
means over seven conditions. At the baseline condition itself, which is where
the entire Jacobian is evaluated, the width error is **-15.54 %**, worse than
the quoted aggregate and **3.4x the measurement's own expanded uncertainty**
(U, k=2, of 6.2 um). The depth error there is +1.72 %, 0.2x its uncertainty -
the best of all seven. The base case is lopsided, and the aggregate hides it.

**(b) A mean absolute percentage error implies two-sided scatter. It is a
one-sided miss.** All seven width errors are negative. The model is
systematically narrow at every condition, which is a structural property of a
constant-property conduction solution - it has no Marangoni convection and no
recoil-driven spreading, so it cannot widen a pool.

**(c) The depth figure is 13.0 or 13.1 depending on which parameter set is
used.** `calibrate.py` re-runs the fit and gets mu = 0.383549, giving 13.036 %.
The runtime model uses the stored rounded constant mu = 0.384, giving 13.061 %.
The paper quotes the fit. The difference is immaterial but the two numbers do
differ, and anyone re-running the code will see 13.1 and wonder.

## Evidence

| case | width model | width meas | width err | xU | depth model | depth meas | depth err | xU |
|---|---|---|---|---|---|---|---|---|
| **0 baseline** | 115.1 | 136.3 | **-15.54 %** | **3.4** | 142.1 | 139.7 | **+1.72 %** | **0.2** |
| 1.1 small spot | 104.1 | 106.2 | -1.97 % | 0.4 | 163.0 | 227.2 | -28.25 % | 2.8 |
| 1.2 large spot | 125.1 | 141.7 | -11.73 % | 2.8 | 130.2 | 102.4 | +27.10 % | 2.7 |
| 2.1 fast | 106.5 | 112.9 | -5.66 % | 1.3 | 122.7 | 109.7 | +11.83 % | 1.2 |
| 2.2 slow | 123.5 | 156.1 | -20.86 % | 4.2 | 159.8 | 176.5 | -9.46 % | 0.9 |
| 3.1 high power | 118.9 | 134.3 | -11.43 % | 2.6 | 157.6 | 166.1 | -5.12 % | 0.5 |
| 3.2 low power | 110.7 | 129.4 | -14.43 % | 3.4 | 126.2 | 116.9 | +7.95 % | 0.8 |
| | | | **MAPE 11.7 %** | | | | **MAPE 13.0 %** | |

Also relevant and also unstated in draft 1: three of the four fitted parameters
sit on their bounds - conductivity at its upper bound (35.0 of 11-35), heat
capacity at its lower (450 of 450-1200), keyhole factor at its lower (1.00 of
1-5). Only absorptivity is interior. The 11.7 % is the best this model can do
*while remaining physically arguable*, not its unconstrained best. Draft 1 does
say "the fitted parameters sit at their bounds" in the limitations, but does not
connect that to the quality of the fit.

## Does it change the result?

**No.** Diagnosability depends on the *direction* the readings move under a
fault, not on absolute geometry being right. The operating-point sweep (O1
below) confirms the conclusions hold across all seven benchmark cases. Nothing
in Sections 4.2 to 4.7 moves.

What it changes is how much accuracy a reader should credit the model with at
the one point that matters.

## Change for draft 2

1. Add one sentence after the Gate 1 figures: *"At the baseline condition
   itself, where the Jacobian is evaluated, the errors are -15.5 % on width and
   +1.7 % on depth, against expanded uncertainties (k=2) of 6.2 and 14.1 um."*
2. Add a half-sentence that all seven width errors are negative, so the model is
   systematically narrow rather than scattered. This is more honest and it is
   also a cleaner statement of the model's limitation than the current prose.
3. Decide 13.0 or 13.1 and make the code and paper agree, or state which
   parameter set the figure comes from.

---

# E3. The energy-density correlation check [E]

## What draft 1 says

Section 4.1, `paper.tex` lines 345-348:

> "**Two checks are made against data not used in the fit.** Over 27 melted
> conditions the model reproduces the benchmark correlation structure: depth
> correlates with volumetric energy density (**r = +0.727**) while width does
> not (**r = +0.032**)."

## What is wrong

Three separate things.

**(a) The coefficients do not reproduce.** Running the check now:

| source | n | width r | depth r |
|---|---|---|---|
| `sanity_checks.py` as it stands | 27 | **+0.206** | **+0.778** |
| same grid, calibrated absorptivity 0.384 | 27 | +0.201 | +0.767 |
| **paper** | 27 | **+0.032** | **+0.727** |

The "27 melted conditions" does identify the grid - a 3 x 3 x 3 sweep over power
{150, 250, 350} W, speed {0.4, 0.8, 1.6} m/s and spot {60, 100, 140} um - but
that grid returns +0.206 for width, not +0.032. Five other plausible grids were
tried and none produced the published pair. The width figure is the one that
moved, and it is the load-bearing one: +0.032 reads as "no relationship at all",
+0.206 does not.

**(b) The width result is not robust to the sweep grid.** Depth is stable
everywhere; width is not:

| grid | width r | depth r |
|---|---|---|
| Weaver's own spot range 49/67/82 um | **+0.644** | +0.860 |
| Weaver-like P and v | **-0.376** | +0.527 |
| wide spots 50/100/200 um | -0.223 | +0.704 |
| 4 x 4 x 2 grid | -0.004 | +0.704 |
| sanity_checks 3 x 3 x 3 | +0.206 | +0.778 |

Width's correlation swings from -0.38 to +0.64 depending purely on which region
of parameter space is sampled. **"Width does not correlate with VED" is a
statement about the chosen grid, not a property of the model.** What survives
every grid is the weaker comparative claim: depth tracks VED far more strongly
than width does. That is the defensible version and it is what the code's own
pass criterion actually tests (`abs(r_depth) > abs(r_width)`).

**(c) "Two checks are made against data not used in the fit" is wrong for this
check.** It is true of the Guo check. It is false here on two counts:

- **No data enters it.** All 27 points are model output. The check correlates
  the model's own input with the model's own output; nothing is compared against
  a measurement.
- **The property is not independent of the fit.** Weaver's "depth tracks VED,
  width does not" is derived from the same seven Table 4 cases that the four
  parameters were fitted to.

Something real remains - the fit targeted seven point residuals, never a
correlation, and the sweep extrapolates to a parameter region containing none of
the fitted points - but the honest description is **one external validation
(Guo) and one structural self-consistency check**, not two external checks. The
module docstring in `src/validation.py` already states this correctly
("Validation means reproducing something the fit did not target"); the paper
overstates it.

## Does it change the result?

**No diagnosability result.** The r values appear nowhere downstream. Angles,
ranks, condition numbers and the matrix are untouched.

**It does weaken one of the two validation legs**, and it removes one strand of
support for "width carries information depth does not". Note that the split-
camera recommendation in Section 4.7 does **not** rest on these coefficients -
it rests on the constant-VED sweep, where length varies 2.53x against 1.11x for
width and depth, which is a different measurement and is unaffected.

## Change for draft 2

1. Regenerate the coefficients from the calibrated model and quote what it
   actually returns, with the grid stated so the number is reproducible.
2. Replace the absolute claim with the comparative one, which holds on every
   grid tried: *"depth tracks volumetric energy density far more strongly than
   width does"*, and state the grid sensitivity rather than hiding it.
3. Reword the opening sentence. Proposed: *"One external check and one check of
   internal structure. Over 27 melted conditions spanning power, speed and spot
   size, ..."*.

**Also fix in the code, not the paper:** `src/sanity_checks.py` hard-codes
`ABS = 0.35` and `NQ = 100` at module level instead of using the calibrated
`IN718_ABSORPTIVITY = 0.384` and the standard quadrature. The module that
produces this validation figure is therefore not running the calibrated model.
That alone accounts for +0.206 against +0.201, not for the gap to +0.032, but it
should not be there.

---

# O1. The operating point is never stated [O]

## What draft 1 says

Nothing. `paper.tex` contains no mention of the laser power, scan speed or spot
size the analysis is performed at. Grepping the source for "67", "spot", "D4" or
"Gaussian" returns only the phrase "Gaussian heat source" in the model
description and unrelated numeric matches.

## What is wrong

Every result in the paper is a linearisation about one operating point - AM
Bench case 0, 285 W, 960 mm/s, 67 um D4-sigma spot, bare IN718 plate. A reader
cannot tell this from the paper. They cannot reproduce the Jacobian, cannot
judge whether the condition is representative of their machine, and cannot see
that the analysis is local at all.

This is the kind of omission a reviewer will catch and it is cheap to fix.

## Does it change the result?

**No** - and this has now been tested, which draft 1 could not claim because the
sweep had never been run. Diagnosability recomputed at all seven benchmark cases
plus five off-benchmark points:

| operating point | inst rank | power/gas | enl rank | enl worst |
|---|---|---|---|---|
| **case 0 baseline (used)** | 3 | 0.00 | 5 | **25.83** |
| case 1.1 small spot 49 um | 3 | 0.01 | 5 | 25.71 |
| case 1.2 large spot 82 um | 3 | 0.00 | 5 | 25.65 |
| case 2.1 fast 1.2 m/s | 3 | 0.00 | 5 | 29.34 |
| case 2.2 slow 0.8 m/s | 3 | 0.00 | 5 | 29.03 |
| case 3.1 high power 325 W | 3 | 0.00 | 5 | 29.34 |
| case 3.2 low power 245 W | 3 | 0.00 | 5 | 29.34 |
| off-bench 200 W | 3 | 0.00 | 5 | 29.34 |
| off-bench 400 W | 3 | 0.00 | 5 | 26.41 |
| off-bench 0.5 m/s | 3 | 0.00 | 5 | 29.34 |
| off-bench 1.8 m/s | 3 | 0.00 | 5 | 29.34 |
| off-bench spot 120 um | 3 | 0.01 | 5 | 26.89 |

Instantaneous rank 3 and enlarged rank 5 everywhere; power/gas confounded at
0.00-0.01 degrees everywhere; enlarged worst angle within 25.65-29.34 degrees.
Case 0's 25.83 degrees sits near the **bottom** of that band, so the inherited
operating point understates the result rather than flattering it.

## Change for draft 2

1. State the operating point in Section 3.1, one clause: *"...evaluated at the
   benchmark's baseline condition, 285 W, 960 mm s^-1, 67 um D4-sigma spot."*
2. Add one sentence to Section 4.5 reporting the sweep, since it closes what was
   the study's largest untested assumption: *"Recomputing at all seven benchmark
   conditions and five off-benchmark points leaves the instantaneous rank at 3,
   the enlarged rank at 5 and the enlarged worst pair within 25.65-29.34
   degrees."* This is a strengthening, not a concession.

---

# W1. Spot diameter used as the Gaussian sigma [W]

## Where it happened

Not in the paper. In an analysis script written during the session that produced
the operating-point sweep in O1.

## What is wrong

Weaver et al. quote the spot size as a **D4-sigma diameter** ("laser spot size
(Gaussian diameter) 67 um"). The `Beam` object wants the Gaussian standard
deviation, sigma = D/4 = **16.75 um**. The script passed 67e-6 directly as
sigma, a factor-of-four error corresponding to a 268 um spot.

`src/eagar_tsai.py` provides `sigma_from_spot_diameter` for exactly this, and
the `Beam` docstring warns: *"Use `sigma_from_spot_diameter` rather than
guessing - a factor-of-two error in the spot convention will quietly wreck the
calibration."* The warning was there and was not heeded.

## How it was caught

The first run of the operating-point sweep produced y(0) = 7.687e-03 for the
photodiode and 2933 K for the pyrometer at case 0. The study's own values are
8.383867e-03 and 3030.644 K. **Case 0 failed to reproduce the model it is the
baseline of**, which is the one cross-check that could expose it. After the fix
the sweep reproduces the study Jacobian at case 0 to `max|difference| = 0.00e+00`.

## Does it change the result?

**No.** The error never reached the paper. The corrected sweep is the one
reported in O1, and the first table was discarded.

## Change for draft 2

None to the paper. Two process notes worth keeping:

- Any script that recomputes the model at a new operating point must assert that
  it reproduces the stored case-0 Jacobian before its output is trusted. That
  single check caught a 4x error immediately.
- When a quantity has two conventions in the literature (D4-sigma vs 1/e^2 vs
  FWHM, radius vs diameter), pass it through the provided converter rather than
  inline arithmetic.

---

# Still open, not yet errata

Carried here so they are not lost. These are decisions, untested assumptions and
loose ends rather than established defects.

- **The sqrt(N) noise gain assumes independent segment-to-segment noise, and
  nothing tests that.** Section 3.5 states: *"...which here lies between 0.109
  and 0.136, so fitting N = 84 segments to five regressors buys roughly a
  ninefold noise reduction."* That factor is sqrt(84) = 9.165, and it follows
  from `Cov(r) = sigma_s^2 I` - the assumption that the noise on each segment is
  independent of every other and of the same size. Real in-process noise need
  not be: laser drift, a thermal transient across a build, or a slow detector
  gain change would all correlate neighbouring segments, and correlated noise
  averages down more slowly than sqrt(N). The true gain would then be smaller,
  by an amount set by the correlation length relative to the 84 segments.
  **What it would and would not touch:** nothing in the reported angles, rank or
  condition number, which are invariant to a common scaling - the same argument
  as in E1 of `explainers/07-coefficient-noise.md`. It would touch any absolute
  statement about how quiet the enlarged observation is, and it would matter a
  great deal for a detectability claim, which the paper is careful not to make.
  The honest status is that this is an unexamined assumption in a sentence that
  currently reads as a derived fact. Options for draft 2: soften "buys roughly a
  ninefold noise reduction" to note the i.i.d. condition, or test it by imposing
  a correlated noise model on the residuals and re-deriving the coefficient
  covariance as `(G^T G)^-1 G^T Sigma G (G^T G)^-1` for a non-diagonal Sigma.
  Not yet done either way.
- **Class 3 is empty by construction.** The class-2 test allows an idealised
  direct sensor with 5 % relative noise, which forces any pair containing the
  measured fault to 83-84 degrees. Class 3 cannot be populated unless that
  sensor is worse than about 247 % relative noise. "Nothing is structurally
  irreducible for this suite" is therefore a property of the test, not a finding
  about LPBF. A proposed redefinition - class 3 = *not resolvable by any
  additional melt-pool observable* - would put power/gas into class 3 for
  configurations A-D and make the matrix genuinely three-class. Decision pending.
- **The term "structurally irreducible"** collides with the precise FDI sense of
  "structural" used elsewhere in the same paper, where the matrix carries a
  column reporting genuine structural isolability. Rename regardless of the
  decision above.
- **`matrix.classify()` cannot represent a configuration with a direct sensor.**
  It takes only a sensor-name list, so configuration E is silently scored as C.
  `commercial.py` handles it correctly and the paper's Table 1 is right, but the
  function is a trap for reuse.
- **Trapp et al. (2017)** still lacks volume and page numbers; the DOI is
  confirmed, publisher hosts are unreachable from the build environment.
- **The Reijonen comparison** proposed in Section 5.1 has not been carried out.
  Their fitted speed exponent b is directly comparable to our Jacobian entry of
  -0.483, and their power response to our +1.518. It could contradict the model.
