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
    """How each fault reaches the thermal model's inputs.

    Earlier versions of this class held four constants chosen as round numbers of
    the right sign and order. That is not defensible in a paper, so each is now
    either (a) derived from published measurements, with the derivation and its
    sensitivity recorded, or (b) eliminated by defining the fault as a physical
    quantity, or (c) explicitly marked as the one remaining estimate.

    Fault definitions, all now physical
    -----------------------------------
    f_power     fractional power deviation. Direct.
    f_speed     fractional speed deviation. Direct.
    f_layer     fractional layer-THICKNESS deviation, positive = thinner.
    f_gas       optical depth of the plume along the beam path. Beer-Lambert
                gives transmission exp(-f_gas), so f_gas = 0.2 is 18%
                attenuation. No conversion constant exists to be chosen.
    f_geometry  local preheat rise in units of 100 K. f = 1 is +100 K, which is
                the documented order for a thin wall or overhang.

    (a) layer_to_absorptivity = -0.230, DERIVED
    ------------------------------------------
    A powder bed absorbs more than bare solid because light scatters between
    particles. Trapp et al. (Applied Materials Today, 2017) measured, in situ at
    1070 nm, powder absorptivity about **twice** that of the bare polished disc
    for ~100 um layers. Radiative-transfer treatments of metal powder beds put
    the radiation penetration depth at a few particle diameters.

    Model that as saturation with thickness:

        A(t) = A_s + (A_p - A_s) * (1 - exp(-t / delta)),   A_p = 2 * A_s

    with delta = 2 * d50 = 60 um (d50 = 30 um, typical IN718 LPBF cut) and a
    nominal layer t0 = 40 um. Then A(t0) = 1.487 * A_s, and since f_layer is
    positive for a *thinner* layer,

        layer_to_absorptivity = -d(lnA)/d(ln t) = -0.230

    **Self-consistency check.** That implies a bare-solid absorptivity of
    0.384 / 1.487 = 0.258, and bare nickel alloy at ~1 um is roughly 0.25-0.35.
    So the Gate 1 fitted value and this derivation agree independently, which
    neither was built to do.

    Sensitivity: across d50 of 15-45 um and a powder/solid ratio of 1.5-2.5, the
    coefficient runs -0.12 to -0.30. Swept over that range.

    (a) layer_to_powder_enthalpy = +0.186, DERIVED - and it was MISSING
    ------------------------------------------------------------------
    The model had no term for the energy spent melting the powder itself, which
    is not a small correction. Per unit track length, at the nominal condition:

        absorbed energy          A*P/v = 0.384*285/0.960       = 114.0 J/m
        powder cross-section     40um * 115um * 0.55 packing   = 2530 um^2
        mass per unit length     8190 * that                   = 20.7 mg/m
        enthalpy to melt         450*(1609-293) + 270e3        = 862 kJ/kg
        energy to melt the layer                               = 17.9 J/m

    So melting the powder consumes **15.7%** of the absorbed energy. A thinner
    layer spends less of it there and leaves more to penetrate the substrate.
    Normalising so that f = 0 is unchanged, the effective-power multiplier is
    1 + f * phi/(1 - phi) with phi = 0.157, giving

        layer_to_powder_enthalpy = +0.186

    This matters more than its size suggests. It acts in the **opposite**
    direction to the absorptivity term and is of the same order - 1.6% against
    3.0% equivalent power change per 10% layer deviation - so omitting it left
    the net sign of the layer fault unreliable. See the record for what that did
    to the power/layer result.

    (c) layer_to_conductivity = +0.50, THE ONE REMAINING ESTIMATE
    ------------------------------------------------------------
    Less insulating powder beneath the track raises the effective conductivity
    the melt pool sees. Published values bracket the powder itself at roughly a
    tenth to a hundredth of solid, and loose-powder conduction is dominated by
    the gas in the pores. But the conductivity in this model is a *lumped fitted*
    parameter, not the powder's own, so the published ratio does not transfer and
    no measurement constrains its sensitivity to layer thickness.

    It is kept, declared an estimate, and swept 0 to 1.5. It is also by far the
    weakest of the three layer effects: isolating each at f = 0.2 moves the melt
    depth by 3.4% (absorptivity), 1.6% (enthalpy) and 0.35% (conductivity).
    """

    layer_to_absorptivity: float = -0.230
    layer_to_powder_enthalpy: float = +0.186
    layer_to_conductivity: float = +0.50
    geometry_preheat_kelvin: float = 100.0


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
    # Plume attenuation is Beer-Lambert with f_gas as the optical depth, so no
    # conversion constant is involved in either form.
    if form == "exponential":
        mu = absorptivity * np.exp(
            couplings.layer_to_absorptivity * fault.layer - fault.gas
        )
        k_eff = material.k * np.exp(couplings.layer_to_conductivity * fault.layer)
        power_scale = np.exp(couplings.layer_to_powder_enthalpy * fault.layer)
    elif form == "linear":
        mu = absorptivity * (
            1.0 + couplings.layer_to_absorptivity * fault.layer
        ) * np.exp(-fault.gas)
        k_eff = material.k * (1.0 + couplings.layer_to_conductivity * fault.layer)
        power_scale = 1.0 + couplings.layer_to_powder_enthalpy * fault.layer
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
        power=power * (1.0 + fault.power) * power_scale,
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
