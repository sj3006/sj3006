"""Why the keyhole correction is necessary, not optional (paper Section 3.1).

The forward model is the Eagar-Tsai conduction solution plus the
Gladush-Smurov keyhole depth term of Honarmandi et al. The paper claims the
second part is necessary rather than cosmetic, on two grounds: every benchmark
condition satisfies Honarmandi's keyholing criterion, and a pure conduction fit
of the same data is much worse on depth.

This module computes both, and it reports the conduction-only fit at the *same*
degrees of freedom as the adopted fit - absorptivity, conductivity and heat
capacity, over the same bounds - because that is the like-for-like comparison. A
one-parameter fit with uncalibrated properties is also reported, since it is
what an earlier draft quoted, and it flatters the argument by failing worse.

Aspect-ratio convention
-----------------------
Two conventions are in use in this literature and they differ by a factor of
two. Honarmandi's keyholing criterion is `depth >= width / 1.5`, i.e. a
depth-to-width ratio of at least 0.667. Depth-to-*half*-width is the other
convention, twice as large. Both are reported here so a quoted range cannot be
read against the wrong criterion; the paper quotes depth-to-width.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, str(Path(__file__).parent))

from calibrate import BOUNDS_HI, BOUNDS_LO, START, WEAVER_POINTS, _material, fit
from eagar_tsai import (Beam, Material, is_keyholing, melt_pool_dimensions,
                        sigma_from_spot_diameter)

__all__ = ["PROVISIONAL", "aspect_ratios", "conduction_only_fit",
           "historical_one_parameter_fit", "report"]

# The uncalibrated "literature-typical" IN718 properties the project started
# from, kept only to reproduce the figure an earlier draft quoted.
PROVISIONAL = Material("IN718 (provisional, uncalibrated)", 8190.0, 650.0, 30.0,
                       1533.0, 1609.0, 293.0, 3190.0)


def _geom(point, absorptivity: float, material: Material) -> dict[str, float]:
    beam = Beam(point.power, point.speed,
                sigma_from_spot_diameter(point.spot_diameter), absorptivity)
    return melt_pool_dimensions(beam, material)


def aspect_ratios() -> dict:
    """Measured aspect ratios of the seven benchmark single tracks."""
    dw = np.array([p.depth / p.width for p in WEAVER_POINTS])
    return {
        "depth_over_width": dw,
        "depth_over_width_range": (float(dw.min()), float(dw.max())),
        "depth_over_half_width_range": (float(2 * dw.min()), float(2 * dw.max())),
        "criterion_depth_over_width": 1.0 / 1.5,
        "n_keyholing": int(sum(is_keyholing(p.width, p.depth)
                               for p in WEAVER_POINTS)),
        "n_conditions": len(WEAVER_POINTS),
    }


def _mape(absorptivity, material, use_corrected=False, C=None):
    w, d = [], []
    for p in WEAVER_POINTS:
        g = _geom(p, absorptivity, material)
        w.append(abs(g["width"] - p.width) / p.width)
        d.append(abs(g["depth"] - p.depth) / p.depth)
    return 100 * float(np.mean(w)), 100 * float(np.mean(d))


def conduction_only_fit() -> dict:
    """Fit absorptivity, conductivity and heat capacity with no keyhole term.

    Same three parameters and the same bounds as the adopted fit, minus the
    keyhole factor, so the only difference between this and `calibrate.fit` is
    the depth mechanism.
    """
    def residuals(theta):
        mu, kappa, cp = (float(v) for v in theta)
        material = _material(kappa, cp)
        out = []
        for p in WEAVER_POINTS:
            g = _geom(p, mu, material)
            out.append((g["width"] - p.width) / p.width)
            out.append((g["depth"] - p.depth) / p.depth)
        return np.asarray(out)

    r = least_squares(residuals, x0=list(START[:3]),
                      bounds=(list(BOUNDS_LO[:3]), list(BOUNDS_HI[:3])),
                      xtol=1e-8, diff_step=0.03)
    mu, kappa, cp = (float(v) for v in r.x)
    wm, dm = _mape(mu, _material(kappa, cp))
    return {"absorptivity": mu, "conductivity": kappa, "heat_capacity": cp,
            "width_mape_pct": wm, "depth_mape_pct": dm,
            "at_absorptivity_bound": abs(mu - BOUNDS_HI[0]) < 1e-3}


def historical_one_parameter_fit() -> dict:
    """Conduction only, absorptivity alone, uncalibrated properties.

    This is the fit an earlier draft quoted as "pure conduction gives 27.8 %
    depth error". It is reproduced here so the figure is traceable, but it is
    not the like-for-like comparison: it holds conductivity and heat capacity at
    uncalibrated values and drives absorptivity to 0.95, which no nickel alloy
    shows at 1 um.
    """
    def residuals(a):
        mu = float(np.ravel(a)[0])
        out = []
        for p in WEAVER_POINTS:
            g = _geom(p, mu, PROVISIONAL)
            out.append((g["width"] - p.width) / p.width)
            out.append((g["depth"] - p.depth) / p.depth)
        return np.asarray(out)

    r = least_squares(residuals, x0=[0.35], bounds=([0.05], [0.95]),
                      xtol=1e-4, diff_step=0.02)
    mu = float(r.x[0])
    wm, dm = _mape(mu, PROVISIONAL)
    return {"absorptivity": mu, "width_mape_pct": wm, "depth_mape_pct": dm}


def report() -> None:
    a = aspect_ratios()
    print("IS THE KEYHOLE CORRECTION NECESSARY?\n")
    print(f"1. THE REGIME, from the measured dimensions of the "
          f"{a['n_conditions']} benchmark tracks")
    print(f"   Honarmandi's criterion: depth >= width / 1.5, i.e. a "
          f"depth-to-width ratio\n   of at least "
          f"{a['criterion_depth_over_width']:.3f}.")
    print(f"   measured depth-to-width:      "
          f"{a['depth_over_width_range'][0]:.2f} to "
          f"{a['depth_over_width_range'][1]:.2f}")
    print(f"   same in depth-to-half-width:  "
          f"{a['depth_over_half_width_range'][0]:.2f} to "
          f"{a['depth_over_half_width_range'][1]:.2f}   "
          f"(the other convention in use)")
    print(f"   conditions meeting the criterion: {a['n_keyholing']} of "
          f"{a['n_conditions']}")

    print("\n2. THE FITS, all on the same seven conditions and relative residuals")
    theta, rep = fit(WEAVER_POINTS)
    print(f"   adopted (conduction + keyhole, 4 parameters)")
    print(f"      width {rep['width_mape_pct']:5.1f} %   depth "
          f"{rep['depth_mape_pct']:5.1f} %   "
          f"mu={theta[0]:.3f} k={theta[1]:.1f} cp={theta[2]:.0f} C={theta[3]:.2f}")
    c = conduction_only_fit()
    print(f"   conduction only, same 3 free parameters, same bounds")
    print(f"      width {c['width_mape_pct']:5.1f} %   depth "
          f"{c['depth_mape_pct']:5.1f} %   "
          f"mu={c['absorptivity']:.3f} k={c['conductivity']:.1f} "
          f"cp={c['heat_capacity']:.0f}"
          f"{'   (absorptivity at its bound)' if c['at_absorptivity_bound'] else ''}")
    h = historical_one_parameter_fit()
    print(f"   conduction only, absorptivity alone, uncalibrated properties")
    print(f"      width {h['width_mape_pct']:5.1f} %   depth "
          f"{h['depth_mape_pct']:5.1f} %   mu={h['absorptivity']:.3f}"
          f"   (at its bound; what an earlier draft quoted)")
    print(f"\n   The like-for-like comparison is the middle row: "
          f"{c['depth_mape_pct']:.1f} % depth error\n   against "
          f"{rep['depth_mape_pct']:.1f} %, at the same freedom, with width "
          f"essentially unchanged\n   ({c['width_mape_pct']:.1f} % against "
          f"{rep['width_mape_pct']:.1f} %). Conduction cannot reach these "
          f"depths\n   because it has no vapour depression and no multiple "
          f"reflections.")


if __name__ == "__main__":
    report()
