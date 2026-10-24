"""Certify a process window on a (power, speed) grid.

Procedure (structure="monotone"), for each failure mode m:

1. Split the grid into chains: one chain per speed row. Each chain starts at
   a point chosen from the simulator alone (before any data), and walks
   toward settings that are riskier for mode m.
2. Each (mode, setting) pair has its own betting e-process (eprocess.py).
   Every coupon built at a setting updates the e-processes of all modes at
   that setting.
3. Within a chain, only the current point may be certified. When its wealth
   reaches 1/alpha_chain it is certified and the chain moves to the next
   point. This is fixed-sequence testing, so the chain needs no further
   multiplicity correction.
4. A certified point certifies every setting that is safer for mode m
   (monotone spreading).
5. Chains share the error budget by Bonferroni: alpha_chain = alpha / (M * C).

The certified window is the set of settings certified for every mode.
Validity (Theorem 1 in notes/02_problem_statement.md): if each mode is
monotone in the stated directions, then with probability >= 1 - alpha no
setting in the certified window is truly unsafe, whatever the simulator and
however coupons are allocated.

structure="spread": every (mode, setting) is its own one-point chain (so
alpha is split over all M * N of them, a log factor more than chains), but
certificates still spread. This lets the allocation rule jump straight to
the riskiest certifiable setting in a region instead of walking a chain
through the expensive transition band. Theorem 1 covers it (it is the
special case where every chain has length one).

structure="hybrid": the "monotone" chains AND the "spread" one-point
chains, with the error budget split equally between the two families. Costs
a factor 2 in budget (ln 2 in log-wealth) and is robust to whichever of the
two is worse for the simulator at hand.

structure="none" is the unstructured baseline: one-point chains and no
spreading.

Allocation (which settings go on the next plate):
- alloc="margin": settings whose pending certification has the largest
  estimated margin eps - p_hat.
- alloc="frontier": settings with the most new predicted-window area
  certified per expected coupon: gain / cost, where gain counts uncertified
  settings that a certificate would cover by spreading and that currently
  look safe for every mode, and cost is the remaining log-wealth needed
  divided by the estimated growth rate KL(p_hat || eps) (note 1, sec. 4).
Neither rule affects validity; both are decided before the plate is built.
"""

import numpy as np

from .eprocess import BettingEProcess
from .synthetic import MODES


class WindowCertifier:
    def __init__(self, scenario, alpha=0.05, structure="monotone",
                 strategy="hedge", use_sim_prior=True, start="boundary",
                 boundary_q=(0.3,), hedge_center=True, pilot_per_point=4, prior_weight=10.0, cap=0.8, batch=24,
                 max_per_point=800, futility_n=60, alloc="margin", rng=None):
        if structure not in ("monotone", "spread", "hybrid", "none"):
            raise ValueError("structure must be 'monotone', 'spread', 'hybrid' or 'none'")
        if alloc not in ("margin", "frontier"):
            raise ValueError("alloc must be 'margin' or 'frontier'")
        self.alloc = alloc
        self.sc = scenario
        self.alpha = alpha
        self.structure = structure
        self.batch = batch
        self.max_per_point = max_per_point
        self.futility_n = futility_n
        self.rng = np.random.default_rng() if rng is None else rng

        self.nP, self.nV = len(scenario.power), len(scenario.speed)
        self.N = self.nP * self.nV
        self.M = len(MODES)
        self.eps = np.array([[scenario.eps[m]] * self.N for m in MODES])        # (M, N)
        self.truth = np.stack([scenario.truth[m].ravel() for m in MODES])       # (M, N)
        sim = np.stack([scenario.sim[m].ravel() for m in MODES])                # (M, N)
        self.prior = sim if use_sim_prior else self.eps.copy()

        self.ep = BettingEProcess(self.eps, shape=(self.M, self.N), strategy=strategy,
                                  prior_mean=self.prior, prior_weight=prior_weight, cap=cap)
        self.certified = np.zeros((self.M, self.N), dtype=bool)
        self.n_at = np.zeros(self.N, dtype=int)

        self.coupons = 0
        self.history = []
        if start not in ("boundary", "sim", "middle", "pilot"):
            raise ValueError("start must be 'boundary', 'sim', 'middle' or 'pilot'")
        self.start, self.boundary_q, self.hedge_center = start, boundary_q, hedge_center
        if start == "pilot":
            start_guess = self._pilot(pilot_per_point)
        elif start in ("sim", "boundary"):
            start_guess = sim
        else:
            start_guess = None
        self._build_chains(start_guess)

    # -- setup ------------------------------------------------------------

    def _flat(self, i, j):
        return i * self.nV + j

    def _pilot(self, per_point):
        """Spend a pilot plate on every setting and use it ONLY to choose
        chain starting points. These coupons never enter the e-processes,
        so the starts are independent of the test data (data splitting)."""
        k = self.rng.binomial(per_point, self.truth.repeat(1, axis=1))
        self.coupons += per_point * self.N
        return (k + 0.5) / (per_point + 1.0)   # Jeffreys-smoothed rate

    def _build_chains(self, guess):
        """chains[m] is a list of 1-D arrays of flat indices, in test order.

        guess: (M, N) predicted rates used to pick each chain's start, or
        None to start every chain mid-row. Must not depend on test data.

        Start rules (all walk toward riskier settings for the mode):
        - "boundary": per mode, start at the riskiest setting in the row
          whose predicted rate is at most boundary_q * eps. One certificate
          there covers the whole safer side of the row by spreading, so
          interior points never need direct testing.
        - "sim" / "pilot": start at the point the guess says is safest across
          all modes (the middle of the predicted window).
        - "middle": start mid-row (no information).
        """
        self.chains = []
        singles = [[np.array([x]) for x in range(self.N)] for _ in range(self.M)]
        if self.structure in ("none", "spread"):
            self.chains = singles
        else:
            margin = (None if guess is None
                      else np.min(self.eps - guess, axis=0).reshape(self.nP, self.nV))
            for m, mode in enumerate(MODES):
                d_p, _ = self.sc.directions[mode]
                mode_chains = []
                for j in range(self.nV):
                    row = None if margin is None else margin[:, j]
                    if self.start == "boundary":
                        # One chain per aggressiveness level q. Overlapping
                        # chains are fine for Theorem 1 (union bound).
                        g = guess[m].reshape(self.nP, self.nV)[:, j]
                        safest_first = np.arange(self.nP)[::-1] if d_p > 0 else np.arange(self.nP)
                        starts = set()
                        for q in np.atleast_1d(self.boundary_q):
                            ok = safest_first[g[safest_first] <= q * self.eps[m, 0]]
                            starts.add(int(ok[-1]) if len(ok) else int(safest_first[0]))
                        if self.hedge_center:
                            # Robust chain from the middle of the predicted
                            # window, in case the simulator is optimistic.
                            best = np.flatnonzero(row >= row.max() - 1e-12)
                            starts.add(int(best[len(best) // 2]))
                        for s in sorted(starts):
                            steps = np.arange(s, -1, -1) if d_p > 0 else np.arange(s, self.nP)
                            mode_chains.append(np.array([self._flat(i, j) for i in steps]))
                        continue
                    elif row is not None and np.ptp(row) > 0:
                        # Middle of the best-scoring points, so ties (common
                        # with a small pilot) do not push the start to an edge.
                        best = np.flatnonzero(row >= row.max() - 1e-12)
                        s = int(best[len(best) // 2])
                    else:
                        s = self.nP // 2
                    # Walk toward riskier settings for this mode.
                    steps = np.arange(s, -1, -1) if d_p > 0 else np.arange(s, self.nP)
                    mode_chains.append(np.array([self._flat(i, j) for i in steps]))
                self.chains.append(mode_chains)

        # Error budget per chain (Bonferroni within each family).
        n_chains = sum(len(c) for c in self.chains)
        if self.structure == "hybrid":
            n_long = n_chains
            self.chains = [self.chains[m] + singles[m] for m in range(self.M)]
            n_single = self.M * self.N
            self.alpha_c = [np.array([self.alpha / 2 / n_long] * (len(self.chains[m]) - self.N)
                                     + [self.alpha / 2 / n_single] * self.N)
                            for m in range(self.M)]
        else:
            self.alpha_c = [np.full(len(self.chains[m]), self.alpha / n_chains)
                            for m in range(self.M)]
        self.alpha_chain = min(a.min() for a in self.alpha_c)
        if self.structure != "none":
            self.dominance = np.stack([np.stack([self._upset(m, x) for x in range(self.N)])
                                       for m in range(self.M)])   # (M, N, N): [m, x, y] = y safer than x
        self.pos = [np.zeros(len(c), dtype=int) for c in self.chains]
        self.done = [np.zeros(len(c), dtype=bool) for c in self.chains]
        self._advance_all()

    # -- spreading ----------------------------------------------------------

    def _upset(self, m, x):
        """Mask of settings at least as safe as x for mode m."""
        i0, j0 = divmod(x, self.nV)
        d_p, d_v = self.sc.directions[MODES[m]]
        ii, jj = np.meshgrid(np.arange(self.nP), np.arange(self.nV), indexing="ij")
        return (((ii - i0) * d_p >= 0) & ((jj - j0) * d_v >= 0)).ravel()

    def _certify(self, m, x):
        if self.structure != "none":
            self.certified[m] |= self.dominance[m, x]
        else:
            self.certified[m, x] = True

    # -- chain bookkeeping ---------------------------------------------------

    def _advance_all(self):
        for m in range(self.M):
            for c, chain in enumerate(self.chains[m]):
                while not self.done[m][c] and self.certified[m, chain[self.pos[m][c]]]:
                    self.pos[m][c] += 1
                    if self.pos[m][c] >= len(chain):
                        self.done[m][c] = True

    def current_points(self):
        """Set of (m, x) pairs that are currently allowed to be certified."""
        out = []
        for m in range(self.M):
            for c, chain in enumerate(self.chains[m]):
                if not self.done[m][c]:
                    out.append((m, chain[self.pos[m][c]], c))
        return out

    # -- allocation ---------------------------------------------------------

    def _estimates(self):
        w = self.ep.n + self.ep.prior_weight
        return (self.ep.s1 + self.ep.prior_weight * self.prior) / w

    def choose_plate(self):
        """Pick self.batch settings for the next build plate (may repeat)."""
        cur = self.current_points()
        if not cur:
            return []
        xs = np.unique([x for _, x, _ in cur])
        p_hat = self._estimates()
        if self.alloc == "frontier":
            return self._frontier_plate(cur, xs, p_hat)
        # Score each candidate by its most promising pending certification:
        # the largest estimated margin eps - p_hat among modes for which it is
        # a chain's current point.
        best = {}
        for m, x, _ in cur:
            best[x] = max(best.get(x, -np.inf), self.eps[m, x] - p_hat[m, x])
        score = np.array([best[x] for x in xs])
        order = xs[np.lexsort((self.n_at[xs], -score))]
        reps = int(np.ceil(self.batch / len(order)))
        return list(np.tile(order, reps)[: self.batch])

    def _frontier_plate(self, cur, xs, p_hat):
        looks_safe = (p_hat < self.eps).all(axis=0)                     # (N,)
        a = np.full((self.M, self.N), self.alpha_chain)
        is_cur = np.zeros((self.M, self.N), dtype=bool)
        for m, x, c in cur:
            a[m, x] = max(a[m, x], self.alpha_c[m][c])
            is_cur[m, x] = True
        need = np.maximum(-np.log(a) - self.ep.log_wealth(), 0.0)        # (M, N)
        if self.structure == "none":
            gain = np.broadcast_to(looks_safe.astype(float), (self.M, self.N))
        else:
            target = (~self.certified & looks_safe[None, :]).astype(float)   # (M, N)
            gain = np.einsum("mxy,my->mx", self.dominance, target)
        rate = _kl_vec(p_hat, self.eps)                                  # 0 where p >= eps
        ok = is_cur & (rate > 0)
        per = np.where(ok, gain / (need / np.maximum(rate, 1e-4) + 1.0), 0.0)
        score = per.sum(axis=0)
        cand = xs[score[xs] > 0]
        if len(cand) == 0:
            cand = xs
        order = cand[np.argsort(-score[cand], kind="stable")][: self.batch]
        reps = int(np.ceil(self.batch / len(order)))
        return list(np.tile(order, reps)[: self.batch])

    # -- one build plate ------------------------------------------------------

    def run_plate(self):
        plate = self.choose_plate()
        if not plate:
            return False
        # A point may be current in several chains (overlapping chains, or
        # hybrid). It is certified as soon as its wealth beats the threshold
        # of ANY of them; the union bound in Theorem 1 covers this.
        alpha_ok = np.full((self.M, self.N), 0.0)
        for m, x, c in self.current_points():
            alpha_ok[m, x] = max(alpha_ok[m, x], self.alpha_c[m][c])
        for x in plate:
            y = (self.rng.random(self.M) < self.truth[:, x]).astype(float)
            self.ep.update_at((slice(None), x), y)
            self.n_at[x] += 1
            self.coupons += 1
            # Check every current point at x (anytime-valid, so per coupon is fine).
            lw = self.ep.log_wealth((slice(None), x))
            for m in range(self.M):
                if alpha_ok[m, x] > 0 and lw[m] >= -np.log(alpha_ok[m, x]):
                    self._certify(m, x)
                    alpha_ok[m, x] = 0.0
        self._advance_all()
        self._futility()
        self._record()
        return True

    def _futility(self):
        """Stop chains whose current point looks hopeless. Never certifies
        anything, so it cannot hurt validity."""
        p_data = np.divide(self.ep.s1, self.ep.n, out=np.zeros_like(self.ep.s1),
                           where=self.ep.n > 0)
        for m, x, c in self.current_points():
            n = self.ep.n[m, x]
            if n >= self.max_per_point or (n >= self.futility_n and p_data[m, x] > self.eps[m, x]):
                self.done[m][c] = True

    # -- results --------------------------------------------------------------

    def window(self):
        return self.certified.all(axis=0).reshape(self.nP, self.nV)

    def _record(self):
        win = self.window().ravel()
        bad = (self.truth >= self.eps).any(axis=0)   # null is p >= eps
        self.history.append(dict(coupons=self.coupons, area=int(win.sum()),
                                 errors=int((win & bad).sum())))

    def run(self, budget):
        while self.coupons < budget and self.run_plate():
            pass
        return self.history


def _kl_vec(p, q):
    """Elementwise KL(Bernoulli(p) || Bernoulli(q)), set to 0 where p >= q."""
    p = np.clip(p, 1e-12, 1 - 1e-12)
    kl = p * np.log(p / q) + (1 - p) * np.log((1 - p) / (1 - q))
    return np.where(p < q, kl, 0.0)


def _kl(p, q):
    """KL(Bernoulli(p) || Bernoulli(q)) for p < q."""
    p = min(max(p, 1e-12), 1 - 1e-12)
    return p * np.log(p / q) + (1 - p) * np.log((1 - p) / (1 - q))
