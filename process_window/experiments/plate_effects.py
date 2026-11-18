"""Correlated trials on one build plate: what breaks, and two valid fixes.

The paper assumes trials are independent given the setting. On a laser
powder bed fusion plate they may not be: powder lot, gas flow and position
shift every coupon on the plate together. Model: trials at setting x on
plate b share a plate-level rate p_b(x) ~ Beta with mean p(x) and
intra-plate correlation rho (a beta-binomial); plates are independent. The
rate a certificate is about is the mean p(x) over plates.

Three ways to run the certifier:
  per trial  - each trial is its own outcome and the bets update after each
               one, as in the paper. Valid when rho = 0. With rho > 0 the
               trials on a plate are not independent, so the betting
               argument no longer applies.
  per plate  - each (setting, plate) pair contributes one outcome: the
               failure fraction on that plate at that setting, in [0, 1].
               Plates are independent, so given earlier plates its mean is
               p(x) and the betting argument goes through for any rho.
  spread     - a plate-aware edge rule: one trial at each of the settings
               the edge rule wants (up to the plate size), then re-checks.
               With one trial per setting per plate, per trial and per
               plate coincide, so it is valid for any rho.

Parts:
  single  one setting at the tolerance (the worst case for validity):
          how often is it certified, per trial vs per plate?
  cost    one safe setting: trials to certify, per trial vs per plate.
  grid    the cone certifier: the 8 x 8 all-at-tolerance worst case
          (validity) and the 16 x 16 synthetic window (cost to certify half
          the safe region, in trials and in plates), for the three designs.

Writes results/final/plate_effects_{single,cost,grid}.csv.
Run: OMP_NUM_THREADS=1 python3 experiments/plate_effects.py --parts single,cost,grid
"""

import argparse
import csv
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.cone import ConeCertifier, _kl_vec, cone_sum  # noqa: E402
from pwcert.eprocess import BettingEProcess  # noqa: E402
from pwcert.synthetic import Scenario, make_scenario  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "final")
ALPHA = 0.05
EPS = 0.10


def plate_rates(p, rho, size, rng):
    """Plate-level rates with mean p and intra-plate correlation rho."""
    p = np.broadcast_to(np.asarray(p, dtype=float), size)
    if rho <= 0:
        return p.copy()
    pc = np.clip(p, 1e-9, 1 - 1e-9)
    a, b = pc * (1 - rho) / rho, (1 - pc) * (1 - rho) / rho
    return rng.beta(a, b)


def write(rows, name):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


# -- one setting ----------------------------------------------------------------

def run_single(p, rho, k, unit, reps, max_trials, rng, stop_when_all=False):
    """Return (ever certified, first certification time in trials) per run."""
    ep = BettingEProcess(EPS, shape=reps, strategy="hedge", prior_weight=10.0)
    thr = np.log(1 / ALPHA)
    hit = np.zeros(reps, dtype=bool)
    when = np.full(reps, np.inf)
    for b in range(max_trials // k):
        pb = plate_rates(p, rho, reps, rng)
        y = (rng.random((k, reps)) < pb).astype(float)
        if unit == "trial":
            for i in range(k):
                ep.update(y[i])
        else:
            ep.update(y.mean(axis=0))
        new = (ep.log_wealth() >= thr) & ~hit      # checked once per plate, as the certifier does
        when[new] = (b + 1) * k
        hit |= new
        if stop_when_all and hit.all():
            break
    return hit, when


def cmd_single(args):
    rng = np.random.default_rng(1)
    rows = []
    for k in (4, 12, 24):
        for rho in (0.0, 0.02, 0.05, 0.1, 0.2):
            for unit in ("trial", "plate"):
                t0 = time.time()
                hit, _ = run_single(EPS, rho, k, unit, args.reps, args.max_trials, rng)
                r = hit.mean()
                rows.append(dict(k=k, rho=rho, unit=unit, rate=EPS, runs=args.reps, max_trials=args.max_trials,
                                 error=round(float(r), 4), se=round(float(np.sqrt(r * (1 - r) / args.reps)), 4)))
                print(rows[-1], f"({time.time() - t0:.0f}s)", flush=True)
    write(rows, "plate_effects_single.csv")


def cmd_cost(args):
    rng = np.random.default_rng(2)
    rows = []
    for p in (0.02, 0.05):
        for k in (1, 4, 12, 24):
            for rho in (0.0, 0.05, 0.1):
                for unit in (("trial",) if k == 1 else ("trial", "plate")):
                    _, when = run_single(p, rho, k, unit, 400, 40_000, rng, stop_when_all=True)
                    rows.append(dict(p=p, k=k, rho=rho, unit=unit, runs=400,
                                     median_trials=float(np.median(when)),
                                     certified=f"{int(np.isfinite(when).sum())}/400"))
                    print(rows[-1], flush=True)
    write(rows, "plate_effects_cost.csv")


# -- the cone certifier with plate effects ---------------------------------------

class PlateCertifier(ConeCertifier):
    """ConeCertifier whose trials share a plate effect.

    design: "trial" (per trial, as in the paper), "plate" (one outcome per
    setting and plate: the failure fraction), or "spread" (at most one trial
    per setting per plate)."""

    def __init__(self, *a, rho=0.0, design="trial", **kw):
        super().__init__(*a, **kw)
        self.rho, self.design = rho, design
        self.plates = 0

    def choose_plate(self):
        if self.design != "spread":
            return super().choose_plate()
        # Plate-aware edge rule: the same settings the edge rule wants (the
        # riskiest uncertified points of the shrunken target, for each mode),
        # one trial each, most nearly finished first; then re-checks.
        p_hat = self._estimates()
        target = (p_hat < self.target_q * self.eps).all(axis=0)
        need, rate = self._need(), _kl_vec(p_hat, self.eps)
        remaining = {}
        for m in range(self.M):
            u = target & ~self.certified[m] & ~self.hopeless[m]
            if not u.any():
                continue
            count = cone_sum(self._grid(u.astype(float)), self.dirs[m]).ravel()
            for x in np.flatnonzero(u & (count < 1.5) & (rate[m] > 0) & np.isfinite(need[m])):
                remaining[x] = max(remaining.get(x, 0.0), need[m, x] / rate[m, x] + 1.0)
        plate = [x for x, _ in sorted(remaining.items(), key=lambda kv: kv[1])][: self.batch]
        if len(plate) < self.batch:
            more = self._recheck_plate(p_hat, per_point=1)
            plate += [x for x in dict.fromkeys(more) if x not in plate][: self.batch - len(plate)]
        return plate

    def run_plate(self):
        plate = self.choose_plate()
        if not plate:
            return False
        xs, counts = np.unique(plate, return_counts=True)
        for x, c in zip(xs, counts):
            pb = plate_rates(self.truth[:, x], self.rho, self.M, self.rng)
            y = (self.rng.random((c, self.M)) < pb).astype(float)
            if self.design == "plate":
                self.ep.update_at((slice(None), x), y.mean(axis=0))
            else:
                for i in range(c):
                    self.ep.update_at((slice(None), x), y[i])
            self.n_at[x] += c
            self.coupons += c
        self.plates += 1
        self._check()
        self._futility()
        self._record()
        return True


def cmd_grid(args):
    rows = []
    base = make_scenario(8, 8, simulator="good")
    truth = {m: np.full((8, 8), base.eps[m]) for m in base.modes}      # every setting at the tolerance
    worst = Scenario(base.power, base.speed, base.eps, truth, base.sim, directions=base.directions)
    for design in ("trial", "plate", "spread"):
        for rho in (0.0, 0.05, 0.2):
            t0, err = time.time(), 0
            for r in range(args.reps):
                c = PlateCertifier(worst, rule="cone", weights="ensemble", alloc="edge", target_q=0.7, batch=16,
                                   rng=np.random.default_rng(100_000 + r), rho=rho, design=design)
                c.run(4000)
                err += int(c.certified.any())
            e = err / args.reps
            rows.append(dict(part="validity 8x8 at tolerance", design=design, rho=rho, runs=args.reps,
                             error=round(e, 4), se=round(float(np.sqrt(e * (1 - e) / args.reps)), 4),
                             median_trials="", median_plates="", unsafe_certified=""))
            print(rows[-1], f"({time.time() - t0:.0f}s)", flush=True)
    sc = make_scenario(16, 16, simulator="good")
    safe = sc.true_window()
    goal = 0.5 * safe.sum()
    for design in ("trial", "plate", "spread"):
        for rho in (0.0, 0.1):
            t0, trials, plates, bad = time.time(), [], [], 0
            for r in range(args.cost_reps):
                c = PlateCertifier(sc, rule="cone", weights="ensemble", alloc="edge", target_q=0.7, batch=32,
                                   rng=np.random.default_rng(200_000 + r), rho=rho, design=design)
                tr, pl = np.inf, np.inf
                while c.coupons < args.budget and c.run_plate():
                    if c.history[-1]["area"] >= goal and not np.isfinite(tr):
                        tr, pl = c.coupons, c.plates
                        break
                trials.append(tr)
                plates.append(pl)
                bad += int(c.history[-1]["errors"] > 0) if c.history else 0
            rows.append(dict(part="cost 16x16, half the safe region", design=design, rho=rho, runs=args.cost_reps,
                             error="", se="", median_trials=float(np.median(trials)),
                             median_plates=float(np.median(plates)), unsafe_certified=f"{bad}/{args.cost_reps}"))
            print(rows[-1], f"({time.time() - t0:.0f}s)", flush=True)
    write(rows, "plate_effects_grid.csv")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="single,cost,grid")
    ap.add_argument("--reps", type=int, default=400)
    ap.add_argument("--max-trials", type=int, default=2400)
    ap.add_argument("--cost-reps", type=int, default=8)
    ap.add_argument("--budget", type=int, default=200_000)
    args = ap.parse_args()
    for part in args.parts.split(","):
        {"single": cmd_single, "cost": cmd_cost, "grid": cmd_grid}[part](args)


if __name__ == "__main__":
    main()
