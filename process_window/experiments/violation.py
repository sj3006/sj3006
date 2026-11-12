"""Robustness when monotonicity fails, and whether an audit catches it.

A pocket of settings inside the true window gets a lack-of-fusion rate of
`pocket_rate` (non-monotone: safer settings around it are fine). We measure
how often the method certifies a pocket setting, and how often an audit
with a small extra budget flags the violation.

Run from process_window/:  python3 experiments/violation.py
"""

import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.audit import audit  # noqa: E402
from pwcert.cone import ConeCertifier  # noqa: E402
from pwcert.synthetic import Scenario, make_scenario  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "final")


def pocket_scenario(n, size, rate, seed):
    base = make_scenario(n, n, simulator="good")
    W = base.true_window()
    rng = np.random.default_rng(seed)
    inside = np.argwhere(W)
    # Pocket: a size x size block of window settings well inside the window.
    for _ in range(200):
        i, j = inside[rng.integers(len(inside))]
        blk = W[i:i + size, j:j + size]
        if blk.shape == (size, size) and blk.all():
            break
    truth = {m: v.copy() for m, v in base.truth.items()}
    truth["lof"][i:i + size, j:j + size] = rate
    mask = np.zeros_like(W)
    mask[i:i + size, j:j + size] = True
    return Scenario(base.power, base.speed, base.eps, truth, base.sim, name="pocket"), mask


def main():
    rows = []
    n, reps = 16, 60
    for size, rate in ((1, 0.15), (2, 0.15), (1, 0.08), (2, 0.08)):
        cert_err = flag = 0
        audit_cost = []
        for r in range(reps):
            sc, mask = pocket_scenario(n, size, rate, seed=r)
            c = ConeCertifier(sc, rng=np.random.default_rng(r), batch=2 * n)
            c.run(30000)
            hit = (c.window() & mask).any()
            cert_err += int(hit)
            # Full audit: every certified setting, up to 300 coupons each.
            flagged, cost = audit(c, n_settings=10 ** 6, per_setting=300,
                                  rng=np.random.default_rng(10_000 + r))
            audit_cost.append(cost)
            flag += int(hit and any(mask.ravel()[x] for _, x in flagged))
        rows.append(dict(pocket_size=size, pocket_rate=rate, runs=reps,
                         pocket_certified=round(cert_err / reps, 3),
                         caught_by_audit_given_certified=round(flag / max(cert_err, 1), 3),
                         audit_budget=int(np.mean(audit_cost)), certification_budget=30000))
        print(rows[-1], flush=True)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "violation.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
