"""Diagnosability matrices for sensor suites found on commercial machines.

The abstract promises "matrices reported for configurations found on current
commercial machines". Route B swept *generic* subsets - photodiode only, camera
plus pyrometer. This maps real vendor suites onto the observable set and reports
a matrix for each.

VERIFICATION STATUS - read before citing
----------------------------------------
Vendor sensor details come from secondary literature (reviews and comparative
studies), not from vendor datasheets, and the sources disagree in places. Bands
are commonly withheld: at least one study records that the detection range is
"protected under the confidentiality clause by the supplier". Specific caveats:

  - SLM Solutions MPM is described in one source as two photodiodes with
    different spectral ranges, and in another as a coaxial pyrometer. Modelled
    here as two spectral bands, which is the more conservative reading.
  - Concept Laser QM Meltpool 3D appears only as a table entry: coaxial
    photodiodes giving melt pool area and intensity.
  - EOSTATE Exposure OT is an off-axis camera producing a layer-wise thermal
    map. It is inherently an accumulated observable - it integrates a whole
    layer - which is noted in the results rather than modelled separately.

Every row below must be checked against vendor documentation before submission.
The *method* does not depend on getting these exactly right; the specific
per-vendor conclusions do.

The Renishaw case is the interesting one
----------------------------------------
InfiniAM Spectral is described as two functions: LaserVIEW, "a photosensitive
diode measuring the intensity of the laser energy", and MeltVIEW, capturing melt
pool emissions in NIR and IR.

If LaserVIEW measures laser output *upstream of the plume*, it is a direct
measurement of delivered power that does not see gas attenuation - which is
exactly the Route C sensor that breaks the power/gas confound. Modelled that way
here, flagged as conditional on that reading being right, because it is the one
place where a real commercial machine may already carry the remedy.
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
    "EOS - EOSTATE MeltPool only": {
        "obs": ("photodiode",), "direct": (),
        "note": "coaxial photodiode in the beam path"},
    "EOS - MeltPool + Exposure OT": {
        "obs": ("photodiode", "camera"), "direct": (),
        "note": "coaxial photodiode plus off-axis layer-wise thermal map"},
    "SLM Solutions - MPM": {
        "obs": ("photodiode", "photodiode_swir"), "direct": (),
        "note": "two photodiodes, different spectral ranges (sources conflict)"},
    "Concept Laser - QM Meltpool 3D": {
        "obs": ("photodiode", "camera"), "direct": (),
        "note": "coaxial photodiodes giving melt pool area and intensity"},
    "Renishaw - InfiniAM Spectral": {
        "obs": ("photodiode", "photodiode_swir"), "direct": ("power",),
        "note": "MeltVIEW NIR+IR, plus LaserVIEW measuring laser energy directly"},
    "research-grade reference suite": {
        "obs": ("photodiode", "camera", "pyrometer"), "direct": (),
        "note": "the baseline used throughout this study"},
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

    print("\n\nTHE PAIR THAT SEPARATES THE VENDORS: power / gas (instantaneous)")
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
