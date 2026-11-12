"""No simulator? Learn one from a pilot plate.

Build per_point coupons at every stride-th setting along both axes, fit a
monotone surface to the observed defect rates for each failure mode (2D
isotonic regression in the mode's risk directions), and use that surface as
the "simulator" for weights, allocation and priors.

The pilot coupons are never fed to the e-processes, so the certificates
remain valid (data splitting: the weights are fixed given the pilot, and the
test data are fresh). Their cost is counted.
"""

import numpy as np

from .certify import _isotonic_2d
from .synthetic import Scenario


def pilot_simulator(sc, rng, per_point=4, stride=2, prior_strength=0.5):
    """Return (scenario with sim replaced by the pilot fit, pilot coupons)."""
    modes = sc.modes
    shape = sc.truth[modes[0]].shape
    mask = np.zeros(shape, dtype=bool)
    mask[stride // 2::stride, stride // 2::stride] = True
    coupons = int(mask.sum()) * per_point
    fitted = {}
    for m in modes:
        k = np.zeros(shape)
        k[mask] = rng.binomial(per_point, sc.truth[m][mask])
        # Fit raw proportions so that blocks of clean settings pool their
        # counts (a single setting with 0/4 defects says little; twenty
        # neighbouring ones do). Unobserved settings: a weak neutral guess
        # (eps) that the monotone fit can override.
        z = np.where(mask, k / per_point, sc.eps[m])
        w = np.where(mask, float(per_point), prior_strength)
        d_p, d_v = sc.directions[m]
        f = _isotonic_2d(z, w, -d_p, -d_v, iters=6)
        # Alternating projections are only approximately monotone; a running
        # maximum toward risk on each axis makes the fit exactly monotone
        # (and slightly conservative).
        f = f[::-d_p, ::-d_v]
        f = np.maximum.accumulate(np.maximum.accumulate(f, axis=0), axis=1)[::-d_p, ::-d_v]
        fitted[m] = np.clip(f, 1e-3, 1 - 1e-3)
    new = Scenario(sc.power, sc.speed, sc.eps, sc.truth, fitted,
                   name=sc.name + "+pilot", meta=dict(sc.meta, pilot_coupons=coupons),
                   directions=sc.directions)
    return new, coupons
