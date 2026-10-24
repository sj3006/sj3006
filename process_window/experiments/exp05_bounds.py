"""Experiment 5: theory next to practice.

For a target T = {settings with every defect rate <= q * eps} and n x n
grids, compute
- LB_A: Theorem 4a lower bound with the physics ordering, L * LP_A(T)
- LB_U: Theorem 4b lower bound without it, L * sum_{z in T} max_m 1/k_m(z)
- UB:   Theorem 3 oracle upper bound from notes/05, section 6
and measure the coupons our method (and the unstructured baseline) actually
use until T is entirely certified.

If LB_A and our measured cost grow like n while LB_U grows like n^2, the
boundary-vs-area story holds with numbers attached.

Run from process_window/:  python3 experiments/exp05_bounds.py [--quick]
"""

import argparse
import csv
import os
import sys
import time

import numpy as np
from scipy.optimize import linprog

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.certify import WindowCertifier, _kl_vec  # noqa: E402
from pwcert.synthetic import make_scenario  # noqa: E402

ALPHA = BETA = 0.05
Q = 0.5
CAP = 0.8
OUT = os.path.join(os.path.dirname(__file__), "..", "results")


def growth_rate(p, eps, cap=CAP, grid=400):
    """Best expected log-growth of a bet capped at cap / (1 - eps)."""
    lam = np.linspace(0, cap / (1 - eps), grid)
    g = p * np.log1p(-lam * (1 - eps)) + (1 - p) * np.log1p(lam * eps)
    return g.max()


def bounds(sc):
    wc = WindowCertifier(sc, structure="spread", rng=np.random.default_rng(0))
    M, N, eps, truth, dom = wc.M, wc.N, wc.eps, wc.truth, wc.dominance
    T = (truth <= Q * eps).all(axis=0)
    k = _kl_vec(truth, eps)                                     # (M, N)
    L = (1 - BETA) * np.log(1 / ALPHA) - np.log(2)

    edges = []
    for m in range(M):
        t_idx = np.flatnonzero(T)
        # z is minimal (riskiest) in T for mode m if no other t in T is riskier: z safer than t.
        sub = dom[m][np.ix_(t_idx, t_idx)]                      # [t, z] = z safer than t
        np.fill_diagonal(sub, False)
        edges.append(t_idx[~sub.any(axis=0)])

    rows_A = []
    for m in range(M):
        for z in edges[m]:
            D = dom[m][:, z] & (truth[m] < eps[m])              # y with z safer than y, y safe
            rows_A.append(np.where(D, k[m], 0.0))
    A = np.array(rows_A)
    lp = linprog(np.ones(N), A_ub=-A, b_ub=-np.ones(len(A)), bounds=(0, None), method="highs")
    lb_a = L * lp.fun

    lb_u = L * np.sum(np.max(1.0 / np.maximum(k[:, T], 1e-12), axis=0))

    need = {}
    for m in range(M):
        for z in edges[m]:
            c = (np.log(M * N / ALPHA) + np.log(16)) / growth_rate(truth[m, z], eps[m, 0])
            need[z] = max(need.get(z, 0.0), c)
    ub = sum(need.values())
    n_edge = len(set().union(*[set(e) for e in edges]))
    return T, dict(T_size=int(T.sum()), edge_points=n_edge, LB_A=lb_a, LB_U=lb_u, UB=ub)


def measured(sc, T, structure, n, reps):
    out = []
    for r in range(reps):
        # Edge allocation needs the physics ordering; the unstructured
        # baseline uses the frontier rule restricted to the same target.
        alloc = "frontier" if structure == "none" else "edge"
        wc = WindowCertifier(sc, structure=structure, start="boundary", boundary_q=(0.2, 0.6),
                             alloc=alloc, target_q=Q, batch=max(24, 2 * n),
                             rng=np.random.default_rng(r))
        budget, c = 300 * n * n, np.inf
        while wc.coupons < budget and wc.run_plate():
            if (wc.window().ravel() >= T).all():
                c = wc.coupons
                break
        out.append(c)
    return float(np.median(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    sizes, reps = ((8, 12, 16), 3) if args.quick else ((8, 12, 16, 24, 32), 3)
    rows = []
    for n in sizes:
        t0 = time.time()
        sc = make_scenario(n, n, simulator="good")
        T, b = bounds(sc)
        b["ours_hybrid"] = measured(sc, T, "hybrid", n, reps)
        b["unstructured"] = measured(sc, T, "none", n, reps)
        b["grid"] = n
        rows.append(b)
        print(f"{n:2d}x{n:<2d} |T|={b['T_size']:4d} edge={b['edge_points']:3d}  "
              f"LB_A={b['LB_A']:8.0f}  UB={b['UB']:8.0f}  ours={b['ours_hybrid']:8.0f}  |  "
              f"LB_U={b['LB_U']:9.0f}  unstructured={b['unstructured']:8.0f}  "
              f"({time.time() - t0:.0f}s)", flush=True)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "exp05_bounds" + ("_quick" if args.quick else "") + ".csv")
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["grid", "T_size", "edge_points", "LB_A", "UB",
                                           "ours_hybrid", "LB_U", "unstructured"])
        w.writeheader()
        w.writerows(rows)
    print("->", path)


if __name__ == "__main__":
    main()
