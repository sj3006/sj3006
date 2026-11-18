# Lab notebook

Chronological record of the fidelity work, written as it happens rather than
reconstructed afterwards. Dead ends, wrong turns and corrections stay in. Each
entry says what was done, what was found, and any decision taken without the
authors' input together with the reason, so that it can be revisited.

Branch: `claude/lucid-feynman-bqpmqw` on `sj3006/sj3006`.
Run anything here with `python3.13` from `cirfcms2027/fidelity/`; the modules put
`../src` and `../certificate` on the path themselves.

---

## 2026-11-18, entry 1: starting point

Asked to begin the twin-fidelity paper, idea 2 of the original brainstorm, with
no input available from the authors and an instruction to document everything
on GitHub so it survives the session.

**What already exists to build on.** The calibrated Eagar–Tsai model with keyhole
correction (`../src/eagar_tsai.py`, `../src/calibrate.py`), the fault routes
(`../src/faults.py`), the sensor models (`../src/sensors.py`), the conduction-only
and uncalibrated alternatives (`../src/conduction_baseline.py`), the scattering
channel (`../src/scattering_channel.py`), the four noise sets
(`../src/route_b.py`), and from the certificate paper the profile test, the
Kronecker covariance and the case generator (`../certificate/`). Health check on
this date: certificate `verify.py` 32 of 32, `claims.py` 76 of 76.

**Reading the code for what a twin can vary.** The calibration fits four
parameters, absorptivity, conductivity, heat capacity and a keyhole coefficient
`C`. The sensors (`sensor_readings`) read the surface temperature field and the
surface dimensions only; `C` enters `calibrate.predict` through
`depth_corrected` and nowhere in the sensor path. So `C` affects prediction and
cannot affect diagnosis. The fault couplings in `FaultCouplings` act only when a
fault is nonzero, so they cannot affect a healthy build and cannot be seen by
validation. The parameters therefore partition into prediction-only,
diagnosis-only and shared, which became the organising idea of the plan in
`ROADMAP.md`.

**Decision, taken without the authors: truth is the calibrated model.** Every
twin experiment needs one model designated truth. The calibrated model of the two
earlier papers is the natural choice because the results then speak directly
about the twin those papers use. The alternative, treating a structurally richer
model as truth, is unavailable: there is no higher-fidelity model in the
repository. Reversible by changing one line in `twins.py`.

**Decision: validation-equivalent twins by a nonlinear-regression confidence
region, not a Laplace approximation.** The calibrated conductivity and heat
capacity sit on their bounds, where a Laplace approximation of the posterior is
not valid. The region of parameters the data cannot rule out is instead taken as
the classical F-test region of nonlinear regression,
`(SSR(theta) - SSR_min)/p / (SSR_min/(n-p)) <= F_{p, n-p, 0.95}`, which inflates
the measurement uncertainty by the observed residual variance and so remains
meaningful when the model is misspecified, as this one demonstrably is (depth
error 13 % against a measurement uncertainty near 5 %). The keyhole coefficient
enters depth linearly, so it is profiled out in closed form for each sample.
