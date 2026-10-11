"""Day-1 sanity checks on the Eagar-Tsai module.

Run: python3 src/sanity_checks.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from eagar_tsai import IN718, Beam, melt_pool_dimensions, sigma_from_spot_diameter

ABS = 0.35
NQ = 100


def dims(power: float, speed: float, spot: float = 100e-6) -> dict[str, float]:
    beam = Beam(power=power, speed=speed, sigma=sigma_from_spot_diameter(spot), absorptivity=ABS)
    return melt_pool_dimensions(beam, IN718, n_quad=NQ)


def check_directional() -> bool:
    """Width and depth must grow with power and shrink with speed.

    A failure here is a sign or units bug, not physics.
    """
    print("1. DIRECTIONAL SWEEP")
    print("   power sweep at v = 0.8 m/s, spot 100 um")
    rows = [(p, dims(p, 0.8)) for p in (150.0, 200.0, 250.0, 300.0, 350.0)]
    for p, d in rows:
        print(f"     P={p:5.0f} W   width {d['width']*1e6:7.2f} um   depth {d['depth']*1e6:7.2f} um")
    ok_p = all(
        b["width"] >= a["width"] and b["depth"] >= a["depth"]
        for (_, a), (_, b) in zip(rows, rows[1:])
    )
    print(f"     monotonic increasing with power: {ok_p}")

    print("   speed sweep at P = 250 W, spot 100 um")
    rows = [(v, dims(250.0, v)) for v in (0.4, 0.6, 0.8, 1.2, 1.6)]
    for v, d in rows:
        print(f"     v={v:4.1f} m/s width {d['width']*1e6:7.2f} um   depth {d['depth']*1e6:7.2f} um")
    ok_v = all(
        b["width"] <= a["width"] and b["depth"] <= a["depth"]
        for (_, a), (_, b) in zip(rows, rows[1:])
    )
    print(f"     monotonic decreasing with speed: {ok_v}")
    return ok_p and ok_v


def check_peak_temperature() -> None:
    """Peak temperature is expected to be unphysical. Put it on the record."""
    print("\n2. PEAK TEMPERATURE (expected unphysical)")
    d = dims(250.0, 0.8)
    print(f"     peak {d['peak_temperature']:.0f} K   liquidus {IN718.t_liquidus:.0f} K"
          f"   vaporisation {IN718.t_vaporisation:.0f} K")
    print("     Inherent to constant-property Eagar-Tsai: no latent heat, no")
    print("     vaporisation, no melt pool convection. GEOMETRY is usable, peak")
    print("     temperature is not. Consequence: a photodiode model integrating")
    print("     radiance ~ T^4 would be dominated by this artefact, so the Gate 2")
    print("     fallback (melt pool area as photodiode proxy) is likely REQUIRED.")


def check_energy_density_correlation() -> bool:
    """Weaver et al. (2024): depth tracked volumetric energy density, width did not.

    That is a correlation claim across a parameter set in which power, speed AND
    spot size all varied - not an invariance claim at fixed spot size. Spot size
    is almost certainly what breaks the width relationship, so it has to be in
    the sweep or the test cannot see the effect.
    """
    print("\n3. ENERGY-DENSITY CORRELATION (Weaver et al. 2024)")
    print("   varying power, speed AND spot size; VED proxy = P / (v * d^2)")
    rows = []
    for power in (150.0, 250.0, 350.0):
        for speed in (0.4, 0.8, 1.6):
            for spot in (60e-6, 100e-6, 140e-6):
                d = dims(power, speed, spot)
                if d["depth"] <= 0.0 or d["width"] <= 0.0:
                    continue
                ved = power / (speed * spot**2)
                rows.append((ved, d["width"], d["depth"]))

    ved = np.array([r[0] for r in rows])
    width = np.array([r[1] for r in rows])
    depth = np.array([r[2] for r in rows])
    print(f"     {len(rows)} melted conditions")

    # Correlate in log space: these are power-law relationships, so a log-log
    # Pearson coefficient is the right measure of "tracks with".
    lv = np.log(ved)
    r_width = float(np.corrcoef(lv, np.log(width))[0, 1])
    r_depth = float(np.corrcoef(lv, np.log(depth))[0, 1])
    print(f"     log-log correlation with VED:   width r = {r_width:+.3f}"
          f"     depth r = {r_depth:+.3f}")
    reproduced = abs(r_depth) > abs(r_width)
    print(f"     depth tracks VED more strongly than width (Weaver): {reproduced}")
    print("     If True: power and speed are confounded in depth but separable in")
    print("     width. That is the paper's central claim, reproduced independently.")
    return reproduced


if __name__ == "__main__":
    ok1 = check_directional()
    check_peak_temperature()
    ok3 = check_energy_density_correlation()
    print("\n" + "=" * 70)
    print(f"   directional sweep:        {'PASS' if ok1 else 'FAIL'}")
    print(f"   Weaver reproduction:      {'PASS' if ok3 else 'FAIL'}")
