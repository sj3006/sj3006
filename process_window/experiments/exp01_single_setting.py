"""Experiment 1: one setting, one failure mode.

Part A (validity): when the setting is truly bad (p >= eps), how often does
the test wrongly certify it? Must be at most alpha for every betting
strategy and every prior, including a lying simulator.

Part B (power): when the setting is good, how many coupons until it is
certified? Compared against the zero-failure success-run rule
n = ln(alpha) / ln(1 - eps).

Run from process_window/:  python3 experiments/exp01_single_setting.py
"""

import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.eprocess import coupons_to_certify  # noqa: E402

ALPHA, EPS = 0.05, 0.05
OUT = os.path.join(os.path.dirname(__file__), "..", "results")


def part_a(rng, reps=4000, max_n=2000):
    rows = []
    for p in (EPS, EPS + 0.02):
        for strategy in ("fixed", "agrapa", "mixture", "hedge"):
            for prior_name, prior in (("none", None), ("lying", 0.001)):
                stop = coupons_to_certify(p, EPS, ALPHA, rng, strategy=strategy,
                                          prior_mean=prior, prior_weight=10.0,
                                          max_n=max_n, reps=reps)
                rate = np.isfinite(stop).mean()
                se = np.sqrt(rate * (1 - rate) / reps)
                rows.append(dict(p=p, strategy=strategy, prior=prior_name,
                                 false_cert_rate=round(rate, 4), se=round(se, 4)))
    return rows


def part_b(rng, reps=1000, max_n=3000):
    rows = []
    for p in (0.0, 0.005, 0.01, 0.02, 0.03):
        for strategy in ("fixed", "agrapa", "mixture", "hedge"):
            for prior_name in ("none", "accurate", "pessimistic"):
                prior = {"none": None, "accurate": p, "pessimistic": 0.2}[prior_name]
                stop = coupons_to_certify(p, EPS, ALPHA, rng, strategy=strategy,
                                          prior_mean=prior, prior_weight=10.0,
                                          max_n=max_n, reps=reps)
                rows.append(dict(p=p, strategy=strategy, prior=prior_name,
                                 median_coupons=float(np.median(stop)),
                                 certified_frac=round(np.isfinite(stop).mean(), 3)))
    return rows


def write(rows, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return path


def main():
    rng = np.random.default_rng(20261024)
    print(f"alpha = {ALPHA}, eps = {EPS}")
    print(f"success-run rule (zero failures): {np.log(ALPHA) / np.log(1 - EPS):.1f} coupons\n")

    a = part_a(rng)
    print("Part A: false certification rate when the setting is bad (must be <= alpha)")
    for r in a:
        flag = "" if r["false_cert_rate"] <= ALPHA + 2 * r["se"] else "  <-- VIOLATION"
        print(f"  p={r['p']:.3f} {r['strategy']:8s} prior={r['prior']:6s} "
              f"rate={r['false_cert_rate']:.4f} (se {r['se']:.4f}){flag}")
    print("  ->", write(a, "exp01_validity.csv"))

    b = part_b(rng)
    print("\nPart B: median coupons to certify a good setting")
    for r in b:
        print(f"  p={r['p']:.3f} {r['strategy']:8s} prior={r['prior']:11s} "
              f"median={r['median_coupons']:7.1f}  certified={r['certified_frac']:.3f}")
    print("  ->", write(b, "exp01_power.csv"))


if __name__ == "__main__":
    main()
