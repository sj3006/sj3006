"""Gate 1: fit the single free parameter (effective absorptivity) to measured
melt pool geometry, and report the error.

Four parameters are fitted, following Honarmandi et al. (2021): absorption
efficiency, effective thermal conductivity, effective heat capacity, and the
keyhole depth correction factor C. Treating conductivity and heat capacity as
calibration parameters rather than fixed constants is their explicit
recommendation - a constant-property conduction model absorbs the physics it
omits into the properties it has.

Conductivity is bounded to a physically arguable range for IN718 near melting.
Without that bound the fit drifts to ~90 W/mK, which fits marginally better and
would be indefensible in review.

Usage
-----
Fill in `WEAVER_POINTS` with single-track measurements from

    Weaver, J.S. et al. (2024), "Cross-Sectional Melt Pool Geometry of Laser
    Scanned Tracks and Pads on Nickel Alloy 718 for the 2022 Additive
    Manufacturing Benchmark Challenges", Integrating Materials and Manufacturing
    Innovation 13, 363-379. DOI 10.1007/s40192-024-00355-5

    Honarmandi, P. et al. (2021), "A rigorous test and improvement of the
    Eagar-Tsai model for melt pool characteristics in laser powder bed fusion
    additive manufacturing", Additive Manufacturing 47, 102300.
    DOI 10.1016/j.addma.2021.102300

then run:  python3 src/calibrate.py

Gate 1 passes at roughly 15% mean absolute percentage error on width and depth.
If it fails, the same-day fallback is a simpler analytical form with wider
stated error bars - do not spend a second day on it.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, str(Path(__file__).parent))

from eagar_tsai import (Beam, Material, keyhole_depth, melt_pool_dimensions,
                        sigma_from_spot_diameter)


@dataclass(frozen=True)
class Point:
    """One measured single-track melt pool cross-section.

    Lengths in metres, power in watts, speed in m/s. Set width or depth to None
    if that dimension was not reported for this condition.
    """

    power: float
    speed: float
    spot_diameter: float
    width: float | None = None
    depth: float | None = None
    label: str = ""


# ---------------------------------------------------------------------------
# PASTE THE WEAVER SINGLE-TRACK POINTS HERE.
#
# 4-6 conditions spanning a useful range of power and speed is enough. Include
# the spot diameter actually used for each condition - Weaver varied it, and
# getting it wrong is the fastest way to a bad fit.
#
# Example of the expected form (these numbers are PLACEHOLDERS, not real data):
#     Point(power=250.0, speed=0.8, spot_diameter=100e-6,
#           width=130e-6, depth=55e-6, label="AMB2022-03 track 1"),
# ---------------------------------------------------------------------------
WEAVER_POINTS: list[Point] = [
    # Weaver et al. (2024) Table 4, single-track melt pool measurements on bare
    # IN718 plate. Mean of six measurements per case (three tracks, two cross
    # sections each). Spot size column is D4sigma; the paper states D4sigma/4 =
    # sigma, which matches `sigma_from_spot_diameter`.
    #
    # Expanded uncertainties U(k=2) from the same table, in um:
    #   case 0    width 6.2   depth 14.1
    #   case 1.1  width 5.5   depth 22.9
    #   case 1.2  width 6.0   depth 10.4
    #   case 2.1  width 4.9   depth 11.2
    #   case 2.2  width 7.7   depth 17.9
    #   case 3.1  width 6.0   depth 16.8
    #   case 3.2  width 5.5   depth 11.8
    Point(285.0, 0.960, 67e-6, 136.3e-6, 139.7e-6, "case 0 baseline"),
    Point(285.0, 0.960, 49e-6, 106.2e-6, 227.2e-6, "case 1.1 small spot"),
    Point(285.0, 0.960, 82e-6, 141.7e-6, 102.4e-6, "case 1.2 large spot"),
    Point(285.0, 1.200, 67e-6, 112.9e-6, 109.7e-6, "case 2.1 fast"),
    Point(285.0, 0.800, 67e-6, 156.1e-6, 176.5e-6, "case 2.2 slow"),
    Point(325.0, 0.960, 67e-6, 134.3e-6, 166.1e-6, "case 3.1 high power"),
    Point(245.0, 0.960, 67e-6, 129.4e-6, 116.9e-6, "case 3.2 low power"),
]


def _material(kappa: float, cp: float) -> Material:
    return Material("IN718 fitted", 8190.0, cp, kappa, 1533.0, 1609.0, 293.0, 3190.0)


# (absorptivity, conductivity W/mK, heat capacity J/kgK, keyhole factor C)
BOUNDS_LO = (0.30, 11.0, 450.0, 1.0)
BOUNDS_HI = (0.80, 35.0, 1200.0, 5.0)
START = (0.62, 30.0, 700.0, 1.5)


def predict(point: Point, theta) -> dict[str, float]:
    mu, kappa, cp, C = (float(v) for v in theta)
    material = _material(kappa, cp)
    beam = Beam(point.power, point.speed, sigma_from_spot_diameter(point.spot_diameter), mu)
    geom = melt_pool_dimensions(beam, material)
    geom["depth_corrected"] = geom["depth"] + C * keyhole_depth(beam, material)
    return geom


def residuals(theta, points: list[Point]) -> np.ndarray:
    """Relative residuals so width (~130 um) and depth (~150 um) weigh equally."""
    out: list[float] = []
    for p in points:
        pred = predict(p, np.asarray(theta).ravel())
        if p.width is not None:
            out.append((pred["width"] - p.width) / p.width)
        if p.depth is not None:
            out.append((pred["depth_corrected"] - p.depth) / p.depth)
    return np.asarray(out, dtype=float)


def fit(points: list[Point]) -> tuple[tuple[float, ...], dict[str, float]]:
    result = least_squares(residuals, x0=list(START), bounds=(list(BOUNDS_LO), list(BOUNDS_HI)),
                           args=(points,), xtol=1e-8, diff_step=0.03)
    theta = tuple(float(v) for v in result.x)
    width_err, depth_err = [], []
    for p in points:
        pred = predict(p, theta)
        if p.width is not None:
            width_err.append(abs(pred["width"] - p.width) / p.width)
        if p.depth is not None:
            depth_err.append(abs(pred["depth_corrected"] - p.depth) / p.depth)
    return theta, {
        "width_mape_pct": 100.0 * float(np.mean(width_err)) if width_err else float("nan"),
        "depth_mape_pct": 100.0 * float(np.mean(depth_err)) if depth_err else float("nan"),
        "n_conditions": len(points),
    }


def main() -> int:
    if not WEAVER_POINTS:
        print("No calibration points loaded. Fill in WEAVER_POINTS and re-run.")
        return 1

    theta, rep = fit(WEAVER_POINTS)
    mu, kappa, cp, C = theta
    print("fitted parameters (effective, not physical constants)")
    print(f"   absorption efficiency  mu    = {mu:.3f}")
    print(f"   thermal conductivity   kappa = {kappa:.1f} W/mK")
    print(f"   heat capacity          Cp    = {cp:.0f} J/kgK")
    print(f"   keyhole factor         C     = {C:.2f}")
    print()
    for p in WEAVER_POINTS:
        pred = predict(p, theta)
        print(f"   P={p.power:6.1f} W  v={p.speed:5.2f} m/s  d={p.spot_diameter*1e6:5.1f} um"
              f"   width {pred['width']*1e6:6.1f} vs {p.width*1e6:6.1f}"
              f"   depth {pred['depth_corrected']*1e6:6.1f} vs {p.depth*1e6:6.1f} um"
              f"   [{p.label}]")
    print()
    print(f"   width MAPE {rep['width_mape_pct']:.1f} %     depth MAPE {rep['depth_mape_pct']:.1f} %"
          f"     over {rep['n_conditions']} conditions")
    worst = max(rep["width_mape_pct"], rep["depth_mape_pct"])
    print(f"   GATE 1: {'PASS' if worst <= 15.0 else 'FAIL'} (threshold 15 % MAPE)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
