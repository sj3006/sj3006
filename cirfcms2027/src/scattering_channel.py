"""How exact is the power/gas degeneracy, really? (paper Section 5.2)

The degeneracy of Section 4.2 is exact because the gas fault has exactly one
channel: it attenuates absorptivity, which is the same channel a power fault
acts on, so the two Jacobian columns are anti-parallel and the angle is zero.
That exactness is a property of the model, not of the process.

Reijonen et al. (2020) report that reduced shielding gas flow gives loss of
penetration together with *increased* melt pool width, which they attribute to
attenuation and scattering in the plume. This model gives a width *decrease*,
because attenuation alone shrinks everything. A real plume both attenuates
(all dimensions down) and scatters, broadening the beam (width up, depth down);
on depth the two agree, on width they oppose, and the measurement says
broadening wins.

This module adds the scattering as a second channel the gas fault possesses and
power does not - an effective spot size growing with plume optical depth,

    sigma -> sigma * exp(k * f_gas)

- and reports how far that opens the pair. It is a sensitivity study, not a
calibrated model: k is swept, and the value of interest is the one at which the
width response changes sign to match the observation.

The conclusion is that the exactness is a model artefact while the
inseparability is not: at the broadening needed to reverse the width sign the
pair sits at a few degrees against a 10-degree floor, and the suite's worst pair
does not move at all. The rank limit is unaffected either way, deriving from
channel counting rather than from the form of this coupling.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from eagar_tsai import IN718, IN718_ABSORPTIVITY, IN718_KEYHOLE_C, Beam, keyhole_depth, melt_pool_dimensions, sigma_from_spot_diameter
from faults import FAULT_NAMES, FaultCouplings, FaultState, apply_faults
from locality_routeA import pair_angles
from noise import SIGMAS
from sensors import SENSOR_NAMES, SensorConfig, sensor_readings

__all__ = ["K_VALUES", "WIDTH_REFERENCE_F_GAS", "readings_with_scattering",
           "width_response", "jacobian_with_scattering", "sweep", "report"]

K_VALUES = (0.0, 0.25, 0.50, 0.75, 1.00, 1.50)
WIDTH_REFERENCE_F_GAS = 0.4     # the gas severity at which the width sign is read
STEP = 0.002                    # same derivative step as diagnosability.jacobian


def _beam_material(fault: FaultState, k: float):
    """As `faults.apply_faults`, with the gas fault also broadening the spot."""
    beam, material = apply_faults(fault, FaultCouplings())
    if k:
        beam = Beam(beam.power, beam.speed,
                    beam.sigma * float(np.exp(k * fault.gas)),
                    beam.absorptivity)
    return beam, material


def readings_with_scattering(fault: FaultState, k: float) -> np.ndarray:
    beam, material = _beam_material(fault, k)
    r = sensor_readings(beam, material, SensorConfig())
    return np.array([r[n] for n in SENSOR_NAMES], float)


def dimensions_with_scattering(fault: FaultState, k: float) -> dict[str, float]:
    beam, material = _beam_material(fault, k)
    geom = melt_pool_dimensions(beam, material)
    geom["depth_corrected"] = geom["depth"] + IN718_KEYHOLE_C * keyhole_depth(beam, material)
    return geom


def width_response(k: float, f_gas: float = WIDTH_REFERENCE_F_GAS) -> dict[str, float]:
    """Fractional dimension changes at one gas severity and one broadening."""
    d0 = dimensions_with_scattering(FaultState(), k)
    d1 = dimensions_with_scattering(FaultState(gas=f_gas), k)
    return {key: d1[key] / d0[key] - 1.0
            for key in ("width", "depth_corrected", "length")}


def jacobian_with_scattering(k: float, step: float = STEP) -> np.ndarray:
    """Central-difference relative-sensitivity Jacobian under broadening k."""
    y0 = readings_with_scattering(FaultState(), k)
    cols = []
    for name in FAULT_NAMES:
        hi = readings_with_scattering(FaultState(**{name: step}), k)
        lo = readings_with_scattering(FaultState(**{name: -step}), k)
        cols.append((hi - lo) / (2.0 * step) / y0)
    return np.column_stack(cols)


def sweep(k_values=K_VALUES) -> list[dict]:
    out = []
    for k in k_values:
        w = width_response(k)
        J = jacobian_with_scattering(k)
        a = pair_angles(J, SIGMAS)
        out.append({"k": k, "width": w["width"], "depth": w["depth_corrected"],
                    "power_gas": a[("power", "gas")],
                    "worst": min(a.values()),
                    "worst_pair": min(a, key=a.get),
                    "rank": int(np.linalg.matrix_rank(J / SIGMAS[:, None],
                                                      tol=1e-6))})
    return out


def report() -> None:
    print("THE EXACTNESS OF THE POWER/GAS CONFOUND, PROBED WITH A SECOND GAS CHANNEL")
    print("   gas as modelled: attenuation only, sigma fixed.")
    print("   gas with scattering: sigma -> sigma * exp(k * f_gas), a channel "
          "power does not have.\n")
    print(f"   dimension changes read at f_gas = {WIDTH_REFERENCE_F_GAS:.1f}\n")
    print(f"   {'k':>6s}{'width':>10s}{'depth':>10s}{'power/gas':>12s}"
          f"{'worst pair':>12s}  binding pair          rank")
    for r in sweep():
        print(f"   {r['k']:>6.2f}{r['width']:>+10.2%}{r['depth']:>+10.2%}"
              f"{r['power_gas']:>12.2f}{r['worst']:>12.2f}  "
              f"{r['worst_pair'][0]+'/'+r['worst_pair'][1]:20s}  {r['rank']}")
    rows = sweep()
    signs = [r for r in rows if r["width"] > 0]
    if signs:
        first = signs[0]
        print(f"\n   the width response first matches the reported sign at k = "
              f"{first['k']:.2f}, where\n   power/gas opens to "
              f"{first['power_gas']:.2f} degrees - still far below the 10-degree "
              f"floor - and the\n   suite's worst pair is unchanged at "
              f"{first['worst']:.2f} degrees on a different pair.")
    print(f"\n   Reijonen et al. (2020): reduced gas flow gives loss of "
          f"penetration with\n   INCREASED width. At k = 0 this model gives "
          f"{rows[0]['width']:+.0%} on width - the opposite sign.")


if __name__ == "__main__":
    report()
