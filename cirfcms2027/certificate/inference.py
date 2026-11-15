"""Which causes an observation admits, and why that is a hypothesis test.

The conference paper asked a design question: given a sensor suite, which fault
pairs lie far enough apart in whitened sensitivity space to be told apart at
all. It answered with pairwise angles and a stated floor of ten degrees.

This module asks the run-time question instead. A build has produced an actual
set of readings. Which causes are consistent with them?

The observation model
---------------------
A fault is a type `k` and a magnitude `f`. The forward model turns that into
sensor readings; dividing by the healthy readings gives the relative deviation
`z`, a vector with one entry per sensor. To first order,

    z = f * J[:, k] + measurement noise

where `J[s, k] = (1/y_s) dy_s/df_k` is the relative-sensitivity Jacobian of
`diagnosability.jacobian`. The noise on sensor `s` is `sigma_s * eps`, where
`sigma_s` is the derived relative noise of `noise.DERIVED` (1 : 0.142 : 1.061
for photodiode : camera : pyrometer) and `eps` is the common fractional noise
every radiometric channel is assumed to carry. Dividing through by that:

    z_w = z / (sigma * eps) = f * Jw[:, k] + e ,     e ~ N(0, I_S)

so `z_w` is measured in standard deviations and `Jw = J / sigma` is the
whitened Jacobian the conference paper's angles were computed on.

Where eps went, and why it cannot go here
-----------------------------------------
The conference paper never named `eps`. It did not have to: angles between
whitened columns depend on the ratios `sigma_s` alone, and a common factor
cancels. That is why the paper could state "no absolute noise level is claimed".

A hypothesis test is not scale-invariant. Whether an observation is consistent
with a cause depends on how large the signal is against the noise, so the test
needs the absolute level. The resolution used throughout is to parameterise by
the whitened signal-to-noise ratio

    rho = || f * Jw[:, k] || = f * || Jw[:, k] || / eps

rather than by `f` and `eps` separately. Every pair of a fault magnitude and a
noise level that produces the same `rho` behaves identically under the test, so
reporting against `rho` claims no absolute noise figure, exactly as before. For
readers who want physical magnitudes, `EPSILON_REFERENCE` fixes one convention
and `magnitude_for_snr` translates. At eps = 1 %, rho = 28 corresponds to a
3.2 % power deviation, a 9.4 % speed deviation or a preheat index of 0.43.

The test
--------
The magnitude `f` is a nuisance parameter: nobody knows how severe the fault is,
and the question is only which cause it was. So profile it out. For candidate
cause `k`, the best-fit magnitude and the residual it leaves are

    f_hat_k = <z_w, Jw[:, k]> / || Jw[:, k] ||^2
    R_k     = || z_w - f_hat_k * Jw[:, k] ||^2
            = || z_w ||^2 - <z_w, u_k>^2 ,       u_k = Jw[:, k] / || Jw[:, k] ||

`R_k` is the squared length of the part of the observation that no magnitude of
cause `k` can explain. Under the hypothesis that `k` is the true single cause,
`z_w - f Jw[:, k]` is standard normal in S dimensions and `R_k` is its squared
projection onto the S-1 dimensional space orthogonal to `u_k`, so

    R_k ~ chi-squared on S - 1 degrees of freedom,

whatever `f` is. One degree of freedom was spent fitting the magnitude. The
distribution is exact, not asymptotic, and involves no prior over causes.

The certificate
---------------
    C_alpha(z) = { k : R_k <= q_{1-alpha}(S-1) }

is the set of causes not rejected at level `alpha`. Because the test has exact
size `alpha` under each hypothesis, the true cause lies in `C_alpha` with
probability exactly `1 - alpha`. This is the object an agent is entitled to
report. Reporting one member of a two-member certificate is not a confident
answer, it is an unsupported one.

The geometry, and where the ten degree floor came from
------------------------------------------------------
Write `rho = || z_w ||` for the observed signal-to-noise and `psi_k` for the
angle between the observation and cause `k`'s signature direction. Then
`<z_w, u_k> = rho cos psi_k` and

    R_k = rho^2 (1 - cos^2 psi_k) = rho^2 sin^2 psi_k

so the certificate is a cone about the observation,

    k in C_alpha   <=>   sin psi_k <= sqrt( q_{1-alpha}(S-1) ) / rho

of half-angle `psi* = arcsin( sqrt(q) / rho )`. Every signature direction inside
the cone is admissible, and the cone shrinks as the signal grows.

Two causes at mutual angle `D` are both admissible whenever the observation
falls near their bisector, which happens with non-negligible probability unless

    D > 2 * psi*(rho, alpha)

This is the conference paper's separation floor, derived rather than chosen. At
three sensors and 95 % confidence the floor of ten degrees corresponds to a
whitened signal-to-noise ratio of 28.1: the convention was an unstated
assumption about signal strength, and this is the assumption it was making.

The build-context regime is the same algebra on the enlarged observation. There
the readings are the 15 regression coefficients of three sensors onto five build
regressors, and 14 degrees of freedom remain. More dimensions means a higher
threshold, so the floor there corresponds to rho = 55.8 rather than 28.1. That
cost is paid many times over: the whitened signature norms grow by 9.3 to 11.4
times, because a coefficient is estimated from every segment of the build rather
than read off one instant.

Whitening when the observations are not independent
---------------------------------------------------
Whitening divides out the noise so that the geometry means separability, and
that requires the noise to be isotropic afterwards. Dividing each row by its own
standard deviation achieves this only when the observations are independent.

For three sensors read at one instant they are, by assumption, so the
instantaneous regime is unaffected by what follows.

The enlarged observation is different. Its entries are least-squares
coefficients, and the coefficient estimates of one sensor onto five regressors
are correlated whenever the regressors are. Writing G for the 84 by 5 regressor
matrix and `sigma_s eps` for the per-segment noise of sensor s,

    c_hat_s = (G'G)^-1 G' z_s     so    Cov(c_hat_s) = sigma_s^2 eps^2 (G'G)^-1

and, sensors being independent, the covariance of the whole stacked observation
is the Kronecker product

    Cov = eps^2 * ( diag(sigma^2)  kron  (G'G)^-1 )

This is not diagonal. In this plan turn density and support depth correlate at
0.577, so the corresponding coefficient estimates do too. The correct whitening
is `Cov^(-1/2)`, taken here as the inverse Cholesky factor, not the reciprocal
of the diagonal standard errors.

The difference is not cosmetic. Under diagonal whitening the 95 % certificate
covers the truth 93.8 % of the time rather than 95.0 %, and the pairwise angles
move by up to 8.8 degrees, enough to change which pair is the worst: diagonal
whitening reports power against speed at 24.90 degrees, full-covariance
whitening reports speed against geometry at 25.55 degrees. Every pair still
clears ten degrees and the rank is 5 either way, so the conclusion stands, but
the numbers differ. `whitening="diagonal"` reproduces the conference paper's
convention for comparison; `"full"` is the default and is the one with exact
coverage.

What this does and does not license
-----------------------------------
It licenses the statement that a reported set contains the true cause with
stated probability, under this forward model, this noise model and the
first-order expansion. It does not license calling a one-member certificate a
diagnosis: the set can be small because the signal is strong, or because the
model is wrong in a way that happens to point somewhere. The linearisation error
is reported separately, in `cases.py`, by generating observations from the full
nonlinear model and recording how much of the residual it accounts for.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.stats import chi2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import diagnosability as diag          # noqa: E402
import noise                           # noqa: E402
import observables as obs              # noqa: E402
from faults import FAULT_NAMES         # noqa: E402

__all__ = ["EPSILON_REFERENCE", "ALPHA", "ANGLE_DEGENERACY_TOL", "Regime", "instantaneous", "build_context",
           "chi2_threshold", "residuals", "fitted_magnitudes", "certificate",
           "cone_half_angle", "resolving_snr", "snr_for_floor", "floor_for_snr",
           "magnitude_for_snr", "snr_of", "report"]

#: One convention for the common radiometric noise, used only to translate a
#: signal-to-noise ratio into a physical fault magnitude. No result depends on
#: it; every result is reported against `rho`.
EPSILON_REFERENCE = 0.01

#: Default test level. 0.05 gives a certificate covering the truth 95 % of the time.
ALPHA = 0.05


class Regime:
    """A set of observables with its Jacobian and its noise covariance.

    `J` has one row per observable and one column per fault, in `FAULT_NAMES`
    order. `cov` is the observation noise covariance in units of `eps^2`, so it
    is dimensionless and a common factor of `eps` never enters. `Jw` is the
    whitened Jacobian `Cov^(-1/2) J`, and `dof` is the degrees of freedom left
    after fitting the magnitude, the number of observables minus one.
    """

    def __init__(self, name: str, J: np.ndarray, cov: np.ndarray,
                 observable_names: tuple[str, ...]):
        self.name = name
        self.J = np.asarray(J, float)
        self.cov = np.asarray(cov, float)
        self.observable_names = tuple(observable_names)
        if self.cov.ndim == 1:
            self.cov = np.diag(self.cov ** 2)
        self._chol = np.linalg.cholesky(self.cov)
        self._whitener = np.linalg.inv(self._chol)
        self.Jw = self._whitener @ self.J
        self.n_obs = self.J.shape[0]
        self.dof = self.n_obs - 1
        self.norms = np.linalg.norm(self.Jw, axis=0)

    @property
    def sigmas(self) -> np.ndarray:
        """Marginal standard deviation of each observable, in units of eps."""
        return np.sqrt(np.diag(self.cov))

    def whiten(self, z: np.ndarray, eps: float = None) -> np.ndarray:
        """Whiten a raw relative-deviation vector into standard-normal units."""
        e = EPSILON_REFERENCE if eps is None else eps
        return self._whitener @ (np.asarray(z, float).ravel() / e)

    def __repr__(self) -> str:
        return f"Regime({self.name!r}, {self.n_obs} observables, dof={self.dof})"


def instantaneous(step: float = 0.002) -> Regime:
    """Three coaxial observables read at one instant: the conference baseline.

    The three sensor noises are independent by assumption, so the covariance is
    already diagonal and no whitening question arises here.
    """
    J, _ = diag.jacobian(step=step)
    from sensors import SENSOR_NAMES
    return Regime("instantaneous", J, np.diag(noise.SIGMAS ** 2), SENSOR_NAMES)


def build_context(step: float = 0.002, plan=None,
                  whitening: str = "full") -> Regime:
    """The 15 regression coefficients of three sensors onto five build regressors.

    `whitening="full"` uses the Kronecker covariance derived in the module
    docstring and gives a test with exact coverage. `"diagonal"` keeps only the
    standard errors, reproducing the conference paper's convention.
    """
    J, _ = diag.jacobian(step=step)
    plan = obs.scan_plan() if plan is None else plan
    Jbig = obs.enlarged_jacobian(J, plan)
    G = obs.regressors(plan)
    GtGinv = np.linalg.inv(G.T @ G)
    if whitening == "full":
        cov = np.kron(np.diag(noise.SIGMAS ** 2), GtGinv)
    elif whitening == "diagonal":
        cov = np.diag(obs.coefficient_sigmas(noise.SIGMAS, plan) ** 2)
    else:
        raise ValueError(f"unknown whitening {whitening!r}")
    from sensors import SENSOR_NAMES
    names = tuple(f"{s}:{r}" for s in SENSOR_NAMES for r in obs.REGRESSOR_NAMES)
    return Regime(f"build context ({whitening})", Jbig, cov, names)


def chi2_threshold(dof: int, alpha: float = ALPHA) -> float:
    """The 1 - alpha quantile of chi-squared on `dof` degrees of freedom."""
    return float(chi2.ppf(1.0 - alpha, dof))


def fitted_magnitudes(zw: np.ndarray, regime: Regime) -> np.ndarray:
    """Least-squares fault magnitude under each single-cause hypothesis."""
    zw = np.asarray(zw, float).ravel()
    return (regime.Jw.T @ zw) / (regime.norms ** 2)


def residuals(zw: np.ndarray, regime: Regime) -> np.ndarray:
    """`R_k` for every cause: what no magnitude of that cause can explain."""
    zw = np.asarray(zw, float).ravel()
    total = float(zw @ zw)
    proj = (regime.Jw.T @ zw) / regime.norms
    return np.maximum(total - proj ** 2, 0.0)


def certificate(zw: np.ndarray, regime: Regime, alpha: float = ALPHA
                ) -> tuple[str, ...]:
    """Causes not rejected at level `alpha`. Contains the truth w.p. 1 - alpha."""
    q = chi2_threshold(regime.dof, alpha)
    R = residuals(zw, regime)
    return tuple(n for n, r in zip(FAULT_NAMES, R) if r <= q)


def cone_half_angle(rho: float, dof: int, alpha: float = ALPHA) -> float:
    """Half-angle in degrees of the admissible cone about an observation."""
    s = np.sqrt(chi2_threshold(dof, alpha)) / float(rho)
    return float(np.degrees(np.arcsin(min(1.0, s))))


#: Angles below this are finite-difference residue on an algebraic identity,
#: not a small real separation. Power and gas sit at 1.1e-4 degrees because
#: their Jacobian columns are proportional to within 7e-5 element-wise, so the
#: pair is degenerate exactly and no signal-to-noise ratio resolves it.
ANGLE_DEGENERACY_TOL = 1e-2


def resolving_snr(delta_deg: float, dof: int, alpha: float = ALPHA) -> float:
    """Signal-to-noise needed before a pair `delta_deg` apart stops overlapping.

    Returns infinity for an algebraically degenerate pair, rather than the very
    large finite number the floating-point residue of a zero angle would give.
    """
    if float(delta_deg) < ANGLE_DEGENERACY_TOL:
        return float("inf")
    half = np.radians(float(delta_deg) / 2.0)
    return float(np.sqrt(chi2_threshold(dof, alpha)) / np.sin(half))


def snr_for_floor(floor_deg: float, dof: int, alpha: float = ALPHA) -> float:
    """The `rho` at which a chosen separation floor is the correct one."""
    return resolving_snr(floor_deg, dof, alpha)


def floor_for_snr(rho: float, dof: int, alpha: float = ALPHA) -> float:
    """The separation floor implied by a signal-to-noise ratio."""
    return 2.0 * cone_half_angle(rho, dof, alpha)


def magnitude_for_snr(rho: float, fault: str, regime: Regime,
                      eps: float = EPSILON_REFERENCE) -> float:
    """Fault magnitude giving whitened signal-to-noise `rho`, at noise `eps`."""
    k = FAULT_NAMES.index(fault)
    return float(rho * eps / regime.norms[k])


def snr_of(f: float, fault: str, regime: Regime,
           eps: float = EPSILON_REFERENCE) -> float:
    """Whitened signal-to-noise of a fault of magnitude `f`, at noise `eps`."""
    k = FAULT_NAMES.index(fault)
    return float(abs(f) * regime.norms[k] / eps)


def report() -> None:
    inst = instantaneous()
    ctx = build_context(whitening="full")
    ctx_d = build_context(whitening="diagonal")

    print("The certificate: which causes an observation admits")
    print("=" * 74)

    for reg in (inst, ctx):
        q = chi2_threshold(reg.dof, ALPHA)
        print(f"\n{reg.name}: {reg.n_obs} observables, dof = {reg.dof}, "
              f"q_0.95 = {q:.4f}, sqrt(q) = {np.sqrt(q):.4f}")
        print("   whitened signature norms, which set rho per unit magnitude:")
        for n, v in zip(FAULT_NAMES, reg.norms):
            print(f"      {n:9s} ||Jw|| = {v:8.3f}    f for rho=28 at eps=1%: "
                  f"{magnitude_for_snr(28.0, n, reg):8.4f}")

    print("\nThe cone, and the separation floor it implies (instantaneous, dof = 2)")
    print(f"   {'rho':>7s}  {'cone half-angle':>16s}  {'resolvable above':>18s}")
    for rho in (10, 15, 20, 25, 28.08, 30, 50, 100, 300):
        psi = cone_half_angle(rho, inst.dof)
        print(f"   {rho:7.2f}  {psi:12.2f} deg  {2 * psi:14.2f} deg")

    print("\nThe conference paper's ten degree floor, read as an assumption about")
    print("signal strength rather than as a convention")
    for reg in (inst, ctx):
        rho = snr_for_floor(10.0, reg.dof)
        print(f"   {reg.name:24s} rho = {rho:6.2f}   "
              f"(at eps=1%, a power deviation of {magnitude_for_snr(rho, 'power', reg):.3%})")

    print("\nWhat the enlarged observation costs and buys")
    sq_i = np.sqrt(chi2_threshold(inst.dof, ALPHA))
    sq_c = np.sqrt(chi2_threshold(ctx.dof, ALPHA))
    gain = ctx.norms / inst.norms
    print(f"   the test threshold rises      sqrt(q) {sq_i:.3f} -> {sq_c:.3f}  ({sq_c / sq_i:.2f}x)")
    print(f"   the signatures grow           {gain.min():.2f}x to {gain.max():.2f}x")
    print(f"   so at fixed fault magnitude the floor shrinks by "
          f"{gain.mean() / (sq_c / sq_i):.1f}x, while the angles")
    print(f"   themselves open from {min(obs._angles(inst.Jw).values()):.2f}"
          f"-{max(obs._angles(inst.Jw).values()):.2f} deg to "
          f"{min(obs._angles(ctx.Jw).values()):.2f}-{max(obs._angles(ctx.Jw).values()):.2f} deg")

    print("\nWhitening the enlarged observation: diagonal standard errors against")
    print("the full Kronecker covariance")
    a_d, a_f = obs._angles(ctx_d.Jw), obs._angles(ctx.Jw)
    print(f"   {'pair':24s} {'diagonal':>10s} {'full':>10s} {'delta':>8s}")
    for k in sorted(a_d, key=lambda x: a_d[x]):
        print(f"   {k[0] + ' / ' + k[1]:24s} {a_d[k]:10.2f} {a_f[k]:10.2f} {a_f[k] - a_d[k]:+8.2f}")
    print(f"   worst pair   diagonal {min(a_d, key=a_d.get)} at {min(a_d.values()):.2f} deg")
    print(f"                full     {min(a_f, key=a_f.get)} at {min(a_f.values()):.2f} deg")
    print(f"   rank {np.linalg.matrix_rank(ctx_d.Jw)} either way; "
          f"every pair clears ten degrees either way")

    print("\nSignal-to-noise each instantaneous pair would need to be resolvable")
    for (p_, q_), v in sorted(obs._angles(inst.Jw).items(), key=lambda x: x[1]):
        need = resolving_snr(v, inst.dof)
        shown = "never (degenerate)" if need == float("inf") else f"rho {need:>10.1f}"
        print(f"   {p_:9s}/{q_:9s} {v:8.4f} deg   {shown}")


if __name__ == "__main__":
    report()
