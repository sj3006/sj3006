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

structure="none" is the unstructured baseline: every (mode, setting) is its
own one-point chain, alpha is split over all M * N of them, and there is no
spreading.
"""

import numpy as np

from .eprocess import BettingEProcess
from .synthetic import MODES, SAFER_DIRECTION


class WindowCertifier:
    def __init__(self, scenario, alpha=0.05, structure="monotone",
                 strategy="hedge", use_sim_prior=True, start="sim",
                 pilot_per_point=4, prior_weight=10.0, cap=0.8, batch=24,
                 max_per_point=800, futility_n=60, rng=None):
        if structure not in ("monotone", "none"):
            raise ValueError("structure must be 'monotone' or 'none'")
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
        if start not in ("sim", "middle", "pilot"):
            raise ValueError("start must be 'sim', 'middle' or 'pilot'")
        if start == "pilot":
            start_guess = self._pilot(pilot_per_point)
        elif start == "sim":
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
        """
        self.chains = []
        if self.structure == "none":
            for _ in range(self.M):
                self.chains.append([np.array([x]) for x in range(self.N)])
        else:
            margin = (None if guess is None
                      else np.min(self.eps - guess, axis=0).reshape(self.nP, self.nV))
            for m, mode in enumerate(MODES):
                d_p, _ = SAFER_DIRECTION[mode]
                mode_chains = []
                for j in range(self.nV):
                    row = None if margin is None else margin[:, j]
                    if row is not None and np.ptp(row) > 0:
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

        n_chains = sum(len(c) for c in self.chains)
        self.alpha_chain = self.alpha / n_chains
        self.pos = [np.zeros(len(c), dtype=int) for c in self.chains]
        self.done = [np.zeros(len(c), dtype=bool) for c in self.chains]
        self._advance_all()

    # -- spreading ----------------------------------------------------------

    def _upset(self, m, x):
        """Mask of settings at least as safe as x for mode m."""
        i0, j0 = divmod(x, self.nV)
        d_p, d_v = SAFER_DIRECTION[MODES[m]]
        ii, jj = np.meshgrid(np.arange(self.nP), np.arange(self.nV), indexing="ij")
        return (((ii - i0) * d_p >= 0) & ((jj - j0) * d_v >= 0)).ravel()

    def _certify(self, m, x):
        if self.structure == "monotone":
            self.certified[m] |= self._upset(m, x)
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
        # Margin over the modes not yet certified at each candidate.
        margin = np.where(self.certified[:, xs], np.inf, self.eps[:, xs] - p_hat[:, xs])
        score = margin.min(axis=0)
        order = xs[np.lexsort((self.n_at[xs], -score))]
        reps = int(np.ceil(self.batch / len(order)))
        return list(np.tile(order, reps)[: self.batch])

    # -- one build plate ------------------------------------------------------

    def run_plate(self):
        plate = self.choose_plate()
        if not plate:
            return False
        cur = {(m, x): c for m, x, c in self.current_points()}
        alpha_ok = np.full((self.M, self.N), 0.0)
        for (m, x) in cur:
            alpha_ok[m, x] = self.alpha_chain
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
