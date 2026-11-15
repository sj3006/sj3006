"""Print the Table 1 and Table 2 rows (main.tex) for one measured language
model, from the result files exp_lm.py writes.

    python3 scripts/lm_table_rows.py                 # SmolLM2-135M, 12x12
    python3 scripts/lm_table_rows.py --suffix _23    # SmolLM2-135M, 23x23
    python3 scripts/lm_table_rows.py --suffix _qwen15b --label "Qwen 1.5B"

Also prints the numbers the text quotes: safe-region size, monotone check,
the 70% costs, and the GP baseline summary.
"""

import argparse
import csv
import os

import numpy as np

LM = os.path.join(os.path.dirname(__file__), "..", "results", "lm")


def k(x):
    return f"{float(x) / 1000:.1f}k"


def read(name):
    p = os.path.join(LM, name)
    if not os.path.exists(p):
        return None
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default="", help="e.g. _23, _qwen05b, _qwen15b")
    ap.add_argument("--label", default="LM")
    ap.add_argument("--grid", default=None, help="grid label, default from the suffix")
    a = ap.parse_args()
    s = a.suffix
    grid = a.grid or ("$23^2$" if s.endswith("_23") else "$12^2$")

    for frac in ("50", "70"):
        rows = read(f"lm_cost_{frac}{s}.csv")
        if rows is None:
            print(f"(no lm_cost_{frac}{s}.csv)")
            continue
        m = {r["method"]: r["median"] for r in rows}
        cols = [m.get(x) for x in ("ours", "no ordering", "grid FST", "grid Bonferroni")]
        line = " & ".join(k(c) if c else "--" for c in cols)
        ratio = float(m["no ordering"]) / float(m["ours"])
        fst = float(m["grid FST"]) / float(m["ours"]) if m.get("grid FST") else float("nan")
        tag = "Table 1" if frac == "50" else "70%"
        print(f"{tag}: {a.label:<9} & {grid} & {line} \\\\   "
              f"(no ordering / ours = {ratio:.2f}x, grid FST / ours = {fst:.2f}x)")

    fc = read(f"lm_fixed_confidence{s}.csv")
    if fc:
        r = fc[0]
        ratio = float(r["search"]) / float(r["LB_ordered"])
        print(f"Table 2: {a.label} {grid} & {k(r['search'])} & {k(r['LB_ordered'])} & {ratio:.1f} & "
              f"{k(r['per-setting'])} & {k(r['LB_unordered'])} \\\\   "
              f"(target {r['target_size']}, search complete {r['search_complete']}, unsafe {r['search_unsafe']}; "
              f"per-setting / search = {float(r['per-setting']) / float(r['search']):.2f}x)")

    mc = read(f"lm_monotone_check{s}.csv")
    if mc:
        print("Monotone check:", "; ".join(f"{kk}={v}" for kk, v in mc[0].items()))

    surf = "surface_scores.npz" if s in ("", "_23") else f"surface_scores{s}.npz"
    path = os.path.join(LM, surf)
    if os.path.exists(path):
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from pwcert.lm_scenario import make_lm_scenario
        sc = make_lm_scenario(path=path)
        if s == "_23":
            print("(safe-region size below is for the 12x12 file; the 23x23 count is in the exp_lm log)")
        w = sc.true_window()
        print(f"Safe region: {int(w.sum())} of {w.size} settings")

    gp = read(f"lm_gp{s}.csv")
    if gp:
        print("GP baseline rows:")
        for r in gp:
            print("  " + ", ".join(f"{kk}={v}" for kk, v in r.items()))


if __name__ == "__main__":
    main()
