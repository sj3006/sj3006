"""Analytical LPBF simulator: Rosenthal melt pool + standard defect criteria.

This replaces the toy logistic model in synthetic.py with physics. It is
cheap (milliseconds per setting) and deliberately imperfect, which is what we
want from the "simulator" in the paper.

Melt pool (Rosenthal 1946, moving point source on a semi-infinite body).
In the frame moving with the laser (xi = x - v t),

    T(xi, y, z) = T0 + A P / (2 pi k R) * exp(-v (xi + R) / (2 kappa)),
    R = sqrt(xi^2 + y^2 + z^2),   kappa = k / (rho c).

The melt pool is where T >= Tm. Rosenthal pools are half-spheroids, so depth
D = W / 2. We compute width W and length L numerically.

Defect criteria, each turned into a probability with a logistic link:

- lack of fusion (Tang, Pistorius & Beuth 2017): tracks fully overlap when
  (h / W)^2 + (t / D)^2 <= 1, with hatch spacing h and layer thickness t.
- keyhole (King et al. 2014): normalized enthalpy
  dH / h_s = A P / (pi h_s sqrt(kappa v sigma^3)), with h_s = rho c Tm and
  beam radius sigma. Keyholing above roughly 30.
- balling (Plateau-Rayleigh instability): L / W above about pi.

Rosenthal ignores latent heat, convection and vaporization, so absolute
numbers are rough. The monotone DIRECTIONS are what matter for the method,
and check_monotone_directions() verifies them numerically instead of
assuming them.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class Material:
    name: str
    k: float        # thermal conductivity, W/(m K)
    rho: float      # density, kg/m^3
    c: float        # specific heat, J/(kg K)
    Tm: float       # melting temperature, K
    A: float        # laser absorptivity

    @property
    def kappa(self):
        return self.k / (self.rho * self.c)


# Typical handbook-level values; refine per powder lot in Phase 2.
SS316L = Material("316L", k=20.0, rho=7900.0, c=500.0, Tm=1700.0, A=0.35)
TI64 = Material("Ti-6Al-4V", k=7.0, rho=4430.0, c=560.0, Tm=1923.0, A=0.35)


@dataclass
class Machine:
    sigma: float = 50e-6     # beam radius, m
    hatch: float = 100e-6    # hatch spacing, m
    layer: float = 30e-6     # layer thickness, m
    T0: float = 300.0        # preheat / ambient, K


def melt_pool(power, speed, mat=SS316L, T0=300.0, n_xi=400):
    """Width, depth and length (m) of the Rosenthal melt pool.

    power in W and speed in m/s, broadcastable arrays.
    """
    P, v = np.broadcast_arrays(np.asarray(power, float), np.asarray(speed, float))
    a = np.log(mat.A * P / (2 * np.pi * mat.k * (mat.Tm - T0)))   # ln of length scale
    kap = mat.kappa
    # Melted points satisfy g(xi, R) = a - ln R - v (xi + R) / (2 kappa) >= 0.
    # Along y = z = 0 (R = |xi|): the front is at xi > 0 with a - ln xi - v xi / kappa = 0,
    # the tail at xi < 0 with a - ln(-xi) = 0, i.e. xi = -exp(a).
    tail = -np.exp(a)
    front = _solve_decreasing(lambda x: a - np.log(x) - v * x / kap, 1e-9, np.exp(a))
    length = front - tail
    # Width: maximize over xi the largest R with g >= 0, then y = sqrt(R^2 - xi^2).
    best = np.zeros_like(P)
    for f in np.linspace(0.0, 1.0, n_xi):
        xi = tail + f * (front - tail)
        R = _solve_decreasing(lambda r: a - np.log(r) - v * (xi + r) / (2 * kap),
                              np.maximum(np.abs(xi), 1e-12), np.exp(a) * 2 + 1e-9)
        y2 = np.maximum(R ** 2 - xi ** 2, 0.0)
        best = np.maximum(best, y2)
    width = 2 * np.sqrt(best)
    return width, width / 2, length


def _solve_decreasing(f, lo, hi, iters=60):
    """Largest x in [lo, hi] with f(x) >= 0, for f decreasing in x (vectorized)."""
    lo = np.array(lo, dtype=float) * np.ones_like(np.asarray(f(np.asarray(lo, float))))
    hi = np.array(hi, dtype=float) * np.ones_like(lo)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        ok = f(mid) >= 0
        lo = np.where(ok, mid, lo)
        hi = np.where(ok, hi, mid)
    return lo


@dataclass
class Criteria:
    """Thresholds and logistic widths that turn indices into defect rates.

    PLACEHOLDER CALIBRATION. The literature values (keyhole ~30, balling ~pi)
    assume real melt pools; with the crude Rosenthal pool they give either
    no keyholing or balling almost everywhere. These defaults were chosen so
    316L at 30 um layers has a visible window on 80-400 W x 300-2400 mm/s.
    Phase 2 refits them to experimental process maps.
    """
    lof_thresh: float = 1.0
    lof_width: float = 0.05
    kh_thresh: float = 9.0
    kh_width: float = 0.6
    ball_thresh: float = 6.5
    ball_width: float = 0.3
    floor: float = 0.002


def defect_indices(power_W, speed_mm_s, mat=SS316L, machine=Machine()):
    """Raw criterion indices on a mesh (indexing='ij', power first)."""
    P, V = np.meshgrid(np.asarray(power_W, float), np.asarray(speed_mm_s, float) * 1e-3,
                       indexing="ij")
    W, D, L = melt_pool(P, V, mat, machine.T0)
    lof = (machine.hatch / W) ** 2 + (machine.layer / D) ** 2
    h_s = mat.rho * mat.c * mat.Tm
    kh = mat.A * P / (np.pi * h_s * np.sqrt(mat.kappa * V * machine.sigma ** 3))
    ball = L / W
    return {"lof": lof, "keyhole": kh, "balling": ball, "W": W, "D": D, "L": L}


def defect_rates(power_W, speed_mm_s, mat=SS316L, machine=Machine(), crit=Criteria()):
    idx = defect_indices(power_W, speed_mm_s, mat, machine)
    sig = lambda z: 1.0 / (1.0 + np.exp(-z))  # noqa: E731
    raw = {
        "lof": sig((idx["lof"] - crit.lof_thresh) / crit.lof_width),
        "keyhole": sig((idx["keyhole"] - crit.kh_thresh) / crit.kh_width),
        "balling": sig((idx["balling"] - crit.ball_thresh) / crit.ball_width),
    }
    return {m: crit.floor + (1 - crit.floor) * r for m, r in raw.items()}


def check_monotone_directions(rates):
    """For each mode, the sign of the change along power and along speed.

    Returns mode -> (sign_power, sign_speed, fraction_consistent), where a
    sign of +1 means the defect rate increases with that parameter. Assumption
    A needs fraction_consistent == 1.0 (up to numerical noise).
    """
    out = {}
    for m, r in rates.items():
        dp, dv = np.diff(r, axis=0), np.diff(r, axis=1)
        sp = np.sign(np.median(dp[np.abs(dp) > 1e-9])) if np.any(np.abs(dp) > 1e-9) else 0.0
        sv = np.sign(np.median(dv[np.abs(dv) > 1e-9])) if np.any(np.abs(dv) > 1e-9) else 0.0
        tol = 1e-6
        ok_p = np.mean(dp * sp >= -tol) if sp else 1.0
        ok_v = np.mean(dv * sv >= -tol) if sv else 1.0
        out[m] = (int(sp), int(sv), float(min(ok_p, ok_v)))
    return out


# Simulator errors relative to the "true" physics: absorptivity and
# criterion-threshold misspecification, the two biggest real-world unknowns.
PHYSICS_ERRORS = {
    "good": dict(dA=+0.01, lof=-0.03, kh=+0.3, ball=+0.2),
    "biased": dict(dA=+0.05, lof=-0.15, kh=+1.5, ball=+1.0),       # optimistic
    "pessimistic": dict(dA=-0.04, lof=+0.15, kh=-1.0, ball=-0.8),
}


def make_physics_scenario(n_power=16, n_speed=16, eps=0.05, simulator="good",
                          mat=SS316L, machine=Machine(), power=(80.0, 400.0),
                          speed=(300.0, 2400.0)):
    """Scenario whose truth and simulator both come from the physics model.

    The simulator differs from the truth by PHYSICS_ERRORS[simulator]
    (wrong absorptivity, wrong criterion thresholds), or is "none" / an
    "adversarial" flat 0.1% prediction. Monotone directions are measured
    from the truth, not assumed.
    """
    from dataclasses import replace

    from .synthetic import MODES, Scenario

    P = np.linspace(*power, n_power)
    V = np.linspace(*speed, n_speed)
    truth = defect_rates(P, V, mat, machine)
    dirs = {}
    for m, (sp, sv, frac) in check_monotone_directions(truth).items():
        if frac < 1.0:
            raise ValueError(f"truth is not monotone for {m} (consistent fraction {frac:.3f})")
        dirs[m] = (-sp, -sv)            # safer = opposite of the direction rates increase
    if simulator == "none":
        sim = {m: np.full_like(truth[m], eps) for m in MODES}
    elif simulator == "adversarial":
        sim = {m: np.full_like(truth[m], 0.001) for m in MODES}
    else:
        e = PHYSICS_ERRORS[simulator]
        c0 = Criteria()
        crit = Criteria(lof_thresh=c0.lof_thresh - e["lof"], kh_thresh=c0.kh_thresh + e["kh"],
                        ball_thresh=c0.ball_thresh + e["ball"])
        sim = defect_rates(P, V, replace(mat, A=mat.A + e["dA"]), machine, crit)
    return Scenario(P, V, {m: eps for m in MODES}, truth, sim,
                    name=f"physics-{mat.name}/{simulator}", directions=dirs)
