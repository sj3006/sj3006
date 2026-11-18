"""How precise must validation be? The local, worst-case answer.

Near the truth, a small change `t` in the log-parameters `(mu, k, cp, C)`
changes the healthy-build predictions by `P t` (relative, 16 values: width and
depth at seven benchmark conditions and the production point) and turns fault
`k`'s whitened direction by an angle `|| A_k t ||` (radians), where `A_k` is the
derivative of the unit direction projected off itself:

    A_k = (I - u_k u_k^T) d u_k / d log theta .

Validation that resolves an RMS prediction difference of `s` (as a fraction)
accepts every `t` with `|| P t || / sqrt(16) <= s`. The largest directional
error among those twins is `s sqrt(16) gamma_k`, where `gamma_k^2` is the
largest generalised eigenvalue of `(A_k^T A_k, P^T P)`. So holding every fault
inside the budget `delta_max` needs validation precise to

    s*  =  delta_max / ( sqrt(16) max_k gamma_k ) .

The worst-case direction `t` is the generalised eigenvector. It is then checked
nonlinearly: twins are built along it at several prediction errors and their
directional error is computed directly, which also tests the linearisation.

The keyhole coefficient enters `P` and not `A_k`, which is the prediction-only
class of Table 1 in algebraic form: it can absorb prediction error at no
diagnostic cost, so it is profiled out by the eigenproblem automatically.

Directional derivatives need a converged instrument model, and the numerical
floor of the direction on the 961 grid is about 0.15 degree (LABNOTEBOOK entry
4), so the derivatives use a 10 % central step on a 1921 grid and are checked
against a 5 % step. Takes about ten minutes on four workers. Writes
`_sloppy.json`.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.linalg import eigh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import theory as th                                               # noqa: E402
import twins as tw_mod                                            # noqa: E402
from faults import FAULT_NAMES                                    # noqa: E402

R = tw_mod.REFERENCE
GRID = 1921
PARAMS = ("absorptivity", "k", "cp", "keyhole_c")
LABELS = ("absorptivity", "conductivity", "heat capacity", "keyhole coefficient")


def _twin(logdelta, grid=GRID):
    ch = {p: getattr(R, p) * float(np.exp(d)) for p, d in zip(PARAMS, logdelta)}
    return R.but("s", n_grid=grid, **ch)


def prediction_matrix(h: float = 1e-3) -> np.ndarray:
    """d log(prediction) / d log(theta), 16 x 4, central differences."""
    cols = []
    for j in range(4):
        e = np.zeros(4)
        e[j] = h
        hi, lo = _twin(e).healthy(), _twin(-e).healthy()
        cols.append((np.log(hi) - np.log(lo)) / (2 * h))
    return np.column_stack(cols)


def _jac(logdelta):
    return _twin(np.asarray(logdelta)).jacobian()


def direction_derivatives(h: float, J0: np.ndarray, Jpm: list) -> list[np.ndarray]:
    """A_k, S x 4, from Jacobians at +-h in each of the first three params."""
    sig = np.asarray(R.sigmas, float)
    A = []
    for k in range(5):
        u = J0[:, k] / sig
        u = u / np.linalg.norm(u)
        cols = []
        for j in range(3):
            up = Jpm[2 * j][:, k] / sig
            dn = Jpm[2 * j + 1][:, k] / sig
            up, dn = up / np.linalg.norm(up), dn / np.linalg.norm(dn)
            if up @ u < 0:
                up = -up
            if dn @ u < 0:
                dn = -dn
            d = (up - dn) / (2 * h)
            cols.append(d - (u @ d) * u)
        cols.append(np.zeros_like(u))          # keyhole coefficient: no effect
        A.append(np.column_stack(cols))
    return A


def split(P: np.ndarray, rtol: float = 1e-6):
    """Orthonormal bases of the identifiable subspace and the null space of P."""
    _, s, Vt = np.linalg.svd(P)
    r = int((s > rtol * s[0]).sum())
    return Vt[:r].T, Vt[r:].T


def worst_case(P: np.ndarray, A: list[np.ndarray]):
    """Largest gamma_k and its direction, for each fault, on the identifiable
    subspace. Directions in the null space of P are invisible to validation at
    any precision and are reported separately by `null_leakage`."""
    Q, _ = split(P)
    M = Q.T @ P.T @ P @ Q
    out = []
    for Ak in A:
        w, V = eigh(Q.T @ Ak.T @ Ak @ Q, M)
        out.append((float(np.sqrt(max(w[-1], 0.0))), Q @ V[:, -1]))
    return out


def null_leakage(P: np.ndarray, A: list[np.ndarray]) -> list[float]:
    """Directional change per unit log-step along the null space, deg."""
    _, N = split(P)
    if N.shape[1] == 0:
        return [0.0] * len(A)
    return [float(np.degrees(np.linalg.norm(Ak @ N, 2))) for Ak in A]


def main() -> dict:
    P = prediction_matrix()
    sv = np.linalg.svd(P, compute_uv=False)
    jobs = [np.zeros(4)]
    for h in (0.10, 0.05):
        for j in range(3):
            for s in (1, -1):
                e = np.zeros(4)
                e[j] = s * h
                jobs.append(e)
    with ProcessPoolExecutor(4) as ex:
        Js = list(ex.map(_jac, jobs))
    J0 = Js[0]
    A10 = direction_derivatives(0.10, J0, Js[1:7])
    A05 = direction_derivatives(0.05, J0, Js[7:13])
    W10, W05 = worst_case(P, A10), worst_case(P, A05)
    _, N = split(P)
    leak = null_leakage(P, A10)
    n = P.shape[0]
    deg = np.degrees(1.0)
    budget = float(th.delta_max(28.0, 3))
    res = {"P_singular_values": sv.tolist(), "grid": GRID, "faults": {},
           "null_space": N.T.tolist(), "null_leakage_deg_per_unit": leak}
    print("prediction sensitivity, singular values of P:", sv.tolist())
    for c in N.T:
        print("   null direction in log-parameters:",
              ", ".join(f"{l} {x:+.3f}" for l, x in zip(LABELS, c)))
    print("   directional change along it, deg per unit log-step, by fault:",
          np.round(leak, 4).tolist())
    print(f"\n{'fault':10s}{'gamma (deg per % RMS), h=10%':>32s}{'h=5%':>10s}"
          f"{'s* for 1.62 deg':>18s}")
    for k, name in enumerate(FAULT_NAMES):
        g10 = W10[k][0] * np.sqrt(n) * deg / 100.0
        g05 = W05[k][0] * np.sqrt(n) * deg / 100.0
        s_star = budget / g10
        res["faults"][name] = {"gamma_deg_per_pct_h10": g10, "gamma_deg_per_pct_h05": g05,
                               "s_star_pct": s_star,
                               "direction": (W10[k][1] / np.linalg.norm(W10[k][1])).tolist()}
        print(f"{name:10s}{g10:32.3f}{g05:10.3f}{s_star:18.3f}")
    kw = max(range(5), key=lambda k: W10[k][0])
    res["worst_fault"] = FAULT_NAMES[kw]
    res["s_star_pct"] = res["faults"][FAULT_NAMES[kw]]["s_star_pct"]
    v = W10[kw][1]
    v = v / np.linalg.norm(v)
    print(f"\nworst fault {FAULT_NAMES[kw]}: validation must resolve "
          f"{res['s_star_pct']:.3f} % RMS; direction in log-parameters "
          + ", ".join(f"{l} {c:+.3f}" for l, c in zip(LABELS, v)))

    # nonlinear check along the worst direction, on the 961 study grid
    unit_rms = np.linalg.norm(P @ v) / np.sqrt(n)
    targets = (0.25, 0.5, 1.0, 2.0)
    steps = [t / 100.0 / unit_rms for t in targets]
    with ProcessPoolExecutor(4) as ex:
        Jline = list(ex.map(_jac961, [s * v for s in steps] + [np.zeros(4)]))
    sig = np.asarray(R.sigmas, float)
    Jt = Jline[-1]
    line = []
    print("\nalong that direction (961 grid):  target RMS %, actual RMS %, "
          "largest direction error deg, linear prediction deg")
    for t, s, J in zip(targets, steps, Jline[:-1]):
        tw = _twin(s * v, grid=tw_mod.STUDY_GRID)
        rms = 100 * float(np.sqrt(np.mean(((tw.healthy() - R.healthy()) / R.healthy()) ** 2)))
        d = max(th.folded_angle(Jt[:, k] / sig, J[:, k] / sig) for k in range(5))
        lin = W10[kw][0] * np.sqrt(n) * deg * rms / 100.0
        line.append({"target": t, "rms": rms, "delta": d, "linear": lin})
        print(f"   {t:5.2f} {rms:8.3f} {d:10.3f} {lin:10.3f}")
    res["line"] = line
    (HERE / "_sloppy.json").write_text(json.dumps(res, indent=1))
    return res


def _jac961(logdelta):
    return _twin(np.asarray(logdelta), grid=tw_mod.STUDY_GRID).jacobian()


if __name__ == "__main__":
    main()
