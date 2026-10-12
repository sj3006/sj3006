"""Tier 1 on the enlarged observation set, so both tiers describe one system.

Tier 1 analysed three instantaneous measurements and found every fault pair
structurally isolable. Tier 2 then showed that at realistic noise most pairs are
not, and Route A showed the enlarged observation recovers them. But Tier 1 was
never re-run on the enlarged set, so the paper currently has two tiers analysing
two different systems - which is the first thing a reviewer will notice.

What the enlarged observation looks like structurally
----------------------------------------------------
Route A regresses each sensor's residual onto five known build regressors. The
regression coefficient of sensor s onto regressor j is the component of that
sensor's response lying along regressor j. The whole causal chain has such a
component, so channel j carries its own copies of the chain's unknowns -
absorbed power along j, effective conductivity along j, and so on - and its own
three measurements. Five channels, 11 equations each: 55 equations, 40 unknowns.

The structural content is *which faults enter which channel*. In the
instantaneous model all five faults enter through one shared chain, which is why
power and gas are inseparable there. In the enlarged model, fault k enters
channel j only if it actually modulates along regressor j, that is only if
B[j, k] is non-zero. The projection matrix's zero pattern is therefore the whole
structural claim, and since B is computed numerically rather than being exactly
zero anywhere, a threshold decides the pattern - so the threshold is swept and
reported, exactly as the equation set was swept in Tier 1.

Why the MSO enumeration is replaced here
----------------------------------------
Tier 1 enumerated all 2^11 subsets to find MSO sets. 2^55 is not available. But
the MSO enumeration was only ever a means to the detectability and isolability
tests, and those need just the structurally overdetermined part M+ of the
equation set:

    f detectable            iff some equation carrying f lies in M+(E)
    f_i isolable from f_j   iff some equation carrying f_i lies in
                                M+(E \\ equations carrying f_j)

M+ is the set of equations that can be left unmatched by some maximum matching,
and an equation e is one of those exactly when removing it drops the redundancy:

    e in M+(E)  iff  phi(E \\ {e}) = phi(E) - 1

because phi = |E| - matching, so losing e costs one equation and the matching
only shrinks if e was matched in every maximum matching. That is |E| matching
computations instead of 2^|E| subsets. `validate_fast_method` checks it against
Tier 1's exhaustive answer on the 11-equation model before it is trusted here.
"""

from __future__ import annotations

import numpy as np

from faults import FAULT_NAMES
from observables import REGRESSOR_NAMES, projection_matrix, scan_plan
from structural import (FAULTS, LPBF_EQUATIONS, LPBF_MODEL, Equation,
                        StructuralModel, redundancy)

__all__ = ["overdetermined_part", "validate_fast_method", "enlarged_equations",
           "detectability", "isolability", "report_enlarged", "plan_dependence"]

# Plans to compare. The point is not that one is right - it is that the operator
# chooses, and the choice changes what the sensors can resolve.
PLAN_VARIANTS = {
    "raster, support grows":      dict(order="raster", support_with_layer=True),
    "raster, flat support":       dict(order="raster", support_with_layer=False),
    "random order":               dict(order="random", support_with_layer=True),
    "interleaved order":          dict(order="layer_interleaved", support_with_layer=True),
}

# Tier 1's fault names map onto the Jacobian's fault order.
FAULT_OF_COLUMN = dict(zip(FAULT_NAMES, ("f_P", "f_v", "f_layer", "f_gas", "f_geo")))


def overdetermined_part(eqs: tuple[Equation, ...]) -> set[str]:
    """Names of the equations in the structurally overdetermined part M+."""
    phi = redundancy(eqs)
    out = set()
    for i, e in enumerate(eqs):
        rest = eqs[:i] + eqs[i + 1:]
        if redundancy(rest) == phi - 1:
            out.add(e.name)
    return out


def _carriers(eqs, fault):
    return {e.name for e in eqs if fault in e.faults}


def detectability(eqs: tuple[Equation, ...], faults) -> dict[str, bool]:
    mplus = overdetermined_part(eqs)
    return {f: bool(_carriers(eqs, f) & mplus) for f in faults}


def isolability(eqs: tuple[Equation, ...], faults) -> dict[tuple[str, str], bool]:
    out = {}
    for fj in faults:
        drop = _carriers(eqs, fj)
        rest = tuple(e for e in eqs if e.name not in drop)
        mplus = overdetermined_part(rest) if rest else set()
        for fi in faults:
            if fi == fj:
                out[(fi, fj)] = True
            else:
                out[(fi, fj)] = bool(_carriers(rest, fi) & mplus)
    return out


def validate_fast_method() -> tuple[bool, bool]:
    """The M+ tests must reproduce Tier 1's exhaustive MSO answer exactly."""
    eqs = tuple(LPBF_EQUATIONS)
    msos = LPBF_MODEL.mso_sets()
    det_ok = detectability(eqs, FAULTS) == LPBF_MODEL.detectability(msos)
    iso_ok = isolability(eqs, FAULTS) == LPBF_MODEL.isolability(msos)
    return det_ok, iso_ok


def enlarged_equations(B: np.ndarray, threshold: float) -> tuple[Equation, ...]:
    """One copy of the chain per regressor, with fault k admitted to channel j
    only where |B[j, k]| exceeds the threshold."""
    out = []
    for j, rname in enumerate(REGRESSOR_NAMES):
        admitted = {FAULT_OF_COLUMN[FAULT_NAMES[k]]
                    for k in range(B.shape[1]) if abs(B[j, k]) > threshold}
        for e in LPBF_EQUATIONS:
            out.append(Equation(
                name=f"{e.name}@{rname}",
                unknowns=frozenset(f"{u}@{rname}" for u in e.unknowns),
                faults=frozenset(e.faults & admitted),
                note=e.note,
            ))
    return tuple(out)


def _blocked(iso):
    return sorted((a, b) for (a, b), ok in iso.items() if not ok and a != b)


def report_enlarged(thresholds=(0.0, 0.01, 0.05, 0.10, 0.20, 0.40)) -> None:
    det_ok, iso_ok = validate_fast_method()
    print("VALIDATION of the M+ tests against Tier 1's exhaustive MSO enumeration")
    print(f"   detectability matches: {det_ok}      isolability matches: {iso_ok}")
    if not (det_ok and iso_ok):
        raise SystemExit("fast method disagrees with the exhaustive one - stop here")

    plan = scan_plan()
    B = projection_matrix(plan)

    print("\nPROJECTION MATRIX ZERO PATTERN, the whole structural claim")
    print(f"   {'':16s}" + "".join(f"{n:>10s}" for n in FAULT_NAMES))
    for j, rn in enumerate(REGRESSOR_NAMES):
        print(f"   {rn:16s}" + "".join(f"{B[j, k]:>10.3f}" for k in range(5)))

    print("\nINSTANTANEOUS MODEL, for reference")
    eqs0 = tuple(LPBF_EQUATIONS)
    iso0 = isolability(eqs0, FAULTS)
    print(f"   11 equations, redundancy {redundancy(eqs0)}, "
          f"non-isolable pairs: {len(_blocked(iso0))}")

    print("\nENLARGED MODEL vs the threshold deciding which couplings count")
    for t in thresholds:
        eqs = enlarged_equations(B, t)
        det = detectability(eqs, FAULTS)
        iso = isolability(eqs, FAULTS)
        blocked = _blocked(iso)
        channels = {}
        for j, rn in enumerate(REGRESSOR_NAMES):
            channels[rn] = sum(1 for k in range(5) if abs(B[j, k]) > t)
        print(f"\n   threshold {t:.2f}   redundancy {redundancy(eqs):>2d}   "
              f"faults admitted per channel "
              f"{ {k: v for k, v in channels.items()} }")
        undetected = [f for f, ok in det.items() if not ok]
        print(f"      detectable: {len(FAULTS) - len(undetected)}/{len(FAULTS)}"
              + (f"   NOT detectable: {undetected}" if undetected else ""))
        if blocked:
            print(f"      non-isolable pairs ({len(blocked)}): "
                  + ", ".join(f"{a} from {b}" for a, b in blocked))
        else:
            print("      every pair structurally isolable")


def plan_dependence(threshold: float = 0.10) -> None:
    """Does diagnosability depend on the scan plan? It does, and that is a lever.

    Power becomes isolable from gas in the enlarged model because the support
    depth channel admits power (B = -0.268) but not gas (B = 0.082). Power only
    loads onto support depth because, in a bottom-up raster, build time and solid
    support beneath the track both grow with height - a correlation the operator
    created by choosing that scan order, not a fact about LPBF. Break the
    correlation and the separation should weaken. If it does, scan-order design
    is a diagnosability lever that costs nothing, which is a stronger and more
    actionable claim than any angle.
    """
    from locality_routeA import SIGMAS, big_sigmas, pair_angles, rank_cond
    from diagnosability import jacobian
    from observables import enlarged_jacobian

    J, _ = jacobian()
    print(f"\nPLAN DEPENDENCE  (structural threshold {threshold:.2f})")
    print(f"   {'plan':26s}{'corr(time,':>12s}{'power onto':>12s}"
          f"{'blocked':>9s}{'worst':>8s}{'pwr/gas':>9s}{'cond':>7s}")
    print(f"   {'':26s}{'support)':>12s}{'support)':>12s}{'pairs':>9s}"
          f"{'angle':>8s}{'angle':>9s}")
    for label, kw in PLAN_VARIANTS.items():
        plan = scan_plan(**kw)
        B = projection_matrix(plan)
        G = __import__("observables").regressors(plan)
        bt = __import__("observables").drivers(plan)[:, 0]
        corr = float(np.corrcoef(bt, G[:, 4])[0, 1])
        iso = isolability(enlarged_equations(B, threshold), FAULTS)
        blocked = _blocked(iso)
        Jb, bs = enlarged_jacobian(J, plan), big_sigmas(plan)
        a = pair_angles(Jb, bs)
        _, c = rank_cond(Jb, bs)
        print(f"   {label:26s}{corr:>+12.3f}{B[4, 0]:>+12.3f}{len(blocked):>9d}"
              f"{min(a.values()):>8.2f}{a[('power', 'gas')]:>9.2f}{c:>7,.0f}")
        if blocked:
            print(f"      -> {', '.join(f'{x} from {y}' for x, y in blocked)}")


if __name__ == "__main__":
    report_enlarged()
    plan_dependence()
