"""Summarise `_study.json` into the numbers the paper reports.

Run after `study.py`. Prints a table per family and the tests behind the main
claims, and writes `_results.json` for the figures and the claims registry.

The questions, in order:

1. Does prediction fidelity predict diagnostic fidelity? Rank correlation of
   `pred_rms` with `delta_max` across the sampled twins, and the same within the
   validation-equivalent set alone.
2. Does validation screen out twins that are bad for diagnosis? Compare the
   directional error of twins the data accept with twins the data reject.
3. How many validation-equivalent twins exceed the directional budget, and what
   does that cost the certificate's coverage and the reported verdicts?
4. Do the controls behave as the theory says: the geometry-preheat constant
   (Theorem 1, no effect) and the diagnosis-only families (no prediction
   error at all)?
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import mannwhitneyu, spearmanr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import theory as th                                               # noqa: E402

STUDY = HERE / "_study.json"
OUT = HERE / "_results.json"
FAMILY_ORDER = ["validation-equivalent", "region-rejected", "structural",
                "prediction only", "one parameter", "operating point",
                "numerical resolution", "couplings", "couplings control",
                "noise model", "noise level", "missing channel",
                "spurious channel"]
FAULTS = ["power", "speed", "layer", "gas", "geometry"]


def budget(rho: float = 28.0, S: int = 3) -> float:
    return float(th.delta_max(rho, S))


def _q(x, p):
    x = np.asarray([v for v in x if np.isfinite(v)], float)
    return float(np.quantile(x, p)) if len(x) else float("nan")


def family_table(rows: list[dict]) -> list[dict]:
    out = []
    b = budget()
    for fam in FAMILY_ORDER:
        R = [r for r in rows if r["family"] == fam]
        if not R:
            continue
        dm = [r["delta_max"] for r in R]
        out.append({
            "family": fam, "n": len(R),
            "pred_rms_median": _q([r["pred_rms"] for r in R], 0.5),
            "pred_rms_max": max(r["pred_rms"] for r in R),
            "amb_mape_median": _q([r["amb_mape"] for r in R], 0.5),
            "delta_max_median": _q(dm, 0.5),
            "delta_max_max": max(dm),
            "frac_over_budget": float(np.mean([d > b for d in dm])),
            "cov_inst_min28_median": _q([r["cov_inst_min28"] for r in R], 0.5),
            "cov_inst_min28_min": min(r["cov_inst_min28"] for r in R),
            "cov_big_min28_median": _q([r["cov_big_min28"] for r in R], 0.5),
            "flips_inst_any": float(np.mean([r["flips_inst"] > 0 for r in R])),
            "flips_big_any": float(np.mean([r["flips_big"] > 0 for r in R])),
            "flips_inst_max": max(r["flips_inst"] for r in R),
            "flips_big_max": max(r["flips_big"] for r in R),
        })
    return out


def tests(rows: list[dict]) -> dict:
    acc = [r for r in rows if r["family"] == "validation-equivalent"]
    rej = [r for r in rows if r["family"] == "region-rejected"]
    sampled = acc + rej
    res = {}
    for nm, R in (("sampled", sampled), ("accepted", acc)):
        x = [r["pred_rms"] for r in R]
        y = [r["delta_max"] for r in R]
        rho, p = spearmanr(x, y)
        res[f"spearman_pred_vs_delta_{nm}"] = {"rho": float(rho), "p": float(p),
                                               "n": len(R)}
        x2 = [r["amb_mape"] for r in R]
        rho2, p2 = spearmanr(x2, y)
        res[f"spearman_amb_vs_delta_{nm}"] = {"rho": float(rho2), "p": float(p2)}
    if acc and rej:
        u = mannwhitneyu([r["delta_max"] for r in acc],
                         [r["delta_max"] for r in rej], alternative="less")
        res["mannwhitney_accepted_less_than_rejected"] = {
            "U": float(u.statistic), "p": float(u.pvalue)}
    # which fault carries the largest error, among accepted twins
    if acc:
        arg = [int(np.argmax(r["delta"])) for r in acc]
        res["worst_fault_counts_accepted"] = {FAULTS[k]: arg.count(k)
                                              for k in range(5)}
        D = np.array([r["delta"] for r in acc])
        res["delta_by_fault_accepted_median"] = dict(zip(FAULTS, np.median(D, 0).tolist()))
        res["delta_by_fault_accepted_max"] = dict(zip(FAULTS, D.max(0).tolist()))
    res["budget_deg_rho28_S3"] = budget()
    res["budget_deg_rho28_S15"] = budget(28.0, 15)
    return res


def controls(rows: list[dict]) -> dict:
    out = {}
    cc = [r for r in rows if r["family"] == "couplings control"]
    out["geometry_preheat_delta_max"] = max((r["delta_max"] for r in cc), default=None)
    out["geometry_preheat_flips"] = sum(r["flips_inst"] + r["flips_big"] for r in cc)
    diag_only = [r for r in rows if r["family"] in
                 ("couplings", "couplings control", "noise model", "noise level",
                 "numerical resolution",
                  "missing channel", "spurious channel")]
    out["diagnosis_only_pred_rms_max"] = max((r["pred_rms"] for r in diag_only),
                                             default=None)
    return out


def spread(rows: list[dict]) -> dict:
    """Disagreement among the accepted twins themselves, no truth designated.

    If the process were any one of the twins the data accept, the others are
    what a practitioner might have deployed instead. The pairwise directional
    disagreement is therefore the error validation leaves open, whichever
    member is closest to reality.
    """
    import study as st_mod
    import twins as tw_mod
    sc = st_mod.Scorer()
    acc = [r for r in rows if r["family"] == "validation-equivalent"]
    sig = np.asarray(tw_mod.REFERENCE.sigmas, float)
    U = []
    for r in acc:
        t = r["twin"]
        tw = tw_mod.REFERENCE.but("x", absorptivity=t["absorptivity"], k=t["k"],
                                  cp=t["cp"], keyhole_c=t["keyhole_c"])
        J = sc.J(tw) / sig[:, None]
        U.append(J / np.linalg.norm(J, axis=0))
    U = np.array(U)
    n = len(U)
    D = np.zeros((n, n))
    for i in range(n):
        c = np.abs(np.einsum("sk,jsk->jk", U[i], U)).clip(0, 1)
        D[i] = np.degrees(np.arccos(c)).max(1)
    iu = np.triu_indices(n, 1)
    pairs = D[iu]
    b = budget()
    per_twin_median = np.nanmedian(np.where(np.eye(n, dtype=bool), np.nan, D), axis=1)
    return {"n_twins": n, "n_pairs": int(len(pairs)),
            "pair_delta_max_median": float(np.median(pairs)),
            "pair_delta_max_q10": float(np.quantile(pairs, 0.10)),
            "pair_delta_max_q90": float(np.quantile(pairs, 0.90)),
            "pair_frac_over_budget": float(np.mean(pairs > b)),
            "best_center_median": float(per_twin_median.min()),
            "worst_center_median": float(per_twin_median.max())}


def tolerances(rows: list[dict]) -> dict:
    """Parameter accuracy that keeps every fault inside the budget.

    From the one-parameter and operating-point families: for each parameter
    and sign, the largest offset tried whose largest directional error is
    within budget, and the error per percent at the smallest offset.
    """
    b = budget()
    out = {}
    R = [r for r in rows if r["family"] in ("one parameter", "operating point")]
    groups: dict[str, list] = {}
    for r in R:
        label, scale = r["name"].rsplit(" x", 1)
        groups.setdefault(label, []).append((float(scale), r["delta_max"], r["pred_rms"]))
    for label, g in groups.items():
        g.sort()
        ok = [abs(s - 1) for s, d, _ in g if d <= b]
        bad = [abs(s - 1) for s, d, _ in g if d > b]
        smallest = min(g, key=lambda x: abs(x[0] - 1))
        out[label] = {"offsets": [(round(100 * (s - 1), 1), round(d, 3), round(p, 3))
                                  for s, d, p in g],
                      "largest_ok_pct": 100 * max(ok) if ok else 0.0,
                      "smallest_bad_pct": 100 * min(bad) if bad else None,
                      "deg_per_pct_at_smallest": smallest[1] / (100 * abs(smallest[0] - 1))}
    return out


def main() -> dict:
    data = json.loads(STUDY.read_text())
    rows = data["rows"]
    table = family_table(rows)
    t = tests(rows)
    c = controls(rows)
    sp = spread(rows)
    tol = tolerances(rows)
    res = {"table": table, "tests": t, "controls": c, "spread": sp,
           "tolerances": tol, "gain": data["gain"],
           "region": data["region"], "n_region_accepted": data["n_region_accepted"],
           "n_region": data["n_region"]}
    OUT.write_text(json.dumps(res, indent=1))

    print(f"budget at rho 28: {t['budget_deg_rho28_S3']:.2f} deg instantaneous, "
          f"{t['budget_deg_rho28_S15']:.2f} deg build context (equal rho)")
    print(f"build-context gains: {np.round(data['gain'], 2).tolist()}\n")
    hdr = (f"{'family':24s}{'n':>4s}{'pred%':>8s}{'predmax':>8s}{'dmed':>7s}"
           f"{'dmax':>7s}{'>bud':>6s}{'cov28':>7s}{'covmin':>7s}{'covB':>7s}"
           f"{'flipI':>6s}{'flipB':>6s}")
    print(hdr)
    for r in table:
        print(f"{r['family']:24s}{r['n']:4d}{r['pred_rms_median']:8.2f}"
              f"{r['pred_rms_max']:8.2f}{r['delta_max_median']:7.2f}"
              f"{r['delta_max_max']:7.2f}{r['frac_over_budget']:6.2f}"
              f"{r['cov_inst_min28_median']:7.3f}{r['cov_inst_min28_min']:7.3f}"
              f"{r['cov_big_min28_median']:7.3f}{r['flips_inst_any']:6.2f}"
              f"{r['flips_big_any']:6.2f}")
    print()
    for k, v in t.items():
        print(f"{k}: {v}")
    print()
    for k, v in c.items():
        print(f"{k}: {v}")
    print("\nspread among accepted twins, no truth designated")
    for k, v in sp.items():
        print(f"   {k}: {v}")
    print("\ntolerances (offset %, largest direction error deg, prediction RMS %)")
    for k, v in tol.items():
        print(f"   {k:14s} ok to {v['largest_ok_pct']:4.1f} %   "
              f"{v['deg_per_pct_at_smallest']:.2f} deg per %   {v['offsets']}")
    return res


if __name__ == "__main__":
    main()
