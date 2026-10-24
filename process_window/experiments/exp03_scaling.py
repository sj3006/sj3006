"""Experiment 3: how the coupon cost grows as the grid gets finer.

The central empirical claim: with monotone structure, the cost of certifying
a fixed fraction of the window grows roughly with the window's BOUNDARY
(about n settings on an n x n grid), while unstructured methods pay for its
AREA (about n^2 settings). We measure coupons needed to certify 25%, 50%
and 70% of the true window on n x n grids.

Methods (all adaptive ones use the frontier allocation rule):
- ours: hybrid (chains + spread), with a good / an optimistic simulator,
  and with no simulator (flat prior; chain starts mid-row)
- ablations: chains only, spread only (good simulator)
- unstructured: betting tests, no physics ordering (good simulator)
- grid DoE + CP + Bonferroni: current practice, equal coupons everywhere

Run from process_window/:  python3 experiments/exp03_scaling.py [--quick]
"""

import argparse
import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.baselines import grid_doe  # noqa: E402
from pwcert.certify import WindowCertifier  # noqa: E402
from pwcert.synthetic import make_scenario  # noqa: E402

ALPHA = 0.05
FRACTIONS = (0.25, 0.5, 0.7)
OUT = os.path.join(os.path.dirname(__file__), "..", "results")

# name: (structure, simulator, start)
ADAPTIVE = {
    "ours, good sim": ("hybrid", "good", "boundary"),
    "ours, optimistic sim": ("hybrid", "biased", "boundary"),
    "ours, no sim": ("hybrid", "none", "middle"),
    "chains only, good sim": ("monotone", "good", "boundary"),
    "spread only, good sim": ("spread", "good", "boundary"),
    "unstructured, good sim": ("none", "good", "boundary"),
}


def coupons_to_reach(history, target):
    for h in history:
        if h["area"] >= target:
            return h["coupons"]
    return np.inf


def adaptive_costs(name, n, reps, budget):
    structure, sim, start = ADAPTIVE[name]
    sc = make_scenario(n, n, simulator=sim)
    true_area = int(sc.true_window().sum())
    costs = np.full((reps, len(FRACTIONS)), np.inf)
    for r in range(reps):
        wc = WindowCertifier(sc, alpha=ALPHA, structure=structure, start=start,
                             boundary_q=(0.2, 0.6), alloc="frontier",
                             batch=max(24, 2 * n), rng=np.random.default_rng(r))
        hist = wc.run(budget)
        for k, f in enumerate(FRACTIONS):
            costs[r, k] = coupons_to_reach(hist, np.ceil(f * true_area))
    return true_area, costs


def doe_costs(n, reps):
    """Smallest equal-allocation DoE (searched on a geometric grid of
    coupons per setting) whose certified area reaches each fraction, on
    average over reps."""
    sc = make_scenario(n, n, simulator="good")
    true_area = int(sc.true_window().sum())
    out = np.full(len(FRACTIONS), np.inf)
    for n_per in np.unique(np.geomspace(50, 3000, 30).astype(int)):
        areas = [grid_doe(sc, int(n_per), ALPHA, rng=np.random.default_rng(r))[0].sum()
                 for r in range(reps)]
        for k, f in enumerate(FRACTIONS):
            if np.isinf(out[k]) and np.mean(areas) >= f * true_area:
                out[k] = n_per * n * n
        if np.isfinite(out).all():
            break
    return true_area, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    sizes = (8, 12, 16) if args.quick else (8, 12, 16, 24, 32)
    reps = 2 if args.quick else 5

    rows = []
    for n in sizes:
        budget = 200 * n * n          # cap, ~200 coupons per setting
        for name in ADAPTIVE:
            t0 = time.time()
            true_area, costs = adaptive_costs(name, n, reps, budget)
            med = np.median(costs, axis=0)
            for f, c in zip(FRACTIONS, med):
                rows.append(dict(grid=n, method=name, fraction=f, median_coupons=c,
                                 true_area=true_area, reps=reps))
            print(f"{n:2d}x{n:<2d} {name:28s} " +
                  "  ".join(f"{int(f*100)}%: {c:>8.0f}" for f, c in zip(FRACTIONS, med)) +
                  f"   ({time.time() - t0:.0f}s)", flush=True)
        t0 = time.time()
        true_area, c = doe_costs(n, reps)
        for f, cc in zip(FRACTIONS, c):
            rows.append(dict(grid=n, method="grid DoE + CP + Bonferroni", fraction=f,
                             median_coupons=cc, true_area=true_area, reps=reps))
        print(f"{n:2d}x{n:<2d} {'grid DoE + CP + Bonferroni':28s} " +
              "  ".join(f"{int(f*100)}%: {cc:>8.0f}" for f, cc in zip(FRACTIONS, c)) +
              f"   ({time.time() - t0:.0f}s)", flush=True)

    os.makedirs(OUT, exist_ok=True)
    suffix = "_quick" if args.quick else ""
    path = os.path.join(OUT, f"exp03_scaling{suffix}.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("->", path)
    plot(rows, os.path.join(OUT, f"exp03_scaling{suffix}.png"))


def plot(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, len(FRACTIONS), figsize=(5 * len(FRACTIONS), 4), squeeze=False)
    methods = list(ADAPTIVE) + ["grid DoE + CP + Bonferroni"]
    for ax, f in zip(axes[0], FRACTIONS):
        for m in methods:
            pts = [r for r in rows if r["method"] == m and r["fraction"] == f
                   and np.isfinite(r["median_coupons"])]
            if pts:
                ax.loglog([p["grid"] for p in pts], [p["median_coupons"] for p in pts],
                          "o-", label=m)
        ns = np.array(sorted({r["grid"] for r in rows}), dtype=float)
        ref = [r for r in rows if r["fraction"] == f and np.isfinite(r["median_coupons"])]
        if ref:
            c0 = min(r["median_coupons"] for r in ref)
            ax.loglog(ns, c0 * (ns / ns[0]), "k:", lw=1, label="slope 1 (boundary)")
            ax.loglog(ns, c0 * (ns / ns[0]) ** 2, "k--", lw=1, label="slope 2 (area)")
        ax.set_title(f"coupons to certify {int(f * 100)}% of the window")
        ax.set_xlabel("grid size n (n x n settings)")
        ax.set_ylabel("coupons")
        ax.grid(alpha=0.3, which="both")
    axes[0][0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    print("->", path)


if __name__ == "__main__":
    main()
