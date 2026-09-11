# Technical stack, in execution order

This is not a machine learning project. It is analytical modelling, linear
algebra and sensitivity analysis. There is exactly one place where a learned
model belongs, and it is at the end as a confirmation step. That is a feature:
no training runs, no GPU, no dataset dependency.

**Libraries:** numpy, scipy, matplotlib, pandas, scikit-learn, scikit-image.
Runs on a laptop.

---

## 1. Forward thermal model

**Method.** Eagar–Tsai analytical solution: a moving Gaussian heat source on a
semi-infinite substrate. Rosenthal's point source convolved with a Gaussian
distribution, so it stays closed-form up to a single integral.

**Implementation.** Fixed-order Gauss–Legendre quadrature over the integration
variable, vectorised across the spatial grid with numpy. Milliseconds per call.

**Objective.** Obtain T(x,y,z) for any (power, speed, spot size, preheat,
material) fast enough to evaluate thousands of fault combinations. Speed and
smoothness matter here; fidelity does not. Finite element would give neither.

## 2. Calibration and verification

**Method.** Nonlinear least squares (`scipy.optimize.least_squares`) fitting a
single free parameter — effective absorptivity — against published melt pool
width and depth at several parameter sets.

**Objective.** Show the model reproduces reality within a stated error using one
calibrated unknown rather than a tuned zoo. Report MAPE on width and depth. One
free parameter is defensible; five is curve fitting.

## 3. Fault parameterisation

**Method.** Fault vector f in R^5, each component a *fractional* deviation from
nominal, each mapped to a specific model input:

| Fault | Enters the model as |
|---|---|
| Laser power deviation | direct input |
| Scan speed deviation | direct input |
| Thin powder layer (recoater short-feed) | effective absorptivity + powder/solid conductivity ratio beneath |
| Degraded shielding gas flow | reduced surface convection + attenuation on delivered power |
| Geometry-driven heat accumulation | elevated initial temperature T0 |

**Objective.** Put all faults into a common dimensionless magnitude space so the
signature directions computed later are comparable.

**Watch out.** This normalisation choice determines whether the angles mean
anything. If power deviation is in watts and layer thinning is in microns, the
geometry is arbitrary. Justify the choice explicitly in the paper — it is the
first thing a careful reviewer will attack.

## 4. Observation models

All derived from the same temperature field.

**Photodiode.** Planck's law spectral radiance integrated over the detector band
and over the melt pool area, weighted by responsivity, under a grey-body
emissivity assumption. Numerically a 2D spatial quadrature nested with a 1D
spectral one.

**Coaxial camera.** Melt pool area where T > T_melt, via contouring
(`skimage.measure.find_contours`) or threshold-and-count.

**Two-colour pyrometer.** Ratio of two band-integrated radiances, inverted to
apparent temperature. Its value is emissivity independence — a genuinely
different observable rather than a third copy of the same information.

**Objective.** Build the map y = h(T), turning one physics field into m sensor
readings.

## 5. Sensitivity Jacobian

**Method.** J = dy/df via **complex-step differentiation**:
h'(x) ~ Im[h(x + ih)]/h. Exact to machine precision, no subtractive cancellation,
three lines of change. Works because the model is analytic — no `abs`, no
branching. Fall back to central differences with a step-convergence check if any
branching creeps in.

**Objective.** The columns of J *are* the fault signature directions in sensor
space. This is the central object of the paper; everything downstream is linear
algebra on this matrix.

## 6. Noise whitening

**Method.** Build covariance Sigma from published sensor specifications,
converting SNR or noise-equivalent-power figures into standard deviations in the
units of y. Whiten: J~ = Sigma^(-1/2) J.

**Objective.** Make distances meaningful. Comparing a photodiode millivolt with a
camera pixel count is nonsense in raw units. After whitening everything is
measured in sigmas and the geometry becomes interpretable.

## 7. Detectability

**Method.** For each fault, find the magnitude at which the whitened signature
norm crosses a threshold. Set the threshold from a chosen false-alarm rate via a
chi-squared test on the residual rather than picking 3 sigma arbitrarily.

**Objective.** Answer "how large must this fault be before this package notices
it at all."

## 8. Isolability — the headline result

**Method.** Pairwise angle between whitened signature directions:
theta_ij = arccos( <j~_i, j~_j> / (||j~_i|| ||j~_j||) ).
Small angle means confounded: a small amount of one fault mimics a large amount
of the other.

**Then SVD of J~.** Singular values give the effective rank — how many
independent fault directions the suite can resolve. Rank below five means some
faults are structurally unidentifiable regardless of algorithm. The condition
number summarises how ill-posed isolation is overall.

**Objective.** The angle matrix is the main figure. The SVD compresses it into
one sentence a reader remembers: "this four-sensor package resolves three
independent fault directions out of five."

## 9. Breaking confusions — three routes

This is what stops the paper being purely a negative result.

**Route A — richer observables, no new hardware.** Enlarge y from instantaneous
sensor values to temporal and spatial statistics, then recompute J~ and see which
angles open up. Faults that look identical at an instant often evolve
differently:

- laser power drift: slow, monotonic
- recoater short-feed: abrupt, synchronised to the layer cycle
- gas flow degradation: spatial gradient along the flow direction
- geometry-driven heat accumulation: spatially correlated with the part shape

The last is the strongest case, because **the geometry is a known input, not an
unknown**. The build file gives a predictable spatial fingerprint no other fault
can mimic. Correlating the sensor residual against known geometry breaks that
confusion at zero hardware cost.

**Route B — add a sensor.** Enumerate all subsets of the sensor set (2^m - 1,
trivially small at m = 4). For each, restrict J~ to those rows and recompute rank,
condition number and angles. For an ordering, greedy selection: add whichever
sensor most increases the minimum pairwise angle.

**Route C — deliberate excitation (optional, time permitting).** If two faults
are confounded under normal operation, perturb the process and see which
responds. Compute the excitation maximising the angle between perturbed
signatures. Output reads like "to separate A from B, superimpose a 2% power
modulation at 50 Hz". Established as active fault isolation in control. Keep as
the closing section or the journal extension.

**Objective.** The three-way classification: resolvable by structure, resolvable
by hardware, structurally irreducible.

## 10. Robustness

**Method.** Latin hypercube sampling (`scipy.stats.qmc.LatinHypercube`) over
uncertain material properties and noise levels, recomputing the matrix per draw.
Report the fraction of draws in which each pair is confounded. Sobol indices if
you want to name which uncertainty drives the conclusion.

**Objective.** Convert a deterministic matrix into a probabilistic one.
"Confounded in 94% of draws" is much harder to argue with than "confounded".

## 11. Literature comparison

**Method.** Structured manual extraction of defect class sets and reported
confusions from 15–20 monitoring papers. Then a rank-sum test comparing predicted
angles for pairs the literature tests against pairs it does not.

**Objective.** Test whether the community's benchmarks disproportionately avoid
the hard pairs.

**Watch out.** An LLM can help extract, but verify every row by hand. A
fabricated citation here would be fatal.

## 12. The one ML step

**Method.** Simulate noisy sensor readings for each fault across a range of
magnitudes, train **linear discriminant analysis**
(`sklearn.discriminant_analysis`), report its confusion matrix.

**Objective.** Close the loop empirically. LDA is the optimal classifier under
linear-Gaussian assumptions, so its errors are *determined* by the whitened
separations computed analytically. Showing the trained classifier's confusions
match the predicted angle structure proves the geometry governs classifier
behaviour — the bridge to the monitoring community's language, and the answer to
"what does this mean for my CNN".

**Keep it to LDA.** A neural network here would undercut the argument, because
confusion could then be blamed on architecture instead of physics.
