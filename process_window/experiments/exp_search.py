"""Fixed-confidence experiment: certify the whole target AND know you're done.

Target T = {all rates <= q eps}; settings with rates in (q eps, eps) may be
certified too. A method must stop on its own. We record the coupons used at
its stop and whether T was fully certified then (completeness).

Methods:
- search (ours): SearchCertifier, stops when every row is decided.
- per-setting (no ordering): every setting gets the same two-sided test
  (certify at eps with its own e-process, or reject at q eps) with no
  spreading; stops when every setting is decided.

Lower bounds (computed from the true rates; notes/09):
- certification term: Theorem 2a's LP, L * LP(T);
- boundary term: for each mode, the safest settings outside T (and inside T
  for the other modes) must be resolved: either certified (cost about
  L / KL(p || eps)) or shown to be outside T (about L / KL(p || q eps)), so
  each adds L * min of the two inverse rates.
- unordered: every setting must be resolved on its own: target settings
  certified for every mode, others certified or shown outside for one mode.

Run from process_window/:  python3 experiments/exp_search.py [--quick]
"""

import argparse
import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.certify import _kl_vec  # noqa: E402
from pwcert.cone import ConeCertifier, cone_sum  # noqa: E402
from pwcert.search import SearchCertifier  # noqa: E402
from pwcert.synthetic import make_scenario  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from final import lower_bounds  # noqa: E402

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


def boundary_bound(sc, q=Q, beta=BETA):
    """L * sum over (mode, safest-outside setting) of min(1/KL to eps, 1/KL to q eps)."""
    modes = sc.modes
    truth = np.stack([sc.truth[m] for m in modes])
    eps = np.array([sc.eps[m] for m in modes])[:, None, None]
    inT = truth <= q * eps                           # per mode
    L = (1 - beta) * np.log(1 / ALPHA) - np.log(2)
    total, pts = 0.0, set()
    for a, m in enumerate(modes):
        others = np.all([inT[b] for b in range(len(modes)) if b != a], axis=0)
        outside = ~inT[a] & others
        # safest points of `outside` for mode a: no other outside point is safer.
        safer_count = cone_sum(outside.astype(float), sc.directions[m], riskier=False)
        boundary = outside & (safer_count < 1.5)
        p = truth[a][boundary]
        cert = np.where(p < eps[a].ravel()[0], 1.0 / np.maximum(_kl_vec(p, eps[a].ravel()[0]), 1e-12), np.inf)
        p_rej = np.clip(p, 1e-9, 1 - 1e-9)
        qe = q * eps[a].ravel()[0]
        kl_rej = p_rej * np.log(p_rej / qe) + (1 - p_rej) * np.log((1 - p_rej) / (1 - qe))
        total += float(np.sum(np.minimum(cert, 1.0 / np.maximum(kl_rej, 1e-12))))
        pts |= set(zip(*np.nonzero(boundary)))
    return L * total, len(pts)


def unordered_bound(sc, q=Q, beta=BETA):
    """Without the ordering every setting must be resolved on its own:
    target settings certified for every mode; others either certified (if in
    the window) or shown outside the target for some mode."""
    modes = sc.modes
    truth = np.stack([sc.truth[m].ravel() for m in modes])
    eps = np.array([sc.eps[m] for m in modes])[:, None]
    L = (1 - beta) * np.log(1 / ALPHA) - np.log(2)

    def inv_kl(p, t):
        p = np.clip(p, 1e-9, 1 - 1e-9)
        kl = p * np.log(p / t) + (1 - p) * np.log((1 - p) / (1 - t))
        return 1.0 / np.maximum(kl, 1e-12)

    cert = np.where(truth < eps, inv_kl(truth, eps), np.inf).max(axis=0)       # certify all modes
    rej = np.where(truth > q * eps, inv_kl(truth, q * eps), np.inf).min(axis=0)  # show one mode outside
    inT = (truth <= q * eps).all(axis=0)
    per = np.where(inT, cert, np.minimum(cert, rej))
    return L * float(per[np.isfinite(per)].sum())


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
    args = ap.parse_args()
    sizes = (8, 16) if args.quick else tuple(int(s) for s in args.sizes.split(","))
    reps = 2 if args.quick else 4
    rows = []
    for sim in args.sims.split(","):
        for n in sizes:
            sc = make_scenario(n, n, simulator=sim)
            T, lb_a, lb_u, n_edge = lower_bounds(sc, Q)
            lb_b, n_bd = boundary_bound(sc)
            row = dict(sim=sim, n=n, T_size=int(T.sum()), edge_points=n_edge, boundary_points=n_bd,
                       LB_cert=round(lb_a), LB_boundary=round(lb_b), LB_total=round(lb_a + lb_b),
                       LB_unordered=round(unordered_bound(sc)))
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
