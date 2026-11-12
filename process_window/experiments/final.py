"""Consolidated benchmark for the paper. Each experiment is a subcommand that
writes CSVs to results/final/; `plot` turns whatever CSVs exist into figures.

    python3 experiments/final.py validity  [--reps 400]
    python3 experiments/final.py curves --scen toy-good [--reps 8] [--n 24]
    python3 experiments/final.py scaling --scen toy-good [--reps 5]
    python3 experiments/final.py bounds [--reps 3]
    python3 experiments/final.py ablation --scen toy-good [--reps 8]
    python3 experiments/final.py gp --n 16 [--reps 40]
    python3 experiments/final.py plot

Methods (all adaptive ones share allocation, re-check and futility code):
- ours: cone rule, ensemble weights, frontier allocation with optimism,
  simulator prior.
- ours, no simulator: the same after a pilot plate (pilot.py) learns a
  simulator; pilot coupons are counted.
- unstructured: per-setting betting tests with Bonferroni weights, no
  ordering, same allocation and simulator prior.
- unstructured, no simulator: the same with a flat prior.
- grid DoE: current practice, equal coupons everywhere, Clopper-Pearson +
  Bonferroni.
"""

import argparse
import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.baselines import grid_doe  # noqa: E402
from pwcert.cone import ConeCertifier, cone_sum  # noqa: E402
from pwcert.dose import make_dose_scenario  # noqa: E402
from pwcert.physics import make_physics_scenario  # noqa: E402
from pwcert.pilot import pilot_simulator  # noqa: E402
from pwcert.synthetic import Scenario, make_scenario  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "final")
ALPHA = 0.05

SCENARIOS = {
    "toy-good": lambda n, s="good": make_scenario(n, n, simulator=s),
    "toy-optimistic": lambda n, s="biased": make_scenario(n, n, simulator=s),
    "lpbf-good": lambda n, s="good": make_physics_scenario(n, n, simulator=s),
    "lpbf-optimistic": lambda n, s="biased": make_physics_scenario(n, n, simulator=s),
    "dose-bliss": lambda n, s="bliss": make_dose_scenario(n, n, simulator=s),
}
LABELS = {
    "toy-good": "Toy LPBF window, good simulator",
    "toy-optimistic": "Toy LPBF window, optimistic simulator",
    "lpbf-good": "Rosenthal 316L model, good simulator",
    "lpbf-optimistic": "Rosenthal 316L model, optimistic simulator",
    "dose-bliss": "Two-drug screen, Bliss simulator",
}
METHODS = ["ours", "ours, no simulator", "unstructured", "unstructured, no simulator"]


def build(method, scen, n, rng, **over):
    """Return (certifier, scenario) for one run."""
    mk = SCENARIOS[scen]
    base = dict(alloc="frontier", target_q=1.0, batch=2 * n, rng=rng)
    base.update(over)
    if method == "ours":
        sc = mk(n)
        return ConeCertifier(sc, rule="cone", weights="ensemble", **base), sc
    if method == "ours, no simulator":
        sc, pc = pilot_simulator(mk(n, "none"), rng, per_point=4, stride=2)
        return ConeCertifier(sc, rule="cone", weights="ensemble", prior_weight=4.0,
                             coupons0=pc, **base), sc
    if method == "unstructured":
        sc = mk(n)
        return ConeCertifier(sc, rule="none", weights="uniform", **base), sc
    if method == "unstructured, no simulator":
        sc = mk(n, "none")
        return ConeCertifier(sc, rule="none", weights="uniform", **base), sc
    raise ValueError(method)


def write(rows, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("->", path, flush=True)


def doe_area(sc, n_per, reps, seed=0):
    return float(np.mean([grid_doe(sc, int(n_per), ALPHA, rng=np.random.default_rng(seed + r))[0].sum()
                          for r in range(reps)]))


# -- 1. validity ----------------------------------------------------------------

def cmd_validity(args):
    rows = []
    for grid in ("toy", "dose"):
        for sim in ("good", "adversarial"):
            if grid == "toy":
                base = make_scenario(8, 8, simulator=sim)
                eps_ = base.eps
            else:
                base = make_dose_scenario(8, 8, simulator="good" if sim == "good" else "adversarial")
                eps_ = base.eps
            truth = {m: np.full((8, 8), eps_[m]) for m in base.modes}   # every setting at threshold
            sc = Scenario(base.power, base.speed, base.eps, truth, base.sim,
                          directions=base.directions)
            for rule, weights in (("cone", "ensemble"), ("max", "ensemble"), ("none", "uniform")):
                t0, any_err = time.time(), 0
                for r in range(args.reps):
                    c = ConeCertifier(sc, rule=rule, weights=weights, alloc="frontier", target_q=1.0,
                                      batch=16, rng=np.random.default_rng(100_000 + r))
                    c.run(4000)
                    any_err += int(c.certified.any())
                rate = any_err / args.reps
                rows.append(dict(grid=grid, simulator=sim, rule=rule, runs=args.reps,
                                 fwer=round(rate, 4), se=round(np.sqrt(rate * (1 - rate) / args.reps), 4)))
                print(rows[-1], f"({time.time() - t0:.0f}s)", flush=True)
    write(rows, "validity.csv")


# -- 2. certified area vs coupons --------------------------------------------------

def cmd_curves(args):
    n, scen = args.n, args.scen
    budget = args.budget or 200 * n * n
    checkpoints = np.linspace(0, budget, 41)[1:]
    rows = []
    for method in METHODS:
        t0 = time.time()
        frac = np.zeros((args.reps, len(checkpoints)))
        errors = 0
        for r in range(args.reps):
            c, sc = build(method, scen, n, np.random.default_rng(r))
            A = sc.true_window().sum()
            hist = c.run(budget)
            cs = np.array([h["coupons"] for h in hist])
            ar = np.array([h["area"] for h in hist])
            errors += int(max(h["errors"] for h in hist) > 0)
            for k, cp in enumerate(checkpoints):
                i = np.searchsorted(cs, cp, side="right") - 1
                frac[r, k] = ar[i] / A if i >= 0 else 0.0
        for cp, m_, s_ in zip(checkpoints, frac.mean(0), frac.std(0) / np.sqrt(args.reps)):
            rows.append(dict(scen=scen, n=n, method=method, coupons=int(cp), frac=round(m_, 4),
                             se=round(s_, 4), runs_with_errors=errors, reps=args.reps))
        print(f"{scen} {method:28s} final frac {frac.mean(0)[-1]:.3f}  errors {errors}/{args.reps}"
              f"  ({time.time() - t0:.0f}s)", flush=True)
    sc = SCENARIOS[scen](n)
    A = sc.true_window().sum()
    for cp in checkpoints:
        n_per = cp / (n * n)
        a = doe_area(sc, n_per, 5) / A if n_per >= 1 else 0.0
        rows.append(dict(scen=scen, n=n, method="grid DoE", coupons=int(cp), frac=round(a, 4),
                         se=0.0, runs_with_errors=0, reps=5))
    write(rows, f"curves_{scen}_{n}.csv")


# -- 3. scaling ----------------------------------------------------------------------

def cmd_scaling(args):
    sizes = [int(s) for s in args.sizes.split(",")]
    rows = []
    for n in sizes:
        sc = SCENARIOS[args.scen](n)
        A = sc.true_window().sum()
        target = int(np.ceil(args.frac * A))
        for method in ("ours", "unstructured"):
            t0, costs = time.time(), []
            for r in range(args.reps):
                c, _ = build(method, args.scen, n, np.random.default_rng(r))
                hist = c.run(300 * n * n)
                costs.append(next((h["coupons"] for h in hist if h["area"] >= target), np.inf))
            rows.append(dict(scen=args.scen, n=n, method=method, frac=args.frac,
                             median=float(np.median(costs)), costs=";".join(f"{x:.0f}" for x in costs)))
            print(rows[-1], f"({time.time() - t0:.0f}s)", flush=True)
        cost = np.inf
        for n_per in np.unique(np.geomspace(20, 5000, 60).astype(int)):
            if doe_area(sc, n_per, 3) >= target:
                cost = n_per * n * n
                break
        rows.append(dict(scen=args.scen, n=n, method="grid DoE", frac=args.frac, median=float(cost),
                         costs=f"{cost:.0f}"))
        print(rows[-1], flush=True)
        write(rows, f"scaling_{args.scen}.csv")


# -- 4. bounds next to practice -----------------------------------------------------

def lower_bounds(sc, q, beta=0.05):
    from scipy.optimize import linprog
    from pwcert.certify import _kl_vec
    modes = sc.modes
    M = len(modes)
    truth = np.stack([sc.truth[m] for m in modes])
    eps = np.array([sc.eps[m] for m in modes])[:, None, None]
    T = (truth <= q * eps).all(axis=0)
    k = _kl_vec(truth, eps)
    L = (1 - beta) * np.log(1 / ALPHA) - np.log(2)
    rows_A, edge_pts = [], set()
    nP, nV = T.shape
    for a, m in enumerate(modes):
        d = sc.directions[m]
        count = cone_sum(T.astype(float), d)
        edge = T & (count < 1.5)
        for z in zip(*np.nonzero(edge)):
            edge_pts.add(z)
            zmask = np.zeros(T.shape)
            zmask[z] = 1.0
            # settings y with z safer than or equal to y  <=>  z in y's safer cone
            in_cone = cone_sum(zmask, d, riskier=False) > 0.5     # y whose safer cone contains z
            D = in_cone & (truth[a] < eps[a])
            row = np.zeros((M, nP, nV))
            row[a] = np.where(D, k[a], 0.0)
            rows_A.append(row.sum(axis=0).ravel())                 # one coupon at y serves all modes
    A = np.array(rows_A)
    lp = linprog(np.ones(nP * nV), A_ub=-A, b_ub=-np.ones(len(A)), bounds=(0, None), method="highs")
    lb_a = L * lp.fun
    lb_u = L * float(np.sum(np.max(1.0 / np.maximum(k[:, T], 1e-12), axis=0)))
    return T, lb_a, lb_u, len(edge_pts)


def cmd_bounds(args):
    q = 0.5
    rows = []
    for n in [int(s) for s in args.sizes.split(",")]:
        sc = SCENARIOS["toy-good"](n)
        T, lb_a, lb_u, n_edge = lower_bounds(sc, q)
        res = dict(n=n, T_size=int(T.sum()), edge_points=n_edge, LB_ordered=round(lb_a),
                   LB_unordered=round(lb_u))
        for method, rule, weights in (("ours", "cone", "ensemble"), ("unstructured", "none", "uniform")):
            costs = []
            for r in range(args.reps):
                c = ConeCertifier(sc, rule=rule, weights=weights, alloc="edge", target_q=0.7,
                                  batch=2 * n, rng=np.random.default_rng(r))
                costs.append(c.run_until(T, 300 * n * n))
            res[method] = float(np.median(costs))
        rows.append(res)
        print(res, flush=True)
        write(rows, "bounds.csv")


# -- 5. ablations ------------------------------------------------------------------------

ABLATIONS = {
    "ours": {},
    "Bonferroni + spreading (max rule)": dict(rule="max"),
    "no ordering (unstructured)": dict(rule="none", weights="uniform"),
    "uniform weights": dict(weights="uniform"),
    "no optimism": dict(optimism=0.0),
    "no simulator prior in bets": dict(use_sim_prior=False),
    "fixed bet instead of hedge": dict(strategy="fixed"),
    "edge allocation": dict(alloc="edge", target_q=0.7),
}


def cmd_ablation(args):
    n = args.n
    rows = []
    for name, over in ABLATIONS.items():
        t0, costs = time.time(), []
        for r in range(args.reps):
            mk = SCENARIOS[args.scen]
            sc = mk(n)
            kw = dict(rule="cone", weights="ensemble", alloc="frontier", target_q=1.0, batch=2 * n,
                      rng=np.random.default_rng(r))
            kw.update(over)
            c = ConeCertifier(sc, **kw)
            A = sc.true_window().sum()
            hist = c.run(300 * n * n)
            costs.append(next((h["coupons"] for h in hist if h["area"] >= np.ceil(args.frac * A)), np.inf))
        rows.append(dict(scen=args.scen, n=n, variant=name, frac=args.frac,
                         median=float(np.median(costs)), costs=";".join(f"{x:.0f}" for x in costs)))
        print(rows[-1], f"({time.time() - t0:.0f}s)", flush=True)
    write(rows, f"ablation_{args.scen}_{n}.csv")


# -- 6. model-based baseline: GP level-set certification --------------------------------

def cmd_gp(args):
    """How often does a GP upper-confidence-bound certificate include an unsafe
    setting? Ours on the same scenario for comparison (same budget)."""
    from pwcert.gp_baseline import GPLevelSet
    n, budget = args.n, args.budget or 60 * args.n * args.n
    rows = []
    for scen in ("toy-good", "lpbf-good", "dose-bliss"):
        sc = SCENARIOS[scen](n)
        A = sc.true_window().sum()
        for beta in (2.0, 3.0, 4.0):
            for ls in (0.1, 0.2, 0.3):
                t0, errs, areas = time.time(), 0, []
                for r in range(args.reps):
                    g = GPLevelSet(sc, beta=beta, lengthscale=ls, batch=2 * n,
                                   rng=np.random.default_rng(r))
                    h = g.run(budget)
                    errs += int(max(x["errors"] for x in h) > 0)
                    areas.append(h[-1]["area"] - h[-1]["errors"])
                rows.append(dict(scen=scen, n=n, method="GP level set", beta=beta, lengthscale=ls,
                                 runs=args.reps, fwer=round(errs / args.reps, 3),
                                 correct_area_frac=round(float(np.mean(areas)) / A, 3)))
                print(rows[-1], f"({time.time() - t0:.0f}s)", flush=True)
        errs, areas = 0, []
        for r in range(args.reps):
            c, _ = build("ours", scen, n, np.random.default_rng(r))
            h = c.run(budget)
            errs += int(max(x["errors"] for x in h) > 0)
            areas.append(h[-1]["area"])
        rows.append(dict(scen=scen, n=n, method="ours", beta="", lengthscale="", runs=args.reps,
                         fwer=round(errs / args.reps, 3),
                         correct_area_frac=round(float(np.mean(areas)) / A, 3)))
        print(rows[-1], flush=True)
        write(rows, "gp_baseline.csv")


# -- plotting ----------------------------------------------------------------------------

# Reference categorical palette, fixed order (dataviz skill, palette.md).
SERIES = {"ours": "#2a78d6", "ours, no simulator": "#eb6834", "unstructured": "#1baf7a",
          "unstructured, no simulator": "#eda100", "grid DoE": "#e87ba4"}
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def _style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)
    ax.title.set_color(INK)


def _int_ticks(ax, ns):
    """Label a log x-axis with the actual grid sizes as plain integers."""
    from matplotlib.ticker import FixedLocator, NullLocator
    ax.xaxis.set_major_locator(FixedLocator(ns))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels([str(n) for n in ns])


def _read(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def cmd_plot(args):
    import glob

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "figure.facecolor": SURFACE})

    curves = sorted(glob.glob(os.path.join(OUT, "curves_*.csv")))
    if curves:
        k = len(curves)
        cols = min(3, k)
        rws = int(np.ceil(k / cols))
        fig, axes = plt.subplots(rws, cols, figsize=(4.6 * cols, 3.6 * rws), squeeze=False)
        for ax, path in zip(axes.ravel(), curves):
            rows = _read(path)
            for method in METHODS + ["grid DoE"]:
                pts = [r for r in rows if r["method"] == method]
                if not pts:
                    continue
                x = np.array([float(p["coupons"]) for p in pts]) / 1000
                y = np.array([float(p["frac"]) for p in pts])
                ax.plot(x, y, color=SERIES[method], lw=2, label=method,
                        ls="--" if "no simulator" in method else "-")
            _style(ax)
            ax.set_ylim(0, 1)
            ax.set_xlabel("coupons built (thousands)")
            ax.set_ylabel("fraction of true window certified")
            ax.set_title(LABELS.get(rows[0]["scen"], rows[0]["scen"]) + f", {rows[0]['n']}x{rows[0]['n']}",
                         fontsize=10)
        for ax in axes.ravel()[k:]:
            ax.axis("off")
        axes.ravel()[0].legend(fontsize=8, frameon=False, labelcolor=INK)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, "fig_curves.png"), dpi=150)
        print("-> fig_curves.png")

    scal = sorted(glob.glob(os.path.join(OUT, "scaling_*.csv")))
    if scal:
        fig, axes = plt.subplots(1, len(scal), figsize=(4.8 * len(scal), 3.8), squeeze=False)
        for ax, path in zip(axes.ravel(), scal):
            rows = _read(path)
            ns_all = sorted({int(r["n"]) for r in rows})
            for method in ("ours", "unstructured", "grid DoE"):
                pts = [r for r in rows if r["method"] == method and np.isfinite(float(r["median"]))]
                if pts:
                    ax.loglog([int(p["n"]) for p in pts], [float(p["median"]) for p in pts], "o-",
                              color=SERIES[method], lw=2, ms=5, label=method)
            ours = [r for r in rows if r["method"] == "ours" and np.isfinite(float(r["median"]))]
            if ours:
                n0, c0 = int(ours[0]["n"]), float(ours[0]["median"])
                ns = np.array(ns_all, float)
                ax.loglog(ns, c0 * ns / n0, ":", color=INK2, lw=1, label="slope 1 (boundary)")
                ax.loglog(ns, c0 * (ns / n0) ** 2, "--", color=INK2, lw=1, label="slope 2 (area)")
            _style(ax)
            _int_ticks(ax, ns_all)
            ax.set_xlabel("grid size n (n x n settings)")
            ax.set_ylabel(f"coupons to certify {int(float(rows[0]['frac']) * 100)}% of window")
            ax.set_title(LABELS.get(rows[0]["scen"], rows[0]["scen"]), fontsize=10)
        axes.ravel()[-1].legend(fontsize=8, frameon=False, labelcolor=INK, loc="upper left")
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, "fig_scaling.png"), dpi=150)
        print("-> fig_scaling.png")

    bpath = os.path.join(OUT, "bounds.csv")
    if os.path.exists(bpath):
        rows = _read(bpath)
        ns = [int(r["n"]) for r in rows]
        fig, ax = plt.subplots(figsize=(5.2, 3.8))
        spec = [("LB_ordered", "lower bound, with ordering", INK2, ":"),
                ("LB_unordered", "lower bound, without ordering", INK2, "--"),
                ("ours", "ours", SERIES["ours"], "-"),
                ("unstructured", "unstructured", SERIES["unstructured"], "-")]
        for key, lab, col, ls in spec:
            ys = [float(r[key]) for r in rows]
            ok = [i for i, y in enumerate(ys) if np.isfinite(y)]
            ax.loglog([ns[i] for i in ok], [ys[i] for i in ok], "o" + ls if ls != "-" else "o-",
                      color=col, lw=2 if ls == "-" else 1.2, ms=5, label=lab)
        _style(ax)
        _int_ticks(ax, ns)
        ax.set_xlabel("grid size n (n x n settings)")
        ax.set_ylabel("coupons to certify all rates <= eps/2")
        ax.legend(fontsize=8, frameon=False, labelcolor=INK)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT, "fig_bounds.png"), dpi=150)
        print("-> fig_bounds.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["validity", "curves", "scaling", "bounds", "ablation", "gp", "plot"])
    ap.add_argument("--scen", default="toy-good", choices=list(SCENARIOS))
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--budget", type=int, default=0)
    ap.add_argument("--sizes", default="8,12,16,24,32,48")
    ap.add_argument("--frac", type=float, default=0.5)
    args = ap.parse_args()
    globals()["cmd_" + args.cmd](args)


if __name__ == "__main__":
    main()
