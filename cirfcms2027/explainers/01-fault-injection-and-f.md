# Fault injection, the magnitude f, and the Jacobian

Reference document. Everything here is traceable to `src/faults.py`,
`src/diagnosability.py` and the literature cited inline.

---

## 1. What "injecting a fault" actually means

The thermal model accepts exactly six inputs:

    power, speed, spot size, absorptivity, conductivity, preheat temperature

It knows nothing else. There is no layer in it, no gas, no part geometry. So
injecting a fault can only ever mean: **nudge one or more of those six numbers.**

The table below is the entire fault model. There is nothing else to it.

| fault | what it nudges |
|---|---|
| power | `power x (1 + f)` |
| speed | `speed x (1 + f)` |
| gas | `absorptivity x exp(-f)` |
| geometry | `preheat + 100f` kelvin |
| layer | three at once: `absorptivity x exp(-0.230f)`, `conductivity x exp(+0.50f)`, `power x exp(+0.186f)` |

Layer touches three inputs because a thinner powder layer does three physically
distinct things: it traps less light, it insulates less, and it needs less energy
to melt.

---

## 2. How each nudge was decided

Two separate questions for every entry: what **form** (the functional shape), and
what **constant**. They have different answers and must not be conflated.

| | form | constant |
|---|---|---|
| power, speed | direct multiplier. Not a choice. | none |
| gas | **Beer-Lambert law.** Textbook physics. | **none exists** - f *is* the optical depth |
| geometry | not a choice: Eagar-Tsai takes preheat as an input, you add kelvin to it | 100 K is a **unit**, anchored to documented thin-wall and overhang rises of tens to a couple hundred K |
| layer to absorptivity | saturation shape from radiative transfer | **-0.230, derived** (section 2.1) |
| layer to power | **energy balance.** Mass x enthalpy. First principles. | **+0.186, derived** (section 2.2) |
| layer to conductivity | mine | **mine.** Not backed by anything (section 2.3) |

Four of the five are literature or first-principles. One is entirely an estimate.

### 2.1 layer_to_absorptivity = -0.230, derived

A powder bed absorbs more than bare solid because light scatters between
particles and gets repeated chances to be absorbed. Two published anchors:

- **Trapp, Rubenchik, Guss & Matthews**, *Applied Materials Today* (2017),
  "In situ absorptivity measurements of metallic powders during laser powder-bed
  fusion additive manufacturing". Measured at 1070 nm: powder absorptivity about
  **twice** that of the bare polished disc for ~100 um layers.
- Radiative-transfer treatments of metal powder beds put the radiation
  penetration depth at **a few particle diameters**.

Model saturation with thickness:

    A(t) = A_s + (A_p - A_s) * (1 - exp(-t/delta)),    A_p = 2 * A_s

with `delta = 2 * d50 = 60 um` (d50 = 30 um, a typical IN718 LPBF cut) and a
nominal layer `t0 = 40 um`:

    saturation at t0   1 - exp(-40/60)      = 0.487
    A(t0)/A_s          1 + 1 x 0.487        = 1.487
    d(lnA)/d(ln t)                          = 0.230

f_layer is positive for a *thinner* layer, so the coupling is **-0.230**.

**Self-consistency check, which neither side was built to pass.** This implies a
bare-solid absorptivity of `0.384 / 1.487 = 0.258`. Bare nickel alloy at ~1 um is
roughly 0.25-0.35. The Gate 1 *fitted* absorptivity and this *derived*
decomposition agree independently.

Sensitivity across d50 15-45 um and powder/solid ratio 1.5-2.5: **-0.12 to
-0.30**. That is the sweep range.

### 2.2 layer_to_powder_enthalpy = +0.186, derived

This term was **missing entirely** until an IN718 single-track study was found
reporting melt pool depth *decreasing* with thicker powder layers - the opposite
of what the model then gave. The cause was not a wrong constant but an absent
one: Eagar-Tsai is a semi-infinite solid with no powder in it, so the energy
spent melting the powder itself had nowhere to appear.

**Step 1 - energy the laser delivers, per metre of track.**

    absorptivity x power / speed = 0.384 x 285 / 0.960 = 114.0 J/m

**Step 2 - energy needed to melt the powder in that metre.**

    cross-section   40 um x 115 um x 0.55 packing   = 2530 um^2
    mass            8190 kg/m^3 x that              = 20.7 mg/m
    enthalpy        450 x (1609 - 293) + 270,000    = 862 kJ/kg
                      ^ heat it up      ^ melt it
    energy          20.7 mg x 862 kJ/kg             = 17.9 J/m

**Step 3 - the fraction.**

    phi = 17.9 / 114.0 = 15.7%

So 15.7% of the absorbed energy goes into melting powder. The other 84.3% does
the job Eagar-Tsai models: heating the solid beneath.

**Step 4 - why phi/(1-phi) and not phi.**

The model is calibrated to the *healthy* case, so its power already represents
the 84.3% that is left over. Make the layer thinner by fraction f. Powder energy
drops to `phi(1-f)`, so the energy left over becomes

    1 - phi(1-f) = 1 - phi + phi*f

As a multiple of the healthy case:

    (1 - phi + phi*f) / (1 - phi) = 1 + f * phi/(1-phi)

    phi/(1-phi) = 0.157 / 0.843 = 0.186

A 10% thinner layer therefore frees up 1.86% more effective power.

Nothing in those four steps is a modelling choice - it is mass, enthalpy and
division. The only inputs are the nominal layer thickness (40 um), the packing
fraction (0.55) and the latent heat (270 kJ/kg). All three are swept, giving
**0.13 to 0.24**, which changes no conclusion.

**Why this term matters more than its size suggests.** It acts in the *opposite*
direction to the absorptivity term and is of the same order - 1.6% against 3.0%
equivalent power change per 10% layer deviation. Omitting it left the net sign of
the layer fault unreliable. And the sign matters: flipping the relative sign of
the layer couplings moves the power/layer angle from 2.04 to 44.58 degrees, a
20x change.

With the term included, the net layer effect falls from +/-4% to **+/-1.2%** over
a +/-20% thickness change, which moves the model *towards* the published review
finding of no significant depth change between 20 and 60 um layers.

### 2.3 layer_to_conductivity = +0.50, the one remaining estimate

Less insulating powder beneath the track raises the effective conductivity the
melt pool sees. Published values bracket powder conductivity at roughly a tenth
to a hundredth of solid, and loose-powder conduction is dominated by gas in the
pores. **But the conductivity in this model is a lumped fitted parameter, not the
powder's own**, so the published ratio does not transfer, and no measurement
constrains its sensitivity to layer thickness.

It is kept, declared an estimate, and swept 0 to 1.5. Mitigations:

- It is by far the weakest of the three layer effects. Isolating each at f = 0.2
  moves melt depth by 3.4% (absorptivity), 1.6% (enthalpy), 0.35% (conductivity).
- Every conclusion is invariant to it across its full range (section 4.3).

**One result it does own, and it is worth stating plainly.** At
`layer_to_conductivity = 0`, the power/layer angle is *exactly* 0.00 degrees.
With that channel removed, a layer fault acts only through absorptivity and
through the powder-melting enthalpy, and **both are pure multipliers on the
energy reaching the pool** - which is exactly what a power fault is. So the
entire instantaneous separation of layer from power lives in this one estimated
constant, and it buys at most 3.8 degrees, below the conventional 10 degree
floor. The conservative reading is that power and layer are effectively
confounded instantaneously whatever this constant is. The result therefore
survives the estimate going to zero rather than depending on it.

### 2.4 Why exponentials

The shape is a deliberate choice, and the reason is a bug. The original form was
`1 + cf`, which goes negative when `f < -1/c`. At large faults that drove
effective conductivity through zero and negative - negative thermal diffusivity,
an imaginary integrand, and NaNs that were then swallowed into finite-looking
nonsense. Exponentials cannot do that; they are strictly positive by
construction.

To first order `exp(cf) = 1 + cf`, so for small faults the two agree and the
Jacobian is identical to two decimal places. Verified, not assumed.
`apply_faults` also now raises if absorptivity leaves (0, 1], conductivity goes
non-positive, or preheat reaches the solidus.

### 2.5 The structural choice: which inputs each fault touches at all

That gas hits absorptivity and not speed, that layer hits three things - these
are physics judgements, not measurements, and they should be counted as decided
rather than derived.

They are swept too. Tier 1 runs four variants that remove each route in turn. The
central result, that power is not isolable from gas, survives all four.

---

## 3. One honest flag

Defining `f_gas` as pure optical depth drops the convective-cooling channel that
a real gas-flow fault would also have. That corresponds exactly to Tier 1's
variant V1, under which power/gas is non-isolable in **both** directions - i.e.
*more* confounded than the baseline.

Since the paper's headline is "confounded before, separable after", adopting the
more-confounded model makes the improvement look bigger. That is self-serving and
must not pass silently. **The quantitative 0.00 degrees should be reported as an
upper bound on the confounding**, with the convection-included baseline stated as
the conservative case. Restoring the convection channel quantitatively needs a
surface-loss term Eagar-Tsai does not have, so it is named as a limitation rather
than patched.

---

## 4. The magnitude f

### 4.1 f is an input, not an output

We never *find* f. We choose it, compute what the sensors would read, and record
the pair. The inverse direction - recovering f from readings - is only used in
the Route B robustness metric.

### 4.2 What f means, per fault

All five are now physical quantities, which is what removed most of the arbitrary
constants:

| fault | f = 1 means |
|---|---|
| power | 100% more power |
| speed | 100% faster |
| layer | layer thickness 100% thinner |
| gas | plume optical depth 1, i.e. transmission `exp(-1)` = 37% |
| geometry | local preheat +100 K |

For orientation, `f_gas = 0.2` is 18.1% beam attenuation.

### 4.3 The two things we do with f: test it, then sweep it

**The step-convergence test.** A Jacobian entry is a slope obtained from two
points:

    slope = (reading at +f  -  reading at -f) / 2f

Two failure modes. If f is too large you measure a chord across a curve rather
than the tangent. If f is too small the two readings are nearly identical,
and subtracting them leaves floating-point noise. The right f is where the answer
stops moving:

    step 0.080   (reference)
    step 0.040   max change  267.33%
    step 0.020   max change   39.35%
    step 0.010   max change   20.59%
    step 0.005   max change    0.25%   <- settles here
    step 0.002   max change    0.05%
    step 0.001   max change    0.01%

At 0.02 the answer is still moving by 39%. Below 0.005 it is stable. The study
uses **0.002**.

This test caught a real error: an earlier default of 0.02 produced numbers that
were wrong by about 20%, and they had already been reported. Nothing but the test
would have found it.

**Sweeping.** Running the entire study again at each value in a range, and
reporting only conclusions that hold at every value. Example, the estimated
conductivity coupling:

    value 0.00 -> enlarged worst 25.83 deg, rank 5
    value 0.50 -> enlarged worst 25.83 deg, rank 5
    value 1.50 -> enlarged worst 25.83 deg, rank 5

Identical. That licenses the sentence *"the conclusion is invariant to this
constant across its full plausible range"*, which does not require the constant
to be right.

**A sweep converts "trust my number" into "it does not matter what the number
is."** That is the defence used throughout this work, and it should replace any
sentence in the paper that reads like a derivation of a chosen constant.

### 4.4 One caveat that must appear in the paper

In the finite-magnitude study every fault is given the same f. But f = 0.05 is a
real 5% for power and only a 1.5% absorptivity change for layer. So those rows do
**not** compare equal physical severities, and the magnitude axis is an index
rather than a common scale.

This does not undermine the conclusion drawn from that study, which is that the
enlarged result stays rank 5 and in the 22-49 degree band across the whole sweep
while the instantaneous one swings between 0 and 7 degrees - that holds at every
point tested. What it rules out is any sentence of the form *"at a 5% fault, pair
X separates and pair Y does not."* Comparisons across pairs at fixed f are not
physically meaningful.

---

## 5. The Jacobian

### 5.1 Definition

Write `y_s` for sensor s's reading and `f_k` for fault k's magnitude. The
Jacobian is the matrix of partial derivatives

    J[s, k] = d(y_s) / d(f_k)

expressed as a *relative* change so units cancel. Three sensors, five faults, so
J is 3 x 5. Computed by central differences at step 0.002.

**Column k is a vector in three-dimensional sensor space: the direction the
readings move when fault k appears.**

### 5.2 The real matrix

                 power     speed     layer       gas  geometry
    photodiode 1.51768  -0.48347  -0.58388  -1.51769   0.06536
    camera     1.22347  -0.41977  -0.45569  -1.22347   0.09297
    pyrometer  0.03632  -0.01542  -0.01205  -0.03632  -0.00178

### 5.3 Whitening

Raw sensitivity means nothing without noise. A sensor that moves a lot but is
noisy tells you less than one that moves a little and is quiet. So divide each
row by that sensor's noise sigma. Everything is then in units of "how many
standard deviations does this move", and comparison is fair.

### 5.4 The angle, and the arithmetic that produces the paper's problem

The angle between two whitened columns is the diagnosability of that pair.

- **0 degrees** - the two faults push readings along the *same line*. No
  measurement can ever separate them.
- **90 degrees** - orthogonal, perfectly separable.
- **~10 degrees** - roughly where practitioners stop believing a separation.

Divide the power column by the gas column, element by element:

    1.51768 / (-1.51769) = -0.99999
    1.22347 / (-1.22347) = -1.00000
    0.03632 / (-0.03632) = -0.99993

Constant. The two columns are the same vector scaled by -1. The angle is
**exactly 0.00 degrees**, and the 7e-05 spread is finite-difference noise on an
exact identity.

**Why it is exact.** Both faults enter the model only through the product
(absorptivity x power), and the Eagar-Tsai temperature rise is linear in that
product. So the gas column is always a scalar multiple of the power column. This
is algebra, not calibration: **no value of any coupling constant can break it.**
Tier 1 found the same thing independently, from equation structure alone, with no
numbers at all.

### 5.5 Rank and condition number

Stack the five whitened columns and take the SVD.

- **Rank** - how many independent directions the five faults span. Three sensors
  can span at most three, so with five faults at least two directions are lost
  regardless of noise. A hardware ceiling.
- **Condition number** - ratio of largest to smallest singular value. How much
  measurement noise is amplified when inverting.

Current values: instantaneous rank 3, condition 85. Enlarged rank 5,
condition 30.

### 5.6 What a Jacobian does and does not license

It is a **first-order Taylor expansion**: a statement about behaviour in a small
neighbourhood of the healthy condition. Conclusions drawn from it are local.

This was tested rather than assumed, and the test found that the *instantaneous*
angles swing non-monotonically with fault size - 0.00 degrees at the derivative
limit, 4.26 at +5%, 6.61 at +20%. So the instantaneous result is genuinely local.

The enlarged result is not: it stays rank 5 and in a narrow band at every
magnitude tested, confirmed by a full no-interpolation run agreeing to 0.66
degrees at +5% and 0.22 at +20%. That difference is itself one of the paper's
findings.
