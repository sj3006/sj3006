# How accurate must a digital twin be for fault diagnosis?

Third paper in this repository, after the conference paper (`../overleaf/`) and
the certificate paper (`../certificate/`). Simulation only. Started 2026-11-18
without input from the authors, on the instruction to proceed on best judgement;
every decision taken without them is recorded in `LABNOTEBOOK.md` with its reason,
so that each can be reversed.

## The question

A digital twin is normally validated by comparing what it predicts with what a
healthy process produces: melt pool width and depth, sensor readings at nominal
conditions. A twin used for diagnosis is then trusted to say which fault caused
an anomaly. Those are different tasks, and nothing guarantees that a twin good
at the first is good at the second.

The certificate paper gives this question a precise form. Diagnosis there rests
on the whitened Jacobian: the direction in which each fault moves the
observables. The certificate profiles out the fault magnitude, so the absolute
size of each fault's effect never enters. That suggests the conjecture this paper
tests:

> **A twin is fit for diagnosis if it reproduces the directions in which faults
> move the observables. It need not reproduce the observables themselves, nor
> the magnitudes of the fault effects.**

If that holds, prediction accuracy and diagnostic accuracy are different
properties, and the usual validation measures the wrong one.

## Why the parameters split three ways

The twin here is parameterised by quantities that enter it in different places.
Reading the code, they partition cleanly:

| class | parameters | affects a healthy build? | affects fault directions? |
|---|---|---|---|
| prediction only | keyhole coefficient `C` | yes, depth | **no**, sensors read the surface |
| diagnosis only | fault couplings `c_A, c_k, c_H, c_geo`; noise ratios; fault channels the twin omits | **no** | yes |
| shared | absorptivity, conductivity, heat capacity; operating point | yes | yes |

Validation against healthy data constrains the first and third rows only. It is
blind, by construction, to every diagnosis-only parameter, and it spends effort on
`C`, which diagnosis does not use. That is the observation the paper is built on,
and it is structural rather than numerical: it follows from where each parameter
enters the model.

## Planned results

**Theorem 1, magnitude invariance.** The certificate is exactly invariant to an
error in the magnitude of any fault's sensitivity column. Scaling column `k` of
the twin's Jacobian by any nonzero factor leaves every residual, and hence every
certificate, unchanged, because the magnitude is profiled out. Consequence: of
the four coupling constants, `c_geo` is free, since it scales a single-channel
column, while the ratio `c_k / (c_A + c_H)` matters, since it rotates the layer
column.

**Theorem 2, coverage under directional error.** If the twin's direction for the
true cause is off by angle `delta`, then for linear Gaussian observations the
twin's residual for the true cause is noncentral chi-squared,

    R ~ chi^2_{S-1}( rho^2 sin^2 delta ),

so the nominal `1 - alpha` certificate covers with probability
`F_{chi^2_{S-1}(rho^2 sin^2 delta)}(q_{1-alpha})`, exactly.

**Corollary, stronger signals demand better twins.** Holding coverage at a target
gives a largest admissible directional error that shrinks as `1/rho`. A twin that
is adequate for a weak fault is inadequate for a strong one of the same type.
This is the same mechanism as the linearisation failure found in the certificate
paper, now stated as a fidelity requirement.

**Proposition 3, verdict stability.** The folded angle is a metric on lines, so
the triangle inequality gives `|theta_kl(twin) - theta_kl(truth)| <= delta_k +
delta_l`. A pair's separability verdict is therefore guaranteed to agree between
twin and truth whenever its margin from the floor exceeds `delta_k + delta_l`.

**Noise-model misspecification.** A common error in the assumed noise level
rescales the residual and shifts coverage by a computable amount. Per-sensor
ratio errors both rotate the whitened directions and distort the residual's
distribution into a generalised chi-square; treated numerically.

## Planned study

Truth is the calibrated model of the earlier papers. Each twin differs from it in
one controlled way, and every twin is scored on both kinds of fidelity.

| twin family | what differs | what it tests |
|---|---|---|
| validation-equivalent | absorptivity, conductivity, heat capacity sampled from the region the AM-Bench data cannot rule out, keyhole coefficient profiled | how much diagnosis varies among twins that validate equally well |
| off-ridge | same parameters, perturbed by the same amount in directions the data does constrain | whether error along the ridge is cheaper than error across it |
| conduction-only | no keyhole correction, refitted | a real, structurally different alternative twin |
| uncalibrated | literature properties, one-parameter fit | a real, poorly predicting twin |
| wrong couplings | `c_k / (c_A + c_H)` and `c_geo` varied | perfect prediction, possibly wrong diagnosis; and a control predicted to cost nothing |
| wrong operating point | nominal power and speed offset | a common deployment error |
| wrong noise model | the four noise sets of the conference paper | diagnosis-only, through whitening |
| missing channel | truth carries plume scattering, twin does not | an omitted physical mechanism |

Scores per twin:

- **prediction**: discrepancy from truth on healthy observables at the seven
  AM-Bench conditions, and mean absolute percentage error against the measured
  AM-Bench dimensions;
- **direction**: the angle `delta_k` between twin and truth for each fault's
  whitened signature;
- **pairwise geometry**: the error in each of the ten pairwise angles;
- **verdicts**: agreement on which pairs clear the floor, instantaneously and
  with build context;
- **certificate**: coverage when truth generates the observation and the twin
  certifies it, at several signal-to-noise ratios.

The headline figure is prediction error against diagnostic error across all
twins. The conjecture predicts weak correlation, a family of twins along the
prediction axis with no diagnostic cost, and the coupling twins along the
diagnostic axis with no prediction cost.

## Work packages

| WP | content | module | status |
|---|---|---|---|
| 0 | plan, documentation, GitHub index | this file, `README.md`, `LABNOTEBOOK.md` | in progress |
| 1 | theorems and their verification | `theory.py`, `verify.py` | |
| 2 | parameterised twin | `twin.py` | |
| 3 | twin family | `twins.py` | |
| 4 | study and findings | `study.py`, `FINDINGS.md` | |
| 5 | verified literature | `literature.md` | |
| 6 | results pipeline, figures, draft, claim registry | `results.py`, `figures.py`, `paper/`, `claims.py` | |

## What this paper will not claim

It does not validate the forward model; the earlier papers' limitations stand.
Every twin experiment here is a comparison between models, one of which is
designated truth, so the results say how errors of a given kind propagate into
diagnosis, not how large those errors are in any real twin. Where a real
measurement can bound a directional error, that is reported separately and
labelled as such.

## Target venue

Not yet chosen; the authors decide. The theory suits Mechanical Systems and
Signal Processing; the digital-twin framing suits Journal of Manufacturing
Systems or Advanced Engineering Informatics. The draft is written for the latter
two and can be shifted.
