"""Tier 2: quantitative diagnosability.

Tier 1 asked what the model's structure permits, ignoring noise. This asks what
survives at realistic noise, which is a matter of degree rather than yes/no.

Chain
-----
1. Jacobian J = dy/df, sensor readings against fault magnitudes, at nominal.
2. Whiten:  Jw = Sigma^(-1/2) J, so every sensor is measured in units of its own
   noise. Without this, comparing a photodiode millivolt against a camera square
   micrometre is meaningless.
3. Isolability: angle between whitened fault signature directions. A small angle
   means a little of one fault mimics a lot of another.
4. Collinearity index over fault subsets (Brun, Reichert and Kuensch, 2001):
   reciprocal of the smallest eigenvalue of the normalised cross-product.
   Catches a fault mimicked by a *combination* of two others, which pairwise
   angles miss.
5. Detectability: magnitude at which a fault's whitened signature crosses a
   chi-squared false-alarm threshold.

On derivatives
--------------
The plan called for complex-step differentiation, which is exact to machine
precision. It is not valid here: the model branches. Melt pool extents come from
thresholding at the liquidus, and radiance is capped at the boiling point, both
of which are non-analytic. Complex-step through either returns nonsense silently,
which is worse than being wrong loudly.

Central differences with an explicit step-size convergence check are used
instead, and the check is reported rather than assumed.

On noise figures
----------------
No defensible in-process noise figures exist for these sensors. NIST AMS 100-35
reports a 10 uV resolution on a 35 mV scale for a commercial photodiode, but
that is a bench multimeter reading a static blackbody; using it for a sensor
running at tens of kilohertz against a melt pool with plume and spatter in the
field of view would flatter the hardware and bias every conclusion towards
"separable". It is deliberately not used.

All three noise levels are therefore swept. Weaver et al. (2024) Table 4 gives
U(k=2) = 6.2 um on a 136.3 um width, so a standard uncertainty of 2.3 %, which
is marked as a reference point on the camera axis. It is metrology uncertainty
from cross-sectional microscopy rather than in-process camera noise, so it is a
lower bound, not a value.
"""

from __future__ import annotations

import itertools

import numpy as np

from faults import FAULT_NAMES, FaultState, apply_faults
from sensors import SENSOR_NAMES, sensor_readings

__all__ = ["jacobian", "step_convergence", "whiten", "angles",
           "collinearity_index", "detectability", "WEAVER_CAMERA_SIGMA"]

# Weaver et al. Table 4: U(k=2) = 6.2 um on width 136.3 um -> sigma = 3.1 um.
WEAVER_CAMERA_SIGMA = 3.1 / 136.3


def _readings(fault: FaultState) -> np.ndarray:
    beam, material = apply_faults(fault)
    r = sensor_readings(beam, material)
    return np.array([r[s] for s in SENSOR_NAMES], dtype=float)


def jacobian(step: float = 0.002) -> tuple[np.ndarray, np.ndarray]:
    """Central-difference Jacobian of relative sensor change per unit fault.

    Returns (J, nominal). J has shape (n_sensors, n_faults) and is expressed in
    *relative* sensor units, so that a noise covariance given as fractional
    noise per sensor is directly compatible.
    """
    nominal = _readings(FaultState())
    cols = []
    for name in FAULT_NAMES:
        plus = _readings(FaultState(**{name: step}))
        minus = _readings(FaultState(**{name: -step}))
        cols.append((plus - minus) / (2.0 * step) / nominal)
    return np.column_stack(cols), nominal


def step_convergence(steps=(0.08, 0.04, 0.02, 0.01, 0.005)) -> None:
    """Report how the Jacobian moves with step size.

    Too large and curvature contaminates the derivative; too small and
    cancellation does. The right step is where the answer stops moving.
    """
    prev = None
    print("step-size convergence of the Jacobian (max relative change vs previous)")
    for s in steps:
        J, _ = jacobian(step=s)
        if prev is None:
            print(f"   step {s:6.3f}   (reference)")
        else:
            delta = float(np.max(np.abs(J - prev) / (np.abs(prev) + 1e-30)))
            print(f"   step {s:6.3f}   max change {delta:8.2%}")
        prev = J


def whiten(J: np.ndarray, sigmas) -> np.ndarray:
    """Scale each sensor row by its own noise, putting everything in sigmas."""
    return J / np.asarray(sigmas, dtype=float)[:, None]


def angles(Jw: np.ndarray) -> dict[tuple[str, str], float]:
    """Pairwise angle between whitened signature directions, folded to [0, 90].

    Folded because a fault magnitude can be negative: a signature at 175 degrees
    is just as confounded as one at 5.
    """
    out = {}
    for i, a in enumerate(FAULT_NAMES):
        for j, b in enumerate(FAULT_NAMES):
            if i >= j:
                continue
            u, v = Jw[:, i], Jw[:, j]
            c = float(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v)))
            ang = np.degrees(np.arccos(np.clip(c, -1.0, 1.0)))
            out[(a, b)] = float(min(ang, 180.0 - ang))
    return out


def collinearity_index(Jw: np.ndarray, subset: tuple[int, ...]) -> float:
    """Brun et al. collinearity index for a subset of faults.

    Columns normalised to unit length, then the reciprocal square root of the
    smallest eigenvalue of the cross-product. Large means the subset is close to
    linearly dependent. Conventional cutoffs sit between 10 and 20.
    """
    S = Jw[:, list(subset)]
    norms = np.linalg.norm(S, axis=0)
    if np.any(norms == 0):
        return float("inf")
    Sn = S / norms
    ev = np.linalg.eigvalsh(Sn.T @ Sn)
    smallest = float(max(ev.min(), 1e-300))
    return float(1.0 / np.sqrt(smallest))


def detectability(Jw: np.ndarray, threshold: float = 3.0) -> dict[str, float]:
    """Smallest fault magnitude whose whitened signature exceeds `threshold` sigma."""
    return {
        name: float(threshold / np.linalg.norm(Jw[:, i])) if np.linalg.norm(Jw[:, i]) > 0
        else float("inf")
        for i, name in enumerate(FAULT_NAMES)
    }


if __name__ == "__main__":
    step_convergence()
    J, nominal = jacobian()
    print()
    print("Jacobian, relative sensor change per unit fault")
    print(f"   {'':12s}" + "".join(f"{n:>11s}" for n in FAULT_NAMES))
    for i, s in enumerate(SENSOR_NAMES):
        print(f"   {s:12s}" + "".join(f"{J[i, j]:>11.4f}" for j in range(len(FAULT_NAMES))))
    print()
    print(f"Weaver camera reference sigma: {WEAVER_CAMERA_SIGMA:.2%} "
          f"(metrology lower bound, not in-process noise)")
