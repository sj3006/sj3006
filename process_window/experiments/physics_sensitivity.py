"""Do the Rosenthal 316L results depend on the placeholder calibration?

The criterion thresholds and the absorptivity in pwcert/physics.py are
placeholders (published keyhole thresholds alone range from about 6 to 50
depending on the study and the definition). Here each is moved one at a
time (absorptivity 0.30 / 0.40; lack-of-fusion overlap threshold -10% /
+10%; keyhole and balling thresholds -20% / +20%), the scenario is rebuilt
(the simulator keeps its errors relative to the new truth), and we report
trials to certify half of the safe region for ours, the same tests without
the ordering, and the full grid with fixed-sequence testing.

Run from process_window/:  python3 experiments/physics_sensitivity.py [--n 24] [--reps 5]
"""

import argparse
import csv
import os
import sys
import time
from dataclasses import replace

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.baselines import grid_fst  # noqa: E402
from pwcert.cone import ConeCertifier  # noqa: E402
from pwcert.physics import SS316L, Criteria, make_physics_scenario  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "final")
C0 = Criteria()
SETTINGS = [  # (label, absorptivity, criteria); first row = paper
    ("paper", 0.35, C0),
    ("absorptivity 0.30", 0.30, C0), ("absorptivity 0.40", 0.40, C0),
    ("LoF threshold -10%", 0.35, replace(C0, lof_thresh=0.9 * C0.lof_thresh)),
    ("LoF threshold +10%", 0.35, replace(C0, lof_thresh=1.1 * C0.lof_thresh)),
    ("keyhole threshold -20%", 0.35, replace(C0, kh_thresh=0.8 * C0.kh_thresh)),
    ("keyhole threshold +20%", 0.35, replace(C0, kh_thresh=1.2 * C0.kh_thresh)),
    ("balling threshold -20%", 0.35, replace(C0, ball_thresh=0.8 * C0.ball_thresh)),
    ("balling threshold +20%", 0.35, replace(C0, ball_thresh=1.2 * C0.ball_thresh)),
]


def cost(sc, rule, reps, target, budget):
    """Trials to certify `target` safe settings per run; negative if the run
    ever certified an unsafe setting."""
    n = sc.truth[sc.modes[0]].shape[0]
    out = []
    for r in range(reps):
        c = ConeCertifier(sc, rule=rule, weights="ensemble" if rule == "cone" else "uniform", alloc="edge",
                          target_q=0.7, batch=2 * n, rng=np.random.default_rng(r))
        hist = c.run(budget)
        x = next((h["coupons"] for h in hist if h["area"] >= target), np.inf)
        out.append(x if max(h["errors"] for h in hist) == 0 else -x)
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
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--reps", type=int, default=5)
    args = ap.parse_args()
    n, budget = args.n, 300 * args.n * args.n
    rows = []
    for label, A, crit in SETTINGS:
        t0 = time.time()
        sc = make_physics_scenario(n, n, mat=replace(SS316L, A=A), crit=crit)
        W = sc.true_window()
        target = int(np.ceil(0.5 * W.sum()))
        ours = cost(sc, "cone", args.reps, target, budget)
        noord = cost(sc, "none", args.reps, target, budget)
        row = dict(setting=label, n=n, safe=int(W.sum()), ours=float(np.median(np.abs(ours))),
                   no_ordering=float(np.median(np.abs(noord))), grid_fst=fst_cost(sc, target),
                   runs_with_false_certificate=int(sum(x < 0 for x in ours + noord)))
        row["ratio_no_ordering"] = round(row["no_ordering"] / row["ours"], 2)
        row["ratio_grid_fst"] = round(row["grid_fst"] / row["ours"], 2)
        rows.append(row)
        print(row, f"({time.time() - t0:.0f}s)", flush=True)
        with open(os.path.join(OUT, f"physics_sensitivity_{n}.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)


if __name__ == "__main__":
    main()
