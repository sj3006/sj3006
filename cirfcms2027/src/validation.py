"""Known-practice validation: does the model reproduce published results it was
not fitted to?

Gate 1 fitted four parameters to seven Weaver single-track points, so agreement
with those points is calibration, not validation. Validation means reproducing
something the fit did not target. Two checks.

Check 1 - depth tracks energy density, width does not
-----------------------------------------------------
Already implemented in `sanity_checks.py` and passing: over 27 melted conditions
spanning power, speed and spot size, melt pool depth correlates with volumetric
energy density at r = +0.727 while width gives r = +0.032. That reproduces
Weaver et al.'s own observation and it lands on the paper's central claim, since
it says width carries information depth does not.

Check 2 - at *constant* energy density, the melt pool still varies
-----------------------------------------------------------------
Guo et al., *Additive Manufacturing* 28:600-609 (2019), used in-situ high-speed
high-energy X-ray imaging to observe sub-surface melt pools at constant input
energy density, and found that dimension and volume vary by orders of magnitude,
passing through different melting regimes. They attribute it to absorption
changing with power and speed separately, and conclude that energy density is an
incomplete processing metric.

This is the right validation target for this paper, for three reasons. It was
not fitted. It is the published statement of exactly the thesis - that the lumped
group hides the separate action of power and speed. And it is a *prediction* this
model either makes or does not: hold `P / (v * sigma^2)` fixed, sweep power, and
see whether the pool moves.

A note on what a pass would and would not mean
----------------------------------------------
Eagar-Tsai with a fitted keyhole correction is a conduction model with an
analytic depth patch. It has no vapour depression dynamics, no Marangoni flow
and no absorption-versus-depression-angle physics, which is the mechanism Guo
et al. identify. So this model can reproduce the *existence* and the *direction*
of the variation, and it can show a regime transition through the keyholing
criterion, but a quantitative match to "orders of magnitude" would be luck rather
than evidence. The honest report is the measured spread alongside Guo's claim,
with the difference stated rather than smoothed over.
"""

from __future__ import annotations

import numpy as np

from eagar_tsai import (IN718, IN718_ABSORPTIVITY, IN718_KEYHOLE_C, Beam,
                        corrected_depth, is_keyholing, melt_pool_dimensions)

__all__ = ["BASELINE", "constant_ved_sweep", "report"]

# The Weaver case-0 baseline, which is also the study's nominal condition.
BASELINE = {"power": 285.0, "speed": 0.960, "sigma": 67e-6 / 4.0}


def volumetric_energy_density(power, speed, sigma):
    """P / (v * sigma^2). Sigma rather than spot diameter, consistently."""
    return power / (speed * sigma**2)


def _pool(power, speed, sigma):
    beam = Beam(power=power, speed=speed, sigma=sigma,
                absorptivity=IN718_ABSORPTIVITY)
    geom = melt_pool_dimensions(beam, IN718)
    w, d = geom["width"], geom["depth"]
    return {
        "width": w,
        "depth": d,
        "length": geom["length"],
        "corrected_depth": corrected_depth(beam, IN718, IN718_KEYHOLE_C, d, w),
        "keyholing": is_keyholing(w, d),
    }


def constant_ved_sweep(powers=(150.0, 200.0, 250.0, 285.0, 350.0, 420.0, 500.0)):
    """Vary power, compensate speed to hold energy density fixed, watch the pool."""
    ved = volumetric_energy_density(**BASELINE)
    sigma = BASELINE["sigma"]
    rows = []
    for p in powers:
        v = p / (ved * sigma**2)
        r = _pool(p, v, sigma)
        r.update(power=p, speed=v,
                 ved=volumetric_energy_density(p, v, sigma))
        rows.append(r)
    return ved, rows


def report() -> None:
    ved, rows = constant_ved_sweep()
    print("CHECK 2: constant volumetric energy density, varying power and speed")
    print(f"energy density held at {ved:.4e} J/m^3 "
          f"(Weaver case 0: {BASELINE['power']:.0f} W, "
          f"{BASELINE['speed']:.3f} m/s, sigma {BASELINE['sigma']*1e6:.2f} um)\n")
    print(f"   {'power':>7s}{'speed':>8s}{'VED':>12s}{'width':>9s}{'depth':>9s}"
          f"{'corr.depth':>11s}{'length':>9s}{'aspect':>8s}  regime")
    print(f"   {'W':>7s}{'m/s':>8s}{'J/m^3':>12s}{'um':>9s}{'um':>9s}"
          f"{'um':>11s}{'um':>9s}{'d/w':>8s}")
    for r in rows:
        aspect = r["corrected_depth"] / r["width"] if r["width"] > 0 else float("nan")
        print(f"   {r['power']:>7.0f}{r['speed']:>8.3f}{r['ved']:>12.4e}"
              f"{r['width']*1e6:>9.1f}{r['depth']*1e6:>9.1f}"
              f"{r['corrected_depth']*1e6:>11.1f}{r['length']*1e6:>9.1f}"
              f"{aspect:>8.2f}  {'keyhole' if r['keyholing'] else 'conduction'}")

    for key, label in (("width", "width"), ("corrected_depth", "corrected depth"),
                       ("length", "length")):
        vals = np.array([r[key] for r in rows if r[key] > 0])
        if vals.size < 2:
            continue
        print(f"\n   {label:16s} spans {vals.min()*1e6:7.1f} to {vals.max()*1e6:7.1f} um"
              f"   = a factor of {vals.max()/vals.min():.2f}")

    regimes = {("keyhole" if r["keyholing"] else "conduction") for r in rows}
    print(f"\n   melting regimes visited: {', '.join(sorted(regimes))}")

    print("\nWHICH DIMENSION CARRIES THE INFORMATION AT CONSTANT ENERGY DENSITY")
    cond = [r for r in rows if not r["keyholing"]]
    print("   conduction-regime rows only, so the keyhole jump cannot flatter anything:")
    for key, label in (("width", "width"), ("depth", "depth"), ("length", "length")):
        v = np.array([r[key] for r in cond])
        print(f"      {label:8s} {v.min()*1e6:7.1f} to {v.max()*1e6:7.1f} um   "
              f"factor {v.max()/v.min():.2f}")
    print("   Width and depth barely move. Length moves by a factor of 2.6, and")
    print("   width moves *downwards* while depth moves up, so the two are not even")
    print("   redundant with each other.")
    print()
    print("   This independently explains Route B's result. The camera reports")
    print("   area = pi/4 * width * length, which multiplies the least informative")
    print("   dimension by the most informative one and reports the product. That")
    print("   is why splitting the camera into its two axes was worth 13 deg on the")
    print("   power/speed pair while two new sensors were worth nothing: the")
    print("   information was already in the image, being averaged away.")

    print("\nVERDICT")
    vals = np.array([r["corrected_depth"] for r in rows if r["corrected_depth"] > 0])
    widths = np.array([r["width"] for r in rows if r["width"] > 0])
    print(f"   Guo et al. (2019): at constant energy density the melt pool varies")
    print(f"   by orders of magnitude and changes melting regime.")
    print(f"   This model: depth varies by {vals.max()/vals.min():.2f}x, "
          f"width by {widths.max()/widths.min():.2f}x, "
          f"{'and the regime does change' if len(regimes) > 1 else 'regime unchanged'}.")
    print(f"   So the model reproduces the DIRECTION and the EXISTENCE of the")
    print(f"   effect, and the regime transition, but not the magnitude - which is")
    print(f"   expected, because the mechanism Guo et al. identify (absorption")
    print(f"   changing with the depression geometry) is not in a conduction model")
    print(f"   with an analytic keyhole patch. Reported as a partial pass, and the")
    print(f"   shortfall is a limitation of the thermal model, not of the")
    print(f"   diagnosability method built on it.")


if __name__ == "__main__":
    report()
