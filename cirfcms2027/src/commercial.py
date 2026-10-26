"""Diagnosability matrices for sensor suites typical of commercial machines.

The abstract promises matrices for "configurations found on current commercial
machines". Route B swept generic subsets; this covers the configurations that
are actually fitted.

No vendor is named
------------------
Two reasons, and the second is the stronger one.

First, the mapping from product to observable rests on **secondary review
literature rather than vendor datasheets**. Detection bands are routinely
withheld under supplier confidentiality - one survey records them as "protected
under the confidentiality clause by the supplier" - and published descriptions
of the same product disagree. Attaching a named product to a computed
diagnosability limit on that basis would assert more than the evidence carries.

Second, **naming adds nothing**. The result depends only on what a suite
measures, not on whose badge is on it. Stripping the names also reveals
something the vendor-by-vendor table hid: across five commercial systems there
are only **three distinct configurations**. Several vendors ship what is, for
this analysis, the same instrument set.

The configurations below are described by their contents. Readers who wish to
map them to products can do so from the monitoring surveys cited in the paper.

The unresolved case, handled conservatively
-------------------------------------------
One commercial system is described as pairing melt pool emission sensing with a
photodiode that measures laser energy. Whether that photodiode samples the beam
**upstream of the process zone** or views it through the process window changes
the answer completely:

    upstream    a direct measurement of delivered power that cannot see plume
                attenuation - the sensor that breaks the power/gas confound
    downstream  another melt-pool observable: a row, not a direction

This could not be established from public documentation, so the conservative
reading is taken - downstream, the assumption that does **not** flatter this
analysis. The upstream case is retained as configuration E, a configuration
*type* rather than any product, because the design lesson holds regardless of
which machine implements it.
"""

from __future__ import annotations

import numpy as np

from faults import FAULT_NAMES
from locality_routeA import pair_angles, rank_cond
from matrix import FLOOR, PAIRS, classify
from observables import coefficient_sigmas, enlarged_jacobian, scan_plan
from route_b import full_jacobian
from route_c_added_sensor import add_direct_sensor
from sensors import ALL_SENSOR_NAMES

__all__ = ["CONFIGS", "report"]

# Mapping onto this study's observable set. `direct` names a fault measured
# directly rather than through the melt pool.
CONFIGS = {
    "A  single coaxial photodiode": {
        "obs": ("photodiode",), "direct": (),
        "note": "one melt pool emission channel; the minimum fitted suite"},
    "B  photodiode + melt pool imaging": {
        "obs": ("photodiode", "camera"), "direct": (),
        "note": "emission plus pool area; two commercial systems map here"},
    "C  two photodiodes, separate bands": {
        "obs": ("photodiode", "photodiode_swir"), "direct": (),
        "note": "two emission channels at different wavelengths; two systems map here"},
    "D  research reference": {
        "obs": ("photodiode", "camera", "pyrometer"), "direct": (),
        "note": "emission, pool area and two-colour pyrometry; the study baseline"},
    "E  C plus upstream power monitoring": {
        "obs": ("photodiode", "photodiode_swir"), "direct": ("power",),
        "note": "CONFIGURATION TYPE: adds delivered-power sensing before the plume"},
}

ADDED_SIGMA = 0.05


def _angles(cfg, plan):
    J_all, _ = full_jacobian()
    idx = [list(ALL_SENSOR_NAMES).index(n) for n in cfg["obs"]]
    J = J_all[idx, :]
    sig = np.array([1.0 if "pyrometer" not in n else 0.03 for n in cfg["obs"]])
    if cfg["direct"]:
        J, sig = add_direct_sensor(J, sig, list(cfg["direct"]), ADDED_SIGMA)
    inst = pair_angles(J, sig)
    ri, ci = rank_cond(J, sig)
    # the enlarged observation uses the same rows, regressed onto build context
    big = enlarged_jacobian(J, plan)
    bsig = coefficient_sigmas(sig, plan)
    enl = pair_angles(big, bsig)
    re_, ce = rank_cond(big, bsig)
    return inst, enl, (ri, ci, re_, ce)


def report() -> None:
    plan = scan_plan()
    print(f"COMMERCIAL CONFIGURATIONS   (separation floor {FLOOR:.0f} degrees)\n")
    print(f"   {'configuration':34s}{'rank':>5s}{'cls1':>6s}{'cls2':>6s}{'cls3':>6s} | "
          f"{'rank':>5s}{'cls1':>6s}{'worst':>8s}")
    print(f"   {'':34s}{'--- instantaneous ---':>23s} | {'--- accumulated ---':>19s}")
    detail = {}
    for name, cfg in CONFIGS.items():
        inst, enl, (ri, ci, re_, ce) = _angles(cfg, plan)
        c1i = sum(1 for p in PAIRS if inst[p] >= FLOOR)
        c1e = sum(1 for p in PAIRS if enl[p] >= FLOOR)
        # class 2 instantaneous: a direct measurement of either fault would clear it
        J_all, _ = full_jacobian()
        idx = [list(ALL_SENSOR_NAMES).index(n) for n in cfg["obs"]]
        J = J_all[idx, :]
        sig = np.array([1.0 if "pyrometer" not in n else 0.03 for n in cfg["obs"]])
        if cfg["direct"]:
            J, sig = add_direct_sensor(J, sig, list(cfg["direct"]), ADDED_SIGMA)
        resc = {f: pair_angles(*add_direct_sensor(J, sig, [f], ADDED_SIGMA))
                for f in FAULT_NAMES}
        c2 = sum(1 for p in PAIRS if inst[p] < FLOOR
                 and max(resc[f][p] for f in p) >= FLOOR)
        c3 = 10 - c1i - c2
        detail[name] = (inst, enl)
        print(f"   {name:34s}{ri:>5d}{c1i:>6d}{c2:>6d}{c3:>6d} | "
              f"{re_:>5d}{c1e:>6d}{min(enl.values()):>8.2f}")

    print("\n\nTHE PAIR THAT SEPARATES THE CONFIGURATIONS: power / gas (instantaneous)")
    for name, cfg in CONFIGS.items():
        inst, _ = detail[name]
        v = inst[("power", "gas")]
        tag = "SEPARATED" if v >= FLOOR else "confounded"
        print(f"   {name:34s}{v:>8.2f} deg   {tag}   ({cfg['note']})")

    print("\n\nFULL INSTANTANEOUS ANGLES BY CONFIGURATION (degrees)")
    names = list(CONFIGS)
    print(f"   {'pair':20s}" + "".join(f"{i+1:>8d}" for i in range(len(names))))
    for p in sorted(PAIRS, key=lambda q: detail[names[-1]][0][q]):
        print(f"   {p[0]+' / '+p[1]:20s}"
              + "".join(f"{detail[n][0][p]:>8.2f}" for n in names))
    print()
    for i, n in enumerate(names):
        print(f"   {i+1} = {n}")


if __name__ == "__main__":
    report()
