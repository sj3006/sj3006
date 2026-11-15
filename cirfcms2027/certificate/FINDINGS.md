# Two results from work package 1

Both come out of writing the certificate as a hypothesis test rather than as a
geometric convention. Both are checked in `verify.py`, which passes 14 of 14.

## 1. The ten degree separation floor was an assumption about signal strength

The conference paper states a floor of ten degrees and calls it a practical
convention. It is not a free choice. Profiling out the unknown fault magnitude
leaves, for each candidate cause `k`, a residual

    R_k = || z_w ||^2 - <z_w, u_k>^2 = rho^2 sin^2(psi_k)

distributed as chi-squared on `S - 1` degrees of freedom, where `rho = ||z_w||`
is the whitened signal-to-noise ratio and `psi_k` is the angle between the
observation and cause `k`'s signature direction. Not rejecting `k` at level
`alpha` therefore means

    sin psi_k <= sqrt( q_{1-alpha}(S-1) ) / rho

so the admissible causes form a cone of half-angle `psi*` about the observation,
and two causes at mutual angle `D` are both admissible unless `D > 2 psi*`.

Inverting that at three sensors and 95 % confidence:

| separation floor | implied `rho` | at eps = 1 %, a power deviation of |
|---|---|---|
| 10 degrees, instantaneous (dof 2) | 28.08 | 3.22 % |
| 10 degrees, build context (dof 14) | 55.84 | 0.69 % |

So the paper's floor is the statement "the whitened signal is about 28 standard
deviations". That is a defensible assumption, and it is better stated than
assumed. The same inversion gives, for each pair, the signal-to-noise ratio at
which it would become resolvable:

| pair | angle (deg) | `rho` required |
|---|---|---|
| power / gas | 0.0001 | never, the pair is degenerate |
| layer / gas | 0.3233 | 868 |
| power / layer | 0.3234 | 867 |
| power / speed | 0.7045 | 398 |
| speed / gas | 0.7046 | 398 |
| speed / layer | 1.0280 | 273 |
| speed / geometry | 3.6175 | 77.6 |
| power / geometry | 4.3109 | 65.1 |
| gas / geometry | 4.3110 | 65.1 |
| layer / geometry | 4.6304 | 60.6 |

Power against gas is reported as degenerate rather than as needing a very large
ratio, because the two Jacobian columns are proportional element-wise to within
4.3e-5: the 1.1e-4 degree angle is finite-difference residue on an algebraic
identity, not a small real separation.

## 2. The enlarged observation was whitened with the wrong matrix

This one changes two numbers in the conference paper.

Whitening exists so that the geometry means separability, which requires the
noise to be isotropic after whitening. Dividing each row by its own standard
deviation achieves that only when the observations are independent. For three
sensors read at one instant they are by assumption, so **the instantaneous
results are unaffected**, Table 1's per-segment columns included.

The enlarged observation is different. Its entries are least-squares
coefficients of each sensor's residual onto five build regressors, and

    c_hat_s = (G'G)^-1 G' z_s    so   Cov(c_hat_s) = sigma_s^2 eps^2 (G'G)^-1

which is not diagonal. In this scan plan turn density and support depth are
correlated, giving a coefficient correlation of 0.577. The project already knew
this: `observables.coefficient_sigmas` documents the 0.571 regressor
correlation and computes the marginal standard errors correctly, to 1.9e-16.
What went wrong is using those marginal errors as if the coefficients were
independent. The correct whitening is the inverse Cholesky factor of

    Cov = eps^2 ( diag(sigma^2)  kron  (G'G)^-1 )

verified against per-segment noise put through the same least squares
(agreement to 0.95 % at 60 000 draws, within Monte Carlo error).

Consequences. The 95 % certificate covers the truth 93.8 % of the time under
diagonal whitening and 95.0 % under the full covariance. The pairwise angles
move by up to 8.8 degrees:

| pair | paper (diagonal) | corrected (full) | delta |
|---|---|---|---|
| power / speed | 24.90 | 33.67 | +8.77 |
| power / geometry | 25.42 | 30.02 | +4.60 |
| power / gas | 29.34 | 30.06 | +0.72 |
| gas / geometry | 31.39 | 32.41 | +1.02 |
| speed / geometry | 31.95 | 25.55 | **-6.40** |
| speed / gas | 35.87 | 36.58 | +0.71 |
| power / layer | 36.26 | 34.78 | -1.48 |
| layer / geometry | 40.54 | 46.55 | +6.01 |
| layer / gas | 44.48 | 45.55 | +1.07 |
| speed / layer | 46.16 | 48.98 | +2.82 |

What this does to the conference paper, precisely:

- Rank is 5 either way. The rank claim stands.
- All ten pairs clear the ten degree floor either way. The conclusion stands.
- The worst pair over a build changes from **24.90 degrees on power against
  speed** to **25.55 degrees on speed against geometry**. The abstract, the
  results and Table 1's final column carry the old figure.
- The condition number over retained singular values moves from 49.8 to 52.7.
- The claimed rise "from 0.00 to 24.90 degrees" becomes "from 0.00 to 25.55".

The correction is small and in the paper's favour: the worst pair is further
above the floor than claimed, not closer to it.

## 3. The linearised certificate is valid only below about rho = 30

A certificate built on the Jacobian assumes the response to a fault is a
straight line through the nominal point. The exact response is not, and the
departure is not noise: it is a fixed bias perpendicular to the fault's own
signature direction, which enters the residual as its square and so eats the
test's budget `q = 5.99`.

Measured at eps = 1 %, the perpendicular bias for a power fault is 0.19 at
rho = 28, 0.78 at rho = 56 and 1.72 at rho = 120. Coverage of the 95 %
certificate, with observations generated from the exact model:

| rho | linearised test | exact profile test |
|---|---|---|
| 28 | 0.946 to 0.952 | 0.949 to 0.952 |
| 56 | 0.903 to 0.944 | 0.948 to 0.953 |
| 120 | 0.684 to 0.849 | 0.947 to 0.957 |

The failure is in the dangerous direction. Under-coverage means the test
*excludes the true cause* more often than advertised, so a linearised
certificate would licence an agent to rule out the actual fault.

The fix is to profile the magnitude through the exact forward model rather than
its tangent,

    R_k(z) = min over f of || z_w - g_k(f) / (sigma eps) ||^2

which is a profile likelihood with one nuisance parameter and so keeps the same
chi-squared reference distribution. It restores nominal coverage at every
signal-to-noise ratio tested, including 0.951 for a power fault at rho = 120
where the linearised test gives 0.684. Cost is 49 forward evaluations per fault
once, cached as monotone cubic interpolants, after which a case is a table
lookup.

Worth noting what does not change: the mean certificate size in the
instantaneous regime is 2.7 to 3.9 causes under the exact test, against 2.7 to
3.8 under the linearised one. The paper's central claim is not an artefact of
the linearisation.

## What is not affected

The instantaneous Jacobian, its angles, the rank-4 channel bound, the derived
noise set, the Kronecker collapse theorem, and the 1/sqrt(84) coefficient
noise-reduction factor are all untouched. The marginal standard errors in
`coefficient_sigmas` were right; only their use in place of a covariance was
wrong.
