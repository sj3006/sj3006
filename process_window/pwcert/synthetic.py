"""Toy LPBF-like ground truth and simulators for week-1 experiments.

These are placeholders with the right *shape*, not fitted to any material.
Phase 2 replaces them with a ground truth fitted to process-map data and an
analytical melt-pool simulator.

Each failure mode is a logistic curve in one physical driver, chosen so the
monotone directions match the physics:

- lack of fusion (LoF): driven by volumetric energy density
  VED = P / (v h t). Less energy -> more LoF. Decreasing in P, increasing in v.
- keyhole (KH): driven by P / sqrt(v), a common proxy for normalized enthalpy.
  Increasing in P, decreasing in v.
- balling (BALL): driven by v / P (long, thin melt tracks break up).
  Increasing in v, decreasing in P.
"""

from dataclasses import dataclass, field

import numpy as np

MODES = ("lof", "keyhole", "balling")

# Monotone directions on the (power, speed) grid, written as the sign of the
# index step that makes a mode SAFER. (+1, -1) means "safer at higher power and
# lower speed".
SAFER_DIRECTION = {
    "lof": (+1, -1),
    "keyhole": (-1, +1),
    "balling": (+1, -1),
}


@dataclass
class LPBFModel:
    """Logistic defect-rate model. Thresholds set where each rate is ~50%."""
    ved_lof: float = 50.0      # J/mm^3
    w_lof: float = 6.0
    kh_index: float = 10.0     # W / sqrt(mm/s)
    w_kh: float = 0.6
    ball_ratio: float = 9.0    # (mm/s) / W
    w_ball: float = 0.8
    hatch_mm: float = 0.1
    layer_mm: float = 0.03
    floor: float = 0.002       # background defect rate in every mode

    def rates(self, power, speed):
        """Defect rate per mode on a mesh. Returns dict mode -> array."""
        P, V = np.meshgrid(power, speed, indexing="ij")
        ved = P / (V * self.hatch_mm * self.layer_mm)
        raw = {
            "lof": _sigmoid((self.ved_lof - ved) / self.w_lof),
            "keyhole": _sigmoid((P / np.sqrt(V) - self.kh_index) / self.w_kh),
            "balling": _sigmoid((V / P - self.ball_ratio) / self.w_ball),
        }
        return {m: self.floor + (1 - self.floor) * r for m, r in raw.items()}


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


@dataclass
class Scenario:
    """Grid, thresholds, ground truth and a simulator, all in one place."""
    power: np.ndarray
    speed: np.ndarray
    eps: dict
    truth: dict          # mode -> (nP, nV) true defect rates
    sim: dict            # mode -> (nP, nV) simulator-predicted rates
    name: str = ""
    meta: dict = field(default_factory=dict)
    # mode -> (sign, sign): index step along (power, speed) that makes the
    # mode SAFER. Must match the physics of the ground truth (Assumption A).
    directions: dict = field(default_factory=lambda: dict(SAFER_DIRECTION))

    def true_window(self):
        ok = np.ones_like(self.truth[MODES[0]], dtype=bool)
        for m in MODES:
            ok &= self.truth[m] < self.eps[m]   # null is p >= eps
        return ok


# Ground-truth shapes. "wide" has window area well above its boundary length
# (where monotone spreading should pay off); "thin" is a narrow diagonal band
# where area ~ boundary (the hard case).
WINDOWS = {
    "wide": dict(ved_lof=38.0, w_lof=4.0, kh_index=12.0, w_kh=0.5,
                 ball_ratio=11.0, w_ball=0.8),
    "thin": dict(),
}

# Simulator errors, as shifts of the ground-truth thresholds.
SIMULATORS = {
    # Same physics, slightly shifted thresholds.
    "good": dict(ved_lof=-2.0, kh_index=+0.3, ball_ratio=+0.3),
    # Optimistic: says the window is much bigger than it is.
    "biased": dict(ved_lof=-10.0, kh_index=+1.5, ball_ratio=+1.5),
    # Pessimistic: says the window is much smaller than it is.
    "pessimistic": dict(ved_lof=+10.0, kh_index=-1.0, ball_ratio=-1.5),
}


def make_scenario(n_power=12, n_speed=12, eps=0.05, simulator="good", window="wide"):
    """Build a toy scenario.

    simulator: one of SIMULATORS, "none" (flat prior at eps), or
    "adversarial" (claims every setting has a 0.1% defect rate).
    window: one of WINDOWS.
    """
    power = np.linspace(120.0, 380.0, n_power)
    speed = np.linspace(400.0, 2000.0, n_speed)
    base = LPBFModel(**WINDOWS[window])
    truth = base.rates(power, speed)
    eps_d = {m: eps for m in MODES}
    if simulator == "none":
        sim = {m: np.full_like(truth[m], eps) for m in MODES}
    elif simulator == "adversarial":
        sim = {m: np.full_like(truth[m], 0.001) for m in MODES}
    else:
        params = {k: getattr(base, k) + d for k, d in SIMULATORS[simulator].items()}
        sim = LPBFModel(**{**WINDOWS[window], **params}).rates(power, speed)
    return Scenario(power, speed, eps_d, truth, sim, name=f"{window}/{simulator}")
