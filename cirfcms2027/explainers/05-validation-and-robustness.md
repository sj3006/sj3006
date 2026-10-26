# Validation and robustness: the full record

Every test run against this work, what it returned, and what the number means
both mathematically and physically. Numbers regenerated from the current code,
not quoted from earlier notes.

The tests fall into four kinds, and they answer different questions:

    A  VALIDATION   is the physics model right?
    B  NUMERICS     is the arithmetic sound?
    C  ROBUSTNESS   does the answer depend on what I assumed?
    D  CONTROLS     is the mechanism what I claim it is?

Then two sections that are not tests but belong with them:

    E  WHAT BROKE   the seven things that were wrong and how each was caught
    F  WHAT IT RESTS ON   the one condition, the three conservative choices,
                          and the numbers that are still estimates

---

# How to read the numbers

Three quantities recur. Each has a precise mathematical meaning and a physical
one, and confusing them is easy.

### Angle between two faults

**Mathematically.** Each fault produces a column in the Jacobian - a vector
giving how much each sensor moves per unit of that fault. Divide each row by
that sensor's noise (whitening), then take the angle between two columns.

**Physically.** How differently two faults push the readings.

    0 deg    the two faults move the readings along the same line. They are
             not "hard to separate" - they are indistinguishable by any
             measurement whatsoever, because the underlying states are identical
    90 deg   orthogonal; perfectly separable
    ~10 deg  the conventional floor below which practitioners stop believing a
             separation

The angle is **scale-free**. Doubling a fault's size doubles its column but does
not rotate it, so the angle is unchanged. That is why it measures *identity*
rather than *severity*.

### Rank

**Mathematically.** The number of non-zero singular values of the whitened
Jacobian - how many independent directions the fault columns span.

**Physically.** How many separate things the suite can distinguish. Three
sensors give a three-dimensional space, so five faults can span at most three
directions; **two are lost regardless of noise**. That is a counting limit, not
a quality limit.

Tolerance matters: a direction 10^6 times weaker than the strongest is counted
as absent, because it is not a measurement in any practical sense.

### Condition number

**Mathematically.** Largest singular value divided by smallest.

**Physically.** How much measurement noise is amplified when inverting. Rank
says *whether* a direction exists; condition number says *how fragile* the
weakest one is. A rank-5 system with condition 10,000 is nominally solvable and
practically useless.

---

# Part A - Validation: is the physics right?

## A1. Calibration against AM-Bench (Gate 1)

**Question.** Does the thermal model reproduce real melt pools?

**Method.** Four parameters - absorptivity, effective conductivity, heat
capacity, keyhole constant - fitted to the seven IN718 single-track cases of
Weaver et al. (AM-Bench 2022). Seven conditions x two measurements (width,
depth) = 14 numbers constraining 4 unknowns.

**Result.** 11.7% error on width, 13.0% on depth.

**Mathematically.** An over-determined least-squares fit, 14 constraints on 4
parameters, spanning three independent directions (spot size, speed, power) so
the fit is not degenerate.

**Physically.** The model gets melt pool size right to about one part in eight at
the condition we perturb around. Good enough for derivatives, which is all we
take from it.

**What it does not establish.** Agreement here is *calibration*, not validation -
these are the points we fitted to. See A2 and A3.

## A2. Energy density correlation (not fitted)

**Question.** Does the model reproduce a relationship it was not fitted to?

**Method.** 27 melted conditions spanning power, speed and spot size. Correlate
melt pool depth and width against volumetric energy density.

**Result.**

    depth vs VED    r = +0.727
    width vs VED    r = +0.032

**Mathematically.** Pearson correlation across a sweep that varies all three
inputs, so no single input drives the result.

**Physically.** Depth tracks the lumped energy group; width does not. This
reproduces Weaver et al.'s own observation and it lands directly on the paper's
thesis - **width carries information depth does not**, so the lumped group is an
incomplete description.

## A3. Guo et al.'s constant-energy-density experiment

**Question.** At fixed energy density, does the model show the melt pool varying?

**Background.** Guo et al. (*Addit. Manuf.* 28:600-609, 2019) held input energy
density constant and observed, by X-ray, melt pool dimension and volume varying
by **orders of magnitude** with regime changes, because power and speed alter
absorption separately.

**Method.** Hold `P/(v*sigma^2)` at the AM-Bench case-0 value, sweep power from
150 to 500 W with speed compensating.

**Result - partial pass.**

| power, W | speed, m/s | width, um | depth, um | length, um | regime |
|---|---|---|---|---|---|
| 150 | 0.505 | 121.6 | 64.5 | 240.8 | conduction |
| 285 | 0.960 | 115.1 | 69.7 | 415.5 | conduction |
| 420 | 1.415 | 109.9 | 71.6 | 609.3 | conduction |
| 500 | 1.684 | 107.9 | 152.9 | 645.3 | **keyhole** |

Model gives **2.37x** variation in depth; Guo report orders of magnitude.

**Mathematically.** The existence, sign and regime transition reproduce; the
magnitude does not.

**Physically.** Honest reading: a conduction model with an analytic keyhole patch
does not contain the mechanism Guo identify - absorption changing with the
vapour-depression geometry. **This is a stated model limitation, not a success.**
It bounds what the paper may claim about absolute magnitudes.

## A4. Which melt pool dimension carries the information

**Question.** At constant energy density, which dimension moves?

**Method.** The A3 sweep, restricted to conduction-regime rows so the keyhole
jump cannot flatter the answer.

**Result.**

| dimension | span | factor |
|---|---|---|
| width | 109.9 - 121.6 um | 1.11 |
| depth | 64.5 - 71.6 um | 1.11 |
| **length** | **240.8 - 609.3 um** | **2.53** |

Width falls while depth rises.

**Mathematically.** Length's sensitivity to the (P, v) direction at fixed energy
density is ~2.3x that of width or depth, and width and depth have opposite
signs, so they are not redundant with each other.

**Physically.** This independently explains the paper's cheapest recommendation.
A camera reporting **area = (pi/4) x width x length** multiplies the least
informative dimension by the most informative one and reports the product,
discarding most of the information. Reporting the two axes separately recovers
it - worth 13.4 deg on the binding pair, while two new instruments were worth
nothing.

Two independent routes - a thermal sweep against a published experiment, and a
noise-weighted signature calculation - reaching the same conclusion is the
strongest internal consistency check in the study.

---

# Part B - Numerics: is the arithmetic sound?

## B1. Derivative step-size convergence

**Question.** Is the Jacobian a derivative, or an artefact of the step used to
compute it?

**Method.** A Jacobian entry is `(y(+f) - y(-f)) / 2f`. Too large a step measures
a chord across a curve rather than a tangent; too small and floating-point
cancellation dominates. Shrink the step and watch when the answer stops moving.

**Result.**

    step 0.080   (reference)
    step 0.040   max change vs previous  267.33%
    step 0.020   max change vs previous   39.35%
    step 0.010   max change vs previous   20.59%
    step 0.005   max change vs previous    0.25%   <- settles
    step 0.002   max change vs previous    0.05%
    step 0.001   max change vs previous    0.01%

Study uses **0.002**.

**Mathematically.** The second-order Taylor term dominates above ~0.005 and is
negligible below it; cancellation has not yet appeared at 0.001.

**Physically.** At a 2% fault the model's response is already visibly curved, so
a chord over +/-2% is not the local slope.

**This test caught a real error.** An earlier default of 0.02 produced numbers
that were wrong by about 20%, and those numbers had already been reported. No
amount of code review would have found it.

## B2. No-interpolation cross-check

**Question.** The finite-magnitude study uses an interpolated response curve for
speed. Does the shortcut distort the answer?

**Method.** Re-run the entire finite-magnitude study with no interpolation at
all - the full thermal model evaluated at every one of 84 segments x 5 faults,
per magnitude - and compare the resulting angle tables.

**Result.** The two paths agree to **0.10 deg at +5%** and **0.10 deg at +20%**
(largest disagreement across all ten pairs), with identical rank (5) and
condition number (41). On the worst pair specifically: 30.77 deg exact against
30.75 deg interpolated at +5%, and 30.78 against 30.82 at +20%. The exact run
costs 51-53 s against well under a second interpolated.

**Mathematically.** The interpolation error in the whitened residual peaks at
5.59e-3, which is **15.6% of a typical whitened residual** - large enough to be
alarming on its own. It is almost entirely the pyrometer in a flat region of its
response, where a small error in the fitted value is a large fraction of a small
residual. It does not propagate to the end quantity, because the angle depends
on the *direction* of a 15-component vector and the error sits in components
that barely contribute to its length.

**Physically.** The shortcut is safe. Worth noting that the intermediate error
metric was alarming and the end-quantity check was reassuring - **the end
quantity is the one that matters**, and checking the intermediate alone would
have led to the wrong conclusion.

## B3. Rank tolerance

**Question.** What counts as a non-zero singular value?

**Result.** Tolerance set at `1e-6` relative. At the floating-point default of
`1e-12`, a system with condition number 6.8 x 10^9 was being reported as full
rank.

**Physically.** A direction a billion times weaker than the strongest is not a
measurement. Calling it one inflates every rank in the study.

---

# Part C - Robustness: does the answer depend on what I assumed?

## C1. Profile contrast sweep

**Question.** The five fault patterns are asserted, not measured. How strong do
they need to be?

**Method.** Scale all five pattern strengths by a common factor and recompute.
Contrast 1.0 is the asserted strength; the patterns span a factor of `exp(2c)`
across a build.

**Result (enlarged observation, derivative limit).**

| contrast | rank | condition | worst pair | power/gas |
|---|---|---|---|---|
| 0.00 | 3 | 85 | 0.00 | 0.00 |
| 0.05 | 5 | 119 | 1.68 | 1.68 |
| 0.10 | 5 | 85 | 3.35 | 3.35 |
| 0.25 | 5 | 54 | 8.30 | 8.30 |
| **0.40** | 5 | 39 | **11.22** | 13.08 |
| 0.50 | 5 | 35 | 13.28 | 16.14 |
| 0.75 | 5 | 31 | 19.32 | 23.20 |
| 1.00 | 5 | 30 | 25.83 | 29.34 |
| 1.50 | 5 | 30 | 37.25 | 38.90 |
| 2.00 | 5 | 30 | 43.59 | 45.48 |

**Mathematically.** Rank jumps from 3 to 5 as soon as contrast is non-zero - the
rank gain is structural and instantaneous. The *angle* then grows smoothly and
monotonically with contrast. The floor is crossed between 0.25 and 0.40.

**Physically.** Two distinct things are happening. Any amount of differing
variation makes the faults formally recoverable; how much separation you get is
proportional to how differently they vary.

**This is the number to quote.** The conclusion survives the patterns being
**2.5x weaker** than asserted. That is a far stronger claim than "25.83 degrees",
because it does not ask a reader to accept the pattern strengths.

## C2. Pattern assignment - all 120 permutations

**Question.** I assigned each fault a build variable to follow. What if I
assigned them wrongly?

**Method.** Reshuffle which fault follows which variable. All 5! = 120 ways.

**Result.**

    rank 5 in 120/120 cases
    worst pair:  min 17.13   median 23.84   max 30.58   (as assigned: 25.83)

**Mathematically.** Permuting the columns of the driver matrix permutes the
columns of the projection matrix B. The *set* of signature directions is
preserved up to relabelling, so separability is preserved.

**Physically and importantly.** It does **not matter** which fault follows which
variable - only that they differ. The paper does not need to defend five
individual claims about fault behaviour; it needs to defend distinctness.

## C3. Pattern collapse - two faults sharing a variable

**Question.** What if two faults genuinely vary the same way?

**Method.** Force one fault's pattern equal to another's, for all ten pairs.

**Result.**

| forced equal | rank | worst pair | |
|---|---|---|---|
| **layer = gas** | 5 | **3.84** | **breaks** |
| **speed = gas** | 5 | **8.12** | **breaks** |
| speed = layer | 5 | 13.02 | |
| power = speed | 5 | 15.47 | |
| power = gas | 5 | 15.98 | |
| power = layer | 5 | 18.34 | |
| anything = geometry | 5 | 25.83 | unchanged |

**Mathematically.** Rank stays 5 throughout - the columns remain linearly
independent - but conditioning degrades and the smallest angle collapses. This is
the distinction between formal and practical identifiability.

**Physically.** This is the real dependency of the whole paper, and it reduces to
one question:

> **Do the recoater fault and gas degradation vary differently across a build?**

One is tied to layer index, the other to position across the plate. Physically
they must. But that is now the single assumption carrying weight, and it should
be named rather than buried among five.

**Consequence for priorities.** Anything sharing a pattern with geometry leaves
the answer at 25.83, unchanged. **The geometry pattern is the least load-bearing
of the five** - which is why the NIST overhang dataset, which validates exactly
that pattern, was dropped as non-blocking.

## C4. Fault coupling constants

**Question.** Four constants describe how faults reach the model's inputs. Two
are derived, one is an estimate, one is a unit. Does the answer depend on them?

**Method.** Sweep each across its plausible range - for the derived ones, across
their own derivation sensitivity.

**Result.**

| constant | range swept | inst. power/gas | enlarged rank | enlarged worst | condition |
|---|---|---|---|---|---|
| layer_to_absorptivity | -0.30 to -0.12 | 0.00 throughout | 5 | **25.83 throughout** | 30-31 |
| layer_to_powder_enthalpy | 0.13 to 0.24 | 0.00 throughout | 5 | **25.83 throughout** | 30-31 |
| layer_to_conductivity | 0 to 1.50 | 0.00 throughout | 5 | **25.83 throughout** | 30-47 |
| geometry_preheat_kelvin | 50 to 400 K | 0.00 throughout | 5 | **25.83 throughout** | 10-60 |

**Mathematically.** The worst enlarged pair is power/speed, and neither of those
faults has a coupling constant - power enters through the power multiplier,
speed through the speed multiplier. So that particular number is invariant *by
construction*, and the invariance must not be oversold. What does move is
conditioning, from 10 to 60.

**Physically.** The conclusions do not rest on the one constant that is still an
estimate. The honest sentence is: *the constant is a guess, and the conclusions
are invariant to the guess across its whole plausible range* - which is stronger
than any derivation, because it does not require the number to be right.

**A result that is algebra, not calibration.** Power and gas both act only on the
product (absorptivity x power), and the temperature rise is linear in that
product, so the gas Jacobian column is always a scalar multiple of the power
column. Measured ratio: **-0.99999, -1.00000, -0.99993** across the three
sensors, a spread of 7 x 10^-5 attributable to finite-difference error on an
exact identity. **No value of any constant can break this.**

## C5. Sensor noise ratios

**Question.** No in-process noise characterisation was found for the photodiode
or pyrometer. Does the answer depend on the ratios assumed?

**Result.**

| ratios | inst. rank | inst. power/gas | enlarged rank | enlarged worst | condition |
|---|---|---|---|---|---|
| [1, 1, 0.03] study default | 3 | 0.00 | 5 | 25.83 | 30 |
| [1, 1, 1] equal | 3 | 0.00 | 5 | 24.98 | 55 |
| [1, 1, 0.003] fine pyrometer | 3 | 0.00 | 5 | 24.97 | 61 |
| [1, 1, 0.3] coarse pyrometer | 3 | 0.00 | 5 | 24.99 | 54 |

**Mathematically.** Angles, rank and condition number are **invariant to scaling
all sensor noise by a common factor** - whitening divides each row by its own
sigma, so a common factor rescales the whole matrix without changing column
directions or singular value ratios. Only *relative* noise matters, and that is
what is swept.

**Physically.** The absolute noise level is not merely unknown but **irrelevant
to what is claimed**. The cost: absolute detection thresholds cannot be claimed.
Every result here concerns *isolation* - telling two faults apart - not
*detection*.

**A finding that came from sweeping rather than assuming.** The pyrometer has an
**optimum** near ratio 0.03. Making it quieter does not monotonically improve the
suite: whitening by 1/sigma lets an over-specified sensor dominate the matrix,
and one scalar cannot separate five faults. A fixed "best available" figure would
have hidden this.

## C6. Print size

**Question.** The synthetic build has 84 passes. Invented. Does it matter?

**Result.**

| layers x passes | total | rank | worst pair | power/gas |
|---|---|---|---|---|
| 2 x 6 | 12 | 5 | 11.74 | 30.17 |
| 3 x 10 | 30 | 5 | 23.91 | 30.43 |
| 6 x 14 | **84** | 5 | **25.83** | 29.34 |
| 10 x 20 | 200 | 5 | 26.50 | 28.83 |
| 20 x 40 | 800 | 5 | 24.50 | 28.35 |
| 40 x 60 | 2400 | 5 | 23.03 | 28.17 |

**Mathematically.** Flat above ~30 passes. The standard error on each regression
coefficient falls as `1/sqrt(n)` - from 0.289 at n=12 to 0.020 at n=2400 - but
that factor scales **all fifteen rows equally**, so it cancels out of the angles.
More data buys precision, not separability.

**Physically.** Same lesson as the rank argument, in a different costume: more of
the same information is not new information. And 84 is conservative - a real part
has hundreds of passes *per layer*.

## C7. Scan plan variants

**Question.** Does the result depend on how the part is scanned?

**Result (structural threshold 0.10).**

| plan | corr(time, support) | blocked pairs | worst angle | power/gas |
|---|---|---|---|---|
| raster, support grows | -0.642 | **0** | 25.83 | 29.34 |
| raster, flat support | -0.000 | 2 | 26.21 | 28.01 |
| random order | +0.078 | 2 | 28.83 | 28.83 |
| interleaved order | -0.022 | 1 | 14.80 | 14.80 |

**Mathematically.** The *structural* classification changes decisively - zero
blocked pairs versus two - while the *angles* barely move and in two cases
improve.

**Physically, and this corrects an earlier overstatement.** An earlier draft
claimed "diagnosability is partly designed" citing the angles. The angles do not
support it. Scan order changes whether a residual exists that is **decoupled**
from the other fault - which governs robustness to wrong magnitudes - not the
sharpness of the separation. The claim is narrower than first stated and must be
made structurally.

## C8. Structural threshold window

**Question.** The structural analysis needs a threshold deciding when a coupling
counts as present. Does the answer depend on it?

**Result.**

| threshold | 0.00 | 0.01 | 0.05 | 0.10 | 0.20 | 0.40 |
|---|---|---|---|---|---|---|
| non-isolable pairs | 2 | **0** | **0** | **0** | 2 | 2 |

**Mathematically.** Full isolability appears in a **window**, not above a
threshold. At 0 every channel admits every fault, so the enlarged model is five
copies of the instantaneous one and reproduces its blocked pairs exactly - a
useful consistency check. Too high and channels admit so little that equations
are lost.

**Physically.** The paper must report the window rather than a single threshold.

---

# Part D - Controls: is the mechanism what I claim?

## D1. The shared-profile control

**Question.** Is the gain from the patterns *differing*, or just from having 15
numbers instead of 3?

**Method.** Give all five faults one identical pattern. The enlarged matrix still
has 15 rows.

**Result.**

    all five share one profile:  rank 3   condition 85   worst 0.00   power/gas 0.00
    instantaneous:               rank 3   condition 85   worst 0.00   power/gas 0.00
    identical: True

**Mathematically.** With a shared profile, B's columns become proportional, so
the enlarged Jacobian's columns inherit the instantaneous column directions
exactly. Fifteen rows, three independent directions.

**Physically.** This is the single most important control in the study. **The
gain is not dimensionality.** It is the patterns differing. Had this returned
anything other than the instantaneous result, the whole mechanism would have been
an artefact.

## D2. Does the answer hold for faults of realistic size?

**Question.** Every angle quoted so far comes from a Jacobian, which is a
derivative - the limit as the fault goes to zero. Real faults are not
infinitesimal. A 20% power drop is a 20% power drop. Does the conclusion survive
at that size, where the thermal model is distinctly nonlinear?

**Method.** Replace every derivative with a **secant**: inject a fault of finite
size `f`, run the full nonlinear chain (couplings, thermal model, radiometry,
sensor response) at all 84 segments, and take the actual difference. Do it at
nine magnitudes, both signs, and recompute all ten pairwise angles, the rank and
the condition number from scratch each time.

**Result, angles** (degrees; "limit" is the derivative, "+0%" is a +0.2% fault):

| pair | limit | +0% | +1% | +2% | +5% | +10% | +20% | -2% | -5% | -20% |
|---|---|---|---|---|---|---|---|---|---|---|
| power / speed | 25.83 | 25.20 | 32.21 | 37.75 | 46.15 | 57.40 | 51.32 | **22.19** | 35.99 | 45.96 |
| power / gas | 29.34 | 29.19 | 30.54 | 29.57 | 30.75 | 36.30 | 33.27 | 28.93 | 37.26 | 37.49 |
| power / layer | 36.40 | 36.50 | 37.21 | 35.94 | 36.28 | 40.20 | 41.76 | 36.81 | 38.53 | 36.90 |
| speed / gas | 36.47 | 36.31 | 41.71 | 42.93 | 40.27 | 41.12 | 39.16 | 35.72 | 43.78 | 44.11 |
| layer / gas | 44.58 | 44.39 | 45.03 | 45.07 | 43.13 | 42.51 | 42.08 | 43.23 | 45.09 | 48.51 |
| speed / layer | 47.08 | 46.86 | 52.25 | 53.32 | 52.69 | 52.00 | 45.40 | 44.99 | 51.11 | 58.93 |
| power / geometry | 64.30 | 65.02 | 67.25 | 59.80 | 44.94 | 33.16 | 30.82 | 66.05 | 60.38 | 45.94 |
| gas / geometry | 65.80 | 64.82 | 65.54 | 65.75 | 58.42 | 51.77 | 44.36 | 58.68 | 45.06 | 39.66 |
| layer / geometry | 66.45 | 65.98 | 64.11 | 61.80 | 57.06 | 54.16 | 52.98 | 64.61 | 54.76 | 51.82 |
| speed / geometry | 71.13 | 70.58 | 75.32 | 77.88 | 79.45 | 75.97 | 65.69 | 70.23 | 59.84 | 42.73 |

**Result, rank and conditioning:**

| magnitude | inst rank | inst cond | enlarged rank | enlarged cond | enlarged worst |
|---|---|---|---|---|---|
| +0.2% | 3 | 83 | 5 | 30 | 25.20 |
| +1% | 3 | 77 | 5 | 31 | 30.54 |
| +2% | 3 | 96 | 5 | 32 | 29.57 |
| +5% | 3 | 104 | 5 | 41 | 30.75 |
| +10% | 3 | 83 | 5 | 43 | 33.16 |
| +20% | 3 | 64 | 5 | 41 | 30.82 |
| -2% | 3 | 95 | 5 | 31 | **22.19** |
| -5% | 3 | 98 | 5 | 34 | 35.99 |
| -20% | 3 | 39 | 5 | 42 | 36.90 |

**Mathematically.** Four things, and the third is the one to be careful about.

First, the **structural result is magnitude-independent**. Instantaneous rank is
3 and enlarged rank is 5 at every magnitude and both signs. The enlarged
condition number stays in a narrow band, 30-43. So the central claim - that the
melt pool offers three independent channels and the enlarged observation offers
five - is a property of the system, not of the linearisation.

Second, the **individual angles move a great deal and non-monotonically**.
power/speed goes 25.83 -> 46.15 -> 57.40 -> 51.32 as the fault grows to 5%, 10%,
20%: it rises then turns over. power/geometry goes the other way, 64.30 -> 44.94
-> 30.82. These are not small corrections; they are factors of two. Quoting a
single Jacobian angle as "the" separation between two causes would be wrong.

Third, and this is the honest caveat: **the derivative limit is not strictly
conservative.** The smallest entry in the whole table is 22.19 degrees -
power/speed at a -2% fault - which is 3.6 degrees *below* the infinitesimal
25.83. So "the limit is the worst case" is false, and the paper must not say it.
What is true is weaker and still sufficient: across nine magnitudes, both signs,
and all ten pairs - ninety values - the minimum is 22.19 degrees, which is
**2.2x the 10-degree floor**. No pair collapses anywhere.

Fourth, the **identity of the binding pair changes with magnitude**. It is
power/speed at the limit and at -2%, power/gas between +1% and +5%, power/geometry
at +10% and +20%, and power/layer at -20%. Every one of them involves power.

**Physically.** Two readings, in opposite directions.

The nonlinearity *helps* for the pair that matters most at small size. power and
speed are the classic confound - both move the melt pool along the energy-density
direction - and at small amplitude they are nearly parallel. As the fault grows,
they separate strongly (25.83 -> 57.40 degrees), because power enters the
thermal problem through the source term and speed enters through the interaction
time, and those two routes stop looking alike once the melt pool geometry itself
changes. A large fault is easier to attribute than a small one.

The nonlinearity *hurts* for geometry. Geometry acts as a preheat offset, and the
three geometry pairs all degrade as the other faults grow - power/geometry loses
33 degrees between the limit and +20%. Physically a large power or gas excursion
drives the melt pool into a regime where its own response to preheat changes, so
the preheat signature starts to resemble the excursion that produced it. The
practical consequence is that a geometry-driven overheat is hardest to identify
precisely when something else is also badly wrong - which is the realistic case.

That asymmetry is a genuine result and belongs in the paper as one sentence: the
energy-density confound eases with fault size, the preheat confound worsens.

## D3. Does a second sensor buy anything at all?

**Question.** Once the enlarged observation is used, a **single** sensor already
reaches rank 5 (table below). So on rank alone, extra sensors buy nothing. Is
there any honest sense in which a richer suite is better?

**Method.** Treat diagnosis as an inverse problem and let the assumption be
wrong. The data is generated by the *true* enlarged Jacobian `T`; diagnosis
inverts the *assumed* one `A`:

    f_hat = pinv(A_w) T_w f

so the worst-case relative error over all fault directions is the operator norm

    || pinv(A_w) T_w - I ||_2

Zero means the wrong assumption does not matter at all. One means the recovered
fault vector can be as wrong as the fault itself. The misspecification is in the
modulation profiles: each fault's contrast is perturbed independently and
uniformly by up to `delta`, 40 draws, seed fixed.

**Result** (mean / worst over 40 draws):

| subset | rows | delta = 10% | delta = 30% | delta = 50% |
|---|---|---|---|---|
| photodiode only | 1 | 0.717 / 1.029 | 2.148 / 3.072 | 3.577 / 5.148 |
| camera only | 1 | 0.422 / 0.596 | 1.263 / 1.800 | 2.103 / 3.021 |
| pyrometer only | 1 | 0.656 / 0.945 | 1.965 / 2.861 | 3.272 / 4.808 |
| photodiode + pyrometer | 2 | 0.145 / 0.230 | 0.433 / 0.685 | 0.716 / 1.128 |
| all three (baseline) | 3 | 0.122 / 0.185 | 0.365 / 0.555 | 0.605 / 0.918 |
| + split the camera (free) | 4 | 0.098 / 0.137 | **0.293 / 0.408** | 0.487 / 0.672 |
| everything (7) | 7 | 0.096 / 0.139 | **0.288 / 0.413** | 0.479 / 0.680 |

And the rank/angle picture that makes the question necessary:

| subset | rows | inst rank | inst cond | enlarged rank | enlarged worst | enlarged cond |
|---|---|---|---|---|---|---|
| photodiode only | 1 | 1 | 1 | 5 | 24.89 | 88 |
| camera only | 1 | 1 | 1 | 5 | 24.89 | 50 |
| pyrometer only | 1 | 1 | 1 | 5 | 24.89 | 78 |
| photodiode + camera | 2 | 2 | 72 | 5 | 24.97 | 55 |
| photodiode + pyrometer | 2 | 2 | 21 | 5 | 26.12 | 35 |
| camera + pyrometer | 2 | 2 | 20 | 5 | 25.57 | 24 |
| all three (baseline) | 3 | 3 | 85 | 5 | 25.83 | 30 |
| + split the camera (free) | 4 | 4 | 698,596 | 5 | 29.34 | 32 |
| + SWIR photodiode | 4 | 3 | 98 | 5 | 25.75 | 33 |
| + wide-band pyrometer | 4 | 4 | 400,320 | 5 | 25.70 | 20 |
| split camera + SWIR | 5 | 4 | 818,009 | 5 | 29.34 | 34 |
| everything | 7 | 4 | 229,212 | 5 | 29.34 | 22 |

**Mathematically.** Three things are visible and each matters.

First, **rank saturates immediately**. One sensor regressed onto five known
regressors already produces five numbers for five unknowns, so the enlarged rank
is 5 for every subset including the singletons. Rank is therefore the wrong
yardstick for comparing suites past the first sensor, and any paper claiming a
second sensor "unlocks" a fault on rank grounds, in this regime, would be wrong.

Second, the misspecification error **falls roughly as the square root of the
number of independent rows**, which is the signature of error averaging rather
than of new information: 1 sensor 2.15, 2 sensors 0.433, 3 sensors 0.365, 4 rows
0.293, 7 rows 0.288 (all mean, delta = 30%). The error is also very nearly
linear in delta - baseline 0.122, 0.365, 0.605 against delta of 0.1, 0.3, 0.5,
i.e. about 1.2 x delta - which is what a first-order perturbation of a
well-conditioned inverse should do, and a check that the metric is behaving.

Third, the instantaneous condition numbers of the four- and five-sensor sets
blow up to 4 x 10^5 - 8 x 10^5 while rank reads 4. Those rows are very nearly
duplicates of each other. **Rank without condition number is misleading**, which
is exactly why both are reported everywhere in this document.

**Physically.** A single in-situ sensor can, on paper, separate all five causes
once spatial context is used - but only if you trust the assumed spatial
patterns to within a few per cent, which nobody can. At a realistic 30% error in
those patterns the single-sensor answer is worthless (error 2.15, i.e. the
recovered cause is more wrong than the cause is large), the standard three-sensor
suite is usable but loose (0.365), and the saturation point is reached at four
rows.

The practical finding is the fourth row: **splitting one existing camera into
two regions of interest** - no new hardware, a change in how a frame is reduced -
delivers 0.293, which is within noise of what all seven channels deliver
(0.288). Buying a SWIR photodiode or a wide-band pyrometer instead gives 25.75
and 25.70 degrees worst-angle against the baseline's 25.83, i.e. nothing.

This is the result to put in front of a machine builder, and it is the opposite
of the intuitive answer.

---

# Part E - What broke

Seven things in this study were wrong at some point and were caught. They are
recorded because each one changed a number that had already been written down,
and because the pattern of how they were caught is the argument that the rest is
sound.

**E1. Negative thermal conductivity.** With the layer-to-conductivity coupling
set to 1.0 (a value the sweep tries), a -100% layer fault drove conductivity to
zero, raising `ZeroDivisionError`, and just past it to negative, where the model
produced NaNs that were being silently absorbed and reported as finite numbers.
Fixed two ways: couplings became exponential, `k = k0 * exp(c * f)`, which cannot
cross zero for any finite fault; and explicit domain checks now **raise** if
absorptivity leaves (0, 1], if conductivity goes non-positive, or if preheat
reaches the solidus. A model that fails loudly is worth more than one that
returns a number.

**E2. A +20% fault acting as a +116% fault.** The `MAX_REACH = 0.70` guard fired:
a nominally +20% fault was reaching 116% of nominal somewhere in the build. Root
cause was not the fault model but the **driver normalisation** - drivers were
being scaled to unit variance, so a driver whose range happened to be narrow got
multiplied up by a large factor. Fixed by range-normalising every driver to
[-1, 1] instead, which bounds the reach by construction.

**E3. Sign reversal.** Same root cause as E2, different symptom and found first:
32 of 420 modulation entries came out negative, so a +20% fault was acting as a
-31% fault on those segments. My first instinct was that the linear profile form
was at fault; the fix that worked was the normalisation. **Diagnosing the real
cause mattered** - changing the profile form would have hidden the problem
without removing it.

**E4. The wrong noise model in Route A.** This is the one that would have been
hardest to catch after publication. Each regression coefficient was being
whitened by the raw sensor noise `sigma_s`, when the correct scale for the
*j*-th coefficient from sensor *s* is

    sigma_s * sqrt( [ (G^T G)^-1 ]_jj )

The error threw away an averaging gain of roughly 9x (84 segments fitted to 5
regressors) and mis-weighted the regressors relative to each other by up to 25%,
which distorts every angle. Fixed with `coefficient_sigmas`, and `pair_angles`
and `rank_cond` now **refuse** a noise vector whose length does not match the
matrix rather than broadcasting it.

**E5. An unconverged derivative step.** The first step size tried gave a 267%
error in the derivative. Caught by running the convergence study in B1 rather
than assuming a step was small enough.

**E6. A rationalisation presented as a derivation.** I picked the
layer-to-absorptivity coupling as -0.30 and then constructed arithmetic that
produced 0.25, and described the gap as rounding. Amit caught it. The record was
corrected explicitly, and the coupling was then **actually derived** from Trapp
et al. (2017) as -0.230. This is in the robustness document because the number is
load-bearing and the reader is entitled to know which numbers were derived and
which were asserted.

**E7. A cherry-picked literature claim.** I wrote that the RAISE-LPBF results
confirmed our mechanism, citing two of their four models. The PDF showed the
other two - a 16-frame transformer underperforming an 8-frame 3D ResNet - which
points the other way. Downgraded in both files to "suggestive only, not
evidence". No claim in the paper now rests on it.

---

# Part F - What the whole thing rests on

After all of the above, the result reduces to **two physical conditions** and
three conservative modelling choices.

## The two conditions

Both come from C3, and both are about the gas fault.

**Condition 1: the recoater-driven effect and the gas-flow effect must vary
differently across the build.** If those two faults are given the same spatial
pattern the worst angle collapses to **3.84 degrees**, well below the 10-degree
floor, and the method fails outright.

Physically this one is mild. Layer-to-layer powder-bed variation follows the
recoater, which advances once per layer in a fixed direction. Gas flow follows
the nozzle-to-outlet axis, fixed in the chamber frame and in-plane. These are
different axes of the build volume by construction - for them to be aligned, the
recoater would have to be the gas source.

**Condition 2: commanded speed must not track the gas axis.** Forcing those two
equal gives **8.12 degrees**, also below the floor. This condition is weaker than
the first, because speed is set by the scan strategy and a strategy *could*
align with the gas axis - a part whose contours cluster downstream of the nozzle
would do it. It is a condition on the build, not just on the machine, and it is
the one a reviewer is most entitled to press on.

A third case sits close to the line without crossing it: speed sharing the layer
pattern gives 13.02 degrees, only 1.3x the floor. Everything else is comfortable,
and anything sharing a pattern with geometry leaves the answer at 25.83 entirely
unchanged. Pattern *assignment* is irrelevant (C2: rank 5 in all 120
permutations) - it is pattern *distinctness* that carries the result.

These two sentences are what the paper should state plainly, in their own
paragraph, rather than leave the reader to assemble from the sweep tables.

## The three choices made against our own interest

Each of these makes the reported result *harder* to obtain, so none of them can
be inflating it. They belong together in one limitations paragraph.

1. **The gas convection channel was dropped.** Gas flow could plausibly change
   the surface heat-transfer coefficient as well as the plume. Including that
   would give the gas fault a second, distinct signature and make it easier to
   separate. We model only the plume.
2. **Plume attenuation was made independent of power and speed.** In reality a
   hotter, faster melt pool ejects more spatter and more vapour, which would
   couple the gas fault to the power and speed faults in a way our enlarged
   observation could exploit. We treat attenuation as a pure multiplier on the
   emitted signal.
3. **Upstream power monitoring was modelled downstream.** A true upstream monitor
   measures commanded or delivered laser power before the melt pool and would be
   a near-direct observation of the power fault. We model it as yet another
   melt-pool-derived signal, which is the pessimistic reading.

## The numbers that remain estimates

Stated plainly, with what was done about each.

| quantity | status | protection |
|---|---|---|
| layer-to-absorptivity, -0.230 | derived from Trapp et al. (2017) | - |
| layer-to-powder-enthalpy, +0.186 | derived, phi / (1 - phi) with phi = 0.157 | - |
| layer-to-conductivity, +0.50 | **estimate** | swept 0.1-1.0 in C4; enlarged worst angle 25.83 throughout |
| geometry preheat, 100 K | a **unit**, not a constant; results are per 100 K | magnitude sweep, D2 |
| profile contrasts (0.3, 0.8, 1.0, 0.9, 1.0) | **asserted**, based on mechanism not measurement | swept in C1; misspecification tested in D3 |
| sensor noise ratios | **asserted** from datasheet-class figures | four sets swept in C5, 24.97-25.83 |
| 10-degree isolability floor | **a convention we chose** | threshold window reported in C8; contrast-to-clear reported in C1 |

The honest summary: one coupling constant and the five profile contrasts are not
measured. Both have been swept, and the conclusion does not move. The floor is a
convention and is reported as such.

## What a reviewer can legitimately still attack

- The profile contrasts are asserted. D3 is the defence, and it is a partial one:
  it shows how much a wrong contrast costs, not that ours are right.
- Validation is partial. Gate 1 passes at 11.7% / 13.0%; the Guo constant-energy
  -density check passes only in direction and order (2.37x, see A3). No
  experimental dataset has been fitted.
- The thermal model is analytical. It has no powder-scale physics, no fluid flow,
  no recoil pressure. The keyhole correction is a depth correction, not a
  mechanism.
- Everything is a diagnosability statement, not a detection statement. It says
  what a suite can distinguish **in principle**, at a given noise level, with a
  given forward model. It does not say any algorithm achieves it.

Each of those four is stated in the paper. None of them is hidden.
