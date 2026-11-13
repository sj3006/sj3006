"""Language-model application: certify safe (temperature, top-p) settings.

Uses the measured failure-rate surface (pwcert/lm_scenario.py). Three parts:

1. fixed budget: certified fraction of the true safe region vs generations,
   for ours (cone rule + edge allocation, pilot-study simulator, pilot cost
   counted), ours without a simulator, the same tests without the ordering,
   and a full-grid evaluation with exact binomial bounds and Bonferroni
   (the non-adaptive, Learn-then-Test-style approach: every setting gets
   the same number of generations);
2. fixed confidence: SearchCertifier vs a per-setting two-sided test, with
   lower bounds;
3. the GP level-set baseline's error rate on this surface.

Run from process_window/:  python3 experiments/exp_lm.py [--reps 8]
"""

import argparse
import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from exp_search import PerSetting, boundary_bound, unordered_bound  # noqa: E402
from final import lower_bounds  # noqa: E402
from pwcert.baselines import grid_doe  # noqa: E402
from pwcert.cone import ConeCertifier  # noqa: E402
from pwcert.gp_baseline import GPLevelSet  # noqa: E402
from pwcert.lm_scenario import make_lm_scenario  # noqa: E402
from pwcert.search import SearchCertifier  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "lm")
EPS, Q = 0.10, 0.5


def write(rows, name):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("->", name, flush=True)


def fixed_budget(reps, budget):
    pilot = make_lm_scenario(EPS, "pilot")
    flat = make_lm_scenario(EPS, "none")
    n = pilot.truth["degenerate"].shape[0]
    W = pilot.true_window()
    print("true safe settings:", int(W.sum()), "of", W.size, flush=True)
    checkpoints = np.linspace(0, budget, 41)[1:]
    methods = {
        "ours": lambda r: ConeCertifier(pilot, rule="cone", weights="ensemble", alloc="edge", target_q=0.7,
                                        batch=2 * n, coupons0=pilot.meta["pilot_coupons"],
                                        rng=np.random.default_rng(r)),
        "ours, no simulator": lambda r: ConeCertifier(flat, rule="cone", weights="uniform", alloc="edge",
                                                      target_q=0.7, batch=2 * n, rng=np.random.default_rng(r)),
        "no ordering": lambda r: ConeCertifier(pilot, rule="none", weights="uniform", alloc="edge",
                                               target_q=0.7, batch=2 * n,
                                               coupons0=pilot.meta["pilot_coupons"],
                                               rng=np.random.default_rng(r)),
    }
    rows = []
    for name, mk in methods.items():
        frac = np.zeros((reps, len(checkpoints)))
        errors = 0
        t0 = time.time()
        for r in range(reps):
            c = mk(r)
            hist = c.run(budget)
            cs = np.array([h["coupons"] for h in hist])
            ar = np.array([h["area"] for h in hist])
            errors += int(max(h["errors"] for h in hist) > 0)
            for k, cp in enumerate(checkpoints):
                i = np.searchsorted(cs, cp, side="right") - 1
                frac[r, k] = ar[i] / W.sum() if i >= 0 else 0.0
        for cp, m_ in zip(checkpoints, frac.mean(0)):
            rows.append(dict(method=name, generations=int(cp), frac=round(m_, 4), runs_with_errors=errors))
        print(f"{name:20s} final {frac.mean(0)[-1]:.3f}  runs with an unsafe setting certified: {errors}/{reps}"
              f"  ({time.time() - t0:.0f}s)", flush=True)
    for cp in checkpoints:
        n_per = cp / W.size
        a = np.mean([grid_doe(pilot, int(n_per), 0.05, rng=np.random.default_rng(s))[0].sum()
                     for s in range(5)]) / W.sum() if n_per >= 1 else 0.0
        rows.append(dict(method="full grid (Bonferroni)", generations=int(cp), frac=round(a, 4),
                         runs_with_errors=0))
    write(rows, "lm_fixed_budget.csv")


def fixed_confidence(reps):
    sc = make_lm_scenario(EPS, "pilot")
    n = sc.truth["degenerate"].shape[0]
    T, lb_a, _, n_edge = lower_bounds(sc, Q)
    lb_b, n_bd = boundary_bound(sc, Q)
    row = dict(target_size=int(T.sum()), LB_ordered=round(lb_a + lb_b), LB_unordered=round(unordered_bound(sc, Q)))
    for name, mk in (("search", lambda r: SearchCertifier(sc, q=Q, batch=2 * n, rng=np.random.default_rng(r))),
                     ("per-setting", lambda r: PerSetting(sc, q=Q, batch=2 * n, rng=np.random.default_rng(r)))):
        cs, comp, uns = [], 0, 0
        for r in range(reps):
            c = mk(r)
            while c.coupons < 2_000_000 and c.run_plate():
                pass
            cs.append(c.coupons + sc.meta["pilot_coupons"] * (name == "search"))
            comp += int((c.window() >= T).all())
            uns += int((c.window() & ~sc.true_window()).sum())
        row[name] = float(np.median(cs))
        row[name + "_complete"] = f"{comp}/{reps}"
        row[name + "_unsafe"] = uns
    print(row, flush=True)
    write([row], "lm_fixed_confidence.csv")


def gp(reps, budget):
    sc = make_lm_scenario(EPS, "pilot")
    W = sc.true_window()
    rows = []
    for beta in (2.0, 3.0, 4.0):
        for ls in (0.1, 0.2, 0.3):
            errs, areas = 0, []
            for r in range(reps):
                g = GPLevelSet(sc, beta=beta, lengthscale=ls, batch=24, rng=np.random.default_rng(r))
                h = g.run(budget)
                errs += int(max(x["errors"] for x in h) > 0)
                areas.append(h[-1]["area"] - h[-1]["errors"])
            rows.append(dict(beta=beta, lengthscale=ls, runs=reps, fwer=round(errs / reps, 3),
                             correct_frac=round(float(np.mean(areas)) / W.sum(), 3)))
            print(rows[-1], flush=True)
    write(rows, "lm_gp.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--budget", type=int, default=40_000)
    ap.add_argument("--parts", default="budget,confidence,gp")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if "budget" in args.parts:
        fixed_budget(args.reps, args.budget)
    if "confidence" in args.parts:
        fixed_confidence(args.reps)
    if "gp" in args.parts:
        gp(max(args.reps, 20), args.budget // 2)


if __name__ == "__main__":
    main()
