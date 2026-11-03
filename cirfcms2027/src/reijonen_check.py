"""The one external check on this model's sensor response (paper Section 5.1).

Reijonen (2024) reports the coaxial photodiode response of a commercial LPBF
system to laser power, scan speed, focal position, scan orientation and
shielding gas flow. The speed response is given as a power law y = a*x^-b with
b = 0.337 at 400 W over 400-1200 mm/s, and the exponent is reported to grow with
laser power - "almost non-existent" at 100 W.

This module fits the same functional form to this model's photodiode reading
over the same speed range, at several powers, so the comparison is like for
like. The Jacobian entry is not the comparable quantity: it is a derivative at a
point, where theirs is a fit over a decade of speed.

The model partly fails the check, and the reason is physics it assumes away:
here the plume is a fixed optical depth, independent of power and speed and
emitting nothing of its own, so no mechanism exists by which b could grow with
power. Reijonen attributes the growth to exactly that - the plume appearing as
power rises.

Caveats on the comparison, which belong with any quotation of these numbers:
different material (316L against IN718), different detection band (a shortpass
below 800 nm against 700-1000 nm here) and different bed condition (30 um powder
layers against bare plate).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from eagar_tsai import IN718, IN718_ABSORPTIVITY, Beam, sigma_from_spot_diameter
from sensors import SensorConfig, sensor_readings

__all__ = ["REPORTED_B", "REPORTED_AT_POWER", "SPEED_RANGE_M_S", "POWERS_W",
           "fit_speed_exponent", "report"]

# --- what Reijonen (2024) reports -------------------------------------------
REPORTED_B = 0.337              # exponent of y = a * x^-b
REPORTED_AT_POWER = 400.0       # W, the one power at which b is quoted
SPEED_RANGE_M_S = (0.400, 1.200)
# Their qualitative claim: b grows with power and is "almost non-existent" at
# 100 W. Encoded only as the powers to test, not as a number to compare against.
POWERS_W = (100.0, 200.0, 285.0, 400.0)

SPOT_DIAMETER = 67e-6           # this model's calibrated spot
N_SPEEDS = 25


def _photodiode(power: float, speed: float) -> float:
    beam = Beam(power, speed, sigma_from_spot_diameter(SPOT_DIAMETER),
                IN718_ABSORPTIVITY)
    return float(sensor_readings(beam, IN718, SensorConfig())["photodiode"])


def fit_speed_exponent(power: float, speed_range=SPEED_RANGE_M_S,
                       n: int = N_SPEEDS) -> dict[str, float]:
    """Least-squares fit of ln y = ln a - b ln x over the given speed range."""
    v = np.geomspace(speed_range[0], speed_range[1], n)
    y = np.array([_photodiode(power, float(s)) for s in v])
    lx, ly = np.log(v), np.log(y)
    slope, intercept = np.polyfit(lx, ly, 1)
    pred = intercept + slope * lx
    ss_res = float(np.sum((ly - pred) ** 2))
    ss_tot = float(np.sum((ly - ly.mean()) ** 2))
    return {"b": float(-slope), "ln_a": float(intercept),
            "r2": 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")}


def report() -> None:
    print("REIJONEN (2024) SPEED-RESPONSE CHECK")
    print(f"   their form y = a*x^-b, b = {REPORTED_B:.3f} at "
          f"{REPORTED_AT_POWER:.0f} W over "
          f"{SPEED_RANGE_M_S[0]*1e3:.0f}-{SPEED_RANGE_M_S[1]*1e3:.0f} mm/s")
    print(f"   this model, same form fitted over the same range "
          f"({N_SPEEDS} log-spaced speeds):\n")
    print(f"   {'power, W':>9s}{'fitted b':>10s}{'fit R2':>9s}   theirs")
    fits = {}
    for p in POWERS_W:
        f = fit_speed_exponent(p)
        fits[p] = f
        theirs = f"{REPORTED_B:.3f}" if p == REPORTED_AT_POWER else (
            "~0 (qualitative)" if p == 100.0 else "-")
        print(f"   {p:>9.0f}{f['b']:>10.3f}{f['r2']:>9.4f}   {theirs}")
    b400 = fits[REPORTED_AT_POWER]["b"]
    print(f"\n   magnitude: {b400:.3f} against {REPORTED_B:.3f}, "
          f"{b400/REPORTED_B - 1:+.0%}")
    bs = np.array([fits[p]["b"] for p in POWERS_W])
    print(f"   trend with power: {bs.min():.2f} to {bs.max():.2f} over "
          f"{POWERS_W[0]:.0f}-{POWERS_W[-1]:.0f} W - flat, where theirs grows "
          f"strongly.")
    print("\n   The discrepancy is physics this model assumes away: a plume of "
          "fixed optical\n   depth, independent of power and speed and emitting "
          "nothing, has no mechanism\n   by which b could grow with power. That "
          "same assumption is what makes the\n   power/gas degeneracy exact, so "
          "the reported 0.00 degrees is an upper bound on\n   external evidence "
          "rather than merely by assertion.")


if __name__ == "__main__":
    report()
