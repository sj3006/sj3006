"""The diagnosability matrix: the paper's headline deliverable.

The accepted abstract promises "a diagnosability matrix per sensor
configuration, separating fault pairs into those resolvable from the temporal
and spatial structure of existing signals, those requiring an additional
measurement, and those structurally irreducible for the configuration."

Every ingredient exists across the other modules; nothing assembled them into
the artefact the abstract names. This does.

Two regimes, because one matrix is degenerate
---------------------------------------------
Classifying on the enlarged observation alone puts **all ten pairs in class 1
for every configuration, including a single photodiode**. That is a true
statement and a useless matrix: classes 2 and 3 come out empty and the artefact
discriminates nothing.

The reason is Route A itself. Regressing onto known build context converts a
static problem (3 equations, 5 unknowns) into a regression whose equation count
is set by the number of known regressors, so one sensor already reaches rank 5.

So the matrix is reported in **two regimes**, and the distinction is an
engineering one a machine builder actually faces:

    INSTANTANEOUS   decisions taken per segment, in real time, with no
                    opportunity to accumulate context across a build. Closed-
                    loop control lives here.
    ACCUMULATED     diagnosis over a completed build or a substantial part of
                    one, where the spatial and temporal structure is available.
                    Post-build qualification and drift monitoring live here.

The instantaneous regime is where the structure is, and it is the regime in
which the "requires an additional measurement" class is populated. The
accumulated regime is the paper's positive result.

The three classes, made operational
-----------------------------------
For each fault pair, in a given regime, in order. First test that passes wins.

**Class 1 - resolvable from existing signals.** The regime's own observation
separates the pair by at least FLOOR degrees. No new hardware.

**Class 2 - requires an additional measurement.** Class 1 fails, but an
idealised direct measurement of one of the two faults clears the pair. Route C
shows what such a measurement would be and that its precision barely matters.
Reported with *which* measurement does it, since that is the actionable part.

**Class 3 - structurally irreducible for the configuration.** Neither works.
The pair cannot be separated by this suite however it is processed, and no
single direct cause measurement rescues it either.

A fourth label is carried alongside, because it means something different and
stronger than class 1:

**Structurally isolable (Tier 1).** The pair is separable from the *zero
pattern* of the equations alone, with no reliance on calibrated magnitudes. A
class 1 pair that is also structurally isolable survives any amount of
calibration error; one that is not relies on the magnitudes being right. That
distinction is what the two tiers are for and it belongs in the matrix.

What the matrix is conditional on
---------------------------------
Noise ratios (swept; see the noise note), the modulation profiles (asserted and
swept), and the fault couplings (two derived, one estimated, all swept). The
matrix is reported with its threshold and its assumptions stated, not as an
absolute.
"""

from __future__ import annotations

import numpy as np

from diagnosability import jacobian
from faults import FAULT_NAMES
from locality_routeA import SIGMAS, pair_angles, rank_cond
from observables import coefficient_sigmas, enlarged_jacobian, scan_plan
from route_b import full_jacobian
from route_c_added_sensor import add_direct_sensor
from sensors import ALL_SENSOR_NAMES
from structural_enlarged import FAULTS as TIER1_FAULTS
from structural_enlarged import enlarged_equations, isolability
from observables import projection_matrix

__all__ = ["FLOOR", "STRUCT_THRESHOLD", "classify", "render", "CLASS_LABEL",
           "contrast_to_clear"]

FLOOR = 10.0              # degrees; the practical separation floor
STRUCT_THRESHOLD = 0.05   # |B[j,k]| above which a fault counts as present in a channel
ADDED_SENSOR_SIGMA = 0.05 # relative noise of the idealised direct measurement

PAIRS = [(a, b) for i, a in enumerate(FAULT_NAMES) for b in FAULT_NAMES[i + 1:]]
CLASS_LABEL = {1: "existing signals", 2: "needs a measurement", 3: "irreducible"}
TIER1_OF = dict(zip(FAULT_NAMES, TIER1_FAULTS))


def classify(sensor_subset, plan=None, floor=FLOOR, regime="accumulated"):
    """Classify every fault pair for one sensor configuration, in one regime."""
    plan = scan_plan() if plan is None else plan
    J_all, _ = full_jacobian()
    idx = [list(ALL_SENSOR_NAMES).index(n) for n in sensor_subset]
    J = J_all[idx, :]
    sig = np.array([1.0 if "pyrometer" not in n else 0.03 for n in sensor_subset])

    inst = pair_angles(J, sig)
    big = enlarged_jacobian(J, plan)
    bsig = coefficient_sigmas(sig, plan)
    enl = pair_angles(big, bsig)

    # Class 2 test: does an idealised direct measurement of either fault clear it?
    rescue = {}
    for f in FAULT_NAMES:
        Jn, sn = add_direct_sensor(J, sig, [f], ADDED_SENSOR_SIGMA)
        rescue[f] = pair_angles(Jn, sn)

    # Tier 1, on the enlarged observation set for this configuration
    B = projection_matrix(plan)
    iso = isolability(enlarged_equations(B, STRUCT_THRESHOLD), TIER1_FAULTS)

    primary = enl if regime == "accumulated" else inst
    rows = {}
    for p in PAIRS:
        a, b = p
        structural = iso[(TIER1_OF[a], TIER1_OF[b])] and iso[(TIER1_OF[b], TIER1_OF[a])]
        if primary[p] >= floor:
            cls, by = 1, None
        else:
            helpers = [f for f in (a, b) if rescue[f][p] >= floor]
            cls, by = (2, helpers[0]) if helpers else (3, None)
        rows[p] = {"instant": inst[p], "enlarged": enl[p], "primary": primary[p],
                   "class": cls,
                   "measure": by, "structural": structural,
                   "best_rescue": max(rescue[f][p] for f in (a, b))}
    r_i, c_i = rank_cond(J, sig)
    r_e, c_e = rank_cond(big, bsig)
    return rows, {"inst_rank": r_i, "inst_cond": c_i,
                  "enl_rank": r_e, "enl_cond": c_e, "n_sensors": len(sensor_subset)}


def render(name, rows, meta, floor=FLOOR, regime="accumulated"):
    print(f"\n{'='*74}\nCONFIGURATION: {name}\nREGIME: {regime}")
    print(f"   {meta['n_sensors']} observable(s).  instantaneous rank {meta['inst_rank']}"
          f" (cond {meta['inst_cond']:,.0f})   enlarged rank {meta['enl_rank']}"
          f" (cond {meta['enl_cond']:,.0f})")
    print(f"\n   {'pair':20s}{'instant':>9s}{'enlarged':>10s}{'class':>7s}"
          f"  {'struct':>7s}  note")
    for p in sorted(PAIRS, key=lambda q: (rows[q]["class"], -rows[q]["primary"])):
        r = rows[p]
        note = ""
        if r["class"] == 2:
            note = f"measure {r['measure']} -> {r['best_rescue']:.1f} deg"
        elif r["class"] == 3:
            note = f"best rescue only {r['best_rescue']:.1f} deg"
        elif not r["structural"]:
            note = "relies on calibrated magnitudes"
        print(f"   {p[0]+' / '+p[1]:20s}{r['instant']:>9.2f}{r['enlarged']:>10.2f}"
              f"{r['class']:>7d}  {'yes' if r['structural'] else 'no':>7s}  {note}")
    counts = {c: sum(1 for p in PAIRS if rows[p]["class"] == c) for c in (1, 2, 3)}
    print(f"\n   class 1 (existing signals) {counts[1]}/10   "
          f"class 2 (needs a measurement) {counts[2]}/10   "
          f"class 3 (irreducible) {counts[3]}/10")
    n_struct = sum(1 for p in PAIRS if rows[p]["structural"])
    print(f"   of the class 1 pairs, {n_struct} are also structurally isolable, "
          f"i.e. robust to calibration error")
    return counts


def contrast_to_clear(sensor_subset, plan=None, floor=FLOOR,
                      grid=(0.05, 0.10, 0.15, 0.25, 0.4, 0.6, 0.8, 1.0, 1.5, 2.0)):
    """Smallest profile contrast at which each pair clears the floor.

    The accumulated-regime result rests on the modulation profiles, which are
    asserted rather than measured. Reporting a single angle hides that. This
    reports, per pair, how much of the asserted profile strength is actually
    needed - so a reader can judge the result against their own view of how
    strongly faults vary across a build. Contrast 1.0 is the asserted strength.
    """
    from observables import modulations, regressors
    plan = scan_plan() if plan is None else plan
    J_all, _ = full_jacobian()
    idx = [list(ALL_SENSOR_NAMES).index(n) for n in sensor_subset]
    J = J_all[idx, :]
    sig = np.array([1.0 if "pyrometer" not in n else 0.03 for n in sensor_subset])
    G = regressors(plan)
    out = {}
    for p in PAIRS:
        out[p] = None
        for c in grid:
            M = modulations(plan, contrast=c)
            B = np.linalg.lstsq(G, M, rcond=None)[0]
            rows = [J[s_, :] * B[j, :] for s_ in range(J.shape[0])
                    for j in range(B.shape[0])]
            a = pair_angles(np.vstack(rows), coefficient_sigmas(sig, plan))
            if a[p] >= floor:
                out[p] = c
                break
    return out


if __name__ == "__main__":
    print(f"DIAGNOSABILITY MATRIX   (separation floor {FLOOR:.0f} degrees)")
    base = ("photodiode", "camera", "pyrometer")
    for regime in ("instantaneous", "accumulated"):
        rows, meta = classify(base, regime=regime)
        render("baseline coaxial suite: photodiode + camera area + pyrometer",
               rows, meta, regime=regime)

    print(f"\n{'='*74}\nTHE SAME PAIRS, BOTH REGIMES SIDE BY SIDE")
    ri, _ = classify(base, regime="instantaneous")
    ra, _ = classify(base, regime="accumulated")
    print(f"   {'pair':20s}{'instant':>9s}{'class':>7s}  |{'enlarged':>10s}{'class':>7s}"
          f"   what changes it")
    for p in sorted(PAIRS, key=lambda q: ri[q]["instant"]):
        note = ("-" if ri[p]["class"] == 1 else
                f"measure {ri[p]['measure']}, or use build context"
                if ra[p]["class"] == 1 else "nothing available")
        print(f"   {p[0]+' / '+p[1]:20s}{ri[p]['instant']:>9.2f}{ri[p]['class']:>7d}  |"
              f"{ra[p]['enlarged']:>10.2f}{ra[p]['class']:>7d}   {note}")

    print(f"\n{'='*74}\nHOW MUCH OF THE ASSERTED PROFILE STRENGTH EACH PAIR NEEDS")
    print("   contrast 1.0 = the profile strengths written into the model.")
    print("   A pair clearing at 0.15 needs only 15% of the asserted variation.\n")
    ctc = contrast_to_clear(base)
    print(f"   {'pair':20s}{'contrast needed':>17s}   reading")
    for p in sorted(PAIRS, key=lambda q: (ctc[q] is None, ctc[q] or 0)):
        v = ctc[p]
        if v is None:
            print(f"   {p[0]+' / '+p[1]:20s}{'>2.0':>17s}   needs more than twice the asserted strength")
        else:
            tag = ("very robust" if v <= 0.15 else "robust" if v <= 0.4
                   else "needs most of the asserted strength" if v <= 1.0
                   else "needs MORE than asserted")
            print(f"   {p[0]+' / '+p[1]:20s}{v:>17.2f}   {tag}")
