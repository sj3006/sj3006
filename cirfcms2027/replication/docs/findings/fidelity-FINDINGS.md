# Findings: how accurate must a digital twin be for fault diagnosis?

Plain summary of what the fidelity work established, as of 2026-11-19. Every
number here is printed in `paper/paper.tex` and checked by `claims.py` (71 of 71
pass); the theory is checked by `verify.py` (16 of 16 pass). How each was found,
including the wrong turns, is in `LABNOTEBOOK.md`.

## The question

The calibrated melt-pool model of the two earlier papers was validated by how
well it predicts melt-pool width and depth. It was then used for diagnosis: to
say which of five process faults caused a change in three coaxial instrument
readings, through the certificate of the journal paper. Prediction and
diagnosis ask different things of a model. This work measures the difference.

## The answer, in six statements

**1. Diagnosis needs only directions.** The certificate uses each fault's
signature only through its direction (Theorem 1). An error in the size of a
fault's effect costs nothing. Checked: the geometry preheat constant varied by a
factor of sixteen moves no direction by more than 0.001 degree.

**2. The required accuracy is tight and gets tighter with signal.** An error of
`delta` in the direction of the true cause makes the certificate's coverage
`P(chi2_{S-1}(rho^2 sin^2 delta) <= q)`, exactly (Theorem 2). To stay at 90 %
coverage the error must be below `arcsin(sqrt(0.624)/rho)`: 3.23 deg at rho 14,
**1.62 deg at rho 28** (the signal the ten-degree floor implies), 0.81 at 56,
0.38 at 120. With build context, at matched fault severity, **0.24 to 0.29
deg**.

**3. Validation on melt-pool geometry does not deliver that.** Of 2048 sampled
parameter sets, 328 fit the AM-Bench data as well as the calibrated model by the
standard nonlinear-regression test. Those twins differ from the calibrated model
in fault direction by a median of **22.5 deg**, and from each other by **30.1
deg**; 99 % exceed the budget. Tightening the fit helps but not enough: twins
within 25 % of the best fit still have a median error of 8.7 deg. No twin with a
prediction error below 2.09 % exceeded the budget, but twins at 2.6 % and 3.3 %
reached 16 and 45 deg, so validation would need to resolve predictions to about
2 %, against the model's own 12.4 % error on the data.

**4. Prediction error is a poor guide.** Within the accepted twins, rank
correlation of prediction error with directional error is 0.18. The keyhole
coefficient changes predicted depth by 18 % with zero effect on any direction.
Diagnosis-only quantities change no prediction and still matter: an omitted
plume-scattering channel turns the gas signature by up to 2.27 deg; a noise
model that takes the pyrometer to be 35 times quieter than it is cuts coverage
to 5 %.

**5. Small parameter errors are tolerable at one instant.** Up to 5 % in any one
thermal parameter or 10 % in the operating point gives at most 1.32 deg, inside
the budget. With build context the same errors are not tolerable: a 5 % power
offset leaves 0.05 % coverage.

**6. Directions can be measured instead.** Four commanded steps per fault, each
as strong as the fault to be diagnosed, keep the certificate at 90 % coverage at
every signal strength (Proposition 6). At the earlier papers' noise convention
that is a 3.2 % power step, a 9.4 % speed step or a preheat index of 0.43. Gas
degradation shares the power direction in the model and geometry is a preheat,
so all five directions are reachable by commanded steps, subject to the fault
model's own assumptions.

## Findings that affect the earlier papers

These are reported to the authors, not changed in those papers.

* **Instrument-model grid.** The photodiode and pyrometer integrate a capped
  temperature field on a 121 x 121 grid. Fault directions on that grid are up to
  0.97 deg from converged; quoted pairwise angles shift by up to 0.60 deg (for
  example layer against geometry 4.63 to 4.03 deg). No separability verdict
  changes, because every pair is far from the 10 deg floor. A 961 grid is within
  0.17 deg of 1921. The certificate paper's build-context results require
  directions right to about 0.25 deg, so its instrument model should use at least
  the 961 grid, or move those integrals off the grid as was done for the camera.
* **Calibration identifiability.** The model depends on absorptivity,
  conductivity and heat capacity only through absorbed power per conductivity
  and diffusivity; scaling all three together changes nothing, exactly. The
  calibrated conductivity and heat capacity sit on their bounds because the fit
  is degenerate along that line. Only the two groups are determined by the data.
* **Identical-twin caveat.** Both earlier papers generated and interpreted
  observations with the same model. The certificate's exact coverage holds only
  under that condition; this work measures how fast it is lost otherwise.

## What is not claimed

The truth is a model, so these results say how errors of a given kind propagate,
not how large they are in the real process. Observations were linear in the
truth, separating twin error from the truth's curvature. The validation region
is cut off by the calibration's bounds at the truth's diffusivity. Directional
errors below 0.17 deg are below the model's numerical resolution. A local
linearised precision analysis (`sloppy.py`) was attempted and failed; it is kept
as a recorded negative result and not used.

## Open items for the authors

* Target journal (draft written for Journal of Manufacturing Systems or Advanced
  Engineering Informatics; theory also suits Mechanical Systems and Signal
  Processing).
* The abstract is about 330 words; most Elsevier journals want 250 or fewer.
* Two references to verify before submission: the National Academies DOI and the
  ASME V&V 40 entry (see `paper/refs.bib`).
* Whether to rerun the earlier papers' angles on the 961 grid.
