"""Live LM runs next to surface runs at the same budget.

Reads every results/lm/lm_live_seed*.json (the certifier querying SmolLM2
directly) and runs the same certifier on the measured surface (outcomes
drawn from the fitted rates) at the same budget, so the two can be
compared: settings certified, and unsafe settings certified (judged
against the measured surface).

Writes results/lm/lm_live_summary.csv.
Run: OMP_NUM_THREADS=1 python3 experiments/lm_live_summary.py [--reps 20]
"""

import argparse
import csv
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.cone import ConeCertifier  # noqa: E402
from pwcert.lm_scenario import make_lm_scenario  # noqa: E402

LM = os.path.join(os.path.dirname(__file__), "..", "results", "lm")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    args = ap.parse_args()
    live = []
    for p in sorted(glob.glob(os.path.join(LM, "lm_live_seed*.json"))):
        with open(p) as f:
            r = json.load(f)
        live.append(dict(kind="live", seed=r["seed"], budget=r["budget"], generations=r["generations"],
                         certified=r["certified"], unsafe_certified=r["certified_unsafe_vs_reference"],
                         safe_reference=r["safe_reference"]))
    budget = live[0]["budget"] if live else 8000
    sc = make_lm_scenario(0.10, "pilot")
    n = sc.truth["degenerate"].shape[0]
    W = sc.true_window()
    surf = []
    for s in range(args.reps):
        c = ConeCertifier(sc, rule="cone", weights="ensemble", alloc="edge", target_q=0.7, batch=2 * n,
                          coupons0=sc.meta["pilot_coupons"], rng=np.random.default_rng(s))
        c.run(budget)
        C = c.window()
        surf.append(dict(kind="surface", seed=s, budget=budget, generations=int(c.coupons), certified=int(C.sum()),
                         unsafe_certified=int((C & ~W).sum()), safe_reference=int(W.sum())))
    rows = live + surf
    with open(os.path.join(LM, "lm_live_summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for kind, rs in (("live", live), ("surface", surf)):
        if rs:
            c = [r["certified"] for r in rs]
            print(f"{kind}: {len(rs)} runs, certified {np.mean(c):.1f} on average (range {min(c)}-{max(c)}) "
                  f"of {rs[0]['safe_reference']}; runs with an unsafe setting certified: "
                  f"{sum(r['unsafe_certified'] > 0 for r in rs)}")


if __name__ == "__main__":
    main()
