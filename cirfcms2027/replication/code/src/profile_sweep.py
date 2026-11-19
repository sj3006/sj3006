"""Sweep the modulation profiles, because they are assertions, not measurements.

The Route A result rests on five hand-written claims about how each fault's
severity varies across a build. Three things about those claims could be doing
the work instead of the physics:

1. **Strength.** Each profile carries a contrast coefficient (0.3 for power
   drift up to 1.0 for layer and geometry). If the result only holds at the
   values typed in, it is not a result.
2. **Shape.** The linear form 1 + c*z goes negative where z < -1/c, so a 20%
   fault acts as -31% at some segments: the fault reverses sign across the
   plate. That is not physical and a sign flip is a very distinctive signature.
   The "positive" form cannot do it.
3. **Distinctness.** Faults are separable here because their profiles differ.
   Collapsing all five onto a single shared profile must destroy the gain
   exactly - that is the control, and it also bounds how much of the gain is
   the enlarged observation simply having more rows.

The honest headline is a threshold: the confounded pair separates once profile
contrast exceeds some value. This module finds that value.
"""

from __future__ import annotations

import numpy as np

from diagnosability import jacobian
from faults import FAULT_NAMES
from locality_routeA import (SIGMAS, big_sigmas, pair_angles, rank_cond,
                             response_curves, secant_directions)
from observables import (PROFILE_CONTRAST, PROFILE_FORMS, enlarged_jacobian,
                         modulations, projection_matrix, regressors, scan_plan)

__all__ = ["contrast_threshold", "form_comparison", "shared_profile_control"]

CONTRASTS = (0.0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0)

# A profile that turns a 20% fault into a 180% one at some segment is not a
# modelling range problem, it is nonsense physics. A 20% fault with a 3.1x spatial peak already reaches
# 62%, so the bound sits just above that. Combinations that reach past
# this are reported as out of scope rather than evaluated.
MAX_REACH = 0.70
HEADLINE_PAIR = ("power", "gas")


def _summary(D, sigmas):
    a = pair_angles(D, sigmas)
    r, c = rank_cond(D, sigmas)
    return min(a.values()), a[HEADLINE_PAIR], r, c


def contrast_threshold(curves, nominal, plan, f, form="positive"):
    """Worst-pair and headline-pair angle against profile contrast."""
    out = {}
    for s in CONTRASTS:
        # contrast 0 means every profile is identically 1, so the enlarged
        # observation carries no spatial information and must reproduce the
        # instantaneous case. 1e-9 rather than 0 keeps the regression defined.
        c = 1e-9 if s == 0.0 else s
        reach = float(np.max(np.abs(f * modulations(plan, contrast=c, form=form))))
        out[s] = (None if reach > MAX_REACH else
                  _summary(secant_directions(f, plan, curves, nominal,
                                             contrast=c, form=form),
                           big_sigmas(plan)), reach)
    return out


def form_comparison(curves, nominal, plan, f):
    return {form: _summary(secant_directions(f, plan, curves, nominal, form=form),
                           big_sigmas(plan))
            for form in PROFILE_FORMS}


def shared_profile_control(J, plan):
    """All five faults given one identical profile. Must return the instantaneous result."""
    M = modulations(plan)
    shared = np.tile(M[:, [3]], (1, len(FAULT_NAMES)))      # everyone gets gas's profile
    G = regressors(plan)
    B = np.linalg.lstsq(G, shared, rcond=None)[0]
    rows = [J[s, :] * B[j, :] for s in range(J.shape[0]) for j in range(B.shape[0])]
    return np.vstack(rows)


if __name__ == "__main__":
    curves, nominal = response_curves()
    plan = scan_plan()
    J, _ = jacobian()

    print("CONTROL: one shared profile for all five faults")
    Dc = shared_profile_control(J, plan)
    w, h, r, c = _summary(Dc, big_sigmas(plan))
    wi, hi, ri, ci = _summary(J, SIGMAS)
    print(f"   shared profile   worst {w:6.2f} deg   {HEADLINE_PAIR[0]}/{HEADLINE_PAIR[1]}"
          f" {h:6.2f} deg   rank {r}   condition {c:>10,.0f}")
    print(f"   instantaneous    worst {wi:6.2f} deg   {HEADLINE_PAIR[0]}/{HEADLINE_PAIR[1]}"
          f" {hi:6.2f} deg   rank {ri}   condition {ci:>10,.0f}")
    print(f"   -> the gain is the profiles differing, not the extra rows "
          f"({'identical' if abs(w - wi) < 0.01 and r == ri else 'DIFFERENT - investigate'})")

    print("\nPROFILE SHAPE, at the contrast values actually used")
    for f in (0.002, 0.05, 0.20):
        print(f"   fault magnitude {f:+.1%}")
        for form, (w, h, r, c) in form_comparison(curves, nominal, plan, f).items():
            M = modulations(plan, form=form)
            flips = int((M < 0).sum())
            print(f"      {form:9s} worst {w:6.2f}   power/gas {h:6.2f}   rank {r}"
                  f"   condition {c:>7,.0f}   sign reversals {flips:3d}/{M.size}")

    print("\nCONTRAST THRESHOLD, strictly positive profiles")
    print("   (contrast 1.0 = the coefficients "
          f"{PROFILE_CONTRAST} written into modulations())")
    for f in (0.002, 0.05, 0.20):
        print(f"\n   fault magnitude {f:+.1%}")
        print(f"      {'contrast':>9s}{'worst pair':>12s}{'power/gas':>11s}"
              f"{'rank':>6s}{'condition':>16s}{'peak fault':>12s}")
        for s, (res, reach) in contrast_threshold(curves, nominal, plan, f).items():
            if res is None:
                print(f"      {s:>9.2f}{'-':>12s}{'-':>11s}{'-':>6s}{'-':>16s}"
                      f"{reach:>11.0%}  out of physical scope")
                continue
            w, h, r, c = res
            print(f"      {s:>9.2f}{w:>12.2f}{h:>11.2f}{r:>6d}{c:>16,.0f}{reach:>12.0%}")

    print("\nFor reference, the derivative-limit projection matrix under the "
          "positive form")
    B = projection_matrix(plan, form="positive")
    print(f"   {'':14s}" + "".join(f"{n:>11s}" for n in FAULT_NAMES))
    from observables import REGRESSOR_NAMES
    for j, rn in enumerate(REGRESSOR_NAMES):
        print(f"   {rn:14s}" + "".join(f"{B[j, k]:>11.3f}" for k in range(5)))
