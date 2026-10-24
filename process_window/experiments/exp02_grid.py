"""Experiment 2: the full grid certifier.

Part A (validity, worst case): every setting has defect rate exactly eps in
every mode. This is monotone (constant), and every setting is unsafe by the
"p >= eps" definition, so ANY certification is an error. The fraction of runs
with at least one certified setting estimates the family-wise error rate and
must be at most alpha.

Part B (efficiency): certified window area vs coupons used, averaged over
repetitions, for the method and its ablations, on 12x12 and 24x24 grids.

Run from process_window/:  python3 experiments/exp02_grid.py [--quick]
"""

import argparse
import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.certify import WindowCertifier  # noqa: E402
from pwcert.synthetic import MODES, Scenario, make_scenario  # noqa: E402

ALPHA = 0.05
OUT = os.path.join(os.path.dirname(__file__), "..", "results")

CONFIGS = {
    # name: (structure, simulator, start)
    "monotone + good sim": ("monotone", "good", "sim"),
    "monotone + biased sim": ("monotone", "biased", "sim"),
    "monotone + adversarial sim": ("monotone", "adversarial", "sim"),
    "monotone + pilot (no sim)": ("monotone", "none", "pilot"),
    "unstructured + good sim": ("none", "good", "sim"),
}


def null_scenario(n, eps=0.05, sim="adversarial"):
    base = make_scenario(n, n, eps=eps, simulator=sim)
    truth = {m: np.full((n, n), eps) for m in MODES}
    return Scenario(base.power, base.speed, base.eps, truth, base.sim, name="null")


def part_a(reps, n=12):
    rows = []
    for name, (structure, sim, start) in CONFIGS.items():
        sc = null_scenario(n, sim="adversarial" if sim == "none" else sim)
        any_err = 0
        for r in range(reps):
            wc = WindowCertifier(sc, alpha=ALPHA, structure=structure, start=start,
                                 rng=np.random.default_rng(10_000 + r))
            wc.run(budget=8000)
            any_err += int(wc.certified.any())
        rate = any_err / reps
        rows.append(dict(config=name, reps=reps, fwer=round(rate, 4),
                         se=round(np.sqrt(rate * (1 - rate) / reps), 4)))
        print(f"  {name:28s} FWER={rate:.4f} over {reps} runs", flush=True)
    return rows


def part_b(reps, n, budget, checkpoints):
    rows = []
    true_area = None
    for name, (structure, sim, start) in CONFIGS.items():
        sc = make_scenario(n, n, simulator=sim)
        true_area = int(sc.true_window().sum())
        curves = np.zeros((reps, len(checkpoints)))
        errs = 0
        t0 = time.time()
        for r in range(reps):
            wc = WindowCertifier(sc, alpha=ALPHA, structure=structure, start=start,
                                 rng=np.random.default_rng(r))
            hist = wc.run(budget)
            c = np.array([h["coupons"] for h in hist])
            a = np.array([h["area"] for h in hist])
            errs += int(max(h["errors"] for h in hist) > 0)
            for k, cp in enumerate(checkpoints):
                idx = np.searchsorted(c, cp, side="right") - 1
                curves[r, k] = a[idx] if idx >= 0 else 0
        mean = curves.mean(axis=0)
        for cp, m_ in zip(checkpoints, mean):
            rows.append(dict(grid=n, config=name, coupons=cp, mean_area=round(m_, 2),
                             true_area=true_area))
        print(f"  {n}x{n} {name:28s} area@{checkpoints[-1]}={mean[-1]:6.1f}/{true_area}"
              f"  runs with errors={errs}/{reps}  ({time.time() - t0:.0f}s)", flush=True)
    return rows


def write(rows, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return path


def plot(rows, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    grids = sorted({r["grid"] for r in rows})
    fig, axes = plt.subplots(1, len(grids), figsize=(6 * len(grids), 4.2), squeeze=False)
    for ax, n in zip(axes[0], grids):
        sub = [r for r in rows if r["grid"] == n]
        for name in CONFIGS:
            pts = [r for r in sub if r["config"] == name]
            ax.plot([p["coupons"] for p in pts],
                    [p["mean_area"] / p["true_area"] for p in pts], label=name)
        ax.set_title(f"{n}x{n} grid (true window = {sub[0]['true_area']} settings)")
        ax.set_xlabel("coupons built")
        ax.set_ylabel("fraction of true window certified")
        ax.set_ylim(0, 1)
        ax.grid(alpha=0.3)
    axes[0][0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=130)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="few reps, for a smoke test")
    args = ap.parse_args()
    reps_a, reps_b = (20, 3) if args.quick else (200, 20)

    print(f"Part A: worst-case validity (all settings at threshold), alpha={ALPHA}")
    a = part_a(reps_a)
    print("  ->", write(a, "exp02_validity.csv"))

    print("\nPart B: certified area vs coupons")
    b = part_b(reps_b, 12, 15000, list(range(1000, 15001, 1000)))
    b += part_b(reps_b, 24, 40000, list(range(2000, 40001, 2000)))
    print("  ->", write(b, "exp02_area.csv"))
    png = os.path.join(OUT, "exp02_area.png")
    plot(b, png)
    print("  ->", png)


if __name__ == "__main__":
    main()
