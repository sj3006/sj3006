"""Sweep the fault coupling constants, the last unswept assertion in the study.

`FaultCouplings` says how each fault acts on the model's inputs: a thinner layer
lowers absorptivity and raises effective conductivity, degraded gas attenuates
the beam, a thin feature preheats the substrate. The values are
order-of-magnitude estimates with signs fixed by physics and nothing more. They
set the *direction* of each fault's signature, so the isolability angles depend
on them directly and the paper cannot report angles without reporting this sweep.

Two of the four behave completely differently, and the difference is the most
instructive thing in the study.

**gas_to_attenuation rescales, it does not rotate.** Degraded gas acts purely as
a multiplier on absorptivity, and the Eagar-Tsai temperature rise is linear in
the product (absorptivity x power). So changing this coupling multiplies the
entire gas column of the Jacobian by a constant and leaves its direction
untouched. Power does the same thing through the power multiplier. The two
signatures are therefore *exactly* parallel for any value of the coupling, and
no choice of constant can separate them. That is why the power/gas confounding
is a structural statement rather than a numerical accident, and why Tier 1 found
it independently of any number.

**The two layer couplings compete, so they do rotate.** A thinner layer lowers
absorptivity (which acts like a power change) and raises conductivity (which
does not). The layer signature's direction is set by the *ratio* of the two, so
as the conductivity coupling goes to zero the layer fault collapses onto power,
and the power/layer angle must go to zero with it. The sweep locates that.

The test that matters for the paper is whether Route A's separation survives
across all of it.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from diagnosability import jacobian
from faults import FAULT_NAMES, FaultCouplings
from locality_routeA import SIGMAS, pair_angles, rank_cond, response_curves, secant_directions
from observables import enlarged_jacobian, scan_plan

__all__ = ["RANGES", "sweep_one", "summarise"]

# Each range is physically bounded, not arbitrary. Defaults are starred in the
# report.
RANGES = {
    # Powder absorptivity is roughly 0.4-0.7 from multiple reflections in the
    # bed; bare solid is nearer 0.3. A full fractional layer change therefore
    # cannot swing absorptivity by more than about half, and the sign is fixed:
    # less powder means less trapping.
    "layer_to_absorptivity": (-0.60, -0.45, -0.30, -0.15, -0.05),
    # Powder conductivity is ~0.2-1 W/mK against 35 for solid IN718, so removing
    # insulating powder can raise the effective value substantially. Sign fixed.
    "layer_to_conductivity": (0.0, 0.10, 0.25, 0.50, 1.00, 1.50),
    # Plume and spatter attenuation. Sign fixed; magnitude poorly known.
    "gas_to_attenuation": (-0.50, -0.35, -0.20, -0.10, -0.05),
    # Kelvin of substrate preheat per unit geometry fault. 600 K/unit means a 10%
    # fault preheats by 60 K, the right order for a thin wall or an overhang.
    "geometry_preheat_kelvin": (200.0, 400.0, 600.0, 900.0, 1200.0),
}

DEFAULTS = FaultCouplings()
PAIRS_OF_INTEREST = (("power", "gas"), ("power", "layer"), ("power", "speed"))


def summarise(D):
    a = pair_angles(D, SIGMAS)
    r, c = rank_cond(D)
    return {"worst": min(a.values()), "angles": a, "rank": r, "cond": c}


def sweep_one(name, value, plan, f=0.05):
    """Instantaneous and enlarged diagnosability at one coupling value."""
    cpl = replace(DEFAULTS, **{name: value})
    J, _ = jacobian(couplings=cpl)
    inst = summarise(J)
    lim = summarise(enlarged_jacobian(J, plan))
    curves, nominal = response_curves(cpl)
    fin = summarise(secant_directions(f, plan, curves, nominal))
    return inst, lim, fin


if __name__ == "__main__":
    plan = scan_plan()
    F = 0.05

    print("FAULT COUPLING SWEEP")
    print(f"instantaneous vs enlarged (derivative limit) vs enlarged at a "
          f"{F:+.0%} fault\n")

    for name, values in RANGES.items():
        print(f"{name}   (default {getattr(DEFAULTS, name)})")
        print(f"   {'value':>9s} | {'inst worst':>10s}{'pwr/gas':>9s}"
              f"{'pwr/layer':>11s}{'rank':>6s} | {'lim worst':>10s}{'rank':>6s}"
              f"{'cond':>7s} | {'fin worst':>10s}{'rank':>6s}{'cond':>7s}")
        for v in values:
            inst, lim, fin = sweep_one(name, v, plan, F)
            star = " *" if v == getattr(DEFAULTS, name) else "  "
            print(f"   {v:>9.2f}{star[1]}| {inst['worst']:>10.2f}"
                  f"{inst['angles'][('power', 'gas')]:>9.2f}"
                  f"{inst['angles'][('power', 'layer')]:>11.2f}{inst['rank']:>6d} | "
                  f"{lim['worst']:>10.2f}{lim['rank']:>6d}{lim['cond']:>7,.0f} | "
                  f"{fin['worst']:>10.2f}{fin['rank']:>6d}{fin['cond']:>7,.0f}")
        print()

    print("THE STRUCTURAL CLAIM, CHECKED EXACTLY")
    J0, _ = jacobian()
    for v in RANGES["gas_to_attenuation"]:
        Jv, _ = jacobian(couplings=replace(DEFAULTS, gas_to_attenuation=v))
        ratio = Jv[:, 3] / J0[:, 3]
        spread = float(ratio.max() - ratio.min())
        print(f"   gas coupling {v:+.2f}: gas column scales by "
              f"{ratio.mean():.4f} in every sensor (spread {spread:.2e}), "
              f"power/gas angle {pair_angles(Jv, SIGMAS)[('power', 'gas')]:.2f} deg")
    print("   -> a pure rescale. The confounding is structural: no value of this "
          "constant can break it.")
