"""Route A: richer observables, no new hardware.

Tier 2 treated each sensor as one instantaneous number. That discards almost
everything the process already tells you. A build has a known toolpath, a known
layer schedule, a known gas flow direction and a known part geometry, and each
fault leaves a different trace across those.

    fault      how it varies across a build          known regressor it loads onto
    --------   -----------------------------------   -----------------------------
    power      roughly uniform, slow drift           constant / build time
    speed      worst where the galvo must turn       1 / vector length
    layer      constant within a layer, steps        layer-synchronous indicator
               between them
    gas        gradient along the flow direction     position along gas flow
    geometry   follows the part's own shape          local solid support depth

The last is the strongest case: the build file tells you the geometry, so heat
accumulation has a fingerprint no other fault can forge.

Why this is cheap
-----------------
Each fault modulates its own magnitude across segments: at segment i a fault k
of magnitude f_k acts as f_k * m_k(i). To first order - which is all a Jacobian
needs - the sensor residual at that segment is

    r(i) = sum_k  J[:, k] * f_k * m_k(i)

with J the instantaneous Jacobian already computed. Regressing r(i) onto the
known regressors g_j(i) gives the enlarged observation, and its Jacobian is

    Jbig[(s, j), k] = J[s, k] * B[j, k],     B = (G'G)^-1 G' M

So the whole route costs one least-squares solve on small matrices rather than
re-running the thermal model thousands of times.

A note on Tier 1
----------------
Adding spatial and temporal regressors is not a trick to squeeze more out of the
same measurement - it is a genuinely different measurement model, with new
equations relating each fault to its spatial signature. If this changes the
isolability conclusions, Tier 1 should be re-run on the enlarged observation set
to keep the two tiers describing the same system.
"""

from __future__ import annotations

import itertools

import numpy as np

from diagnosability import FAULT_NAMES, SENSOR_NAMES, collinearity_index, jacobian, whiten

__all__ = ["REGRESSOR_NAMES", "scan_plan", "projection_matrix", "enlarged_jacobian"]

REGRESSOR_NAMES = ("constant", "gas_axis", "layer_sync", "turn_density", "support_depth")


def scan_plan(n_layers: int = 6, n_vectors: int = 14, seed: int = 0) -> dict[str, np.ndarray]:
    """A synthetic but structured build: several layers of vectors across a plate.

    Everything here is knowable before the build from the sliced file and the
    machine configuration. Nothing depends on the sensors.
    """
    rng = np.random.default_rng(seed)
    layers, ys, lengths, support = [], [], [], []
    for layer in range(n_layers):
        for v in range(n_vectors):
            layers.append(layer)
            # position across the plate, which is also distance along gas flow
            ys.append((v + 0.5) / n_vectors)
            # vector length varies across the cross-section: short at the edges
            # where the part narrows, long through the middle
            edge = abs((v + 0.5) / n_vectors - 0.5) * 2.0
            lengths.append(0.4e-3 + 12e-3 * (1.0 - edge**2) * rng.uniform(0.85, 1.15))
            # solid material depth beneath this vector. Thin near the edges and
            # in the lower layers, which is where heat accumulates.
            support.append((0.2 + 0.8 * (1.0 - edge)) * (0.3 + 0.7 * layer / n_layers))
    return {
        "layer": np.asarray(layers, float),
        "gas_axis": np.asarray(ys, float),
        "length": np.asarray(lengths, float),
        "support": np.asarray(support, float),
    }


def _standardise(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, float)
    s = a.std()
    return (a - a.mean()) / s if s > 0 else np.zeros_like(a)


def regressors(plan: dict[str, np.ndarray]) -> np.ndarray:
    """Known context, one column per regressor. All standardised but the intercept."""
    n = len(plan["layer"])
    return np.column_stack([
        np.ones(n),
        _standardise(plan["gas_axis"]),
        _standardise(plan["layer"] % 2),           # alternating recoater direction
        _standardise(1.0 / plan["length"]),        # turns per unit length
        _standardise(-plan["support"]),            # less support = more accumulation
    ])


def modulations(plan: dict[str, np.ndarray]) -> np.ndarray:
    """How each fault's magnitude actually varies across the build.

    These are physical claims about fault behaviour, not fitted. They set which
    regressor each fault loads onto, so they drive the result and must be swept
    alongside the coupling constants.
    """
    n = len(plan["layer"])
    build_time = _standardise(plan["layer"] * 1000 + np.arange(n) % 1000)
    return np.column_stack([
        1.0 + 0.3 * build_time,                                  # power: drift
        1.0 + 0.8 * _standardise(1.0 / plan["length"]),          # speed: turns
        1.0 + 1.0 * _standardise(plan["layer"] % 2),             # layer: recoater cycle
        1.0 + 0.9 * _standardise(plan["gas_axis"]),              # gas: flow gradient
        1.0 + 1.0 * _standardise(-plan["support"]),              # geometry: part shape
    ])


def projection_matrix(plan: dict[str, np.ndarray]) -> np.ndarray:
    """B[j, k]: how strongly fault k's modulation loads onto regressor j."""
    G = regressors(plan)
    M = modulations(plan)
    return np.linalg.lstsq(G, M, rcond=None)[0]


def enlarged_jacobian(J: np.ndarray, plan: dict[str, np.ndarray]) -> np.ndarray:
    """Jacobian of (sensor x regressor) coefficients against fault magnitudes."""
    B = projection_matrix(plan)
    rows = [J[s, :] * B[j, :] for s in range(J.shape[0]) for j in range(B.shape[0])]
    return np.vstack(rows)


def _angles(Jw: np.ndarray) -> dict[tuple[str, str], float]:
    out = {}
    for i, a in enumerate(FAULT_NAMES):
        for j, b in enumerate(FAULT_NAMES):
            if i >= j:
                continue
            u, v = Jw[:, i], Jw[:, j]
            nu, nv = np.linalg.norm(u), np.linalg.norm(v)
            if nu == 0 or nv == 0:
                out[(a, b)] = 0.0
                continue
            c = float(np.dot(u, v) / (nu * nv))
            ang = np.degrees(np.arccos(np.clip(c, -1.0, 1.0)))
            out[(a, b)] = float(min(ang, 180.0 - ang))
    return out


if __name__ == "__main__":
    J, _ = jacobian()
    plan = scan_plan()
    print(f"scan plan: {len(plan['layer']):.0f} segments over "
          f"{int(plan['layer'].max())+1} layers")

    B = projection_matrix(plan)
    print("\nhow each fault loads onto each known regressor")
    print(f"   {'':14s}" + "".join(f"{n:>11s}" for n in FAULT_NAMES))
    for j, r in enumerate(REGRESSOR_NAMES):
        print(f"   {r:14s}" + "".join(f"{B[j, k]:>11.3f}" for k in range(len(FAULT_NAMES))))

    sig_inst = np.array([1.0, 1.0, 0.03])
    inst = whiten(J, sig_inst)
    big = enlarged_jacobian(J, plan)
    sig_big = np.repeat(sig_inst, len(REGRESSOR_NAMES))
    bigw = whiten(big, sig_big)

    a_i, a_b = _angles(inst), _angles(big_w := bigw)
    print("\nPAIRWISE ANGLES, instantaneous vs enlarged (degrees)")
    print(f"   {'pair':24s}{'instant':>10s}{'enlarged':>11s}{'change':>10s}")
    for (a, b) in sorted(a_i, key=lambda p: a_i[p]):
        print(f"   {a + ' / ' + b:24s}{a_i[(a,b)]:>10.2f}{a_b[(a,b)]:>11.2f}"
              f"{a_b[(a,b)] - a_i[(a,b)]:>+10.2f}")

    print("\nRANK AND CONDITIONING")
    for label, M in (("instantaneous", inst), ("enlarged", bigw)):
        s = np.linalg.svd(M, compute_uv=False)
        s = s[s > s.max() * 1e-12]
        print(f"   {label:14s} rank {len(s)}   condition {s[0]/s[-1]:>12,.0f}")

    print("\nWORST FINITE COLLINEARITY INDEX (cutoff 10)")
    for label, M in (("instantaneous", inst), ("enlarged", bigw)):
        vals = [(collinearity_index(M, s), s) for s in itertools.combinations(range(5), 2)]
        vals = [(v, s) for v, s in vals if np.isfinite(v) and v < 1e12]
        if vals:
            v, s = max(vals)
            print(f"   {label:14s} {v:>12,.1f}  ({FAULT_NAMES[s[0]]}/{FAULT_NAMES[s[1]]})")
        else:
            print(f"   {label:14s} all pairs singular")
