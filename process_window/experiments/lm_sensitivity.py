"""Are the LM results an artefact of the chosen thresholds?

The surface file stores each generation's scores (seq-rep-4, mean NLL), so
the failure definitions and the tolerance can be changed without new
generations. For each choice we rebuild the scenario (truth and pilot from
the same disjoint splits) and report generations to certify 50% of the safe
region for ours, testing without the ordering, and the full grid with
fixed-sequence testing (Learn-then-Test).

Run from process_window/:  python3 experiments/lm_sensitivity.py [--reps 5]
"""

import argparse
import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.baselines import grid_fst  # noqa: E402
from pwcert.cone import ConeCertifier  # noqa: E402
from pwcert.lm_scenario import make_lm_scenario  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "lm")
SETTINGS = [  # (eps, repetition threshold, NLL threshold); first row = paper
    (0.10, 0.2, 3.5),
    (0.10, 0.15, 3.5), (0.10, 0.3, 3.5),
    (0.10, 0.2, 3.0), (0.10, 0.2, 4.0),
    (0.05, 0.2, 3.5), (0.20, 0.2, 3.5),
]


def cost(sc, rule, reps, target, budget):
    n = sc.truth[sc.modes[0]].shape[0]
    out = []
    for r in range(reps):
        c = ConeCertifier(sc, rule=rule, weights="ensemble" if rule == "cone" else "uniform", alloc="edge",
                          target_q=0.7, batch=2 * n, coupons0=sc.meta["pilot_coupons"],
                          rng=np.random.default_rng(r))
        hist = c.run(budget)
        out.append(next((h["coupons"] for h in hist if h["area"] >= target), np.inf))
        out[-1] = out[-1] if max(h["errors"] for h in hist) == 0 else -out[-1]   # flag a false certificate
    return out


def fst_cost(sc, target):
    W = sc.true_window()
    for n_per in np.unique(np.geomspace(20, 5000, 60).astype(int)):
        a = np.mean([grid_fst(sc, int(n_per), 0.05, rng=np.random.default_rng(s))[0].sum() for s in range(3)])
        if a >= target:
            return float(n_per * W.size)
    return np.inf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--budget", type=int, default=60_000)
    args = ap.parse_args()
    rows = []
    for eps, rt, nt in SETTINGS:
        t0 = time.time()
        sc = make_lm_scenario(eps, "pilot", rep_thresh=rt, nll_thresh=nt)
        W = sc.true_window()
        target = int(np.ceil(0.5 * W.sum()))
        ours = cost(sc, "cone", args.reps, target, args.budget)
        noord = cost(sc, "none", args.reps, target, args.budget)
        row = dict(eps=eps, rep_thresh=rt, nll_thresh=nt, safe=int(W.sum()),
                   ours=float(np.median(np.abs(ours))), no_ordering=float(np.median(np.abs(noord))),
                   grid_fst=fst_cost(sc, target),
                   runs_with_false_certificate=int(sum(x < 0 for x in ours + noord)))
        row["ratio_no_ordering"] = round(row["no_ordering"] / row["ours"], 2)
        row["ratio_grid_fst"] = round(row["grid_fst"] / row["ours"], 2)
        rows.append(row)
        print(row, f"({time.time() - t0:.0f}s)", flush=True)
    with open(os.path.join(OUT, "lm_sensitivity.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
