"""How wrong may the modulation profiles be? (paper Section 4.5)

The accumulated-regime result rests on five modulation profiles, which are
physical claims rather than measurements. A profile can be wrong in four ways,
and each has its own test here:

  too weak              `contrast_thresholds`  - the strength each pair needs
  assigned to the wrong fault  `permutation_sweep` - all 5! = 120 reassignments
  identical to another  `collapse_test`        - force two profiles equal
  following the wrong build variable  `misattribution_sweep`

plus the question of how many segments the regression needs, `segment_sweep`.

Everything here uses the derivative-limit Jacobian and the same
`observables.modulations` machinery as the headline result, so no separate
profile construction can drift away from it. Where a profile has to be built by
hand - the collapse and misattribution tests - it is built from
`observables.drivers` and `observables.PROFILE_CONTRAST` and passed through the
same exp-and-renormalise step, which is why the collapse test reproduces the
instantaneous angles exactly.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).parent))

from diagnosability import jacobian
from faults import FAULT_NAMES
from locality_routeA import pair_angles, _rank_cond
from noise import SIGMAS
from observables import (PROFILE_CONTRAST, coefficient_sigmas, drivers,
                         enlarged_jacobian, modulations, regressors, scan_plan)

__all__ = ["FLOOR", "PAIRS", "SEGMENT_PLANS", "contrast_thresholds",
           "permutation_sweep", "collapse_test", "misattribution_sweep",
           "segment_sweep", "report"]

FLOOR = 10.0
PAIRS = [(a, b) for i, a in enumerate(FAULT_NAMES) for b in FAULT_NAMES[i + 1:]]

# The segment-count sweep needs plans that differ in size without differing in
# shape, because the regressors are built from layer index and cross-plate
# position and a plan that is one layer deep has no layer_sync column at all.
# These are near-square plans: roughly twice as many vectors per layer as
# layers, which is the aspect of the default 6 x 14 plan.
SEGMENT_PLANS = ((2, 6), (3, 10), (4, 12), (5, 13), (6, 14), (8, 16),
                 (10, 20), (12, 24))


def _angles_from_profile(J, G, bsig, M):
    """Pair angles for an enlarged observation built from a given profile set."""
    B = np.linalg.lstsq(G, M, rcond=None)[0]
    D = np.vstack([J[s, :] * B[j, :] for s in range(J.shape[0])
                   for j in range(B.shape[0])])
    return pair_angles(D, bsig), D


def _unit_mean_exp(Zc: np.ndarray) -> np.ndarray:
    """exp(.) rescaled to unit mean, the `positive` form of `modulations`."""
    M = np.exp(Zc)
    return M / M.mean(axis=0, keepdims=True)


def _setup(plan=None, sensor_subset=None):
    """The pieces every test here needs, for one sensor configuration.

    `sensor_subset` defaults to the three coaxial observables of the baseline
    suite; pass any subset of `sensors.ALL_SENSOR_NAMES` to run the same tests
    on another configuration.
    """
    plan = scan_plan() if plan is None else plan
    if sensor_subset is None:
        J, _ = jacobian()
        sig = SIGMAS
    else:
        from route_b import full_jacobian
        from sensors import ALL_SENSOR_NAMES
        from noise import sigmas_for
        J_all, _ = full_jacobian()
        J = J_all[[list(ALL_SENSOR_NAMES).index(n) for n in sensor_subset], :]
        sig = sigmas_for(sensor_subset)
    return (J, plan, regressors(plan), coefficient_sigmas(sig, plan),
            drivers(plan), np.asarray(PROFILE_CONTRAST, float))


# ---------------------------------------------------------------------------
# 1. How much of the asserted profile strength does each pair need?
# ---------------------------------------------------------------------------
def contrast_thresholds(floor: float = FLOOR, lo: float = 0.01,
                        hi: float = 3.0, sensor_subset=None) -> dict:
    """Per pair, the contrast multiplier at which it first clears the floor.

    Solved by bisection rather than read off a grid: a grid reports the first
    grid point above the floor, which overstates the requirement by up to a
    whole grid step and is how an earlier version of this analysis reported the
    binding pair as needing 0.6 when it in fact clears at 0.5.
    """
    J, plan, G, bsig, _, _ = _setup(sensor_subset=sensor_subset)

    def angle(c, pair):
        a, _ = _angles_from_profile(J, G, bsig, modulations(plan, contrast=c))
        return a[pair]

    out = {}
    for p in PAIRS:
        if angle(lo, p) >= floor:
            out[p] = lo
        elif angle(hi, p) < floor:
            out[p] = None
        else:
            out[p] = float(brentq(lambda c: angle(c, p) - floor, lo, hi,
                                  xtol=1e-4))
    return out


# ---------------------------------------------------------------------------
# 2. All 120 ways of assigning the five profiles to the five faults
# ---------------------------------------------------------------------------
def permutation_sweep() -> dict:
    """Reassign which fault follows which build variable, all 5! = 120 ways."""
    J, plan, G, bsig, Z, C = _setup()
    worst, cleared, ranks = [], [], []
    base = None
    for perm in itertools.permutations(range(len(FAULT_NAMES))):
        a, D = _angles_from_profile(J, G, bsig,
                                    _unit_mean_exp(Z[:, list(perm)] * C))
        r, _ = _rank_cond(D, bsig)
        worst.append(min(a.values()))
        cleared.append(sum(v >= FLOOR for v in a.values()))
        ranks.append(r)
        if perm == tuple(range(len(FAULT_NAMES))):
            base = min(a.values())
    worst = np.array(worst)
    return {"n": len(worst), "identity_worst": base,
            "worst_min": float(worst.min()), "worst_max": float(worst.max()),
            "worst_median": float(np.median(worst)),
            "all_rank_5": int(np.sum(np.array(ranks) == 5)),
            "all_cleared": int(np.sum(np.array(cleared) == len(PAIRS)))}


# ---------------------------------------------------------------------------
# 3. Two faults with identical profiles
# ---------------------------------------------------------------------------
def collapse_test() -> dict:
    """Give fault b exactly fault a's profile, for all ten pairs.

    The claim this checks is that a shared profile returns that pair to its
    instantaneous angle - so the accumulated gain comes from the profiles
    differing, not from the extra rows.
    """
    J, plan, G, bsig, Z, C = _setup()
    inst = pair_angles(J, SIGMAS)
    out = {}
    for i, j in itertools.combinations(range(len(FAULT_NAMES)), 2):
        Zc = (Z * C).copy()
        Zc[:, j] = Zc[:, i]
        a, _ = _angles_from_profile(J, G, bsig, _unit_mean_exp(Zc))
        p = (FAULT_NAMES[i], FAULT_NAMES[j])
        out[p] = {"forced": a[p], "instantaneous": inst[p],
                  "worst": min(a.values())}
    return out


# ---------------------------------------------------------------------------
# 4. A profile following the wrong build variable
# ---------------------------------------------------------------------------
def misattribution_sweep(contaminated: str = "layer",
                         contaminant: str = "geometry",
                         fractions=(0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0),
                         floor: float = FLOOR) -> dict:
    """Mix a fraction of another fault's driver into one fault's profile.

    Liu et al. (2022) measure local powder layer thickness in a real build and
    find the variation organised by part support rather than by the recoater
    cycle assumed here - and support is the geometry fault's driver. They also
    show the thinning growing with layer index, which is the power fault's
    driver. So there are two contamination routes to test, not one.

    The mixing is done on the contrast-weighted drivers and then passed through
    the same unit-mean exponential as every other profile, so at fraction 1 the
    contaminated profile is exactly the contaminant's and the pair returns to
    its instantaneous angle.
    """
    J, plan, G, bsig, Z, C = _setup()
    ki = FAULT_NAMES.index(contaminated)
    kj = FAULT_NAMES.index(contaminant)
    pair = tuple(sorted((contaminated, contaminant), key=FAULT_NAMES.index))

    def angles_at(alpha):
        Zc = (Z * C).copy()
        Zc[:, ki] = (1.0 - alpha) * Z[:, ki] * C[ki] + alpha * Z[:, kj] * C[ki]
        a, _ = _angles_from_profile(J, G, bsig, _unit_mean_exp(Zc))
        return a

    rows = []
    for alpha in fractions:
        a = angles_at(alpha)
        rows.append({"alpha": alpha, "pair_angle": a[pair],
                     "worst": min(a.values())})
    # the fraction at which this pair crosses the floor, if it does
    lo_a, hi_a = angles_at(0.0)[pair], angles_at(1.0)[pair]
    if (lo_a - floor) * (hi_a - floor) < 0:
        tol = float(brentq(lambda x: angles_at(x)[pair] - floor, 0.0, 1.0,
                           xtol=1e-3))
    else:
        tol = None
    return {"pair": pair, "rows": rows, "tolerance": tol}


# ---------------------------------------------------------------------------
# 5. How many segments does the regression need?
# ---------------------------------------------------------------------------
def segment_sweep(plans=SEGMENT_PLANS) -> list[dict]:
    J, _ = jacobian()
    out = []
    for n_layers, n_vectors in plans:
        plan = scan_plan(n_layers=n_layers, n_vectors=n_vectors)
        D = enlarged_jacobian(J, plan)
        bsig = coefficient_sigmas(SIGMAS, plan)
        a = pair_angles(D, bsig)
        r, c = _rank_cond(D, bsig)
        out.append({"n_layers": n_layers, "n_vectors": n_vectors,
                    "N": len(plan["layer"]), "rank": r, "cond": c,
                    "worst": min(a.values()),
                    "power_gas": a[("power", "gas")]})
    return out


def report() -> None:
    print(f"PROFILE ROBUSTNESS   (floor {FLOOR:.0f} degrees)\n")

    print("1. HOW MUCH OF THE ASSERTED PROFILE STRENGTH EACH PAIR NEEDS")
    print("   contrast 1.0 = the strengths written into observables.PROFILE_CONTRAST;")
    print("   solved by bisection, so these are thresholds and not grid points.\n")
    ct = contrast_thresholds()
    order = sorted(PAIRS, key=lambda p: (ct[p] is None, ct[p] or 0))
    for p in order:
        v = ct[p]
        s = ">3.0" if v is None else f"{v:.3f}"
        print(f"   {p[0]+' / '+p[1]:20s}{s:>10s}")
    vals = [v for v in ct.values() if v is not None]
    print(f"   {sum(v <= 0.25 for v in vals)} of {len(PAIRS)} pairs clear at or "
          f"below 25% of the asserted strength;")
    print(f"   the hardest, {order[-1][0]}/{order[-1][1]}, needs "
          f"{ct[order[-1]]:.2f}.")

    print("\n2. ALL 120 ASSIGNMENTS OF PROFILES TO FAULTS")
    ps = permutation_sweep()
    print(f"   rank 5 in {ps['all_rank_5']}/{ps['n']} assignments")
    print(f"   all ten pairs above the floor in {ps['all_cleared']}/{ps['n']}")
    print(f"   worst pair: min {ps['worst_min']:.2f}, median "
          f"{ps['worst_median']:.2f}, max {ps['worst_max']:.2f} "
          f"(as assigned: {ps['identity_worst']:.2f})")
    print("   -> it does not matter which fault follows which variable, only "
          "that they differ.")

    print("\n3. TWO FAULTS WITH IDENTICAL PROFILES")
    print(f"   {'pair':20s}{'forced equal':>14s}{'instantaneous':>15s}"
          f"{'suite worst':>13s}")
    ctest = collapse_test()
    for p in sorted(ctest, key=lambda q: ctest[q]["forced"]):
        r = ctest[p]
        print(f"   {p[0]+' / '+p[1]:20s}{r['forced']:>14.3f}"
              f"{r['instantaneous']:>15.3f}{r['worst']:>13.2f}")
    gap = max(abs(r["forced"] - r["instantaneous"]) for r in ctest.values())
    print(f"   largest disagreement with the instantaneous angle: {gap:.4f} deg")
    print(f"   every instantaneous angle is below the floor, the mildest at "
          f"{max(r['instantaneous'] for r in ctest.values()):.2f} - so no pair "
          f"of faults may share a profile.")

    print("\n4. A PROFILE FOLLOWING THE WRONG BUILD VARIABLE")
    for contaminant in ("geometry", "power"):
        m = misattribution_sweep(contaminant=contaminant)
        print(f"\n   layer profile mixed with the {contaminant} fault's driver"
              f"   (pair {m['pair'][0]}/{m['pair'][1]})")
        print(f"   {'fraction':>9s}{'pair angle':>12s}{'suite worst':>13s}")
        for r in m["rows"]:
            print(f"   {r['alpha']:>9.2f}{r['pair_angle']:>12.2f}"
                  f"{r['worst']:>13.2f}")
        if m["tolerance"] is None:
            print("   -> never crosses the floor, at any fraction")
        else:
            print(f"   -> crosses the floor at a fraction of "
                  f"{m['tolerance']:.2f}")

    print("\n5. SEGMENT COUNT")
    print("   near-square plans, so the regressors stay well conditioned as N grows\n")
    print(f"   {'layers':>7s}{'vectors':>9s}{'N':>6s}{'rank':>6s}{'cond':>8s}"
          f"{'worst':>8s}{'power/gas':>11s}")
    for r in segment_sweep():
        print(f"   {r['n_layers']:>7d}{r['n_vectors']:>9d}{r['N']:>6d}"
              f"{r['rank']:>6d}{r['cond']:>8.0f}{r['worst']:>8.2f}"
              f"{r['power_gas']:>11.2f}")
    print("   The worst pair depends on the plan's shape as well as its size, "
          "so these\n   figures are for this family; the qualitative finding is "
          "that the regression\n   needs a few tens of segments and is flat "
          "well before the default 84.")


if __name__ == "__main__":
    report()
