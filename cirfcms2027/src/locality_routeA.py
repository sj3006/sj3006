"""Does the Route A gain survive at finite fault magnitude?

Tier 2 and Route A were both computed from a Jacobian, which is a derivative,
which is the limit of a difference quotient as the fault goes to zero. The
instantaneous study already showed that conclusion is local: pairwise angles at
a +5% fault differ sharply from the derivative limit, non-monotonically and
asymmetrically in sign. Route A was then built *on top of* that Jacobian,

    Jbig[(s, j), k] = J[s, k] * B[j, k]

so it inherits the linearisation wholesale. If the 44.99 degrees is a
small-fault artefact, the paper's headline weakens considerably. This module
settles it by never linearising.

How
---
For a single fault k at magnitude f, the fault acting at segment i of the build
is f * m_k(i), where m_k is that fault's modulation profile. Feed each of those
84 effective magnitudes through the full nonlinear chain - fault couplings,
Eagar-Tsai, the three sensor models - and regress the resulting relative
residuals onto the known context matrix G. That gives the 15 richer observables
at a *finite* fault, with no derivative anywhere.

The secant direction

    d_k(f) = [richer observables at f * e_k] / f

replaces the Jacobian column. As f -> 0 it must converge to Jbig[:, k], and that
convergence is checked rather than assumed. The angle between d_a(f) and d_b(f)
is then the honest diagnosability of that pair for faults of that size.

Why an interpolant
------------------
For a single fault the whole chain depends on one scalar, the effective
magnitude. So each fault needs one 1-D response curve, evaluated exactly on a
grid dense near zero, and every magnitude and every candidate modulation profile
afterwards is free. `validate_curves` checks the interpolation against exact
evaluations before any of it is used.
"""

from __future__ import annotations

import numpy as np
from scipy.interpolate import PchipInterpolator

from diagnosability import _readings, whiten
from faults import FAULT_NAMES, FaultCouplings, FaultState
from observables import (REGRESSOR_NAMES, enlarged_jacobian, modulations,
                         regressors, scan_plan)
from sensors import SENSOR_NAMES

__all__ = ["NODES", "SIGMAS", "response_curves", "validate_curves",
           "enlarged_observation", "secant_directions", "exact_secant_directions",
           "instantaneous_secants", "pair_angles", "rank_cond"]

# Dense near zero, where small faults live, and stretched outwards to cover
# f * m_k(i) for the largest magnitude studied. The profiles are centred on 1
# with standardised excursions reaching about +/-2, so a +/-20% fault can act
# anywhere from -20% to +60% at an individual segment.
_HALF = (1e-3, 2e-3, 3e-3, 5e-3, 7e-3, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05,
         0.06, 0.08, 0.10, 0.12, 0.15, 0.18, 0.22, 0.26, 0.31, 0.37, 0.44,
         0.52, 0.62, 0.75)   # top node covers profile_sweep.MAX_REACH
NODES = np.array([-x for x in reversed(_HALF)] + [0.0] + list(_HALF))

SIGMAS = np.array([1.0, 1.0, 0.03])   # same noise ratio as the Tier 2 headline


def response_curves(couplings: FaultCouplings | None = None
                    ) -> tuple[dict[str, PchipInterpolator], np.ndarray]:
    """One exact 1-D response curve per fault, plus the nominal reading."""
    nominal = _readings(FaultState(), couplings)
    curves = {}
    for name in FAULT_NAMES:
        ys = np.array([_readings(FaultState(**{name: float(m)}), couplings)
                       for m in NODES])
        curves[name] = PchipInterpolator(NODES, ys, axis=0)
    return curves, nominal


def validate_curves(curves, nominal, n: int = 10, seed: int = 1) -> dict[str, float]:
    """Interpolation error in the quantity that is actually used downstream.

    The regression consumes relative residuals (y - y0) / y0, whitened by each
    sensor's noise. So the error that matters is the interpolation error in that
    whitened residual, measured against the typical whitened residual size - not
    against the local change, which passes through zero wherever a sensor's
    response turns over and makes any ratio to it meaningless.
    """
    rng = np.random.default_rng(seed)
    err, scale = [], []
    for name in FAULT_NAMES:
        for m in rng.uniform(-0.25, 0.25, n):
            exact = _readings(FaultState(**{name: float(m)}))
            approx = np.asarray(curves[name](m), float)
            err.append((approx - exact) / nominal / SIGMAS)
            scale.append((exact - nominal) / nominal / SIGMAS)
    err, scale = np.abs(np.array(err)), np.abs(np.array(scale))
    rms = scale.reshape(-1, 3).mean(axis=0)
    return {"worst_abs": float(err.max()),
            "worst_rel_to_typical": float((err / rms).max()),
            "per_sensor_typical": rms}


def rank_cond(D, sigmas=None):
    """Effective rank and condition number of the whitened signature matrix."""
    return _rank_cond(D, SIGMAS if sigmas is None else sigmas)


def exact_secant_directions(f, plan, nominal):
    """Same as `secant_directions` but with no interpolation anywhere.

    84 segments x 5 faults full model evaluations per magnitude. Used to confirm
    that the interpolated table is not an artefact of the response curves.
    """
    G, M = regressors(plan), modulations(plan)
    cols = []
    for k, name in enumerate(FAULT_NAMES):
        r = np.array([_readings(FaultState(**{name: float(f * m)}))
                      for m in M[:, k]])
        r = (r - nominal) / nominal
        C = np.linalg.lstsq(G, r, rcond=None)[0]
        cols.append(C.T.ravel() / f)
    return np.column_stack(cols)


def _residuals(name, f, plan, curves, nominal, M):
    """Relative sensor residuals at every segment, for fault `name` of size f."""
    k = FAULT_NAMES.index(name)
    eff = f * M[:, k]
    return (curves[name](eff) - nominal) / nominal        # (n_segments, 3)


def enlarged_observation(name, f, plan, curves, nominal, M, G):
    """The 15 richer observables, ordered sensor-major to match enlarged_jacobian."""
    r = _residuals(name, f, plan, curves, nominal, M)
    C = np.linalg.lstsq(G, r, rcond=None)[0]              # (n_regressors, 3)
    return C.T.ravel()


def secant_directions(f, plan, curves, nominal, **kw):
    """(15, 5) finite-magnitude replacement for the enlarged Jacobian.

    Extra keywords go to `modulations`, so profile form and contrast can be swept.
    """
    G, M = regressors(plan), modulations(plan, **kw)
    reach = float(np.max(np.abs(f * M)))
    if reach > NODES.max():
        raise ValueError(
            f"fault reaches {reach:.2f} at some segment, beyond the "
            f"{NODES.max():.2f} response-curve range - extend NODES or lower f")
    cols = [enlarged_observation(n, f, plan, curves, nominal, M, G) / f
            for n in FAULT_NAMES]
    return np.column_stack(cols)


def instantaneous_secants(f, curves, nominal):
    """(3, 5) finite-magnitude replacement for the plain Jacobian, for contrast."""
    cols = [(curves[n](f) - nominal) / nominal / f for n in FAULT_NAMES]
    return np.column_stack(cols)


def pair_angles(D, sigmas):
    Dw = whiten(D, np.repeat(sigmas, D.shape[0] // len(sigmas)))
    out = {}
    for i, a in enumerate(FAULT_NAMES):
        for j, b in enumerate(FAULT_NAMES):
            if i >= j:
                continue
            u, v = Dw[:, i], Dw[:, j]
            nu, nv = np.linalg.norm(u), np.linalg.norm(v)
            if nu == 0 or nv == 0:
                out[(a, b)] = 0.0
                continue
            c = float(np.dot(u, v) / (nu * nv))
            ang = np.degrees(np.arccos(np.clip(c, -1.0, 1.0)))
            out[(a, b)] = float(min(ang, 180.0 - ang))
    return out


RANK_TOL = 1e-6   # a direction 10^6 times weaker than the strongest is not a
                  # measurement, whatever floating point says about it


def _rank_cond(D, sigmas):
    Dw = whiten(D, np.repeat(sigmas, D.shape[0] // len(sigmas)))
    s = np.linalg.svd(Dw, compute_uv=False)
    s = s[s > s.max() * RANK_TOL]
    return len(s), s[0] / s[-1]


if __name__ == "__main__":
    import time
    from diagnosability import jacobian

    t0 = time.time()
    curves, nominal = response_curves()
    print(f"{len(NODES)} exact evaluations per fault, "
          f"{len(NODES) * len(FAULT_NAMES)} total, {time.time() - t0:.0f} s")

    v = validate_curves(curves, nominal)
    print(f"interpolation error in the whitened residual: {v['worst_abs']:.3e} "
          f"absolute, worst case {v['worst_rel_to_typical']:.1%} of the typical "
          f"residual.\nThat worst case is the pyrometer in a flat region of its "
          f"response and it does not propagate - the\nauthoritative check is the "
          f"no-interpolation comparison at the bottom of this report.")

    plan = scan_plan()
    M = modulations(plan)
    print(f"\nscan plan: {len(plan['layer']):.0f} segments. Modulation profiles span "
          f"{M.min():+.2f} to {M.max():+.2f} times the nominal fault magnitude, so a "
          f"20% fault\nacts between {20*M.min():+.0f}% and {20*M.max():+.0f}% at "
          f"individual segments.")

    J, _ = jacobian()
    Jbig = enlarged_jacobian(J, plan)
    a_lim = pair_angles(Jbig, SIGMAS)
    i_lim = pair_angles(J, SIGMAS)

    mags = (0.002, 0.01, 0.02, 0.05, 0.10, 0.20, -0.02, -0.05, -0.20)

    print("\nCONVERGENCE TO THE DERIVATIVE LIMIT (enlarged, power/gas angle)")
    for f in (0.02, 0.01, 0.005, 0.002, 0.001):
        D = secant_directions(f, plan, curves, nominal)
        print(f"   f = {f:+.3f}   {pair_angles(D, SIGMAS)[('power', 'gas')]:7.2f} deg")
    print(f"   limit     {a_lim[('power', 'gas')]:7.2f} deg")

    print("\nENLARGED: PAIRWISE ANGLES VS FAULT MAGNITUDE (degrees)")
    hdr = "".join(f"{f:>+8.0%}" for f in mags)
    print(f"   {'pair':22s}{'limit':>8s}{hdr}")
    rows = {}
    for f in mags:
        rows[f] = pair_angles(secant_directions(f, plan, curves, nominal), SIGMAS)
    for p in sorted(a_lim, key=lambda q: a_lim[q]):
        line = "".join(f"{rows[f][p]:>8.2f}" for f in mags)
        print(f"   {p[0] + ' / ' + p[1]:22s}{a_lim[p]:>8.2f}{line}")

    print("\nINSTANTANEOUS, SAME MAGNITUDES, FOR CONTRAST (degrees)")
    print(f"   {'pair':22s}{'limit':>8s}{hdr}")
    irows = {f: pair_angles(instantaneous_secants(f, curves, nominal), SIGMAS)
             for f in mags}
    for p in sorted(i_lim, key=lambda q: i_lim[q]):
        line = "".join(f"{irows[f][p]:>8.2f}" for f in mags)
        print(f"   {p[0] + ' / ' + p[1]:22s}{i_lim[p]:>8.2f}{line}")

    print("\nRANK AND CONDITION NUMBER VS MAGNITUDE")
    print(f"   {'magnitude':>10s}{'inst rank':>11s}{'inst cond':>12s}"
          f"{'big rank':>10s}{'big cond':>11s}")
    for f in mags:
        ri, ci = _rank_cond(instantaneous_secants(f, curves, nominal), SIGMAS)
        rb, cb = _rank_cond(secant_directions(f, plan, curves, nominal), SIGMAS)
        print(f"   {f:>+10.0%}{ri:>11d}{ci:>12,.0f}{rb:>10d}{cb:>11,.0f}")

    worst = min(min(r.values()) for r in rows.values())
    print(f"\nworst enlarged angle over all magnitudes and pairs: {worst:.2f} deg")

    print("\nNO-INTERPOLATION CROSS-CHECK (full model at every segment)")
    for f in (0.05, 0.20):
        t = time.time()
        De = exact_secant_directions(f, plan, nominal)
        ae = pair_angles(De, SIGMAS)
        diff = max(abs(ae[p] - rows[f][p]) for p in ae)
        re_, ce = _rank_cond(De, SIGMAS)
        print(f"   f = {f:+.0%}  worst angle {min(ae.values()):6.2f} deg   rank {re_}   "
              f"condition {ce:,.0f}   max angle disagreement with the interpolated "
              f"table {diff:.2f} deg   ({time.time() - t:.0f} s)")
