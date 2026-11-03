"""Inverting the AM-Bench pad measurements into fault units (paper Section 3.5).

The modulation profiles of Section 3.5 are physical claims, not measurements.
One of the five can nonetheless be calibrated from published data, and this
module is that calibration - plus the one that fails, reported alongside so the
exercise is not cherry-picked.

What is measured
----------------
Weaver et al. (2024), Table 5, report cross-sectional melt pool depth for pads
scanned on bare IN718 under a 4.3 m/s argon cross-flow. The Y-pad is scanned
along the gas-flow axis, so its odd and even tracks run anti-parallel and
parallel to the flow respectively; the X-pad is scanned across the flow and acts
as a control. The numbers below are read from that table.

How the inversion works
-----------------------
A measured *fractional* depth change is matched by the model's own depth
response to the fault in question, by bisection on the fault magnitude. The
change is applied to the model's own baseline depth rather than to the measured
one, so the model's absolute depth error does not enter.

Depth is the channel to invert through because it is where the model is
accurate at the benchmark baseline: +1.7 % against -15.5 % on width.

Contrast units
--------------
`observables.modulations` builds a profile as exp(c*z) with z in [-1, 1], so a
profile of contrast c swings by exp(2c) between its mildest and most severe
segment. A measured swing S therefore corresponds to c = ln(S)/2, which is what
makes the measured and asserted profiles comparable.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).parent))

from eagar_tsai import IN718
from faults import FAULT_NAMES, FaultState
from faults import observables as melt_pool
from observables import PROFILE_CONTRAST

__all__ = ["Y_PAD_ANTIPARALLEL", "Y_PAD_PARALLEL", "X_PAD_CONTROL_CHANGES",
           "CROSS_FLOW_M_S", "pad_depth_changes", "baseline_dimensions",
           "depth_response", "invert_depth_change", "gas_inversion",
           "geometry_inversion", "report"]

# --- Weaver et al. (2024) Table 5, Y-pad depths in micrometres --------------
# Four cross-sections per pad. "odd" tracks run anti-parallel to the gas flow,
# "even" tracks parallel to it.
Y_PAD_SECTION_MM = (0.6, 1.5, 1.9, 2.9)
Y_PAD_ANTIPARALLEL = (175.2, 175.1, 174.0, 170.1)
Y_PAD_PARALLEL = (120.0, 123.5, 124.7, 137.1)
# The X-pad is scanned perpendicular to the flow, so odd and even tracks differ
# only in scan reversal, not in orientation to the gas. Table 5 gives two
# cross-sections; these are the odd-to-even changes read from it.
X_PAD_CONTROL_CHANGES = (-0.0241, -0.0471)
# Standard deviations across all twelve Table 5 rows, micrometres.
Y_PAD_SD_RANGE_UM = (3.9, 10.7)
CROSS_FLOW_M_S = 4.3          # argon cross-flow speed stated by Weaver et al.

# The single-track baseline condition, Weaver case 0. These are the defaults of
# `faults.apply_faults`, which this module relies on rather than re-passing.
BASELINE = dict(power=285.0, speed=0.960, spot_diameter=67e-6)
_D = __import__("inspect").signature(__import__("faults").apply_faults).parameters
assert _D["power"].default == BASELINE["power"]
assert _D["speed"].default == BASELINE["speed"]
assert abs(_D["sigma"].default - BASELINE["spot_diameter"] / 4.0) < 1e-12
MEASURED_SINGLE_TRACK_DEPTH_UM = 139.7


def pad_depth_changes() -> dict[str, float]:
    """Fractional parallel-vs-anti-parallel depth changes from Table 5."""
    odd = np.asarray(Y_PAD_ANTIPARALLEL, float)
    even = np.asarray(Y_PAD_PARALLEL, float)
    rel = even / odd - 1.0
    return {
        "per_section": rel,
        "weakest": float(rel.max()),           # least negative
        "strongest": float(rel.min()),
        "mean": float(rel.mean()),
        "control_mean": float(np.mean(X_PAD_CONTROL_CHANGES)),
        "control_range": (float(min(X_PAD_CONTROL_CHANGES)),
                          float(max(X_PAD_CONTROL_CHANGES))),
        "pad_vs_single_track": float(np.mean(odd) * 1e-6
                                     / (MEASURED_SINGLE_TRACK_DEPTH_UM * 1e-6) - 1.0),
        "antiparallel_mean_um": float(np.mean(odd)),
    }


def _dims(fault: FaultState) -> dict[str, float]:
    """Melt pool dimensions at the benchmark baseline under one fault.

    Routed through `faults.observables`, which is the same path the Jacobian and
    every other result in the paper take, so the inversion cannot drift from the
    rest of the analysis. Its defaults already are the benchmark baseline
    condition; `BASELINE` records them for the report and is asserted against
    them below.
    """
    return melt_pool(fault)


def baseline_dimensions() -> dict[str, float]:
    return _dims(FaultState())


def depth_response(fault_name: str, magnitude: float) -> float:
    """Fractional change in corrected depth for one fault at one magnitude."""
    d0 = baseline_dimensions()["depth_corrected"]
    d = _dims(FaultState(**{fault_name: float(magnitude)}))["depth_corrected"]
    return d / d0 - 1.0


# The model refuses a fault that takes it out of its domain, so each bracket
# stops short of that: preheat must stay below the solidus, which is f < 12.4.
_BRACKET = {"gas": (-0.9, 5.0), "geometry": (-2.0, 12.3),
            "power": (-0.9, 5.0), "speed": (-0.9, 5.0), "layer": (-0.9, 2.0)}


def invert_depth_change(fault_name: str, target: float, bracket=None) -> float:
    """The fault magnitude whose depth response equals `target`."""
    f = lambda m: depth_response(fault_name, m) - target
    lo, hi = bracket if bracket is not None else _BRACKET[fault_name]
    return float(brentq(f, lo, hi, xtol=1e-9))


def gas_inversion() -> dict[str, float]:
    """Section 3.5: the gas profile, calibrated against the pad scans."""
    ch = pad_depth_changes()
    f_control = invert_depth_change("gas", ch["control_mean"])
    f_mean = invert_depth_change("gas", ch["mean"])
    f_weak = invert_depth_change("gas", ch["weakest"])
    f_strong = invert_depth_change("gas", ch["strongest"])
    swing = f_mean / f_control
    asserted_c = PROFILE_CONTRAST[FAULT_NAMES.index("gas")]
    return {
        "f_control": f_control, "f_weakest": f_weak,
        "f_mean": f_mean, "f_strongest": f_strong,
        "swing": swing,
        "measured_contrast": float(np.log(swing) / 2.0),
        "asserted_contrast": float(asserted_c),
        "asserted_swing": float(np.exp(2.0 * asserted_c)),
        "understatement": float(np.log(swing) / 2.0 / asserted_c - 1.0),
    }


def geometry_inversion() -> dict[str, float]:
    """Section 5.2: the same method applied to heat accumulation, which fails.

    Weaver's pads are deeper than single tracks, which the authors attribute to
    heat buildup. Inverting that excess through the preheat channel returns a
    preheat so large it cannot be a measurement: a pad differs from a single
    track by remelting adjacent solidified tracks as well as by preheat, so the
    figure is an upper bound with a second mechanism folded into it.
    """
    ch = pad_depth_changes()
    f_geo = invert_depth_change("geometry", ch["pad_vs_single_track"])
    return {
        "pad_excess": ch["pad_vs_single_track"],
        "f_geometry": f_geo,
        "kelvin": f_geo * 100.0,
        "fraction_to_solidus": f_geo * 100.0 / (IN718.t_solidus - IN718.t_ambient),
        "depth_per_100K": depth_response("geometry", 1.0),
    }


def report() -> None:
    ch = pad_depth_changes()
    b = baseline_dimensions()
    print("AM-BENCH PAD SCANS INVERTED INTO FAULT UNITS")
    print(f"\nmodel baseline at {BASELINE['power']:.0f} W, "
          f"{BASELINE['speed']*1e3:.0f} mm/s, {BASELINE['spot_diameter']*1e6:.0f} um:")
    print(f"   width {b['width']*1e6:.2f} um   depth {b['depth_corrected']*1e6:.2f} um")
    print(f"\nWeaver Table 5, Y-pad parallel vs anti-parallel, by cross-section:")
    for mm, o, e, r in zip(Y_PAD_SECTION_MM, Y_PAD_ANTIPARALLEL,
                           Y_PAD_PARALLEL, ch["per_section"]):
        print(f"   {mm:4.1f} mm   {o:6.1f} -> {e:6.1f} um   {r:+7.2%}")
    print(f"   mean {ch['mean']:+.2%}   range {ch['strongest']:+.2%} to "
          f"{ch['weakest']:+.2%}")
    print(f"   X-pad control (perpendicular): {ch['control_range'][0]:+.2%} and "
          f"{ch['control_range'][1]:+.2%}, mean {ch['control_mean']:+.2%}")
    print(f"   table standard deviations {Y_PAD_SD_RANGE_UM[0]:.1f} to "
          f"{Y_PAD_SD_RANGE_UM[1]:.1f} um")

    g = gas_inversion()
    print("\nGAS: inverted through the model's depth channel")
    print(f"   {'measurement':34s}{'depth change':>14s}{'implied f_gas':>15s}")
    for lab, key, chk in (("perpendicular control", "f_control", "control_mean"),
                          ("parallel, weakest cross-section", "f_weakest", "weakest"),
                          ("parallel, mean of four", "f_mean", "mean"),
                          ("parallel, strongest", "f_strongest", "strongest")):
        print(f"   {lab:34s}{ch[chk]:>13.1%}{g[key]:>15.4f}")
    print(f"\n   swing {g['f_mean']:.4f} / {g['f_control']:.4f} = "
          f"{g['swing']:.2f}x   -> contrast ln(swing)/2 = {g['measured_contrast']:.3f}")
    print(f"   asserted here: contrast {g['asserted_contrast']:.2f}, "
          f"swing {g['asserted_swing']:.2f}x")
    print(f"   the one profile that can be checked is understated by "
          f"{g['understatement']:.1%}")

    q = geometry_inversion()
    print("\nGEOMETRY: the same method, which fails")
    print(f"   Y-pad anti-parallel mean {ch['antiparallel_mean_um']:.1f} um against the "
          f"case-0 single track at {MEASURED_SINGLE_TRACK_DEPTH_UM:.1f} um: "
          f"{q['pad_excess']:+.1%}")
    print(f"   inverting that through the preheat channel: f_geometry = "
          f"{q['f_geometry']:.2f}, i.e. {q['kelvin']:+.0f} K")
    print(f"   that is {q['fraction_to_solidus']:.0%} of the way from ambient to the "
          f"solidus - not credible as a measurement, because a pad remelts")
    print(f"   adjacent tracks as well as preheating them.")
    print(f"   for scale, the model's preheat channel buys "
          f"{q['depth_per_100K']:+.2%} depth per 100 K")


if __name__ == "__main__":
    report()
