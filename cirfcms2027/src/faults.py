"""The five process faults, as perturbations to the calibrated thermal model.

Each fault enters through a specific physical route, matching the equation
structure in `structural.py` so that Tier 1 and Tier 2 describe the same system.

    fault     route(s) into the model              structural equations
    -------   -----------------------------------  --------------------
    power     commanded power                      e1
    speed     commanded scan speed                 e2
    layer     absorptivity AND conductivity        e1, e3
    gas       beam attenuation                     e1   (see caveat)
    geometry  local preheat temperature            e4

Sign convention: every fault is a *fractional deviation from nominal* except
geometry, which is a normalised preheat rise. Zero is the healthy process. This
keeps the five components dimensionally comparable, which is what makes the
signature angles in Tier 2 meaningful - see the note on normalisation in
03-technical-stack.md.

Caveat on the gas fault
-----------------------
The structural model gives gas flow two routes: beam attenuation by plume and
spatter, and reduced surface convection. Eagar-Tsai assumes an adiabatic free
surface and has no convection term, so only attenuation can be implemented here.

That is not a gap to apologise for. It places the quantitative tier squarely in
variant V1 of the Tier 1 sensitivity analysis, and V1 predicts that a power
deviation and a gas-flow fault become mutually non-isolable. Since that pair was
already the one structurally irreducible result under every variant, Tier 2
should reproduce it. The two tiers agree on their most important claim, by
different routes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from eagar_tsai import (IN718, IN718_ABSORPTIVITY, IN718_KEYHOLE_C, Beam, Material,
                        keyhole_depth, melt_pool_dimensions)

__all__ = ["FaultState", "FaultCouplings", "FAULT_NAMES", "apply_faults", "observables"]

FAULT_NAMES = ("power", "speed", "layer", "gas", "geometry")


@dataclass(frozen=True)
class FaultState:
    """Fractional deviations from the healthy process. All zero = nominal.

    What a magnitude means differs between faults, and the difference matters.

    `power` and `speed` are physical fractions: 0.05 is 5% more power, or 5%
    faster. They multiply the quantity directly and need no convention.

    `layer`, `gas` and `geometry` are dimensionless **severity indices**. They
    have no unit of their own - their physical meaning comes entirely from the
    coupling constant each one multiplies. f = 1 is a *convention* meaning
    "severe", loosely anchored to the top of the plausible range - not a
    calibrated physical limit, and the paper must not call it one. At f = 1:

        f_layer = 1     absorptivity -25.9%, conductivity +64.9%
                        (about what losing the powder's trapping would do)
        f_gas = 1       beam attenuated 18.1% (a severe plume)
        f_geometry = 1  local preheat +600 K (a thin wall running hot)

    So f reads as "fraction of the way to the worst case".

    **A fault index and its coupling are identifiable only as a product.**
    Doubling the coupling and halving f gives a numerically identical model, so
    the scale is a convention. That is harmless for isolability - scaling a
    Jacobian column does not change its direction, and angles see only
    direction, which the coupling sweep confirms exactly. It is not harmless
    for two things, both of which must be stated in the paper:

      - Detectability, which is an absolute question and so is not well posed
        here. See also the deliberately-unused noise figures.
      - The finite-magnitude study, where every fault is given the same f. At
        f = 0.05 that is a real 5% for power but only a 1.5% absorptivity change
        for layer and 1.0% for gas, so those rows do **not** compare equal
        physical severities. The magnitude axis is an index, not a common scale.
    """

    power: float = 0.0
    speed: float = 0.0
    layer: float = 0.0      # positive = thinner powder layer than nominal
    gas: float = 0.0        # positive = more degraded shielding gas flow
    geometry: float = 0.0   # positive = more local heat accumulation

    def as_vector(self) -> np.ndarray:
        return np.array([getattr(self, n) for n in FAULT_NAMES], dtype=float)

    @classmethod
    def from_vector(cls, v) -> "FaultState":
        return cls(**dict(zip(FAULT_NAMES, (float(x) for x in np.asarray(v).ravel()))))


@dataclass(frozen=True)
class FaultCouplings:
    """How strongly each fault acts on each model input.

    These set the *direction* and relative magnitude of each fault's signature,
    which is what the isolability angles depend on. They are parameters of the
    fault model, not of the thermal model, and they are not calibrated - there
    is no AM-Bench data with deliberately induced faults to calibrate against.

    Values below are order-of-magnitude estimates with the sign fixed by physics.
    Because the Tier 2 result depends on them, they must be swept - see
    `couplings_sensitivity` - and the sweep reported, exactly as the Tier 1
    equation structure was swept.
    """

    # A thinner powder layer means fewer multiple reflections trapping light, so
    # absorptivity falls towards the bare-solid value.
    layer_to_absorptivity: float = -0.30
    # It also means less insulating powder between the track and the solid
    # beneath, so effective conductivity rises.
    layer_to_conductivity: float = +0.50
    # Degraded gas flow leaves plume and spatter in the beam path, attenuating it.
    gas_to_attenuation: float = -0.20
    # Preheat rise per unit geometry fault, in kelvin. 0.1 -> +60 K, which is the
    # right order for a thin feature or overhang.
    geometry_preheat_kelvin: float = 600.0


def apply_faults(
    fault: FaultState,
    couplings: FaultCouplings = FaultCouplings(),
    *,
    power: float = 285.0,
    speed: float = 0.960,
    sigma: float = 67e-6 / 4,
    material: Material = IN718,
    absorptivity: float = IN718_ABSORPTIVITY,
    form: str = "exponential",
) -> tuple[Beam, Material]:
    """Return the beam and material a given fault state produces.

    Absorptivity and conductivity are multiplied by exponential factors rather
    than linear ones. The linear form 1 + c*f agrees to first order - so the
    Jacobian is unchanged to within the derivative step - but it goes to zero at
    f = -1/c and negative beyond, which is not a large fault, it is a broken
    model: a negative effective conductivity makes the thermal diffusivity
    negative and the Eagar-Tsai integrand imaginary. At
    layer_to_conductivity = 1.0 that happens at a 100% fault, and it did, during
    the coupling sweep - raising a ZeroDivisionError at exactly -1.0 and
    producing NaNs that were then swallowed into finite-looking nonsense beyond
    it. The exponential form is strictly positive everywhere by construction,
    which is also the physically right shape: conductivity interpolates between
    powder and solid and cannot pass through zero.

    `form="linear"` keeps the old behaviour for comparison.
    """
    if form == "exponential":
        mu = absorptivity * np.exp(
            couplings.layer_to_absorptivity * fault.layer
            + couplings.gas_to_attenuation * fault.gas
        )
        k_eff = material.k * np.exp(couplings.layer_to_conductivity * fault.layer)
    elif form == "linear":
        mu = absorptivity * (
            1.0
            + couplings.layer_to_absorptivity * fault.layer
            + couplings.gas_to_attenuation * fault.gas
        )
        k_eff = material.k * (1.0 + couplings.layer_to_conductivity * fault.layer)
    else:
        raise ValueError(f"unknown coupling form {form!r}")
    t0 = material.t_ambient + couplings.geometry_preheat_kelvin * fault.geometry

    # Fail loudly rather than returning a finite-looking number from a model
    # that has left its domain.
    if not 0.0 < mu <= 1.0:
        raise ValueError(f"absorptivity {mu:.4f} outside (0, 1] for {fault}")
    if not k_eff > 0.0:
        raise ValueError(f"effective conductivity {k_eff:.4f} not positive for {fault}")
    if not t0 < material.t_solidus:
        raise ValueError(f"local preheat {t0:.0f} K at or above the solidus for {fault}")

    faulted_material = replace(material, k=k_eff, t_ambient=t0)
    faulted_beam = Beam(
        power=power * (1.0 + fault.power),
        speed=speed * (1.0 + fault.speed),
        sigma=sigma,
        absorptivity=mu,
    )
    return faulted_beam, faulted_material


def observables(
    fault: FaultState,
    couplings: FaultCouplings = FaultCouplings(),
    keyhole_c: float = IN718_KEYHOLE_C,
    **kwargs,
) -> dict[str, float]:
    """Melt pool quantities under a given fault state.

    These are the physical intermediates the sensor models will read. Peak
    temperature is returned but is known to be unphysical in this model class -
    see the Gate 2 note in 05-risks-and-decisions.md.
    """
    beam, material = apply_faults(fault, couplings, **kwargs)
    geom = melt_pool_dimensions(beam, material)
    geom["depth_corrected"] = geom["depth"] + keyhole_c * keyhole_depth(beam, material)
    geom["area"] = np.pi / 4.0 * geom["width"] * geom["length"]
    return geom


if __name__ == "__main__":
    base = observables(FaultState())
    print("nominal:")
    print(f"   width {base['width']*1e6:7.2f} um   depth {base['depth_corrected']*1e6:7.2f} um"
          f"   length {base['length']*1e6:7.1f} um")
    print()
    print("response to a +10 % deviation in each fault, as % change from nominal:")
    print(f"   {'fault':10s}{'width':>10s}{'depth':>10s}{'length':>10s}")
    for name in FAULT_NAMES:
        state = FaultState(**{name: 0.10})
        o = observables(state)
        pct = lambda a, b: 100.0 * (a - b) / b if b else float("nan")
        print(f"   {name:10s}{pct(o['width'], base['width']):>9.2f}%"
              f"{pct(o['depth_corrected'], base['depth_corrected']):>9.2f}%"
              f"{pct(o['length'], base['length']):>9.2f}%")
    print()
    print("Faults with near-identical rows here are the ones Tier 2 will struggle")
    print("to separate. Compare against the Tier 1 prediction in structural.py.")
