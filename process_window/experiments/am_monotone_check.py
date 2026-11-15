"""Is Assumption A plausible for laser powder bed fusion? A check on
published 316L melt-pool measurements.

Data: the regression table of MeltpoolNet (Akbari et al., Additive
Manufacturing 55, 102817, 2022), which compiles melt-pool depth and width
measurements from published single-track studies. It has no licence file,
so it is not redistributed here; download it first:

    git clone https://github.com/BaratiLab/MeltpoolNet   # commit 6d68e2a (2022-07-13)
    python3 experiments/am_monotone_check.py --csv MeltpoolNet/Data/meltpoolnet_regression.csv

(sha256 of the file we used: 197b111b...14a4f6; the script prints it.)

What is checked, for 316L laser powder bed fusion (speed at least 20 mm/s):
within each study, along every row of its power-speed grid, does melt-pool
depth (width) grow with power and shrink with speed? We count neighbouring
setting pairs that reverse, and those that reverse by more than two
standard errors of a difference, the standard error being the study's
scatter about a smooth trend (a quadratic in log power and log speed;
linear in the logs for studies with fewer than 15 settings). That scatter
also contains model misfit, so it overstates the noise and the 2-SE count
is a lower bound on clear violations. We also fit log-linear exponents per
study (does depth/width rise with power and fall with speed?).

Excluded: studies with fewer than 6 settings, and two studies whose values
follow a formula rather than measurement noise (depth equal to width with
no speed effect; or exactly (P/v)^0.5). Both are perfectly monotone, so
dropping them can only lower the agreement we report.

Writes results/final/am_monotone_check.csv (one row per study and quantity).
"""

import argparse
import csv
import hashlib
import os

import numpy as np
import pandas as pd

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "final")
QUANTITIES = {"depth": "depth of meltpool", "width": "width of melt pool"}
MIN_SETTINGS = 6


def formula_like(t, col):
    """True for a study whose values are not noisy measurements: depth equal
    to width everywhere, or a log-linear fit with residual sd below 3%."""
    if t["depth of meltpool"].notna().all() and t["width of melt pool"].notna().all() \
            and np.allclose(t["depth of meltpool"], t["width of melt pool"]):
        return True
    A = np.column_stack([np.ones(len(t)), np.log(t.Power), np.log(t.Velocity)])
    y = np.log(t[col].values)
    b, *_ = np.linalg.lstsq(A, y, rcond=None)
    return (y - A @ b).std(ddof=3) < 0.03


def check_study(t, col):
    t = t.groupby(["Power", "Velocity"])[col].mean().reset_index()
    lp, lv, y = np.log(t.Power.values), np.log(t.Velocity.values), np.log(t[col].values)
    k = 6 if len(t) >= 15 else 3
    A = np.column_stack([np.ones_like(lp), lp, lv, lp * lv, lp ** 2, lv ** 2])[:, :k]
    b, *_ = np.linalg.lstsq(A, y, rcond=None)
    sd = (y - A @ b).std(ddof=k)
    thr = 2 * np.sqrt(2) * sd
    pairs = rev = big = 0
    for fixed, along, sign in (("Velocity", "Power", +1), ("Power", "Velocity", -1)):
        for _, g in t.groupby(fixed):
            yy = np.log(g.sort_values(along)[col].values)
            d = sign * np.diff(yy)                      # expected positive
            pairs += len(d)
            rev += int((d < 0).sum())
            big += int((d < -thr).sum())
    e, *_ = np.linalg.lstsq(np.column_stack([np.ones_like(lp), lp, lv]), y, rcond=None)
    return dict(settings=len(t), pairs=pairs, reversed=rev, reversed_2se=big, scatter_sd=round(float(sd), 3),
                exp_power=round(float(e[1]), 2), exp_speed=round(float(e[2]), 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="MeltpoolNet Data/meltpoolnet_regression.csv")
    args = ap.parse_args()
    print("sha256", hashlib.sha256(open(args.csv, "rb").read()).hexdigest())
    d = pd.read_csv(args.csv)
    s = d[d.Material.astype(str).str.contains("316") & (d["Sub-process"] == "SLM")].copy()
    for c in ["Power", "Velocity", "depth of meltpool", "width of melt pool"]:
        s[c] = pd.to_numeric(s[c], errors="coerce")
    s = s[s.Velocity >= 20]
    s["study"] = s["paper ID"].astype(str)
    rows = []
    for q, col in QUANTITIES.items():
        for study, t in s.dropna(subset=[col]).groupby("study"):
            if t.groupby(["Power", "Velocity"]).ngroups < MIN_SETTINGS:
                continue
            if formula_like(t.dropna(subset=[col]), col):
                print(f"{q}: study {study} excluded (values follow a formula)")
                continue
            rows.append(dict(quantity=q, study=study, **check_study(t, col)))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "am_monotone_check.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for q in QUANTITIES:
        r = [x for x in rows if x["quantity"] == q]
        print(f"{q}: {len(r)} studies, {sum(x['settings'] for x in r)} settings, "
              f"{sum(x['pairs'] for x in r)} neighbouring pairs, {sum(x['reversed'] for x in r)} reversed, "
              f"{sum(x['reversed_2se'] for x in r)} by more than 2 SE; exponents: power > 0 in "
              f"{sum(x['exp_power'] > 0 for x in r)}/{len(r)}, speed < 0 in {sum(x['exp_speed'] < 0 for x in r)}/{len(r)}")
    both = {}
    for x in rows:
        both.setdefault(x["study"], {})[x["quantity"]] = x
    dw = [(k, v["depth"]["exp_power"] - v["width"]["exp_power"], v["depth"]["exp_speed"] - v["width"]["exp_speed"])
          for k, v in both.items() if len(v) == 2]
    print(f"depth/width ratio: rises with power in {sum(a > 0 for _, a, _ in dw)}/{len(dw)} studies, "
          f"falls with speed in {sum(b < 0 for _, _, b in dw)}/{len(dw)}")


if __name__ == "__main__":
    main()
