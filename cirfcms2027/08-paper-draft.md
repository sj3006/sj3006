# Which process faults can be told apart? Diagnosability limits of in-situ monitoring in laser powder bed fusion

*Draft for Procedia CIRP, target ~6 pages. Needs transfer to the Elsevier
template. Figure numbering below is the paper's; source files are named in
brackets. Items marked **[PROVISIONAL]** rest on sources that could not be
opened directly and must be verified before submission.*

**Figures:** 6 (old fig1 dropped; fig6 supersedes it)

    Fig. 1  diagnosability matrix, both regimes          [fig6_matrix.png]
    Fig. 2  separation versus profile contrast           [fig2_contrast_threshold.png]
    Fig. 3  separation versus fault magnitude            [fig3_magnitude.png]
    Fig. 4  added measurement versus build context       [fig7_added_sensor.png]
    Fig. 5  robustness to profile misspecification       [fig4_robustness.png]
    Fig. 6  constant energy density sweep                [fig5_constant_ved.png]

---

## 1. Introduction

In-situ monitoring is standard equipment on metal additive manufacturing
systems, and machine learning classifiers routinely report high accuracies for
detecting defects from photodiode, acoustic and imaging signals. Those results
are obtained per study, on defect class sets chosen by their authors, and they
answer a question about **outcomes**: which defect formed.

A machine builder specifying hardware faces a different question, one step
upstream. Given a sensor configuration, which process **causes** can be
separated in principle, and which remain confounded regardless of the classifier
applied? Where two causes produce signatures differing by less than the sensor
noise, no volume of training data will distinguish them; the limit is structural
rather than algorithmic.

The field has circled this question without asking it. Guo et al. [Guo2019]
showed by X-ray imaging that at constant input energy density the melt pool
varies by orders of magnitude and changes melting regime, because laser power
and scan speed alter absorption separately — energy density is an incomplete
process metric. Six years later, state-of-the-art in-situ parameter estimation
still predicts *energy density class* from melt pool imagery [kNN2025], that is,
the lumped group rather than its components. Falling back on a lumped group is
what one does when the components are confounded, but no work establishes
whether they are.

Structural and quantitative diagnosability analysis — fault detection and
isolation (FDI) — was developed precisely to answer such questions, and is
mature in automotive and aerospace process control [Krysander, Frisk]. It has
not previously been applied to laser powder bed fusion (LPBF).

This paper does so. Its contributions are:

1. A model-based diagnosability analysis of five LPBF process fault causes
   against a coaxial sensor suite, reporting the first diagnosability matrix for
   the process.
2. A proof that laser power and shielding gas degradation are **exactly**
   confounded instantaneously — not merely similar — together with the
   demonstration that no sensor of any kind can separate them.
3. The finding that the limit lies in the melt pool, not the instrumentation:
   seven observables span no more directions than three.
4. The demonstration that the spatial and temporal structure already present in
   a build dissolves that limit at zero hardware cost, and outperforms two
   idealised direct measurements of the causes themselves.

**Positioning against the closest prior work.** Raj et al. [Raj2023] observe
significant spatial variation in coaxial melt pool area and intensity on IN718,
attributing it to interaction between the angled beam and the shield gas flow,
and build machine learning surrogates to **predict and compensate** that
variation. This paper uses the same variation for the opposite purpose: it is
the information that breaks a structural confound. They remove what we exploit.

## 2. Method

### 2.1 Process model and calibration

Melt pool geometry is computed from the Eagar–Tsai solution for a moving
Gaussian heat source on a semi-infinite solid, with the Gladush–Smurov keyhole
depth correction after Honarmandi et al. [Hon2021]. Four parameters —
absorptivity, effective conductivity, heat capacity and the keyhole constant —
are fitted to the seven IN718 single-track cases of Weaver et al. [Weaver2024]
from AM-Bench 2022, giving **11.7 % error on melt pool width and 13.0 % on
depth**.

The correction is necessary rather than optional: all seven benchmark cases are
keyholing (aspect ratios 1.45–4.28), and pure conduction gives 27.8 % depth
error.

### 2.2 Fault definitions

Five causes are modelled. Each is defined as a **physical quantity**, so that no
arbitrary conversion constant is required:

| fault | definition | effect on model inputs |
|---|---|---|
| power | fractional power deviation | `P(1+f)` |
| speed | fractional speed deviation | `v(1+f)` |
| gas | plume optical depth | `A·exp(−f)` (Beer–Lambert) |
| geometry | preheat rise in units of 100 K | `T₀ + 100f` |
| layer | fractional layer-thickness deviation | three couplings, below |

The layer fault acts through three channels. Its absorptivity coupling,
**−0.230**, is derived from the measured powder-to-solid absorptivity ratio of
approximately two at 1070 nm [Trapp2017] combined with a radiative penetration
depth of a few particle diameters; the derivation implies a bare-solid
absorptivity of 0.258, consistent with literature values for nickel alloy at
1 µm and in independent agreement with the fitted value. Its powder-melting
enthalpy coupling, **+0.186**, follows from an energy balance: melting the
powder layer consumes 15.7 % of the absorbed energy, so a thinner layer frees
proportionally more for substrate penetration. Its conductivity coupling remains
an estimate and is swept across its full plausible range, with every reported
conclusion invariant to it.

### 2.3 Sensor models

Three coaxial observables are computed from the temperature field: a
band-integrated photodiode (700–1000 nm), melt pool area, and a two-colour
pyrometer (750/950 nm) evaluated as the ratio of integrated band powers.
Temperature is capped at the boiling point before any radiance is computed.

### 2.4 Diagnosability measures

The relative-sensitivity Jacobian `J[s,k] = ∂y_s/∂f_k` is evaluated by central
differences at a step size fixed by a convergence test (0.002; the answer still
moves by 39 % at 0.02). Each row is whitened by its sensor's noise. The angle
between two whitened columns measures the separability of that fault pair: 0°
means the faults move the readings along the same line and are indistinguishable
by any means; a conventional practical floor is 10°.

Structural analysis (Tier 1) is run in parallel on an 11-equation model over
knowns, unknowns and faults, using minimal structurally overdetermined sets. It
uses no numerical values and provides an independent check.

### 2.5 The enlarged observation

A build comprises thousands of segments with a known toolpath, layer schedule,
gas-flow direction and part geometry. Each fault varies in severity across those
segments differently: power drifts with time, galvo error peaks at turns, a
recoater fault cycles with layers, gas degradation follows the flow direction,
heat accumulation follows local support depth.

Regressing each sensor's residual onto five known context variables (a constant
plus gas-axis position, layer parity, turn density and support depth) yields
3 × 5 = 15 coefficients in place of 3 instantaneous readings. Its Jacobian is
`J[s,k]·B[j,k]` with `B = (GᵀG)⁻¹GᵀM`, where `G` is the known context and `M`
the fault modulation profiles. Coefficient noise is `σ_s·√[(GᵀG)⁻¹]_jj`.

The modulation profiles are physical claims, not measurements. One has
independent corroboration [Raj2023]; the others do not. Results are therefore
reported against swept profile contrast (§3.4) rather than at a single value.

### 2.6 Noise treatment — a declared position

Only one in-process noise figure proved citable: a melt pool width uncertainty
of 2.3 % relative [Weaver2024]. No comparable characterisation was found for a
coaxial photodiode or two-colour pyrometer in process. Sensor noise is therefore
treated as a **ratio** and swept over three assumption sets, with every reported
conclusion required to hold under all three.

This is sufficient for the isolability results reported here, which depend only
on relative noise: pairwise angles, rank and condition number are all invariant
to a common scaling of all sensor noise. Absolute detection thresholds are
correspondingly **not** claimed.

## 3. Results

### 3.1 Validation

Two checks against data not used in the fit. Melt pool depth correlates with
volumetric energy density (r = +0.727) while width does not (r = +0.032) over 27
melted conditions, reproducing [Weaver2024]. Against Guo et al.'s constant
energy density result [Guo2019] the model gives a **partial pass**: it
reproduces the existence, direction and regime transition of the variation, but
2.37× in depth against their orders of magnitude. The mechanism they identify —
absorption varying with depression geometry — is absent from a conduction model
with an analytic keyhole patch, and this is reported as a model limitation.

The same sweep yields a result used later (Fig. 6): in the conduction regime at
constant energy density, melt pool **length** varies by 2.53× while width and
depth vary by only 1.11×, and width falls while depth rises.

### 3.2 Power and gas are exactly confounded

Both faults act **only** on the product (absorptivity × power), and the
Eagar–Tsai temperature rise is linear in that product. Choosing
`f_gas = −ln(1+f_power)` therefore produces bit-identical melt pools: identical
temperature at every point, hence identical readings from any instrument that
could exist. The ratio of the two Jacobian columns is −0.99999, −1.00000,
−0.99993 across the three sensors, a spread of 7 × 10⁻⁵ attributable to
finite-difference error on an exact identity. The pairwise angle is **0.00°**.

This is algebraic, not numerical. Sweeping every coupling constant across its
plausible range leaves the angle at 0.00°, and the independent structural
analysis identifies the same pair from equation form alone.

### 3.3 The limit is the melt pool, not the sensors

The 3 × 5 Jacobian has singular values 2.928, 0.0407, 0.0054 — rank 3, so two
fault directions are unobservable. They are computable; one is
`power +0.670, gas +0.731, layer −0.112, speed −0.056`, which when applied as a
real fault moves the sensors by −0.15 %, −0.12 % and −0.004 % against +7.0 %,
+6.0 % and +0.05 % for a plain 5 % power fault.

Adding four candidate observables — a short-wave infrared photodiode, a
wide-band pyrometer, and the camera's two axes reported separately — leaves the
rank at **3**. The reason is structural: everything the model knows funnels into
four physical channels (absorbed power, speed, conductivity, preheat), with
three of the five faults crowding onto the first. Any sensor reads only the melt
pool, so the fault-to-sensor map cannot exceed rank 4 however many instruments
are fitted, and the fourth channel is 5700× weaker than the first.

A new wavelength is a reweighting of the same Planck curve over the same pool: a
new row, not a new direction.

### 3.4 The enlarged observation

With build context, rank rises from 3 to 5, the worst pair from 0.00° to
**25.83°**, power/gas to 29.34°, and the worst finite collinearity index from
141 869 to 2.1 (Fig. 1). The result holds at finite fault magnitude — rank 5 and
22–49° across magnitudes from 0.2 % to 20 %, both signs (Fig. 3) — confirmed by
a no-interpolation run agreeing to 0.66° at +5 %.

A control in which all five faults are given one shared profile returns the
instantaneous result bit-identically, confirming that the gain arises from the
profiles differing rather than from the enlarged matrix having more rows.

Because the profiles are asserted, Fig. 2 reports separation against profile
contrast. **Even the two hardest pairs clear the floor at 40 % of the asserted
strength**, so the conclusion survives the profiles being 2.5× weaker than
claimed.

### 3.5 The diagnosability matrix

Classifying on the enlarged observation alone places all ten pairs in class 1
for every configuration, including a single photodiode — true, and
uninformative. The matrix is therefore reported in two regimes reflecting a real
engineering distinction (Fig. 1):

    INSTANTANEOUS  per-segment decisions in real time (closed-loop control)
    ACCUMULATED    diagnosis over a build (qualification, drift monitoring)

    instantaneous:  class 1  5/10   class 2  5/10   class 3  0/10
    accumulated:    class 1 10/10   class 2  0/10   class 3  0/10

**Class 3 is empty in both regimes.** Nothing is structurally irreducible for
this suite.

### 3.6 Configurations typical of commercial machines

No vendor is named. The mapping from product to observable rests on secondary
review literature rather than datasheets — detection bands are routinely
withheld under supplier confidentiality, and published descriptions of the same
product disagree — so attaching a named product to a computed diagnosability
limit would assert more than the evidence carries. Naming also adds nothing: the
result depends on what a suite measures, not whose badge is on it.

Stripping the names reveals something a vendor-by-vendor table hides. **Across
five commercial systems surveyed there are only three distinct configurations**
for the purposes of this analysis; several vendors ship what is effectively the
same instrument set.

| configuration | inst. rank | class 1 | power/gas |
|---|---|---|---|
| A  single coaxial photodiode | 1 | 0/10 | 0.00 |
| B  photodiode + melt pool imaging | 2 | 4/10 | 0.00 |
| C  two photodiodes, separate bands | 2 | 0/10 | 0.00 |
| D  research reference (A + imaging + pyrometry) | 3 | 5/10 | 0.00 |
| *E  C plus upstream power monitoring* | *3* | *4/10* | ***84.02*** |

**No configuration built solely from melt-pool observables separates laser power
from gas degradation**, whatever its sensor count. All read 0.00°, for the reason
in §3.2: every observable reads the melt pool, and both faults reach it only
through the product (absorptivity × power).

Configuration E is the actionable row. Adding a **direct measurement of delivered
laser power, sampled upstream of the process zone**, separates the pair at
84.02°, because such a sensor sees the laser's output without seeing plume
attenuation. It is a configuration type, and the figure follows from this
analysis alone.

One surveyed system is described as pairing melt pool emission sensing with a
photodiode measuring laser energy, which would place it at E rather than C if
that photodiode samples upstream of the process zone. This could not be
established from public documentation, so it is counted conservatively as C —
the reading that does not favour this analysis.

Note also that C performs worse than B despite both having two observables: two
bands of the same emitted light are near-redundant, whereas a geometric
measurement adds a different direction.

### 3.7 What an added measurement would buy

Since the sensors that would help cannot be simulated — the model has no plume
and no powder layer — we model what such a sensor *measures* rather than the
instrument: a unit row on fault k with relative noise, the idealised best case
for any instrument aimed at that cause.

A direct gas measurement clears power/gas, speed/gas and layer/gas. A direct
geometry measurement clears nothing and leaves the rank at 3, geometry being
already separated at 58–68°. **Precision is almost irrelevant**: sweeping from
50 % to 0.2 % relative noise changes nothing, because adding a row in a new
direction changes the rank while making an existing row quieter does not. A
crude measurement of the right cause beats a precise measurement of the wrong
one.

Fig. 4 gives the comparison that matters. **The free method outperforms two
idealised, perfect direct measurements of the causes themselves** — worst pair
25.83° against 7.12°, condition number 30 against 546, ten pairs cleared against
nine. Neither a gas nor a layer sensor says anything about power versus speed,
and that pair is exactly what spatial context resolves.

Among melt-pool observables, the most valuable addition is free: reporting the
camera's two axes separately rather than as an area is worth **+13.4°** on the
binding pair, while a SWIR photodiode (−0.08°) and a wide-band pyrometer
(−0.13°) are worth nothing. Fig. 6 supplies the mechanism — melt pool length
carries 2.5× the variation of width and depth at constant energy density, and
area multiplies the least informative dimension by the most informative one.

## 4. Discussion

### 4.1 Comparison against reported accuracies

Of 18 extracted works, 12 classify outcomes, about which this analysis makes no
prediction: a melt pool deeper than the layer will fuse whatever made it deep.
That non-comparability is the paper's central point in evidential form.

The one directly comparable work is RAISE-LPBF-LASER [Blanc2023], which
reconstructs power and speed independently from on-axis video — a pair placed
here at 7.12° instantaneously and 25.83° with context. Its best baseline
(SlowFast, 32 input frames) reaches speed RMSE 67.6 and power RMSE 11.12,
against 157.8 and 19.50 for a model using 8 frames. **This is suggestive rather
than evidential**: two further baselines use 16 frames and perform worse than the
8-frame model, so architecture dominates frame count in that table. The authors
themselves offer frames only as a hypothesis for the weaker models' performance.

Two further confirmations of the same kind: that benchmark ranks on **linear
power density** as a target in its own right, and the k-NN study predicts
**energy density class** — two independent groups reporting the lumped group
this analysis identifies as what survives confounding. And no published work
attempts to separate power from gas, or layer from power, the pairs identified
here as identical and effectively confounded respectively. That is absence of
evidence rather than evidence of absence, but no published result contradicts
the predicted limits.

### 4.2 A design rule for sensor selection

The failed candidates and the successful ones differ by a criterion that can be
stated generally:

> A sensor added to break a confound must observe **upstream of the shared
> channel**. A sensor reading the melt pool adds a row, not a direction.

Plume and fume sensing attacks the gas fault; powder-bed and recoater sensing
attacks the layer fault. Both classes exist [Light2026, Liu2022, Bugatti2022].
No benefit is quantified for them here, because the model cannot simulate them.

### 4.3 Limitations

The thermal model is conduction with an analytic keyhole patch; it partial-passes
the Guo validation and absolute magnitudes are not claimed. Fitted parameters sit
at their bounds, and the μ/κ/Cp correlations of 0.93–0.96 reported in [Hon2021]
are the same pathology this paper studies, appearing in its own calibration. One
fault coupling remains an unmeasured estimate; no benchmark dataset with
deliberately induced machine faults exists against which to calibrate any of
them, so each is defended by sweeping rather than by argument.

Two modelling choices make the instantaneous case **more** confounded than
reality, and so inflate the gap the contribution is measured by. Defining `f_gas`
as pure optical depth omits a convective channel a real gas fault would have. And
treating plume attenuation as independent of power and speed is what makes the
power/gas degeneracy exact; published observation suggests the effect depends on
both [Photodiode2024]. **The reported 0.00° should therefore be read as an upper
bound on the instantaneous confounding.** The rank limit is unaffected, deriving
from channel counting rather than from this coupling's form.

Finally, the fault magnitude is a physical quantity per fault but the five are
not on a common severity scale, so comparisons *across pairs at fixed magnitude*
are not meaningful.

## 5. Conclusions

1. Laser power and shielding gas degradation produce **identical** melt pools in
   this model, confounded at 0.00° by algebra rather than by noise. No
   instrument can separate them from a single instant.
2. The limit lies in the melt pool, which has four physical channels, not in the
   instrumentation. Seven observables span no more directions than three.
3. The spatial and temporal structure already present in a build dissolves the
   limit at zero hardware cost: rank 3 → 5, worst pair 0.00° → 25.83°, surviving
   at 40 % of the asserted profile strength.
4. That free method **outperforms two idealised direct measurements of the
   causes themselves**, because neither addresses power versus speed.
5. No configuration built from melt-pool observables alone separates power from
   gas instantaneously, whatever its sensor count. Adding an upstream
   measurement of delivered laser power does, at 84°, and that is the design
   recommendation for real-time control.
6. Among melt-pool observables the most valuable addition is free — reporting
   the camera's two axes separately is worth 13.4° on the binding pair, while
   two new instruments are worth nothing.
7. Nothing is structurally irreducible for this suite. Post-build diagnosis
   requires no new hardware; real-time per-segment isolation does, and crude
   direct sensing of the right cause suffices.

---

## References — to be completed

    [Guo2019]        Guo et al., Additive Manufacturing 28:600-609, 2019
    [Weaver2024]     Weaver et al., IMMI 13:363-379, 2024
    [Hon2021]        Honarmandi et al., Additive Manufacturing 47:102300, 2021
    [Trapp2017]      Trapp et al., Applied Materials Today, 2017
    [Raj2023]        Raj et al., J. Manufacturing Processes 89:24-38, 2023
    [Blanc2023]      Blanc, Ahar & De Grave, Addit. Manuf. Letters 7, 2023
    [kNN2025]        IJAMT, DOI 10.1007/s00170-025-15591-y, 2025
    [Liu2022]        Liu et al., Additive Manufacturing, 2022
    [Bugatti2022]    Bugatti & Colosimo, Addit. Manuf. Letters, 2022
    [Light2026]      Prog. Addit. Manuf., DOI 10.1007/s40964-026-01584-0
    [Photodiode2024] Addit. Manuf. Letters, DOI pending - gas flow / photodiode study
    [Krysander]      Krysander & Frisk, structural analysis / MSO sets
    [Frisk]          Frisk et al., Fault Diagnosis Toolbox

**Outstanding before submission:** complete all references with full author
lists and DOIs; verify the two [PROVISIONAL] items; obtain the four literature
rows read only from abstracts; confirm venue page limit and transfer to the
Elsevier Procedia template.
