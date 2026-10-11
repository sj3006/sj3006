"""Sensor models: what each instrument would report from the computed field.

All three read the same temperature field and differ in how they weight it,
which is what makes them independent observables rather than three copies of
melt pool size.

    photodiode  band-integrated radiance, weighted towards the hot core
    camera      geometric area above the liquidus, the pool outline
    pyrometer   two-colour radiance ratio, an apparent temperature

The temperature cap
-------------------
Eagar-Tsai with constant properties and no vaporisation predicts peak
temperatures around 12 000 K against an IN718 boiling point near 3190 K. Melt
pool *geometry* is unaffected because the liquidus isotherm sits far from the
singular core, but radiance goes as roughly T^4, so an uncapped photodiode model
would be integrating almost pure artefact.

Temperature is therefore capped at the boiling point wherever radiance is
computed. Physically: above boiling the material leaves as vapour rather than
continuing to glow hotter as a condensed surface, so the model has no business
extrapolating there. This keeps the photodiode responsive to the hot core while
refusing to trust a number the model cannot produce.

The cap is what keeps the photodiode distinct from the camera. The camera sees
the area above the *liquidus*; the photodiode is dominated by the area above the
*boiling point*. Different isotherms, different sensitivities, genuinely
separate rows in the Jacobian.
"""

from __future__ import annotations

import numpy as np

from eagar_tsai import IN718, Beam, Material, melt_pool_dimensions, temperature_field

__all__ = ["SENSOR_NAMES", "SensorConfig", "sensor_readings"]

SENSOR_NAMES = ("photodiode", "camera", "pyrometer")

# Planck constants, SI
_H = 6.62607015e-34
_C = 2.99792458e8
_KB = 1.380649e-23


def _spectral_radiance(wavelength: np.ndarray, temperature: np.ndarray) -> np.ndarray:
    """Planck spectral radiance, grey body with emissivity folded out.

    Emissivity is assumed constant over the band and cancels in the pyrometer
    ratio; for the photodiode it scales the signal and is absorbed into the
    sensor gain, which does not affect signature direction.
    """
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        x = _H * _C / (wavelength * _KB * np.maximum(temperature, 1.0))
        out = (2.0 * _H * _C**2) / wavelength**5 / np.expm1(np.clip(x, 1e-12, 700.0))
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


class SensorConfig:
    """Instrument parameters. Defaults are typical of coaxial LPBF monitoring."""

    def __init__(
        self,
        photodiode_band: tuple[float, float] = (700e-9, 1000e-9),
        pyrometer_bands: tuple[float, float] = (750e-9, 950e-9),
        field_of_view: float = 1.5e-3,
        n_grid: int = 121,
        n_lambda: int = 12,
    ) -> None:
        self.photodiode_band = photodiode_band
        self.pyrometer_bands = pyrometer_bands
        self.field_of_view = field_of_view
        self.n_grid = n_grid
        self.n_lambda = n_lambda


def sensor_readings(
    beam: Beam,
    material: Material = IN718,
    config: SensorConfig | None = None,
) -> dict[str, float]:
    """What each sensor reports for a given beam and material state.

    Units are instrument-arbitrary for the photodiode (gain is unknown and
    irrelevant to signature direction), square metres for the camera, kelvin for
    the pyrometer.
    """
    cfg = config or SensorConfig()
    half = cfg.field_of_view / 2.0
    x = np.linspace(-3.0 * half, half, cfg.n_grid)
    y = np.linspace(-half, half, cfg.n_grid)
    xx, yy = np.meshgrid(x, y, indexing="ij")

    surface = temperature_field(xx, yy, np.zeros_like(xx), beam, material)
    capped = np.minimum(surface, material.t_vaporisation)
    cell = float(x[1] - x[0]) * float(y[1] - y[0])

    # Photodiode: radiance integrated over band and field of view.
    lam = np.linspace(*cfg.photodiode_band, cfg.n_lambda)
    radiance = np.trapezoid(
        _spectral_radiance(lam[None, None, :], capped[..., None]), lam, axis=-1
    )
    photodiode = float(radiance.sum() * cell)

    # Camera: melt pool area from the sub-grid interpolated dimensions, as an
    # ellipse. Counting cells above the liquidus quantises the area to the cell
    # size (~0.3 % here), and that quantisation would show up as spurious angle
    # in the Jacobian, where the entire result lives in small differences.
    geom = melt_pool_dimensions(beam, material)
    camera = float(np.pi / 4.0 * geom["width"] * geom["length"])

    # Two-colour pyrometer: ratio of the two band powers integrated over the
    # field of view, inverted to an apparent temperature.
    #
    # Taking the ratio at the single hottest pixel returns the boiling point for
    # every condition, because the cap saturates there - a dead row carrying no
    # information. That is an artefact of the cap, not physics. A real coaxial
    # pyrometer measures two integrated band powers over its spot and ratios
    # them, which is both more faithful and responsive to how the temperature is
    # distributed rather than just how hot the hottest point is.
    l1, l2 = cfg.pyrometer_bands
    p1 = float(_spectral_radiance(np.array(l1), capped).sum())
    p2 = float(_spectral_radiance(np.array(l2), capped).sum())
    ratio = p1 / p2 if p2 > 0 else 0.0
    if ratio > 0:
        denom = np.log(ratio) + 5.0 * np.log(l1 / l2)
        pyrometer = float(_H * _C / _KB * (1.0 / l2 - 1.0 / l1) / denom) if denom != 0 else 0.0
    else:
        pyrometer = 0.0

    return {"photodiode": photodiode, "camera": camera, "pyrometer": pyrometer}


if __name__ == "__main__":
    from faults import FAULT_NAMES, FaultState, apply_faults

    base_beam, base_mat = apply_faults(FaultState())
    base = sensor_readings(base_beam, base_mat)
    print("nominal readings:")
    for k, v in base.items():
        unit = {"photodiode": "(arb)", "camera": "m^2", "pyrometer": "K"}[k]
        print(f"   {k:12s} {v:12.5g} {unit}")
    print()
    print("response to +10 % in each fault, as % change from nominal:")
    print(f"   {'fault':10s}" + "".join(f"{n:>13s}" for n in SENSOR_NAMES))
    for name in FAULT_NAMES:
        b, m = apply_faults(FaultState(**{name: 0.10}))
        r = sensor_readings(b, m)
        cells = "".join(
            f"{100.0*(r[s]-base[s])/base[s]:>12.3f}%" if base[s] else f"{'n/a':>13s}"
            for s in SENSOR_NAMES
        )
        print(f"   {name:10s}{cells}")
