# The base case: where y(0) comes from, and how good it is

Everything in this work is a linearisation about one operating point. This file
documents where that point came from, traces the model calculation at it end to
end, states its error against measurement, and tests whether the conclusions
depend on having chosen it.

It answers four questions, in order:

    1. Who decides the base case?        -> the benchmark does, not us
    2. What does the model compute there? -> the full chain, with arithmetic
    3. How wrong is it at that point?     -> -15.5 % width, +1.7 % depth
    4. Does the choice matter?            -> no, tested at 12 operating points

---

# Part A - Who decides the base case

## A1. Nobody chooses y(0) directly

`y(0)` is the vector of sensor readings with every fault set to zero. It is
**computed, not chosen**. Two decisions sit upstream of it, and `y(0)` is
whatever falls out of them.

**Decision 1, the operating point.** Hard-coded as the keyword defaults of
`apply_faults` in `src/faults.py`:

    power        = 285.0 W
    speed        = 0.960 m/s
    sigma        = 67e-6 / 4      (Gaussian std dev, from a D4-sigma diameter)
    material     = IN718
    absorptivity = IN718_ABSORPTIVITY = 0.384

**Decision 2, the model.** Absorptivity, effective conductivity, effective heat
capacity and the keyhole factor are *fitted* to measured melt pool geometry,
not picked. That fit is Gate 1.

Run the forward chain at zero fault under those two decisions and out comes

    y1(0) = 8.383867e-03      photodiode, instrument-arbitrary units
    y2(0) = 3.756490e-08 m^2  melt pool area
    y3(0) = 3030.644 K        two-colour pyrometer apparent temperature

## A2. The operating point is the benchmark's, and so is the word "baseline"

The numbers come from Weaver et al. (2024), the 2022 Additive Manufacturing
Benchmark single-track measurements on bare IN718 plate. **Their Table 3**:

| case | label *in that paper* | power (W) | speed (mm/s) | spot D4-sigma (um) | VED_sigma |
|---|---|---|---|---|---|
| **0** | **Baseline** | **285** | **960** | **67** | **1058** |
| 1.1 | change spot | 285 | 960 | 49 | 1978 |
| 1.2 | change spot | 285 | 960 | 82 | 706 |
| 2.1 | change speed | 285 | 1200 | 67 | 847 |
| 2.2 | change speed | 285 | 800 | 67 | 1270 |
| 3.1 | change power | 325 | 960 | 67 | 1207 |
| 3.2 | change power | 245 | 960 | 67 | 910 |

**The word "Baseline" is theirs.** Case 0 is the point the other six are
perturbations *of* - one variable moved at a time, everything else held at case
0. It is the base case by the benchmark's own construction. We inherited it; we
did not nominate it.

Two details that are easy to get wrong and that silently wreck the calibration
if you do:

- The spot size is quoted as **D4-sigma** ("laser spot size (Gaussian diameter)
  67 um"), so sigma = D/4 = **16.75 um**, not 67 um. `sigma_from_spot_diameter`
  exists for exactly this, and the `Beam` docstring warns about it. I still got
  it wrong once while writing this file; the tell was that case 0 stopped
  reproducing the study's own `y(0)`.
- Speed is in **mm/s** in their table: 960 mm/s = 0.960 m/s.

**Their Table 4**, the measurements, each the mean of six cross-sections (three
tracks, two sections each):

| case 0 | value | SD (um) | U (k=2) (um) |
|---|---|---|---|
| width | **136.3 um** | 2.9 | 6.2 |
| depth | **139.7 um** | 1.9 | 14.1 |
| aspect ratio | 2.1 | | |

## A3. Why linearise here rather than somewhere else

Because this is the only kind of point where `y(0)` is anchored to a published
measurement. The Jacobian is a derivative evaluated *at* a point; expanding
about a condition with no measured melt pool geometry would mean the expansion
point itself was unverifiable. Case 0 is the benchmark's own reference
condition, so it is the best-characterised point available.

---

# Part B - The model calculation at case 0

## B1. Inputs

**Beam.** P = 285.0 W, v = 0.960 m/s, sigma = 16.75 um (D4-sigma = 67 um),
mu = 0.384.

**Material**, effective and calibrated, not handbook values:

    rho              8190.0 kg/m^3
    cp               450.0 J/kgK      (at its lower fit bound)
    k                35.0 W/mK        (at its upper fit bound)
    t_solidus        1533.0 K
    t_liquidus       1609.0 K
    t_ambient        293.0 K
    t_vaporisation   3190.0 K

## B2. Step 1 - temperature field

Eagar-Tsai history integral, Gauss-Legendre quadrature at 200 nodes. Peak
conduction temperature at the source: **24 724 K**.

That is far above the 3190 K boiling point, and it is not a bug: a pure
conduction solution has a singularity at a point source and no evaporation to
cap it. It is why every radiometric sensor caps the field at the boiling point
before computing anything.

## B3. Step 2 - melt pool geometry

Found by locating where the field crosses the liquidus:

    width               115.12 um
    length              415.47 um
    depth (conduction)   69.70 um

## B4. Step 3 - keyhole correction

Gladush-Smurov depth term after Honarmandi et al., with fitted factor C = 1.00:

    keyhole depth        72.40 um
    corrected depth  =  69.70 + 1.00 * 72.40  =  142.10 um

**Over half the final depth comes from the keyhole patch, not from conduction.**
That is the regime rather than a defect - all seven benchmark cases have aspect
ratio above 1 - but it does mean the depth prediction leans heavily on a
one-term correction.

## B5. Step 4 - the three sensor readings, which are y(0)

**Camera**, melt pool area as an ellipse:

    pi/4 * width * length = pi/4 * 115.12 um * 415.47 um = 3.756490e-08 m^2

which reproduces `y2(0)` exactly. About 0.0376 mm^2.

**Photodiode**: Planck spectral radiance integrated over 700-1000 nm, summed
over the field of view and multiplied by cell area, on the capped field:

    y1(0) = 8.383867e-03   (instrument-arbitrary; gain is unknown and
                            irrelevant to signature direction)

**Pyrometer**: ratio of two band powers (750 / 950 nm) integrated over the
field of view, inverted through Wien:

    y3(0) = 3030.644 K

Note the ratio is taken over the field of view rather than at the hottest
pixel. At the hottest pixel the cap saturates for every condition and the
sensor returns the boiling point every time - a dead row carrying no
information, which would be an artefact of the cap rather than physics.

Note also what the radiometric sensors do **not** see: the temperature field is
pure conduction, and the keyhole correction is applied only to depth,
afterwards. So the photodiode and pyrometer never see the keyhole at all.

---

# Part C - How wrong the model is at the base case

## C1. Case 0 against measurement

| | model | measured | error | as a multiple of U (k=2) |
|---|---|---|---|---|
| **width** | 115.12 um | 136.3 +/- 6.2 um | **-15.54 %** | **3.4x** |
| **depth** | 142.10 um | 139.7 +/- 14.1 um | **+1.72 %** | **0.2x** |

The base case is **lopsided**. Its depth is the best agreement of all seven
conditions and sits comfortably *inside* the measurement uncertainty. Its width
is 3.4x outside the uncertainty and is the third-worst width error in the set.

**This is not the number the paper quotes.** The paper reports 11.7 % and
13.0 %, which are means over all seven conditions. At the base case specifically
the width error is **-15.5 %**, worse than the aggregate.

## C2. All seven conditions

| case | width model | width meas | width err | xU | depth model | depth meas | depth err | xU |
|---|---|---|---|---|---|---|---|---|
| **0 baseline** | 115.1 | 136.3 | **-15.54 %** | **3.4** | 142.1 | 139.7 | **+1.72 %** | **0.2** |
| 1.1 small spot | 104.1 | 106.2 | -1.97 % | 0.4 | 163.0 | 227.2 | -28.25 % | 2.8 |
| 1.2 large spot | 125.1 | 141.7 | -11.73 % | 2.8 | 130.2 | 102.4 | +27.10 % | 2.7 |
| 2.1 fast | 106.5 | 112.9 | -5.66 % | 1.3 | 122.7 | 109.7 | +11.83 % | 1.2 |
| 2.2 slow | 123.5 | 156.1 | -20.86 % | 4.2 | 159.8 | 176.5 | -9.46 % | 0.9 |
| 3.1 high power | 118.9 | 134.3 | -11.43 % | 2.6 | 157.6 | 166.1 | -5.12 % | 0.5 |
| 3.2 low power | 110.7 | 129.4 | -14.43 % | 3.4 | 126.2 | 116.9 | +7.95 % | 0.8 |
| | | | **MAPE 11.7 %** | | | | **MAPE 13.1 %** | |

## C3. Three things the headline number hides

**Every width error is negative.** The model is systematically narrow at all
seven conditions. A mean *absolute* percentage error of 11.7 % reads like
two-sided scatter; it is in fact a one-sided miss, seven times out of seven.
Physically, a constant-property conduction solution has no mechanism - no
Marangoni convection, no recoil-driven spreading - that widens a melt pool, so
it cannot reproduce the measured widths. This is a structural deficiency of the
model class, not a tuning failure.

**Depth errors are two-sided and largest at the spot-size extremes**, -28 % at
the small spot and +27 % at the large spot. The keyhole patch therefore has
roughly the right average strength but the wrong dependence on spot size.

**Three of the four fitted parameters sit on their bounds:**

| parameter | fitted | bounds | status |
|---|---|---|---|
| absorptivity | 0.384 | (0.30, 0.80) | interior |
| conductivity | 35.0 W/mK | (11.0, 35.0) | **at upper bound** |
| heat capacity | 450 J/kgK | (450, 1200) | **at lower bound** |
| keyhole factor C | 1.00 | (1.0, 5.0) | **at lower bound** |

The fit wants to leave the physically arguable box and is being held inside it.
Without the conductivity bound it drifts to about 90 W/mK, which fits marginally
better and would be indefensible in review. So **11.7 % is the best this model
can do while remaining arguable**, not its unconstrained best.

## C4. A note on 13.0 versus 13.1

`calibrate.py` re-runs the fit and reports width 11.687 %, depth 13.036 %. The
runtime model uses the stored rounded constant mu = 0.384 rather than the fitted
0.383549, giving 11.661 % and 13.061 %. The paper quotes 11.7 % and 13.0 % from
the fit. The difference is in the third digit and affects nothing, but the two
numbers do differ and this is why.

---

# Part D - Does the choice of base case matter?

## D1. Why the question is not cosmetic

`y(0)` plays two distinct roles, and only one is harmless.

**As a divisor.** In

    J[s,k] = [ y_s(+h e_k) - y_s(-h e_k) ] / ( 2h * y_s(0) )

it converts an absolute slope into a fractional one so that kelvin and square
metres become comparable. Rescaling it multiplies a whole row by a constant,
which changes no direction, and angles depend only on direction. Harmless.

**As the expansion point.** This is the real role. Every result is a Taylor
expansion about f = 0, with derivatives evaluated *there*. A different operating
point is a different function with different derivatives, hence a different
Jacobian and possibly different diagnosability. Part D2 of
`05-validation-and-robustness.md` already showed angles swinging by factors of
two with fault *magnitude*; there was no reason to assume they would not swing
with operating point too.

**And until now this had never been tested.** Every sweep in the study -
couplings, noise ratios, profiles, fault magnitude, print size, scan plan, all
120 permutations - holds the operating point fixed at case 0. It was the largest
untested assumption in the work.

## D2. Result: the conclusions do not depend on the base case

Diagnosability recomputed from scratch at all seven benchmark cases plus five
off-benchmark points. Spot sizes are diameters, converted internally by D/4.

| operating point | y1(0) | inst rank | power/gas | inst cond | enl rank | enl worst |
|---|---|---|---|---|---|---|
| **case 0 baseline (used)** | 8.3839e-03 | 3 | **0.00** | 85 | 5 | **25.83** |
| case 1.1 small spot 49 um | 7.9824e-03 | 3 | 0.01 | 38 | 5 | 25.71 |
| case 1.2 large spot 82 um | 8.5619e-03 | 3 | 0.00 | 51 | 5 | 25.65 |
| case 2.1 fast 1.2 m/s | 7.4911e-03 | 3 | 0.00 | 111 | 5 | 29.34 |
| case 2.2 slow 0.8 m/s | 8.9717e-03 | 3 | 0.00 | 269 | 5 | 29.03 |
| case 3.1 high power 325 W | 9.9646e-03 | 3 | 0.00 | 186 | 5 | 29.34 |
| case 3.2 low power 245 W | 6.7740e-03 | 3 | 0.00 | 1243 | 5 | 29.34 |
| off-bench 200 W | 5.1312e-03 | 3 | 0.00 | 155 | 5 | 29.34 |
| off-bench 400 W | 1.3191e-02 | 3 | 0.00 | 120 | 5 | 26.41 |
| off-bench 0.5 m/s | 1.1125e-02 | 3 | 0.00 | 136 | 5 | 29.34 |
| off-bench 1.8 m/s | 6.4010e-03 | 3 | 0.00 | 131 | 5 | 29.34 |
| off-bench spot 120 um | 9.0595e-03 | 3 | 0.01 | 69 | 5 | 26.89 |

The recomputation reproduces the study's own Jacobian at case 0 to
`max|difference| = 0.00e+00`, so the sweep is exercising the same code path.

**Three results hold at every operating point.**

**Power and gas stay exactly confounded**, 0.00-0.01 degrees everywhere. This is
what the algebra demands - both act only on the product (absorptivity x power),
and the Eagar-Tsai temperature rise is linear in that product, which is true at
any power, speed or spot size. It is the strongest confirmation available that
the degeneracy is structural rather than an artefact of case 0.

**Instantaneous rank is 3 and enlarged rank is 5**, at all twelve points.

**The enlarged worst angle stays within 25.65-29.34 degrees**, a 3.7 degree band
across a factor of two in power, 3.6x in speed and 2.4x in spot size.

## D3. Case 0 is the pessimistic choice, not a flattering one

The paper quotes **25.83 degrees**, which sits near the **bottom** of the
25.65-29.34 band. Had we inherited case 3.1 or case 2.1 we would be quoting
29.34. The operating point we were handed slightly understates the result.

## D4. The one thing that does move

The **instantaneous** condition number ranges from 38 to 1243, worst at low
power (case 3.2, 245 W). The weakest observable direction gets considerably
thinner as power falls. This changes no class in the diagnosability matrix,
because the pairs concerned are already at 0.00 degrees and cannot get worse,
but it is worth knowing that the instantaneous problem is better conditioned at
high power than at low.

---

# What this file licenses

**It licenses** reporting case 0 as the benchmark's own baseline rather than our
selection; quoting the model's melt pool geometry at that point as traceable
arithmetic; and claiming that the diagnosability conclusions are not artefacts
of the expansion point, on the evidence of twelve operating points.

**It does not license** reading "11.7 % width error" as the accuracy at the base
case. At the base case it is -15.5 % on width, 3.4x the measurement uncertainty.
Nor does it license treating the fitted parameters as physical constants: three
of four are pinned at bounds chosen to keep them arguable.

**Suggested paper change.** Section 3.1 currently gives only the aggregate. One
sentence stating the base-case error - "-15.5 % on width and +1.7 % on depth at
the baseline condition itself, against expanded uncertainties of 6.2 and
14.1 um" - is more honest than the aggregate alone and costs about a line.
