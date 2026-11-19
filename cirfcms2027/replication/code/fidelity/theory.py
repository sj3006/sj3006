"""What a twin must get right for the certificate to stay right.

Setting
-------
The certificate paper tests each candidate cause `k` with the profile residual

    R_k(z) = || z_w ||^2 - < z_w, u_k >^2 ,        u_k = Jw[:,k] / || Jw[:,k] ||,

where `z_w` is the observation in units of its own noise and `Jw` the whitened
Jacobian. The twin supplies `Jw`. The truth supplies `z_w`. This module asks how
an error in the twin propagates into the certificate, and proves four results.

Throughout, `rho` is the true whitened signal norm, `S` the number of
observables, `q = q_{1-alpha}(S-1)` the test threshold, and the folded angle

    d(u, v) = arccos | < u, v > |      in [0, pi/2]

is the angle between the lines spanned by `u` and `v`.

Theorem 1, magnitude invariance
-------------------------------
`R_k` depends on the column `Jw[:,k]` only through its direction `u_k`.
Replacing `Jw[:,k]` by `a_k Jw[:,k]` for any nonzero `a_k`, positive or
negative, leaves `u_k` unchanged up to sign and `< z_w, u_k >^2` unchanged, so
every residual, every certificate and every coverage probability is unchanged.

Proof: the residual formula contains `u_k` only inside a square. []

Consequence for the twin: an error in the *size* of a fault's effect, however
large, costs the certificate nothing. Only the *direction* of the effect is
diagnostic. In the coupling constants this separates sharply: `c_geo` multiplies
the geometry fault's only channel, so it scales a column and is free, while the
layer fault reaches two channels with weights `c_A + c_H` and `c_k`, so their
ratio rotates the layer column and is not free.

The same holds for the exact profile certificate whenever the twin's response
curve is a reparameterisation of the true one, `g_twin(f) = g_true(a f)`: the
minimum over `f` is the same minimum. It does not hold for a general nonlinear
magnitude error, which also bends the curve; that case is measured, not proved.

Theorem 2, coverage under directional error
-------------------------------------------
Let the true cause be `k`, its true whitened direction `u`, and the twin's
direction for it `v`, with `d(u, v) = delta`. Suppose the twin's noise model is
correct, so twin and truth share the whitened space, and the observation is
linear and Gaussian, `z_w = rho u + e`, `e ~ N(0, I_S)`. Then the twin's residual
for the true cause is

    R = || P_v^perp z_w ||^2 ,   P_v^perp = I - v v^T ,

and `P_v^perp z_w = rho P_v^perp u + P_v^perp e`. The noise term is standard
normal on the `S - 1` dimensional complement of `v`; the signal term is a fixed
vector in that complement of squared length `rho^2 || P_v^perp u ||^2 =
rho^2 sin^2 delta`. A standard normal vector in `m` dimensions plus a fixed
offset of squared length `lambda` has squared norm distributed as the noncentral
chi-squared on `m` degrees of freedom with noncentrality `lambda`, so

    R ~ chi^2_{S-1}( lambda = rho^2 sin^2 delta ),

exactly, and the nominal `1 - alpha` certificate covers the true cause with
probability

    c(delta, rho) = P( chi^2_{S-1}(rho^2 sin^2 delta) <= q_{1-alpha}(S-1) ). []

At `delta = 0` this is `1 - alpha`. It falls monotonically as `rho sin delta`
grows, and depends on the twin's error and the signal only through that product.

Corollary, the admissible error shrinks as 1/rho
------------------------------------------------
Fix a coverage target `c* < 1 - alpha`. Let `lambda*` solve
`P(chi^2_{S-1}(lambda*) <= q) = c*`; it depends on `S`, `alpha` and `c*` but not
on `rho`. The largest directional error the twin may have is then

    delta_max(rho) = arcsin( sqrt(lambda*) / rho ) ~ sqrt(lambda*) / rho .

A twin adequate for diagnosing a weak fault is inadequate for a strong fault of
the same type. The intuition is that a strong signal points precisely, so a twin
pointing slightly wrong misses it by a large residual. This is the mechanism by
which the linearised certificate failed at high signal in the certificate paper:
the tangent is a twin with a directional error that grows with magnitude.

Proposition 3, verdict stability
--------------------------------
`d` is a metric on lines: for lines `L1, L2, L3`, choose the representative of
`L2` closest to `L1` and then the representative of `L3` closest to that; the
spherical triangle inequality holds for the chosen vectors and folding can only
shorten the left side. So for faults `k, l` with twin directions off by
`delta_k, delta_l`,

    | theta_kl(twin) - theta_kl(truth) | <= delta_k + delta_l .

A pairwise separability verdict at floor `theta_0` is therefore guaranteed to
agree between twin and truth whenever `| theta_kl(truth) - theta_0 | >
delta_k + delta_l`. The bound is tight: equality is attained when the three
errors lie in one plane and act in the same rotational sense. []

Proposition 4, noise-model misspecification
-------------------------------------------
Suppose instead the twin's Jacobian is right but its noise model is not: it
whitens with `sigma_twin` while the truth has `sigma_true`. Write
`D = diag(sigma_true / sigma_twin)`. The twin's observation is then
`D (rho u + e)` and its direction for the true cause is `D u / || D u ||`, which
is parallel to the signal, so **no signal leaks into the residual**:

    R = e^T D P^perp D e ,      P^perp the projection off  D u ,

a generalised chi-squared variable, `sum_i lambda_i chi^2_1`, with `lambda_i`
the `S - 1` nonzero eigenvalues of `D P^perp D`. Its distribution does not
involve `rho`. Two consequences:

- a common error `D = c I` gives `R ~ c^2 chi^2_{S-1}` and coverage
  `F_{chi^2_{S-1}}(q / c^2)`. Underestimating the noise (`c > 1`) loses
  coverage; overestimating it is conservative. The common level `eps` that the
  certificate paper had to fix by convention is therefore not free: it must not
  be set below the true noise.
- per-sensor ratio errors distort coverage by a fixed amount independent of the
  signal, and separately rotate the whitened directions, which changes the
  pairwise angles and so the certificate's size, not its coverage.

The contrast with Theorem 2 is the useful part: **errors in the fault model cost
more as the signal grows; errors in the noise model cost a fixed amount.**

Proposition 5, how build context carries a twin's error
-------------------------------------------------------
In the build-context regime of the certificate paper, column `k` of the enlarged
Jacobian is the Kronecker product `J[:,k] kron B[:,k]`, and its whitener is
`diag(sigma)^-1 kron L_G^-1`, itself a Kronecker product. So the whitened column
is `u_k kron b_k` with `u_k` the instantaneous whitened direction and
`b_k = L_G^-1 B[:,k]` the whitened profile loading. For unit vectors,
`< u kron b, v kron b' > = < u, v > < b, b' >`, so a twin whose instantaneous
direction is off by `delta_J` and whose profile is off by `delta_B` has, in build
context,

    cos delta_big = cos delta_J  cos delta_B .

With the profiles right, `delta_big = delta_J` exactly: build context neither
amplifies nor attenuates an error in the thermal twin. []

The consequence is not that build context is indifferent to twin error. At a
fixed fault magnitude its whitened signature is longer by `|| b_k ||`, the norm
of the whitened profile loading, which is 9.3 to 11.5 in this plan, and Theorem
2 charges directional error in proportion to `rho`. So at matched fault severity
build context needs a twin several times more accurate than the instantaneous
suite does, despite tolerating more error at matched `rho`. The resolving power
and the fidelity demand come from the same source.

Proposition 6, measuring a direction instead of modelling it
------------------------------------------------------------
Theorem 1 says the certificate needs only each fault's direction. For a fault
that can be commanded on a healthy machine (a power step, a speed step, a
change of layer thickness) that direction can be measured rather than taken
from the twin. Command the step `N` times, each giving a whitened response
`y_i = rho_c u + e_i` with `e_i ~ N(0, I_S)`, and use the direction of the mean,
`v = ybar / || ybar ||`. Scaling the mean by `sqrt(N)` gives `lambda u + z` with
`lambda = rho_c sqrt(N)` and `z ~ N(0, I_S)`, so the estimated direction's error
satisfies, exactly,

    sin^2 delta_hat = W / ( W + (lambda + z_1)^2 ),
    W ~ chi^2_{S-1},  z_1 ~ N(0, 1),  independent.

A later fault of whitened strength `rho` is then certified with coverage

    C(rho, lambda) = E[ F_{chi^2_{S-1}( rho^2 sin^2 delta_hat )}( q ) ],

the average of Theorem 2 over the estimation error. For large `lambda`,
`rho^2 sin^2 delta_hat -> (rho / lambda)^2 W`, so coverage depends on the ratio
`kappa = rho / lambda` alone, and holding it at a target needs

    N  >=  ( rho / (kappa* rho_c) )^2 ,

with `kappa*` a constant fixed by `S` and the target. When the commanded step is
as strong as the fault to be diagnosed, `rho_c = rho`, the number of repeats is
`1 / kappa*^2` **whatever the signal strength**. Unlike a modelled direction,
whose error is fixed and whose cost grows with `rho` (Corollary), a measured
direction's error shrinks with the same signal that makes it expensive. []

This is the constructive counterpart of the paper's negative result. Validation
against healthy-build geometry cannot pin the directions down (the study); a
handful of commanded steps can, for the faults that can be commanded. Faults
that cannot (an overhang, a gas-flow failure that cannot be safely induced)
still need the twin, and for them the Corollary's budget is the requirement.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import integrate, optimize
from scipy.stats import chi2, ncx2

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE.parent / "certificate"))

__all__ = ["folded_angle", "unit_columns", "residuals", "coverage_directional",
           "noncentrality_for_coverage", "delta_max", "verdict_margin",
           "generalised_chi2_cdf", "coverage_noise_model",
           "kron_direction_error", "matched_severity_budget",
           "commanded_coverage", "kappa_star", "commanded_repeats", "ALPHA"]

ALPHA = 0.05


# ---------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------
def folded_angle(u, v) -> float:
    """Angle in degrees between the lines spanned by `u` and `v`, in [0, 90]."""
    u = np.asarray(u, float).ravel()
    v = np.asarray(v, float).ravel()
    c = abs(float(u @ v)) / (np.linalg.norm(u) * np.linalg.norm(v))
    return float(np.degrees(np.arccos(min(1.0, c))))


def unit_columns(Jw: np.ndarray) -> np.ndarray:
    """Columns of `Jw` normalised to unit length."""
    Jw = np.asarray(Jw, float)
    return Jw / np.linalg.norm(Jw, axis=0)


def residuals(Zw: np.ndarray, Jw: np.ndarray) -> np.ndarray:
    """Profile residual of each observation (rows) against each column of `Jw`."""
    Zw = np.atleast_2d(np.asarray(Zw, float))
    U = unit_columns(Jw)
    total = (Zw * Zw).sum(1)
    proj = Zw @ U
    return np.maximum(total[:, None] - proj ** 2, 0.0)


# ---------------------------------------------------------------------------
# Theorem 2 and its corollary
# ---------------------------------------------------------------------------
def coverage_directional(delta_deg, rho, S: int, alpha: float = ALPHA):
    """P(chi^2_{S-1}(rho^2 sin^2 delta) <= q): Theorem 2, exact."""
    q = chi2.ppf(1.0 - alpha, S - 1)
    lam = (np.asarray(rho, float) * np.sin(np.radians(delta_deg))) ** 2
    lam = np.asarray(lam, float)
    out = np.where(lam <= 0, chi2.cdf(q, S - 1),
                   ncx2.cdf(q, S - 1, np.maximum(lam, 1e-300)))
    return out if out.ndim else float(out)


def noncentrality_for_coverage(target: float, S: int,
                               alpha: float = ALPHA) -> float:
    """The noncentrality at which coverage falls to `target`; independent of rho."""
    q = chi2.ppf(1.0 - alpha, S - 1)
    if target >= chi2.cdf(q, S - 1):
        return 0.0
    return float(optimize.brentq(lambda lam: ncx2.cdf(q, S - 1, lam) - target,
                                 1e-12, 1e4, xtol=1e-12))


def delta_max(rho, S: int, target: float = 0.90, alpha: float = ALPHA):
    """Largest directional error in degrees keeping coverage at `target`."""
    lam = noncentrality_for_coverage(target, S, alpha)
    s = np.sqrt(lam) / np.asarray(rho, float)
    out = np.degrees(np.arcsin(np.minimum(1.0, s)))
    return out if np.ndim(out) else float(out)


# ---------------------------------------------------------------------------
# Proposition 3
# ---------------------------------------------------------------------------
def verdict_margin(theta_truth: float, floor: float = 10.0) -> float:
    """How far a pair's angle sits from the floor; the bound on delta_k+delta_l."""
    return abs(float(theta_truth) - floor)


# ---------------------------------------------------------------------------
# Proposition 4
# ---------------------------------------------------------------------------
def generalised_chi2_cdf(x: float, weights) -> float:
    """P( sum_i w_i chi^2_1 <= x ) for positive weights, by Imhof's formula.

    Imhof (1961): for Q = sum_i w_i chi^2_1,

        P(Q > x) = 1/2 + (1/pi) int_0^inf  sin theta(t) / (t rho(t))  dt,
        theta(t) = 1/2 sum_i arctan(w_i t) - x t / 2,
        rho(t)   = prod_i (1 + w_i^2 t^2)^(1/4).

    Checked against Monte Carlo in `verify.py` and against the scalar case,
    where all weights equal `c` and the answer is F_{chi^2_m}(x / c).
    """
    w = np.asarray(weights, float)
    w = w[w > 1e-14]
    if w.size == 0:
        return 1.0

    def A(t):
        return 0.5 * np.sum(np.arctan(w * t))

    def envelope(t):
        return 1.0 / (t * np.prod((1.0 + (w * t) ** 2) ** 0.25))

    def integrand(t):
        if t == 0.0:
            return 0.5 * (float(w.sum()) - x)
        return np.sin(A(t) - 0.5 * x * t) * envelope(t)

    # The integrand oscillates at frequency x/2 under an envelope that decays
    # only as t^-(1 + m/2), so a general-purpose rule over [0, inf) runs out of
    # subdivisions for m = 2 (an earlier version did, and was off by 4e-6). On
    # the tail the oscillation is split out exactly,
    #     sin(A - wt) = sin A cos wt - cos A sin wt ,   w = x/2 ,
    # leaving slowly varying factors for QUADPACK's Fourier-integral routine,
    # which is built for precisely this infinite oscillatory range.
    a = 1.0
    head, _ = integrate.quad(integrand, 0.0, a, limit=200)
    om = 0.5 * x
    t1, _ = integrate.quad(lambda t: np.sin(A(t)) * envelope(t), a, np.inf,
                           weight="cos", wvar=om, limlst=200)
    t2, _ = integrate.quad(lambda t: np.cos(A(t)) * envelope(t), a, np.inf,
                           weight="sin", wvar=om, limlst=200)
    val = head + t1 - t2
    return float(1.0 - (0.5 + val / np.pi))


def coverage_noise_model(u: np.ndarray, sigma_true, sigma_twin,
                         alpha: float = ALPHA) -> float:
    """Coverage for the true cause when the twin whitens with the wrong noise.

    `u` is the true cause's direction in the TRUE whitened space. Proposition 4:
    the residual is e^T D P D e with D = diag(sigma_true/sigma_twin) and P the
    projection off D u; coverage is the generalised chi-square CDF at q.
    """
    u = np.asarray(u, float).ravel()
    D = np.diag(np.asarray(sigma_true, float) / np.asarray(sigma_twin, float))
    v = D @ u
    v = v / np.linalg.norm(v)
    P = np.eye(len(u)) - np.outer(v, v)
    lam = np.linalg.eigvalsh(D @ P @ D)
    q = chi2.ppf(1.0 - alpha, len(u) - 1)
    return generalised_chi2_cdf(q, lam)


# ---------------------------------------------------------------------------
# Proposition 5
# ---------------------------------------------------------------------------
def kron_direction_error(delta_J_deg, delta_B_deg):
    """Build-context directional error from its instantaneous and profile parts."""
    c = np.cos(np.radians(delta_J_deg)) * np.cos(np.radians(delta_B_deg))
    return np.degrees(np.arccos(np.clip(c, -1.0, 1.0)))


def matched_severity_budget(rho_inst: float, gain: float, target: float = 0.90,
                            S_inst: int = 3, S_big: int = 15) -> tuple[float, float]:
    """delta_max instantaneously and with build context, at one fault magnitude.

    `gain` is the ratio of build-context to instantaneous whitened signature
    norm for the fault, so the same magnitude gives `rho_big = gain * rho_inst`.
    """
    return (float(delta_max(rho_inst, S_inst, target)),
            float(delta_max(gain * rho_inst, S_big, target)))


# ---------------------------------------------------------------------------
# Proposition 6
# ---------------------------------------------------------------------------
def _w_nodes(S: int, n: int = 400):
    """Equal-probability nodes of chi^2_{S-1}: midpoints of n quantile bins."""
    p = (np.arange(n) + 0.5) / n
    return chi2.ppf(p, S - 1)


def commanded_coverage(rho: float, lam: float, S: int, alpha: float = ALPHA,
                       n_w: int = 400, n_z: int = 80) -> float:
    """Coverage at signal `rho` with a direction measured at strength `lam`.

    `lam = rho_c sqrt(N)`. Exact up to quadrature: Gauss-Hermite in `z_1`,
    equal-probability nodes in `W`.
    """
    q = chi2.ppf(1.0 - alpha, S - 1)
    W = _w_nodes(S, n_w)
    x, w = np.polynomial.hermite_e.hermegauss(n_z)
    w = w / w.sum()
    z = x[:, None]
    s2 = W[None, :] / (W[None, :] + (lam + z) ** 2)
    F = ncx2.cdf(q, S - 1, rho ** 2 * s2)
    return float((w[:, None] * F).sum() / W.size)


def kappa_star(S: int, target: float = 0.90, alpha: float = ALPHA) -> float:
    """Large-lambda ratio rho / lambda at which coverage falls to `target`."""
    q = chi2.ppf(1.0 - alpha, S - 1)
    W = _w_nodes(S, 2000)
    f = lambda k: float(ncx2.cdf(q, S - 1, k ** 2 * W).mean()) - target
    return float(optimize.brentq(f, 1e-6, 10.0))


def commanded_repeats(rho: float, rho_c: float, S: int, target: float = 0.90,
                      n_max: int = 100000) -> int:
    """Smallest number of commanded steps keeping coverage at `target`, exact."""
    lo, hi = 1, 1
    while commanded_coverage(rho, rho_c * np.sqrt(hi), S) < target:
        hi *= 2
        if hi > n_max:
            return -1
    while lo < hi:
        mid = (lo + hi) // 2
        if commanded_coverage(rho, rho_c * np.sqrt(mid), S) >= target:
            hi = mid
        else:
            lo = mid + 1
    return lo


def report() -> None:
    print("Fidelity theory: what a twin must get right")
    print("=" * 74)
    for S in (3, 15):
        print(f"\nS = {S} observables (dof {S - 1})")
        for target in (0.90, 0.80):
            lam = noncentrality_for_coverage(target, S)
            print(f"   coverage target {target:.2f}: noncentrality {lam:.4f}")
            print("      rho      delta_max (deg)")
            for rho in (14, 28, 56, 120):
                print(f"      {rho:5d}    {delta_max(rho, S, target):8.3f}")
    print("\nCoverage of the 95 % certificate against a common noise error c")
    print("   (c > 1 means the twin underestimates the noise)")
    for c in (0.8, 0.9, 1.0, 1.1, 1.25, 1.5):
        q = chi2.ppf(0.95, 2)
        print(f"   c = {c:4.2f}   coverage {chi2.cdf(q / c ** 2, 2):.4f}")
    print("\nMeasuring a direction by commanded steps (Proposition 6)")
    for S in (3, 15):
        k = kappa_star(S)
        print(f"   S = {S}: kappa* = {k:.4f}; at rho_c = rho, N >= {1 / k ** 2:.1f}")
        for rho in (14, 28, 56, 120):
            print(f"      rho {rho:4d}: exact N = {commanded_repeats(rho, rho, S)}")


if __name__ == "__main__":
    report()
