"""Fixed-confidence experiment: certify the whole target AND know you're done.

Target T = {all rates <= q eps}; settings with rates in (q eps, eps) may be
certified too. A method must stop on its own. We record the coupons used at
its stop and whether T was fully certified then (completeness).

Methods:
- search (ours): SearchCertifier, stops when every row is decided.
- per-setting (no ordering): every setting gets the same two-sided test
  (certify at eps with its own e-process, or reject at q eps) with no
  spreading; stops when every setting is decided.

Lower bounds (computed from the true rates; pwcert/bounds.py, paper Theorem 2):
- LB_target: target points only (Theorem 2a's LP with kl(1-beta, alpha));
- LB_ordered: one joint LP with the target constraints and the boundary
  constraints (settings just outside T must be certified or told apart
  from an alternative where they are in T), so trials that serve both are
  not counted twice;
- LB_unordered: every setting resolved on its own.

Run from process_window/:  python3 experiments/exp_search.py [--quick]
"""

import argparse
import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.bounds import ordered_lower_bound, unordered_lower_bound  # noqa: E402
from pwcert.cone import ConeCertifier  # noqa: E402
from pwcert.search import SearchCertifier  # noqa: E402
from pwcert.synthetic import make_scenario  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "final")
Q, ALPHA, BETA = 0.5, 0.05, 0.05


class PerSetting(ConeCertifier):
    """No ordering: two-sided test at every setting, no spreading."""

    def __init__(self, sc, q=Q, beta=BETA, per_probe=8, **kw):
        super().__init__(sc, rule="none", weights="uniform", **kw)
        self.q, self.per_probe = q, per_probe
        self.reject_level = np.log(self.M * self.N / beta)
        fr = np.array([0.025, 0.05, 0.1, 0.2, 0.4])
        self._lam = fr[None, None, :] / (q * self.eps[:, :, None])
        self._logk = np.zeros(self._lam.shape)
        self.rejected = np.zeros((self.M, self.N), dtype=bool)

    def choose_plate(self):
        excluded = self.rejected.any(axis=0)
        open_ = ((~self.certified & ~self.rejected).any(axis=0)) & ~excluded
        xs = np.flatnonzero(open_)
        if len(xs) == 0:
            return []
        per = max(self.per_probe, int(np.ceil(self.batch / len(xs))))
        return [x for x in xs[: max(1, self.batch // self.per_probe)] for _ in range(per)]

    def run_plate(self):
        plate = self.choose_plate()
        if not plate:
            return False
        for x in plate:
            y = (self.rng.random(self.M) < self.truth[:, x]).astype(float)
            self.ep.update_at((slice(None), x), y)
            eq = (self.q * self.eps[:, x])[:, None]
            self._logk[:, x, :] += np.log1p(self._lam[:, x, :] * (y[:, None] - eq))
            top = self._logk[:, x, :].max(axis=1)
            mix = top + np.log(np.mean(np.exp(self._logk[:, x, :] - top[:, None]), axis=1))
            self.rejected[:, x] |= (mix >= self.reject_level) & ~self.certified[:, x]
            self.n_at[x] += 1
            self.coupons += 1
        self._check()
        self.rejected &= ~self.certified
        self._record()
        return True


def bound_columns(sc):
    T = np.all([sc.truth[m] <= Q * sc.eps[m] for m in sc.modes], axis=0)
    b = ordered_lower_bound(sc, Q, ALPHA, BETA)
    return dict(T_size=int(T.sum()), target_points=b["n_target_pts"], boundary_points=b["n_boundary_pts"],
                LB_target=round(b["lb_target_only"]), LB_ordered=round(b["lb"]),
                LB_unordered=round(unordered_lower_bound(sc, Q, ALPHA, BETA)))


def recompute_bounds(paths):
    """Rewrite the lower-bound columns of existing result files (the bounds
    depend only on the true rates, so the runs need not be repeated)."""
    old = ("edge_points", "LB_cert", "LB_boundary", "LB_total")
    for path in paths:
        rows = list(csv.DictReader(open(path)))
        out = []
        for r in rows:
            sc = make_scenario(int(r["n"]), int(r["n"]), simulator=r["sim"])
            new = dict(sim=r["sim"], n=r["n"], **bound_columns(sc))
            new.update({k: v for k, v in r.items() if k not in new and k not in old})
            out.append(new)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0]))
            w.writeheader()
            w.writerows(out)
        print("rewrote", path, flush=True)


def run(method, sc, n, r):
    T = np.all([sc.truth[m] <= Q * sc.eps[m] for m in sc.modes], axis=0)
    rng = np.random.default_rng(r)
    if method == "search":
        c = SearchCertifier(sc, q=Q, batch=2 * n, rng=rng)
    else:
        c = PerSetting(sc, batch=2 * n, rng=rng)
    budget = 600 * n * n
    while c.coupons < budget and c.run_plate():
        pass
    stopped = c.coupons < budget
    complete = bool((c.window() >= T).all())
    unsafe = int((c.window() & ~sc.true_window()).sum())
    return c.coupons if stopped else np.inf, complete, unsafe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--sims", default="good,biased")
    ap.add_argument("--sizes", default="8,12,16,24,32,48")
    ap.add_argument("--out", default="fixed_confidence.csv")
    ap.add_argument("--recompute-bounds", nargs="*", default=None,
                    help="rewrite the bound columns of these result files and exit")
    args = ap.parse_args()
    if args.recompute_bounds is not None:
        recompute_bounds(args.recompute_bounds)
        return
    sizes = (8, 16) if args.quick else tuple(int(s) for s in args.sizes.split(","))
    reps = 2 if args.quick else 4
    rows = []
    for sim in args.sims.split(","):
        for n in sizes:
            sc = make_scenario(n, n, simulator=sim)
            row = dict(sim=sim, n=n, **bound_columns(sc))
            for method in ("search", "per-setting"):
                if method == "per-setting" and n > 32:
                    row[method] = np.nan
                    continue
                t0, cs, comp, uns = time.time(), [], 0, 0
                for r in range(reps):
                    c, ok, u = run(method, sc, n, r)
                    cs.append(c)
                    comp += int(ok)
                    uns += u
                row[method] = float(np.median(cs))
                row[method + "_complete"] = f"{comp}/{reps}"
                row[method + "_unsafe"] = uns
                print(f"{sim} {n}x{n} {method:12s} median {np.median(cs):9.0f}  complete {comp}/{reps}"
                      f"  unsafe certified {uns}  ({time.time() - t0:.0f}s)", flush=True)
            rows.append(row)
            print(row, flush=True)
            os.makedirs(OUT, exist_ok=True)
            keys = sorted({k for r_ in rows for k in r_}, key=lambda k: list(rows[0]).index(k)
                          if k in rows[0] else 99)
            with open(os.path.join(OUT, args.out), "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                w.writerows(rows)


if __name__ == "__main__":
    main()
