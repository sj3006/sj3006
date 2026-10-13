# Model-based diagnosability of in-situ sensing in LPBF

A short brief for someone working in additive manufacturing. Covers the question,
the method, and the results established so far. It stops at the "before" picture
— the limit we found — and does not cover the remedy.

---

## The question

In-situ LPBF monitoring research is mature at classifying **outcomes**: keyhole
porosity, lack of fusion, balling, density, surface roughness. Given a photodiode
trace or a coaxial image, a classifier will tell you which defect formed.

We ask a question one step upstream. Given a sensor suite, which **causes** can be
told apart *in principle*?

    f_P      commanded-vs-delivered laser power deviation
    f_v      galvo tracking error
    f_layer  recoater short-feed, i.e. layer thickness deviation
    f_gas    shielding gas degradation, plume attenuation
    f_geo    geometry-driven heat accumulation

"In principle" is the load-bearing phrase. If two causes produce identical sensor
readings, no classifier, filter or amount of data can separate them. That is a
property of the process and the instrumentation, not of the algorithm — and it is
what structural and quantitative diagnosability analysis (the FDI literature) was
built to determine. It has not been applied to LPBF.

## Why the gap is real

Three citations make the case:

1. **Guo et al., *Addit. Manuf.* 28:600-609 (2019).** At constant input energy
   density, melt pool dimension and volume vary by orders of magnitude and change
   melting regime, because power and speed alter absorption separately. Energy
   density is an incomplete metric.
2. **Six years later**, state-of-the-art in-situ parameter estimation still
   predicts *energy density class* from melt pool imagery (91.4% CV accuracy),
   i.e. the lumped group — which is what you fall back on when the components are
   confounded.
3. **Nobody asks** whether the individual causes are separable from a given suite
   at all.

A literature extraction table of 18 works is maintained separately. Outcome
classification dominates; cause estimation exists in three forms, none of them
this one.

## Method

Entirely computational — no experiments were available.

**Thermal model.** Eagar-Tsai (moving Gaussian source, semi-infinite solid),
with the Gladush-Smurov keyhole depth correction after Honarmandi et al.
(*Addit. Manuf.* 47:102300, 2021). Four parameters — absorptivity, effective
conductivity, heat capacity, keyhole constant — fitted to the seven IN718
single-track cases of Weaver et al. (*IMMI* 13:363-379, 2024), AM-Bench 2022.

    calibration result:  11.7% error on width, 13.0% on depth

All seven benchmark cases turned out to be keyholing (aspect ratios 1.45-4.28),
which is why the correction is necessary: pure conduction gave 27.8% depth error.

**Sensors.** Three coaxial observables, modelled from the temperature field:
band-integrated photodiode (700-1000 nm), melt pool area, two-colour pyrometer
(750/950 nm).

**Faults.** Each is defined as a physical quantity so that no arbitrary
conversion constant is required: f_gas is the plume optical depth (Beer-Lambert),
f_geo is preheat rise in units of 100 K, f_layer is fractional layer-thickness
deviation. Two layer couplings are derived from published data — the absorptivity
coefficient from Trapp et al.'s measured powder/solid ratio of ~2 at 1070 nm, and
a powder-melting enthalpy term accounting for 15.7% of absorbed energy. One
coupling remains an estimate and is swept.

**Validation**, against data not used in the fit. Two checks:

- Melt pool depth correlates with volumetric energy density (r = +0.727) while
  width does not (r = +0.032), over 27 melted conditions — reproducing Weaver.
- Guo et al.'s constant-energy-density result: **partial pass.** The model
  reproduces the existence, direction and regime transition, but gives 2.37x
  variation in depth against their orders of magnitude. The mechanism they
  identify — absorption changing with depression geometry — is not in a
  conduction model, and this is reported as a limitation rather than smoothed
  over.

## Result 1: power and gas are not merely similar, they are identical

The temperature rise is linear in the product (absorptivity x power), and **both
faults act only on that product** — power as a direct multiplier, gas through
Beer-Lambert attenuation. Choose f_gas = -ln(1 + f_P) and the two produce
bit-identical melt pools:

    power -5%        A*P = 103.968000000   W 113606.96 nm  D 67704.66 nm
    gas   0.051293   A*P = 103.968000000   W 113606.96 nm  D 67704.66 nm
                     photodiode 7.763392259961e-03 for both

Not "within noise". The same field at every point, so *any* instrument that could
ever exist returns the same reading.

The relative-sensitivity Jacobian:

                     power     speed     layer       gas  geometry
    photodiode     1.51768  -0.48347  -0.58388  -1.51769   0.06536
    camera         1.22347  -0.41977  -0.45569  -1.22347   0.09297
    pyrometer      0.03632  -0.01542  -0.01205  -0.03632  -0.00178

Column ratio power/gas = -0.99999, -1.00000, -0.99993 (spread 7e-05, which is
finite-difference noise on an exact identity). Pairwise angle: **0.00 degrees**.

This is algebra, not calibration. Swept over a 10x range of the gas coupling, the
angle stays 0.00 at every value. An independent structural analysis (Dulmage-
Mendelsohn / MSO sets over an 11-equation model, no numbers at all) finds the
same pair.

## Result 2: the full instantaneous picture

Pairwise angles between noise-whitened fault signature directions:

    power / gas       0.00      structurally impossible
    power / layer     3.46      below the 10 deg practical floor
    layer / gas       3.46
    power / speed     7.12
    speed / gas       7.12
    speed / layer    10.58      marginal
    geometry pairs   58-68      the only fault that stands apart

Geometry separates because it is the only fault not acting through A*P — it
raises the local preheat, which enters the model elsewhere.

**Detection works. Isolation does not.** Every fault visibly moves the readings;
saying which one is the problem.

## Result 3: a rank limit, with explicit invisible faults

The 3x5 Jacobian has singular values 2.92801, 0.04069, 0.00544 — rank 3, so two
fault directions are unobservable. They are computable:

    n1:  power +0.670, gas +0.731, layer -0.112, speed -0.056
    n2:  layer +0.838, speed +0.419, power +0.322, gas -0.134

Applied as a real fault, n1 moves the sensors by -0.15%, -0.12%, -0.004% against
+7.0%, +6.0%, +0.05% for a plain 5% power fault — roughly 45x smaller, and
non-zero only because the model is weakly nonlinear. These are specific,
realistic process drifts that the suite cannot see.

## Result 4: more sensors do not help, and the reason matters

Adding four candidate observables — a SWIR photodiode, a wide-band pyrometer, and
the camera's two axes reported separately — leaves the rank at **3**.

The bottleneck is not instrumentation. Everything the model knows funnels into
four physical channels: `A*P`, scan speed, effective conductivity, and local
preheat. Five faults crowd onto those four, three of them onto `A*P` alone. Any
sensor can only read the melt pool, so the fault-to-sensor map cannot exceed rank
4 however many instruments are fitted — and in practice the fourth channel is
5700x weaker than the first, so it is rank 3 at any realistic noise.

A new wavelength is a reweighting of the same Planck curve over the same pool: a
new row in the matrix, not a new direction.

## What this establishes

    - the confounding is structural, not a calibration or noise artefact
    - it is provable from the model's form, and found independently by two methods
    - buying more of the same class of sensor is quantifiably not a remedy
    - two specific fault combinations are invisible, and can be named

Since the bottleneck is the *instantaneous* state of the melt pool, the only
remaining route is information that is not the instantaneous state. That is the
subject of the second half of the work.

## Stated limitations

- The thermal model is conduction plus an analytic keyhole patch; it partial-
  passes the Guo validation and cannot claim absolute magnitudes.
- Fitted parameters sit at their bounds and below Honarmandi's ranges, and the
  mu/kappa/Cp correlations they report (0.93-0.96) are the same pathology this
  paper studies, appearing in its own calibration.
- One fault coupling remains an unmeasured estimate; no benchmark dataset with
  deliberately induced machine faults exists to calibrate any of them against.
  Every such quantity is defended by sweeping rather than by argument.
- Sensor noise is treated as a ratio and swept across three assumptions, because
  no citable in-process noise figures were found. Isolability results are
  invariant to this; absolute detection thresholds are not claimed.
- Defining f_gas as pure optical depth omits a convective channel a real gas
  fault would have. This makes power and gas *more* confounded, so the reported
  0.00 degrees is an upper bound on the confounding, not a neutral estimate.
