"""Where the layer fault's coupling constants come from (paper Section 3.2).

The layer fault is a fractional layer-thickness deviation, positive for a
thinner layer. It reaches the thermal model through three channels, and two of
them are derived from published measurement rather than chosen. This module is
that derivation in executable form, so the constants written into
`faults.FaultCouplings` can be checked against their own arithmetic rather than
read from a docstring, and so the sensitivity of each to its inputs is
reproducible.

The third channel - layer thickness to effective conductivity - is an estimate,
not a derivation. It has no function here; it is swept in `coupling_sweep.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from eagar_tsai import IN718, IN718_ABSORPTIVITY
from faults import FaultCouplings, FaultState
from faults import observables as melt_pool

__all__ = ["POWDER_SOLID_RATIO", "D50_UM", "NOMINAL_LAYER_UM", "PACKING",
           "LATENT_HEAT_J_KG", "absorptivity_coupling", "enthalpy_coupling",
           "channel_decomposition", "report"]

# --- inputs, with their sources ---------------------------------------------
# Trapp et al. (2017) measured, in situ at 1070 nm, powder absorptivity about
# twice that of a bare polished disc for ~100 um layers.
POWDER_SOLID_RATIO = 2.0
# Radiative-transfer treatments of metal powder beds put the radiation
# penetration depth at a few particle diameters. d50 = 30 um is a typical IN718
# LPBF cut, so the saturation length is taken as 2 * d50.
D50_UM = 30.0
PENETRATION_IN_D50 = 2.0
NOMINAL_LAYER_UM = 40.0
# Powder bed packing fraction and the latent heat of fusion for IN718.
PACKING = 0.55
LATENT_HEAT_J_KG = 270e3
# The track width the melted cross-section is taken over: the model's own width
# at the benchmark baseline, so the energy balance is internally consistent.
TRACK_WIDTH_UM = 115.0


def absorptivity_coupling(ratio: float = POWDER_SOLID_RATIO,
                          d50_um: float = D50_UM,
                          layer_um: float = NOMINAL_LAYER_UM) -> dict:
    """d(ln A)/d(ln t) for a powder bed whose absorptivity saturates with depth.

        A(t) = A_s + (A_p - A_s) * (1 - exp(-t / delta)),   A_p = ratio * A_s

    with delta the radiation penetration depth. The coupling is minus this
    derivative, because the fault is positive for a *thinner* layer.
    """
    delta = PENETRATION_IN_D50 * d50_um
    x = layer_um / delta
    # A(t) / A_s
    enhancement = 1.0 + (ratio - 1.0) * (1.0 - np.exp(-x))
    # d(lnA)/d(ln t) = (t/A) dA/dt
    dA_dt_over_As = (ratio - 1.0) / delta * np.exp(-x)
    dln = layer_um * dA_dt_over_As / enhancement
    return {"delta_um": delta, "enhancement": float(enhancement),
            "dlnA_dlnt": float(dln), "coupling": float(-dln),
            "implied_solid_absorptivity": IN718_ABSORPTIVITY / float(enhancement)}


def enthalpy_coupling(layer_um: float = NOMINAL_LAYER_UM,
                      width_um: float = TRACK_WIDTH_UM,
                      packing: float = PACKING) -> dict:
    """The fraction of absorbed energy spent melting the powder, and its coupling.

    Per unit track length at the nominal condition. A thinner layer spends less
    of the absorbed energy melting powder and leaves more to penetrate the
    substrate, so normalising about f = 0 the effective-power multiplier is
    1 + f * phi / (1 - phi).
    """
    absorbed = IN718_ABSORPTIVITY * 285.0 / 0.960            # J per metre
    area = layer_um * width_um * packing * 1e-12             # m^2
    mass = IN718.rho * area                                  # kg per metre
    enthalpy = (IN718.cp * (IN718.t_liquidus - IN718.t_ambient)
                + LATENT_HEAT_J_KG)                          # J per kg
    melting = mass * enthalpy                                # J per metre
    phi = melting / absorbed
    return {"absorbed_J_per_m": absorbed, "area_um2": area * 1e12,
            "mass_mg_per_m": mass * 1e6, "enthalpy_kJ_per_kg": enthalpy / 1e3,
            "melting_J_per_m": melting, "phi": float(phi),
            "coupling": float(phi / (1.0 - phi))}


def channel_decomposition(f: float = 0.2) -> dict:
    """Each layer channel's effect on melt pool dimensions, isolated.

    The first two channels act on the product (absorptivity x power) and nearly
    cancel there; the conductivity channel is what remains, which is why it is
    load-bearing instantaneously despite being the one unmeasured constant.
    """
    d = FaultCouplings()
    zero = dict(layer_to_absorptivity=0.0, layer_to_powder_enthalpy=0.0,
                layer_to_conductivity=0.0)
    cases = {
        "absorptivity": {**zero, "layer_to_absorptivity": d.layer_to_absorptivity},
        "enthalpy": {**zero, "layer_to_powder_enthalpy": d.layer_to_powder_enthalpy},
        "conductivity": {**zero, "layer_to_conductivity": d.layer_to_conductivity},
        "absorptivity + enthalpy": {
            **zero, "layer_to_absorptivity": d.layer_to_absorptivity,
            "layer_to_powder_enthalpy": d.layer_to_powder_enthalpy},
        "all three": {"layer_to_absorptivity": d.layer_to_absorptivity,
                      "layer_to_powder_enthalpy": d.layer_to_powder_enthalpy,
                      "layer_to_conductivity": d.layer_to_conductivity},
    }
    out = {}
    for name, kw in cases.items():
        c = FaultCouplings(**kw)
        base = melt_pool(FaultState(), c)
        hit = melt_pool(FaultState(layer=f), c)
        out[name] = {
            # depth_corrected is what the sensors see: the keyhole term scales
            # with absorbed power, so a channel acting on absorptivity moves it
            # about 40% more than it moves the plain conduction depth. Both are
            # reported because an earlier version of this table quoted the
            # conduction depth without saying so.
            "depth": hit["depth_corrected"] / base["depth_corrected"] - 1.0,
            "depth_conduction": hit["depth"] / base["depth"] - 1.0,
            "width": hit["width"] / base["width"] - 1.0,
        }
    return out


def report() -> None:
    d = FaultCouplings()
    a = absorptivity_coupling()
    print("THE LAYER FAULT'S THREE CHANNELS\n")
    print("1. ABSORPTIVITY, derived from Trapp et al. (2017)")
    print(f"   powder/solid absorptivity ratio {POWDER_SOLID_RATIO:.1f} at 1070 nm, "
          f"saturation length {a['delta_um']:.0f} um ({PENETRATION_IN_D50:.0f} x d50)")
    print(f"   at a {NOMINAL_LAYER_UM:.0f} um layer, A(t)/A_solid = "
          f"{a['enhancement']:.3f}")
    print(f"   d(lnA)/d(ln t) = {a['dlnA_dlnt']:+.4f}  ->  coupling "
          f"{a['coupling']:+.4f}   (model holds {d.layer_to_absorptivity:+.3f})")
    print(f"   self-consistency: implied bare-solid absorptivity = "
          f"{IN718_ABSORPTIVITY:.3f} / {a['enhancement']:.3f} = "
          f"{a['implied_solid_absorptivity']:.3f},")
    print(f"      against 0.25-0.35 reported for nickel alloys near 1 um. The "
          f"calibration\n      was not built to produce that.")
    print("   sensitivity, over d50 15-45 um and ratio 1.5-2.5:")
    lo, hi = 1e9, -1e9
    for d50 in (15.0, 30.0, 45.0):
        for ratio in (1.5, 2.0, 2.5):
            c = absorptivity_coupling(ratio=ratio, d50_um=d50)["coupling"]
            lo, hi = min(lo, c), max(hi, c)
    print(f"      {lo:+.3f} to {hi:+.3f}")

    e = enthalpy_coupling()
    print("\n2. POWDER-MELTING ENTHALPY, from an energy balance")
    print(f"   absorbed energy      A*P/v = {IN718_ABSORPTIVITY:.3f}*285/0.960 "
          f"= {e['absorbed_J_per_m']:.1f} J/m")
    print(f"   powder cross-section {NOMINAL_LAYER_UM:.0f} x {TRACK_WIDTH_UM:.0f} um "
          f"x {PACKING:.2f} packing = {e['area_um2']:.0f} um^2")
    print(f"   mass per unit length {IN718.rho:.0f} x that = "
          f"{e['mass_mg_per_m']:.1f} mg/m")
    print(f"   enthalpy to melt     {IN718.cp:.0f}*({IN718.t_liquidus:.0f}"
          f"-{IN718.t_ambient:.0f}) + {LATENT_HEAT_J_KG/1e3:.0f}e3 = "
          f"{e['enthalpy_kJ_per_kg']:.0f} kJ/kg")
    print(f"   energy to melt the layer = {e['melting_J_per_m']:.1f} J/m")
    print(f"   phi = {e['phi']:.4f}, i.e. {e['phi']:.1%} of the absorbed energy")
    print(f"   coupling phi/(1-phi) = {e['coupling']:+.4f}   "
          f"(model holds {d.layer_to_powder_enthalpy:+.3f})")

    print("\n3. CONDUCTIVITY: an estimate, not a derivation")
    print(f"   model holds {d.layer_to_conductivity:+.2f}, swept 0 to 1.5 in "
          f"coupling_sweep.py")

    net = d.layer_to_absorptivity + d.layer_to_powder_enthalpy
    print(f"\nTHE TWO DERIVED CHANNELS NEARLY CANCEL on the absorbed-power "
          f"product:\n   {d.layer_to_absorptivity:+.3f} "
          f"{d.layer_to_powder_enthalpy:+.3f} = {net:+.3f}")
    print("\nEACH CHANNEL'S EFFECT ON THE POOL, isolated at f_layer = 0.2")
    print(f"   {'channel':26s}{'depth':>9s}{'width':>9s}"
          f"{'(conduction depth)':>20s}")
    for name, r in channel_decomposition().items():
        print(f"   {name:26s}{r['depth']:>+9.2%}{r['width']:>+9.2%}"
              f"{r['depth_conduction']:>+20.2%}")
    print("   With the conductivity channel set to zero the layer column "
          f"becomes exactly\n   {net:+.3f} times the power column, and "
          "power/layer and layer/gas both collapse\n   to 0.00 degrees - see "
          "coupling_sweep.py, layer_to_conductivity = 0.")


if __name__ == "__main__":
    report()
