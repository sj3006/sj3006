"""Active probing: where changing the operating point helps, and where it cannot.

The certificate says which causes an observation admits. The obvious next move
is to stop accepting the observation: if two causes are confounded at the
current operating point, run a deliberate probe at a different one and look
again. This module asks what that buys, and finds a ceiling that is provable
rather than measured.

The factorisation
----------------
Everything the model knows about a fault reaches the sensors through four
physical channels: the absorbed power `A*P`, the scan speed, the effective
conductivity, and the local preheat. So the fault-to-sensor Jacobian factors,

    J = M C

where `C` is 4 by 5 and says how each fault moves each channel, and `M` is
3 by 4 and says how each observable responds to each channel. `C` is a property
of the faults and the material; `M` is a property of the instruments and the
operating point. A probe changes `M`. Nothing a probe does touches `C`.

Writing `C` out from the fault routes in `faults.py`, with channels in log units
except preheat in kelvin:

                power  speed   layer    gas  geometry
    ln(A P)        1      0   c_A+c_H    -1      0
    ln(v)          0      1      0        0      0
    ln(k)          0      0     c_k       0      0
    T_0            0      0      0        0    c_geo

`verify_factorisation` checks `J = M C` against the Jacobian computed directly
from fault perturbations, and they agree to 7e-5 relative, which is the
finite-difference error.

The ceiling
-----------
Read the first row. A power fault raises absorbed power; a gas fault lowers it;
neither does anything else. So

    C[:, power] = -C[:, gas]

exactly, by the form of the model rather than by numerical accident. For any
`M` whatever,

    (M C)[:, power] = -(M C)[:, gas]

so the two columns are antiparallel in every instrument set, at every operating
point, and in any stack of operating points. No probe separates them, and the
null space of `C` is one-dimensional and is exactly that direction: an equal
simultaneous power and gas fault moves no channel, so it moves no observable
that exists.

This is a stronger statement than the conference paper's. There the pair was
confounded for a particular suite at a particular operating point. Here it is
confounded for every suite at every operating point, and the proof is four
entries of a matrix.

What probing does buy
---------------------
The other nine pairs are confounded for a different reason: `M` has rank 3
against a channel count of 4, so one combination of channels is invisible.
Stacking operating points raises the rank, and the measured answer is that it
does not help much. The fourth singular direction stays six orders of magnitude
below the first, because the preheat channel is intrinsically weak: `M[:, T_0]`
is of order 1e-3 where `M[:, A P]` is of order 1, since a kelvin of preheat
barely moves a melt pool running at 3000 K, and no operating point changes that.

Two well-chosen points take the second-worst pair from 0.32 to 5.95 degrees.
Still under the floor. Four points reach nominal rank 4 with a condition number
of 289000, which is rank in name only. More points make the angles slightly
worse rather than better, so probe selection matters and probe count does not.

What escapes the ceiling, and why it is not a probe
---------------------------------------------------
Build context clears power against gas, reaching 30 degrees. That does not
contradict the theorem, and seeing why is the point of this module.

The theorem assumes the fault magnitudes are the same at every epoch, which is
what makes `J = M C` with one `C`. Build context breaks that assumption rather
than enriching `M`: a fault's severity varies across the build along its own
spatial profile, so what is observed is `J[s,k] B[j,k]`, and the profile
loadings `B[:, power]` and `B[:, gas]` are not proportional even though the
channel columns are.

So the escape route is differential modulation of the faults, not richer
observation. The only thing that separates a power fault from a gas fault is
that they vary differently across a build. Not instruments, not operating
points, not probe schedules. A probe could in principle supply that modulation
deliberately, by commanding a known power ripple, and that is the one probe
design with a route past the ceiling; it is also just build context, paid for
rather than free.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import diagnosability as diag                               # noqa: E402
import inference as inf                                    # noqa: E402
import noise                                               # noqa: E402
import observables as obs                                  # noqa: E402
from faults import (FAULT_NAMES, FaultCouplings, FaultState,  # noqa: E402
                    apply_faults)
from sensors import SENSOR_NAMES, sensor_readings           # noqa: E402

__all__ = ["CHANNEL_NAMES", "NOMINAL", "channel_matrix", "observation_matrix",
           "verify_factorisation", "ceiling", "stacked_jacobian",
           "search_two_point", "compare", "report"]

CHANNEL_NAMES = ("ln absorbed power", "ln speed", "ln conductivity", "preheat K")

#: The calibrated operating point, from `faults.apply_faults` defaults.
NOMINAL = (285.0, 0.960)


def channel_matrix(couplings: FaultCouplings | None = None) -> np.ndarray:
    """`C[channel, fault]`, written out from the fault routes rather than fitted."""
    c = couplings or FaultCouplings()
    return np.array([
        [1.0, 0.0, c.layer_to_absorptivity + c.layer_to_powder_enthalpy, -1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, c.layer_to_conductivity, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, c.geometry_preheat_kelvin],
    ])


def observation_matrix(power: float = NOMINAL[0], speed: float = NOMINAL[1],
                       step: float = 2e-3,
                       couplings: FaultCouplings | None = None) -> np.ndarray:
    """`M[observable, channel]` at an operating point, by central differences.

    Each channel is perturbed at its source rather than through a fault, so this
    is the instrument response alone with the fault routes factored out.
    """
    c = couplings or FaultCouplings()
    beam, material = apply_faults(FaultState(), c, power=power, speed=speed)

    def read(**kw) -> np.ndarray:
        b, m = beam, material
        if "absorptivity" in kw:
            b = replace(b, absorptivity=kw["absorptivity"])
        if "speed" in kw:
            b = replace(b, speed=kw["speed"])
        if "k" in kw:
            m = replace(m, k=kw["k"])
        if "t0" in kw:
            m = replace(m, t_ambient=kw["t0"])
        r = sensor_readings(b, m)
        return np.array([r[s] for s in SENSOR_NAMES], dtype=float)

    y0 = read()
    M = np.zeros((len(SENSOR_NAMES), len(CHANNEL_NAMES)))
    e = np.exp(step)
    M[:, 0] = (read(absorptivity=beam.absorptivity * e)
               - read(absorptivity=beam.absorptivity / e)) / (2 * step) / y0
    M[:, 1] = (read(speed=beam.speed * e)
               - read(speed=beam.speed / e)) / (2 * step) / y0
    M[:, 2] = (read(k=material.k * e)
               - read(k=material.k / e)) / (2 * step) / y0
    dT = 1.0
    M[:, 3] = (read(t0=material.t_ambient + dT)
               - read(t0=material.t_ambient - dT)) / (2 * dT) / y0
    return M


def verify_factorisation(step: float = 2e-3) -> float:
    """Largest relative disagreement between `M C` and the direct Jacobian."""
    J_direct, _ = diag.jacobian(step=step)
    J_factored = observation_matrix(step=step) @ channel_matrix()
    return float(np.abs((J_direct - J_factored) / J_direct).max())


def ceiling(couplings: FaultCouplings | None = None) -> dict:
    """The fault directions no observation of any kind can see."""
    C = channel_matrix(couplings)
    _, sv, vt = np.linalg.svd(C)
    rank = int(np.linalg.matrix_rank(C))
    # `sv` has min(4, 5) = 4 entries while `vt` is 5 by 5, so the null space is
    # rows `rank` onward of `vt`, not row `len(sv) - 1`. Indexing by the number
    # of singular values returns the vector for the smallest *non-zero* one,
    # which here is a layer-dominated direction that is not null at all.
    null = vt[rank] if C.shape[1] > rank else None
    power, gas = FAULT_NAMES.index("power"), FAULT_NAMES.index("gas")
    ratio = C[:, gas] / np.where(C[:, power] == 0, np.nan, C[:, power])
    return {
        "rank": int(np.linalg.matrix_rank(C)),
        "singular_values": sv,
        "null_direction": dict(zip(FAULT_NAMES, np.round(null, 12))) if null is not None else None,
        "power_gas_ratio": float(np.nanmin(ratio)),
        "power_gas_exact": bool(np.allclose(C[:, power], -C[:, gas])),
    }


def stacked_jacobian(ops, couplings: FaultCouplings | None = None) -> np.ndarray:
    """Whitened Jacobian for readings taken at several operating points.

    Each epoch contributes three independent readings with the same relative
    noise, so the stacked covariance is block diagonal and whitening row by row
    is correct here, unlike for the enlarged observation of `inference.py`.
    """
    C = channel_matrix(couplings)
    M = np.vstack([observation_matrix(p, v, couplings=couplings) for p, v in ops])
    return (M @ C) / np.tile(noise.SIGMAS, len(ops))[:, None]


def _summary(Jw: np.ndarray) -> dict:
    sv = np.linalg.svd(Jw, compute_uv=False)
    keep = sv[sv > 1e-6 * sv[0]]
    angles = sorted(obs._angles(Jw).values())
    return {"rank": int(len(keep)),
            "condition": float(keep[0] / keep[-1]),
            "sv4_over_sv1": float(sv[3] / sv[0]) if len(sv) > 3 else float("nan"),
            "worst": angles[0], "second": angles[1], "third": angles[2]}


def search_two_point(powers=None, speeds=None, floor: float = 10.0) -> dict:
    """Best second operating point to pair with nominal.

    The objective is the second-worst pairwise angle, not the worst: the worst
    is power against gas, which is fixed at zero by the ceiling, so optimising
    it would be optimising a constant and every candidate would tie.
    """
    powers = powers if powers is not None else np.linspace(120.0, 450.0, 12)
    speeds = speeds if speeds is not None else np.linspace(0.2, 2.5, 12)
    refused = 0

    def evaluate(grid_p, grid_v, best):
        nonlocal refused
        for p in grid_p:
            for v in grid_v:
                if abs(p - NOMINAL[0]) < 1e-9 and abs(v - NOMINAL[1]) < 1e-9:
                    continue
                try:
                    s = _summary(stacked_jacobian([NOMINAL, (float(p), float(v))]))
                except Exception:
                    refused += 1
                    continue
                if best is None or s["second"] > best[0]["second"]:
                    best = (s, (float(p), float(v)))
        return best

    best = evaluate(powers, speeds, None)
    # One local refinement, because a coarse grid can miss the optimum by more
    # than the quantity being optimised varies across a cell: the 12 by 12 grid
    # returns 5.86 degrees while a hand-picked point nearby gives 5.95.
    dp = float(powers[1] - powers[0])
    dv = float(speeds[1] - speeds[0])
    p0, v0 = best[1]
    best = evaluate(np.linspace(max(p0 - dp, 100.0), p0 + dp, 7),
                    np.linspace(max(v0 - dv, 0.05), v0 + dv, 7), best)
    return {"best": best[0], "operating_point": best[1], "refused": refused,
            "clears_floor": best[0]["second"] > floor}


def compare() -> list[tuple[str, dict]]:
    """Probing against build context, on the same whitened footing."""
    rows = [
        ("nominal, one instant", _summary(stacked_jacobian([NOMINAL]))),
        ("two operating points", _summary(stacked_jacobian(
            [NOMINAL, (420.0, 2.20)]))),
        ("three operating points", _summary(stacked_jacobian(
            [NOMINAL, (420.0, 2.20), (150.0, 0.30)]))),
        ("four operating points", _summary(stacked_jacobian(
            [NOMINAL, (420.0, 2.20), (150.0, 0.30), (200.0, 1.50)]))),
        ("six operating points", _summary(stacked_jacobian(
            [NOMINAL, (420.0, 2.20), (150.0, 0.30), (200.0, 1.50),
             (350.0, 0.50), (150.0, 2.20)]))),
        ("build context, no probing",
         _summary(inf.build_context(whitening="full").Jw)),
    ]
    return rows


def report() -> None:
    print("Active probing, and the ceiling on it")
    print("=" * 96)

    C = channel_matrix()
    print("\nC, how each fault moves each channel, written out from the model")
    print(f"   {'':20s}" + "".join(f"{n:>10s}" for n in FAULT_NAMES))
    for i, n in enumerate(CHANNEL_NAMES):
        print(f"   {n:20s}" + "".join(f"{C[i, j]:10.4f}" for j in range(5)))

    M = observation_matrix()
    print("\nM, how each observable responds to each channel, at nominal")
    print(f"   {'':12s}" + "".join(f"{n[:16]:>18s}" for n in CHANNEL_NAMES))
    for i, s in enumerate(SENSOR_NAMES):
        print(f"   {s:12s}" + "".join(f"{M[i, j]:18.6f}" for j in range(4)))
    print("   The preheat column is three orders of magnitude below the first:")
    print("   a kelvin of preheat barely moves a pool running near 3000 K, and")
    print("   that is why the fourth channel stays weak whatever the probe.")

    err = verify_factorisation()
    print(f"\nJ = M C holds to {err:.1e} relative, which is the finite-difference error")

    c = ceiling()
    print(f"\nThe ceiling")
    print(f"   rank(C) = {c['rank']} against {len(FAULT_NAMES)} faults")
    print(f"   C[:, power] = -C[:, gas] exactly: {c['power_gas_exact']}")
    print(f"   so the invisible fault direction is")
    print("      " + ", ".join(f"{k} {v:+.4f}" for k, v in c["null_direction"].items()))
    print("   An equal simultaneous power and gas fault moves no channel, hence")
    print("   no observable. This holds for every instrument and every probe.")

    print("\nWhat probing buys")
    print(f"   {'observation set':28s} {'rank':>5s} {'condition':>11s} "
          f"{'sv4/sv1':>10s} {'worst':>8s} {'2nd':>8s} {'3rd':>8s}")
    for label, s in compare():
        s4 = "n/a" if np.isnan(s["sv4_over_sv1"]) else f"{s['sv4_over_sv1']:.2e}"
        print(f"   {label:28s} {s['rank']:5d} {s['condition']:11.1f} {s4:>10s} "
              f"{s['worst']:8.3f} {s['second']:8.3f} {s['third']:8.3f}")

    best = search_two_point()
    print(f"\nBest two-point probe over a 12 by 12 grid of power and speed")
    print(f"   second point {best['operating_point'][0]:.0f} W, "
          f"{best['operating_point'][1]:.2f} m/s")
    print(f"   second-worst pair {best['best']['second']:.3f} deg, "
          f"clears the ten degree floor: {best['clears_floor']}")
    print(f"   operating points the model refused: {best['refused']}")
    print("\n   Probing does not rescue the instantaneous suite. The pair it")
    print("   cannot touch is fixed by C, and the pairs it can touch stop short")
    print("   of the floor, while build context clears all ten for free.")


if __name__ == "__main__":
    report()
