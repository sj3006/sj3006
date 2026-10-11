"""Gate 1: fit the single free parameter (effective absorptivity) to measured
melt pool geometry, and report the error.

The only unknown in the Eagar-Tsai setup is how much of the incident laser power
is actually absorbed. Everything else is a material property or a machine
setting. Fitting one parameter is defensible; fitting several would be curve
fitting, and a reviewer would say so.

Usage
-----
Fill in `WEAVER_POINTS` with single-track measurements from

    Weaver et al. (2024), "Cross-Sectional Melt Pool Geometry of Laser Scanned
    Tracks and Pads on Nickel Alloy 718 for the 2022 Additive Manufacturing
    Benchmark Challenges", Integrating Materials and Manufacturing Innovation,
    DOI 10.1007/s40192-024-00355-5

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

from eagar_tsai import IN718, Beam, Material, melt_pool_dimensions, sigma_from_spot_diameter


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
WEAVER_POINTS: list[Point] = []


def predict(point: Point, absorptivity: float, material: Material) -> dict[str, float]:
    beam = Beam(
        power=point.power,
        speed=point.speed,
        sigma=sigma_from_spot_diameter(point.spot_diameter),
        absorptivity=absorptivity,
    )
    return melt_pool_dimensions(beam, material)


def residuals(absorptivity: float, points: list[Point], material: Material) -> np.ndarray:
    """Relative residuals on whichever dimensions were reported.

    Relative rather than absolute so width (~100 um) and depth (~50 um) carry
    comparable weight instead of width dominating the fit.
    """
    out: list[float] = []
    for p in points:
        pred = predict(p, float(absorptivity), material)
        if p.width is not None:
            out.append((pred["width"] - p.width) / p.width)
        if p.depth is not None:
            out.append((pred["depth"] - p.depth) / p.depth)
    return np.asarray(out, dtype=float)


def fit(points: list[Point], material: Material = IN718,
        initial: float = 0.35) -> tuple[float, dict[str, float]]:
    """Least-squares fit of absorptivity. Returns (absorptivity, error report)."""
    result = least_squares(
        residuals, x0=[initial], bounds=([0.05], [0.95]),
        args=(points, material), xtol=1e-4, diff_step=0.02,
    )
    absorptivity = float(result.x[0])

    width_err, depth_err = [], []
    for p in points:
        pred = predict(p, absorptivity, material)
        if p.width is not None:
            width_err.append(abs(pred["width"] - p.width) / p.width)
        if p.depth is not None:
            depth_err.append(abs(pred["depth"] - p.depth) / p.depth)

    report = {
        "absorptivity": absorptivity,
        "width_mape_pct": 100.0 * float(np.mean(width_err)) if width_err else float("nan"),
        "depth_mape_pct": 100.0 * float(np.mean(depth_err)) if depth_err else float("nan"),
        "n_conditions": len(points),
    }
    return absorptivity, report


def main() -> int:
    if not WEAVER_POINTS:
        print(__doc__)
        print("No calibration points loaded.")
        print("Fill in WEAVER_POINTS at the top of this file and re-run.")
        return 1

    absorptivity, rep = fit(WEAVER_POINTS)
    print(f"fitted absorptivity        A = {rep['absorptivity']:.4f}")
    print(f"conditions used                {rep['n_conditions']}")
    print(f"width  mean abs pct error      {rep['width_mape_pct']:.1f} %")
    print(f"depth  mean abs pct error      {rep['depth_mape_pct']:.1f} %")
    print()
    print("per-condition:")
    for p in WEAVER_POINTS:
        pred = predict(p, absorptivity, IN718)
        bits = [f"P={p.power:6.1f} W", f"v={p.speed:5.2f} m/s", f"d={p.spot_diameter*1e6:5.1f} um"]
        if p.width is not None:
            bits.append(f"width {pred['width']*1e6:6.1f} vs {p.width*1e6:6.1f} um")
        if p.depth is not None:
            bits.append(f"depth {pred['depth']*1e6:6.1f} vs {p.depth*1e6:6.1f} um")
        print("   " + "   ".join(bits) + (f"   [{p.label}]" if p.label else ""))
    print()
    worst = max(rep["width_mape_pct"], rep["depth_mape_pct"])
    print(f"GATE 1: {'PASS' if worst <= 15.0 else 'FAIL'} (threshold 15 % MAPE)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
