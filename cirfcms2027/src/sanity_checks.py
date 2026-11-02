"""Day-1 sanity checks on the Eagar-Tsai module.

Run: python3 src/sanity_checks.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from eagar_tsai import (IN718, IN718_ABSORPTIVITY, Beam, melt_pool_dimensions,
                        sigma_from_spot_diameter)

# Use the calibrated absorptivity, not a round number. This module produces the
# energy-density validation figure quoted in the paper, and for a while it ran
# an uncalibrated model (0.35 against the fitted 0.384) - errata E3.
ABS = IN718_ABSORPTIVITY
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
    print()
    print("     NOTE: the correlation is grid-dependent and should not be quoted")
    print("     on its own - see check_energy_density_exponents below, which is")
    print("     what the paper reports (errata E3).")
    return reproduced


# VED = P / (v d^2), so a quantity that is a pure function of VED must have
# log-log exponents proportional to this ray in (P, v, d).
VED_RAY = np.array([1.0, -1.0, -2.0])

# Five grids spanning different regions of parameter space. The correlation
# coefficient swings wildly across these; the exponents do not.
_GRIDS = {
    "sanity_checks 3x3x3":  ((150., 250., 350.), (0.4, 0.8, 1.6), (60e-6, 100e-6, 140e-6)),
    "benchmark spot range": ((150., 250., 350.), (0.4, 0.8, 1.6), (49e-6, 67e-6, 82e-6)),
    "benchmark P and v":    ((137., 285., 400.), (0.4, 0.96, 1.6), (49e-6, 67e-6, 82e-6)),
    "wide spots":           ((150., 250., 350.), (0.4, 0.8, 1.6), (50e-6, 100e-6, 200e-6)),
    "dense 4x4x3":          ((150., 220., 290., 360.), (0.4, 0.7, 1.1, 1.6),
                             (60e-6, 100e-6, 140e-6)),
}


def check_energy_density_exponents() -> bool:
    """Weaver's depth/width split, stated so that it does not depend on the grid.

    A Pearson coefficient answers "does this track VED" badly: it depends on which
    region of parameter space happens to be sampled, and width's coefficient runs
    from +0.68 to -0.22 across the five grids below. The exponents of the
    underlying power law do not move, because they are a property of the model
    rather than of the sample.

    Fit  ln y = c + a lnP + b lnv + g lnd  and measure the angle between the
    fitted exponent vector (a, b, g) and the VED ray (1, -1, -2).
    """
    print("\n4. ENERGY-DENSITY EXPONENTS (grid-independent form of check 3)")
    print("   a pure function of VED = P/(v d^2) has exponents along (1, -1, -2)")
    print(f"     {'grid':23s}{'dim':8s}{'a(P)':>7s}{'b(v)':>7s}{'g(d)':>7s}"
          f"{'R2':>7s}{'cos':>8s}")
    agree, cos_by_dim = True, {"width": [], "depth": [], "length": []}
    for name, (Ps, vs, ds) in _GRIDS.items():
        rows = []
        for P in Ps:
            for v in vs:
                for d in ds:
                    g = dims(P, v, d)
                    if min(g["width"], g["depth"], g["length"]) > 0:
                        rows.append((P, v, d, g["width"], g["depth"], g["length"]))
        a = np.array(rows)
        X = np.column_stack([np.ones(len(a)), np.log(a[:, 0]), np.log(a[:, 1]),
                             np.log(a[:, 2])])
        for j, dim in ((3, "width"), (4, "depth"), (5, "length")):
            ln = np.log(a[:, j])
            coef, *_ = np.linalg.lstsq(X, ln, rcond=None)
            e = coef[1:]
            r2 = 1.0 - (ln - X @ coef).var() / ln.var()
            cos = float(e @ VED_RAY / (np.linalg.norm(e) * np.linalg.norm(VED_RAY)))
            cos_by_dim[dim].append(cos)
            print(f"     {name if dim == 'width' else '':23s}{dim:8s}{e[0]:+7.3f}"
                  f"{e[1]:+7.3f}{e[2]:+7.3f}{r2:7.3f}{cos:+8.3f}")
            if r2 < 0.90:
                agree = False
    print()
    for dim in ("width", "depth", "length"):
        c = cos_by_dim[dim]
        print(f"     {dim:8s} cos(exponents, VED ray) spans {min(c):+.3f} to {max(c):+.3f}")
    ok = (max(cos_by_dim["width"]) < min(cos_by_dim["depth"])) and agree
    print(f"\n     depth sits closer to the VED ray than width on EVERY grid: {ok}")
    print("     Mechanism: width and depth depend on spot size with opposite")
    print("     signs, and spot size is the one variable a volumetric density")
    print("     folds away. That is why depth tracks VED and width does not.")
    return ok


if __name__ == "__main__":
    ok1 = check_directional()
    check_peak_temperature()
    ok3 = check_energy_density_correlation()
    ok4 = check_energy_density_exponents()
    print("\n" + "=" * 70)
    print(f"   directional sweep:        {'PASS' if ok1 else 'FAIL'}")
    print(f"   Weaver reproduction:      {'PASS' if ok3 else 'FAIL'}")
    print(f"   VED exponents, all grids: {'PASS' if ok4 else 'FAIL'}")
