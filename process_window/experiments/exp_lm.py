"""Language-model application: certify safe (temperature, top-p) settings.

Uses the measured failure-rate surface (pwcert/lm_scenario.py). Three parts:

1. fixed budget: certified fraction of the true safe region vs generations,
   for ours (cone rule + edge allocation, pilot-study simulator, pilot cost
   counted), ours without a simulator, the same tests without the ordering,
   a full-grid evaluation with exact binomial bounds and Bonferroni,
   and a full grid with fixed-sequence testing along each row (the
   Learn-then-Test approach for monotone risks); both are non-adaptive:
   every setting gets the same number of generations;
2. fixed confidence: SearchCertifier vs a per-setting two-sided test, with
   lower bounds;
3. the GP level-set baseline's error rate on this surface, plain and with
   the monotone closure ("gpmono"), and with BEAM-style active search
   ("gpbeam") or safe expansion with the closure ("gpsafe") as sampling rule;
4. "check": how far the raw measured rates are from the monotone fit used
   as ground truth (Assumption A on real generations).

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
from exp_search import PerSetting  # noqa: E402
from pwcert.baselines import grid_doe, grid_fst  # noqa: E402
from pwcert.bounds import ordered_lower_bound, unordered_lower_bound  # noqa: E402
from pwcert.cone import ConeCertifier  # noqa: E402
from pwcert.gp_baseline import GPLevelSet  # noqa: E402
from pwcert.lm_scenario import LM_DIRECTIONS, NLL_THRESH, PATH, REP_THRESH, load_scores, make_lm_scenario  # noqa: E402
from pwcert.search import SearchCertifier  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "lm")
EPS, Q = 0.10, 0.5
# Set from the command line: which measured surface, how sparse the pilot,
# and a suffix for output files (empty for the 12 x 12 surface).
PILOT_KW, FLAT_KW, SUFFIX = {}, {}, ""


def write(rows, name):
    if SUFFIX:
        name = name.replace(".csv", f"{SUFFIX}.csv")
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("->", name, flush=True)


def fixed_budget(reps, budget):
    pilot = make_lm_scenario(EPS, "pilot", **PILOT_KW)
    flat = make_lm_scenario(EPS, "none", **FLAT_KW)
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
        for name, fn in (("full grid (Bonferroni)", grid_doe), ("full grid (fixed sequence)", grid_fst)):
            a = np.mean([fn(pilot, int(n_per), 0.05, rng=np.random.default_rng(s))[0].sum()
                         for s in range(5)]) / W.sum() if n_per >= 1 else 0.0
            rows.append(dict(method=name, generations=int(cp), frac=round(a, 4), runs_with_errors=0))
    write(rows, "lm_fixed_budget.csv")


def monotone_check(pilot_n=16):
    """Raw rates (the generations after the pilot) vs the monotone fit.
    Per setting: an exact two-sided binomial test of the raw count against
    the fitted rate (standard errors are meaningless at rates near 0); we
    count settings with p < 0.01 (about 1% expected from noise alone) and
    report the largest absolute gap. A neighbouring pair is reversed if the
    raw rate rises by more than two standard errors of the difference when
    moving one step safer (about 2% expected between equal rates)."""
    from scipy.stats import binom
    sc = make_lm_scenario(EPS, "none", pilot_n=pilot_n, **FLAT_KW)
    _, _, scores = load_scores(FLAT_KW.get("path", PATH))
    nT, nP = sc.truth["degenerate"].shape
    rows = []
    for m, k, thr in (("degenerate", 0, REP_THRESH), ("incoherent", 1, NLL_THRESH)):
        fails = [[scores[i][j][k][pilot_n:] > thr for j in range(nP)] for i in range(nT)]
        N = np.array([[len(f) for f in r] for r in fails], float)
        raw = np.array([[f.mean() for f in r] for r in fails])
        fit = sc.truth[m]
        k = np.rint(raw * N)
        pval = np.minimum(1.0, 2 * np.minimum(binom.cdf(k, N, fit), binom.sf(k - 1, N, fit)))
        gap = np.abs(raw - fit)
        i, j = np.unravel_index(np.argmax(gap), gap.shape)
        d = LM_DIRECTIONS[m]
        pairs = reversed_ = 0
        for ax in (0, 1):
            if ax == 0:
                a, b, na, nb = raw[:-1], raw[1:], N[:-1], N[1:]
            else:
                a, b, na, nb = raw[:, :-1], raw[:, 1:], N[:, :-1], N[:, 1:]
            se = np.sqrt(a * (1 - a) / na + b * (1 - b) / nb)
            rise = (b - a) * d[ax]          # > 0: riskier after a step toward safer
            pairs += a.size
            reversed_ += int((rise > 2 * se + 1e-12).sum())
        rows.append(dict(mode=m, settings=raw.size, outside_99=int((pval < 0.01).sum()),
                         max_gap=round(float(gap.max()), 4), at_raw=f"{int(k[i, j])}/{int(N[i, j])}",
                         at_fit=round(float(fit[i, j]), 4), pairs=pairs, reversed_2se=reversed_))
        print(rows[-1], flush=True)
    write(rows, "lm_monotone_check.csv")


def cost_to_fraction(reps, frac=0.5, budget=40_000):
    """Table 1's LM row: generations to certify `frac` of the safe region.
    Adaptive methods: median over runs of the first crossing (pilot counted
    where used). Full grids: smallest per-setting budget whose mean certified
    area reaches the target, on the same geometric grid as final.py."""
    pilot = make_lm_scenario(EPS, "pilot", **PILOT_KW)
    n = pilot.truth["degenerate"].shape[0]
    W = pilot.true_window()
    target = int(np.ceil(frac * W.sum()))
    rows = []
    flat = make_lm_scenario(EPS, "none", **FLAT_KW)
    variants = (("ours", pilot, "cone", "ensemble"), ("no ordering", pilot, "none", "uniform"),
                ("ours, no simulator", flat, "cone", "uniform"), ("no ordering, no simulator", flat, "none", "uniform"))
    for name, sc, rule, wts in variants:
        costs = []
        for r in range(reps):
            c = ConeCertifier(sc, rule=rule, weights=wts, alloc="edge", target_q=0.7, batch=2 * n,
                              coupons0=sc.meta.get("pilot_coupons", 0), rng=np.random.default_rng(r))
            hist = c.run(budget)
            costs.append(next((h["coupons"] for h in hist if h["area"] >= target), np.inf))
        rows.append(dict(method=name, frac=frac, median=float(np.median(costs)),
                         costs=";".join(f"{x:.0f}" for x in costs)))
        print(rows[-1], flush=True)
    for name, fn in (("grid FST", grid_fst), ("grid Bonferroni", grid_doe)):
        cost = np.inf
        for n_per in np.unique(np.geomspace(20, 5000, 60).astype(int)):
            a = np.mean([fn(pilot, int(n_per), 0.05, rng=np.random.default_rng(s))[0].sum() for s in range(3)])
            if a >= target:
                cost = float(n_per * W.size)
                break
        rows.append(dict(method=name, frac=frac, median=cost, costs=f"{cost:.0f}"))
        print(rows[-1], flush=True)
    write(rows, f"lm_cost_{int(100 * frac)}.csv")


def fixed_confidence(reps):
    sc = make_lm_scenario(EPS, "pilot", **PILOT_KW)
    n = sc.truth["degenerate"].shape[0]
    T = np.all([sc.truth[m] <= Q * sc.eps[m] for m in sc.modes], axis=0)
    b = ordered_lower_bound(sc, Q)
    row = dict(target_size=int(T.sum()), LB_target=round(b["lb_target_only"]), LB_ordered=round(b["lb"]),
               LB_unordered=round(unordered_lower_bound(sc, Q)))
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


def gp(reps, budget, monotone=False, acquisition="straddle", lengthscales=(0.1, 0.2, 0.3)):
    sc = make_lm_scenario(EPS, "pilot", **PILOT_KW)
    W = sc.true_window()
    rows = []
    for beta in (2.0, 3.0, 4.0):
        for ls in lengthscales:
            errs, areas = 0, []
            for r in range(reps):
                g = GPLevelSet(sc, beta=beta, lengthscale=ls, batch=24, rng=np.random.default_rng(r),
                               monotone=monotone, acquisition=acquisition)
                h = g.run(budget)
                errs += int(max(x["errors"] for x in h) > 0)
                areas.append(h[-1]["area"] - h[-1]["errors"])
            rows.append(dict(beta=beta, lengthscale=ls, runs=reps, fwer=round(errs / reps, 3),
                             correct_frac=round(float(np.mean(areas)) / W.sum(), 3)))
            print(rows[-1], flush=True)
    if acquisition == "straddle":
        write(rows, "lm_gp_monotone.csv" if monotone else "lm_gp.csv")
    else:
        write(rows, f"lm_gp_{acquisition}{'_monotone' if monotone else ''}.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--budget", type=int, default=40_000)
    ap.add_argument("--parts", default="budget,confidence,gp")
    ap.add_argument("--surface", default=None, help="measured surface .npz (default: the 12 x 12 one)")
    ap.add_argument("--pilot-stride", type=int, default=1)
    args = ap.parse_args()
    global SUFFIX
    if args.surface:
        PILOT_KW.update(path=args.surface)
        FLAT_KW.update(path=args.surface)
        SUFFIX = "_" + os.path.splitext(os.path.basename(args.surface))[0].replace("surface_scores", "").strip("_")
    if args.pilot_stride > 1:
        PILOT_KW.update(pilot_stride=args.pilot_stride)
    os.makedirs(OUT, exist_ok=True)
    if "budget" in args.parts:
        fixed_budget(args.reps, args.budget)
    if "confidence" in args.parts:
        fixed_confidence(args.reps)
    if "gp" in args.parts.split(","):
        gp(max(args.reps, 20), args.budget // 2)
    if "gpmono" in args.parts:
        gp(max(args.reps, 20), args.budget // 2, monotone=True)
    if "gpbeam" in args.parts:
        gp(max(args.reps, 20), args.budget // 2, acquisition="active_search")
    if "gpsafe" in args.parts:
        gp(max(args.reps, 20), args.budget // 2, monotone=True, acquisition="safe_expand",
           lengthscales=(0.1, 0.2, 0.3, 0.5))
    if "check" in args.parts:
        monotone_check()
    if "cost" in args.parts:
        for frac in (0.5, 0.7):
            cost_to_fraction(max(args.reps, 5), frac, args.budget)


if __name__ == "__main__":
    main()
