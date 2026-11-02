"""Relative sensor noise, derived from transduction physics rather than asserted.

Why this file exists
--------------------
Angles, rank and condition number are computed on the *whitened* Jacobian, each
row divided by that sensor's relative noise. The raw Jacobian's rows carry
incommensurable units - arbitrary photodiode units, square metres, kelvin - so
an angle between its columns is not a physical quantity at all. Whitening is
what puts every row in noise widths and makes the columns comparable. The noise
ratios are therefore not an add-on to the Jacobian; they are half of the
measurement geometry, and every reported number depends on them.

Earlier drafts asserted the ratios 1 : 1 : 0.03 (photodiode : camera :
pyrometer) and swept them. No derivation existed, and two of the three values
turned out to be wrong - in opposite directions. See errata E8.

The one assumption
------------------
Each radiometric channel carries the same fractional noise `eps` on its measured
signal. That is a statement about detector class, not about any particular
instrument, and it is the only free quantity here. Everything else follows from
how each instrument converts radiance into the number it reports. Because only
*ratios* enter the whitening - angles, rank and condition number are invariant
to a common scaling of all rows - `eps` cancels and never has to be pinned down.
This is why deriving the ratios is stronger than citing any single vendor noise
figure: the ratios follow from physics, and the absolute scale is not claimed.

The three chains
----------------
**Photodiode.** Its reading *is* a band-integrated radiometric power over the
field of view, so eps appears on it directly:

    sigma_pd = eps                                          ratio 1 (the unit)

**Pyrometer.** It reports a temperature inverted from the ratio of two band
powers. With independent noise on each channel the ratio carries sqrt(2)*eps,
and the inversion divides by the ratio's temperature sensitivity:

    |dlnR/dlnT| = c2 (1/lam2 - 1/lam1) / T                  Wien
    sigma_pyr   = sqrt(2) * eps / |dlnR/dlnT|

At 750/950 nm and the model's reported 3030.6 K this is sqrt(2)/1.3326 = 1.061.
Ratioing two bands that are close together throws away most of the temperature
sensitivity, and the inversion then amplifies what noise remains. A two-colour
pyrometer is a *noisier* relative instrument than the photodiode it is built
from, not a quieter one.

**Camera.** It reports a geometric extent found by thresholding at the liquidus,
so a fractional radiance error is indistinguishable from the threshold sitting
at a different temperature:

    L(T') = L(T_liq)/(1+eps)   =>   dln T_liq = -eps / (dlnL/dlnT)|_T_liq

Planck is steep at 1609 K - dlnL/dlnT = 10.52 at 850 nm - so eps = 1 % moves the
apparent isotherm by only 0.095 % in temperature. Propagating that isotherm
shift through the model's own dimension solver gives the area response. The
camera is intrinsically a *precise* instrument in relative terms, by about a
factor of seven against the photodiode, because thresholding on a steep Planck
function localises an edge well.

Width and length are not equally well localised: the lateral edge sits on a
steep temperature gradient and moves 0.030 % per 1 % of eps, while the trailing
edge sits in the pool's long thermal tail and moves 0.112 %. That is a factor of
3.8, and it is a second, independent reason - alongside the correlation result
of Section 4.3 - why melt pool width is the more informative axis.

Why this set is conservative
----------------------------
Two choices in the above could have gone the other way, and both were taken in
the direction that costs this analysis rather than flatters it.

1. **No perimeter averaging on the area channel.** Independent per-pixel
   detection noise would average down along the melt pool boundary by
   sqrt(N_el). Applying that factor would make the camera quieter still - about
   0.017 rather than 0.142 at this model's grid spacing - but N_el depends on a
   camera's instantaneous field of view, which this model does not represent.
   Inventing one would be asserting an instrument parameter, which is the thing
   this file exists to stop doing. The unaveraged figure is used.

2. **Width and length are whitened as independent.** Under a purely common-mode
   radiance error their edge displacements are perfectly correlated, the
   covariance is rank one, and the differential combination would be noise-free
   - which would make splitting the camera axes infinitely valuable. That is
   unphysical, and treating the two as independent understates the split's
   value rather than overstating it.

A third point, in the other direction and worth stating: the common-mode part of
a real system's radiometric error *cancels* in the pyrometer's ratio, since both
bands share the optical path. A system whose noise is dominated by slow gain or
emissivity drift rather than by detection noise would therefore have a much
quieter pyrometer, approaching the 0.03 earlier drafts asserted. The 0.03 is not
arbitrary so much as the gain-dominated limit, asserted without saying so. For
*per-segment* diagnosability the detection-noise limit is the right one, because
gain is static over a segment and a shared bias does not discriminate between
two fault hypotheses at the same operating point. Both limits are swept.
"""

from __future__ import annotations

import dataclasses

import numpy as np

from eagar_tsai import melt_pool_dimensions, temperature_field
from sensors import ALL_SENSOR_NAMES, SENSOR_NAMES, SensorConfig, _spectral_radiance

__all__ = ["C2", "DERIVED", "SIGMAS", "sigmas_for", "planck_log_sensitivity",
           "derive", "verify"]

_H, _C, _KB = 6.62607015e-34, 2.99792458e8, 1.380649e-23
C2 = _H * _C / _KB          # 1.4387769e-2 m K, Planck's second radiation constant

# Derived by `derive()`; see the module docstring for each chain. Hardcoded so
# that importing this module is free, and checked by `verify()`, which every
# reporting script calls.
DERIVED: dict[str, float] = {
    "photodiode":      1.0000,
    "camera":          0.1422,
    "pyrometer":       1.0612,
    "camera_width":    0.0298,
    "camera_length":   0.1124,
    "photodiode_swir": 1.0000,
    "pyrometer_wide":  0.3583,
}

#: Relative noise for the three-sensor baseline suite, in `SENSOR_NAMES` order.
SIGMAS = np.array([DERIVED[n] for n in SENSOR_NAMES])


def sigmas_for(subset) -> np.ndarray:
    """Relative noise for an arbitrary subset of observables, in its own order."""
    return np.array([DERIVED[n] for n in subset], dtype=float)


def planck_log_sensitivity(wavelength: float, temperature: float) -> float:
    """dlnL/dlnT for Planck spectral radiance: x e^x / (e^x - 1), x = c2/(lam T).

    The Wien limit is simply x, and at these wavelengths and temperatures the
    two agree to better than 1 %.
    """
    x = C2 / (wavelength * temperature)
    return float(x * np.exp(x) / np.expm1(x))


def _surface_field(beam, material, cfg: SensorConfig):
    half = cfg.field_of_view / 2.0
    x = np.linspace(-3.0 * half, half, cfg.n_grid)
    y = np.linspace(-half, half, cfg.n_grid)
    xx, yy = np.meshgrid(x, y, indexing="ij")
    field = temperature_field(xx, yy, np.zeros_like(xx), beam, material)
    return np.minimum(field, material.t_vaporisation)


def _pyrometer_factor(bands, capped) -> float:
    """sigma_T/eps for a two-colour inversion, through the code's own inverter.

    Computed numerically rather than from the Wien expression so that it is the
    sensitivity of the instrument model actually used, not of an idealisation of
    it. The two agree here to 0.01 %.
    """
    l1, l2 = bands
    p1 = float(_spectral_radiance(np.array(l1), capped).sum())
    p2 = float(_spectral_radiance(np.array(l2), capped).sum())

    def invert(a, b):
        denom = np.log(a / b) + 5.0 * np.log(l1 / l2)
        return C2 * (1.0 / l2 - 1.0 / l1) / denom

    d = 1e-4
    g1 = (np.log(invert(p1 * (1 + d), p2)) - np.log(invert(p1 * (1 - d), p2))) / (2 * d)
    g2 = (np.log(invert(p1, p2 * (1 + d))) - np.log(invert(p1, p2 * (1 - d)))) / (2 * d)
    return float(np.hypot(g1, g2))


def _camera_factors(beam, material, cfg: SensorConfig, eps: float = 0.01):
    """(dlnW, dlnL, dlnA) per unit eps, via the equivalent liquidus shift."""
    lam = float(np.mean(cfg.photodiode_band))
    s = planck_log_sensitivity(lam, material.t_liquidus)
    dlnT = eps / s
    out = {}
    for sign in (+1, -1):
        m = dataclasses.replace(material,
                                t_liquidus=material.t_liquidus * np.exp(sign * dlnT))
        out[sign] = melt_pool_dimensions(beam, m)
    dw = (np.log(out[-1]["width"]) - np.log(out[+1]["width"])) / (2 * eps)
    dl = (np.log(out[-1]["length"]) - np.log(out[+1]["length"])) / (2 * eps)
    return float(dw), float(dl), float(dw + dl)


def derive(beam=None, material=None, cfg: SensorConfig | None = None) -> dict[str, float]:
    """Recompute every figure in `DERIVED` from the model and Planck's law."""
    from faults import FaultCouplings, FaultState, apply_faults

    if beam is None or material is None:
        beam, material = apply_faults(FaultState(), FaultCouplings())
    cfg = cfg or SensorConfig()
    capped = _surface_field(beam, material, cfg)

    dw, dl, da = _camera_factors(beam, material, cfg)
    return {
        "photodiode": 1.0,
        "camera": da,
        "pyrometer": _pyrometer_factor(cfg.pyrometer_bands, capped),
        "camera_width": dw,
        "camera_length": dl,
        "photodiode_swir": 1.0,
        "pyrometer_wide": _pyrometer_factor(cfg.pyrometer_wide_bands, capped),
    }


def verify(tol: float = 5e-3) -> None:
    """Assert the hardcoded figures still reproduce. Called by reporting scripts."""
    got = derive()
    bad = {k: (DERIVED[k], got[k]) for k in DERIVED
           if abs(got[k] - DERIVED[k]) > tol * max(abs(DERIVED[k]), 1e-12)}
    if bad:
        raise AssertionError(f"derived noise figures moved: {bad}")


if __name__ == "__main__":
    from faults import FaultCouplings, FaultState, apply_faults
    from sensors import sensor_readings

    beam, material = apply_faults(FaultState(), FaultCouplings())
    cfg = SensorConfig()
    base = sensor_readings(beam, material, cfg)
    got = derive(beam, material, cfg)

    print("derived relative noise, one shared fractional radiometric error eps\n")
    print(f"   {'observable':18s}{'sigma/eps':>11s}{'vs photodiode':>15s}")
    for n in ALL_SENSOR_NAMES:
        print(f"   {n:18s}{got[n]:>11.4f}{got[n] / got['photodiode']:>15.3f}")

    l1, l2 = cfg.pyrometer_bands
    print(f"\n   pyrometer chain, {l1*1e9:.0f}/{l2*1e9:.0f} nm at {base['pyrometer']:.1f} K")
    print(f"      dlnL/dlnT      {planck_log_sensitivity(l1, base['pyrometer']):.4f}"
          f"  and  {planck_log_sensitivity(l2, base['pyrometer']):.4f}")
    print(f"      |dlnR/dlnT|    {C2*abs(1/l2 - 1/l1)/base['pyrometer']:.4f}  (Wien)")
    print(f"      sqrt(2)/that   {np.sqrt(2)*base['pyrometer']/(C2*abs(1/l2-1/l1)):.4f}")

    lam = float(np.mean(cfg.photodiode_band))
    s = planck_log_sensitivity(lam, material.t_liquidus)
    print(f"\n   camera chain, band mid {lam*1e9:.0f} nm at liquidus {material.t_liquidus:.0f} K")
    print(f"      dlnL/dlnT      {s:.3f}")
    print(f"      eps = 1 % moves the apparent isotherm by {100/s:.4f} % in T")
    print(f"      width {got['camera_width']:.4f}, length {got['camera_length']:.4f}"
          f"  ->  length is {got['camera_length']/got['camera_width']:.1f}x worse localised")

    verify()
    print("\n   verify(): hardcoded figures reproduce.")
