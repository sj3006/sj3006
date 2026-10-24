"""Experiment 4: what does learning WHERE to test cost?

Runs the frontier allocation rule twice: with its normal estimates (prior
from the simulator plus data) and with an oracle that knows the true defect
rates. Testing uses only data in both, so both are valid. The ratio of
coupons needed is the "learning overhead"; if it stays bounded as the grid
grows, the learning term in Theorem 3 (notes/04) is lower order.

Run from process_window/:  python3 experiments/exp04_oracle.py
"""

import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.certify import WindowCertifier  # noqa: E402
from pwcert.synthetic import make_scenario  # noqa: E402

FRACTIONS = (0.5, 0.7)
OUT = os.path.join(os.path.dirname(__file__), "..", "results")


def cost(sc, structure, sim_oracle, n, reps):
    A = sc.true_window().sum()
    out = np.full((reps, len(FRACTIONS)), np.inf)
    for r in range(reps):
        wc = WindowCertifier(sc, structure=structure, start="boundary", boundary_q=(0.2, 0.6),
                             alloc="frontier", oracle=sim_oracle, batch=max(24, 2 * n),
                             rng=np.random.default_rng(r))
        hist = wc.run(200 * n * n)
        for k, f in enumerate(FRACTIONS):
            out[r, k] = next((h["coupons"] for h in hist if h["area"] >= np.ceil(f * A)), np.inf)
    return np.median(out, axis=0)


def main():
    rows = []
    for n in (8, 16, 24):
        for sim in ("good", "biased"):
            sc = make_scenario(n, n, simulator=sim)
            for structure in ("spread", "hybrid"):
                t0 = time.time()
                learned = cost(sc, structure, False, n, 4)
                oracle = cost(sc, structure, True, n, 4)
                for f, a, b in zip(FRACTIONS, learned, oracle):
                    rows.append(dict(grid=n, simulator=sim, structure=structure, fraction=f,
                                     learned=a, oracle=b, overhead=round(a / b, 3)))
                print(f"{n:2d}x{n:<2d} {sim:7s} {structure:7s} " +
                      "  ".join(f"{int(f*100)}%: learned {a:7.0f} oracle {b:7.0f} (x{a/b:.2f})"
                                for f, a, b in zip(FRACTIONS, learned, oracle)) +
                      f"  ({time.time() - t0:.0f}s)", flush=True)
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "exp04_oracle.csv")
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("->", path)


if __name__ == "__main__":
    main()
