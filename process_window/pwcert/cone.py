"""Cone rule: closed testing with e-processes under monotone structure.

Every (mode, setting) pair i carries a betting e-process K_i (eprocess.py)
and a fixed weight w_i >= 0, with sum_i w_i <= 1, chosen before any test data
(uniform, or from a simulator; see make_weights). Setting k is certified for
mode m at time t when its *riskier cone* has enough weighted wealth:

    S_m(k, t) = sum over settings i at least as risky as k for mode m of
                w_{m,i} K_{m,i}(t)   >=   1 / alpha.

Certification is sticky (once certified, always certified).

Validity (notes/06_cone_rule.md). Under Assumption A, the set D of truly
unsafe (mode, setting) pairs is closed toward risk: if k is unsafe for m, so
is everything riskier. A false certification of k means S_m(k, t) >= 1/alpha
with k's whole riskier cone inside D, so E_D(t) = sum_{i in D} w_i K_i(t) >=
1/alpha. E_D is one nonnegative supermartingale starting at sum_D w_i <= 1,
so Ville's inequality bounds the chance this ever happens by alpha, for any
sampling rule and any stopping time. This is closed testing with the
weighted-sum intersection e-value, specialized to logically related nulls.

Compared with Bonferroni + spreading (rule="max": certify k when some single
riskier i has w_i K_i >= 1/alpha), the cone rule pools evidence across the
cone and is never less powerful. rule="none" is the unstructured baseline:
k is certified only by its own e-process, and nothing spreads.

Allocation rules (which settings go on the next plate) never affect validity.
- "edge": for each mode, the riskiest uncertified settings of the estimated
  target T_hat (every estimated rate below target_q * eps), i.e. the binding
  constraints of the lower bound (notes/05). Plates are filled with each
  setting's expected remaining coupons, cheapest first. When T_hat is
  covered, re-check the uncertified settings with the lowest lower
  confidence bound (optimism), skipping ones that are confidently unsafe.
- "frontier": settings with the most new estimated-safe area per expected
  coupon (for the "certify as much as possible" goal).
"""

import numpy as np

from .certify import _isotonic_2d, _kl_vec
from .eprocess import BettingEProcess


# -- cone sums on the grid ------------------------------------------------

def cone_sum(v, direction, riskier=True):
    """Sum of v over each setting's riskier (or safer) cone, including itself.

    v: (nP, nV) array. direction: (d_p, d_v), the index steps that make the
    mode SAFER. The riskier cone of k is every i with (i - k) * d <= 0 on both
    axes; the safer cone flips the inequality.
    """
    s_p, s_v = direction
    if not riskier:
        s_p, s_v = -s_p, -s_v
    z = v[::s_p, ::s_v]
    z = np.cumsum(np.cumsum(z, axis=0), axis=1)
    return z[::s_p, ::s_v]


# -- weights ----------------------------------------------------------------

def make_weights(sc, kind="uniform", mix=0.5, q=0.5, width=0.7, sigma=1.0,
                 n_draws=400, seed=0):
    """Fixed weights w (M, nP, nV), summing to 1. Must not use test data.

    kind:
    - "uniform": 1 / (M N) everywhere.
    - "band": a bump around each mode's predicted target edge: weight
      exp(-(log(p_sim / (q eps)))^2 / (2 width^2)) on settings the simulator
      predicts are inside the window for the other modes.
    - "mix": (1 - mix) * uniform + mix * band.
    - "ensemble": (1 - mix) * uniform + mix * P(setting is an edge point of
      the target), where the probability is over perturbed simulators: each
      mode's predicted rates get an independent logit shift ~ N(0, sigma^2).
      sigma says how far you trust the simulator. Rationale: certifying an
      edge point with weight w costs about ln(1 / (alpha w)) / KL coupons, so
      the best fixed weights spread the budget over the settings likely to
      be edge points (notes/06).
    The uniform floor keeps every setting certifiable if the simulator is wrong.
    """
    modes = sc.modes
    M = len(modes)
    shape = sc.truth[modes[0]].shape
    uni = np.full((M,) + shape, 1.0 / (M * np.prod(shape)))
    if kind == "uniform":
        return uni
    if kind == "ensemble":
        return (1 - mix) * uni + mix * edge_probability(sc, q, sigma, n_draws, seed)
    sim = np.stack([np.clip(sc.sim[m], 1e-6, 1.0) for m in modes])
    eps = np.array([sc.eps[m] for m in modes])[:, None, None]
    band = np.zeros_like(sim)
    for a in range(M):
        others = np.ones(shape, dtype=bool)
        for b in range(M):
            if b != a:
                others &= sim[b] < eps[b]
        z = np.log(sim[a] / (q * eps[a]))
        band[a] = np.exp(-z ** 2 / (2 * width ** 2)) * others
    if band.sum() == 0:            # simulator says nothing is safe: fall back
        band = uni.copy()
    band = band / band.sum()
    if kind == "band":
        return band
    if kind == "mix":
        return (1 - mix) * uni + mix * band
    raise ValueError(f"unknown weight kind {kind!r}")


def edge_probability(sc, q=0.5, sigma=1.0, n_draws=400, seed=0, q_spread=(1.0, 1.2, 1.4)):
    """P(each (mode, setting) is a minimal element of the target {all rates <=
    q' eps}) under logit shifts ~ N(0, sigma^2) of the simulator, per mode,
    averaged over q' in q * q_spread. Averaging over slightly larger targets
    also puts weight just on the risky side of the edge, where a certificate
    (if the setting is still safe) covers the edge too. Normalized to sum to
    1 (falls back to uniform if no draw has a target)."""
    modes = sc.modes
    M = len(modes)
    shape = sc.truth[modes[0]].shape
    rng = np.random.default_rng(seed)
    logit = np.stack([np.log(np.clip(sc.sim[m], 1e-9, 1 - 1e-9))
                      - np.log1p(-np.clip(sc.sim[m], 1e-9, 1 - 1e-9)) for m in modes])
    eps = np.array([sc.eps[m] for m in modes])[:, None, None]
    dirs = [sc.directions[m] for m in modes]
    hits = np.zeros((M,) + shape)
    for _ in range(n_draws):
        shift = rng.normal(0.0, sigma, size=(M, 1, 1))
        p = 1.0 / (1.0 + np.exp(-(logit + shift)))
        for f in q_spread:
            T = (p <= f * q * eps).all(axis=0)
            if not T.any():
                continue
            for a in range(M):
                count = cone_sum(T.astype(float), dirs[a])
                hits[a] += T & (count < 1.5)
    if hits.sum() == 0:
        return np.full((M,) + shape, 1.0 / (M * np.prod(shape)))
    return hits / hits.sum()


# -- the certifier ------------------------------------------------------------

class ConeCertifier:
    def __init__(self, scenario, alpha=0.05, rule="cone", weights="ensemble", weight_mix=0.5,
                 weight_q=0.5, weight_sigma=1.0, strategy="hedge", prior_weight=10.0, use_sim_prior=True,
                 cap=0.8, batch=24, alloc="edge", target_q=0.5, futility_n=60,
                 smooth=False, oracle=False, optimism=1.0, coupons0=0, rng=None):
        if rule not in ("cone", "max", "none"):
            raise ValueError("rule must be 'cone', 'max' or 'none'")
        if alloc not in ("edge", "frontier"):
            raise ValueError("alloc must be 'edge' or 'frontier'")
        self.sc, self.alpha, self.rule, self.alloc = scenario, alpha, rule, alloc
        self.batch, self.target_q, self.futility_n = batch, target_q, futility_n
        self.smooth, self.oracle = smooth, oracle
        # Allocation scores use an optimistic rate, p_hat - optimism * se, so
        # settings that have not been explored look promising and a heavily
        # sampled setting just below eps (a "sink") loses priority. Standard
        # optimism in the face of uncertainty; allocation only.
        self.optimism = optimism
        self.rng = np.random.default_rng() if rng is None else rng

        self.modes = scenario.modes
        self.M = len(self.modes)
        self.shape = scenario.truth[self.modes[0]].shape
        self.N = int(np.prod(self.shape))
        self.dirs = [scenario.directions[m] for m in self.modes]
        self.eps = np.stack([np.full(self.N, scenario.eps[m]) for m in self.modes])
        self.truth = np.stack([scenario.truth[m].ravel() for m in self.modes])
        sim = np.stack([scenario.sim[m].ravel() for m in self.modes])
        self.prior = sim if use_sim_prior else self.eps.copy()

        if isinstance(weights, np.ndarray):
            w = weights
        else:
            w = make_weights(scenario, weights, mix=weight_mix, q=weight_q, sigma=weight_sigma)
        assert w.sum() <= 1 + 1e-9 and (w >= 0).all()
        self.w = w.reshape(self.M, self.N)

        self.ep = BettingEProcess(self.eps, shape=(self.M, self.N), strategy=strategy,
                                  prior_mean=self.prior, prior_weight=prior_weight, cap=cap)
        self.certified = np.zeros((self.M, self.N), dtype=bool)
        self.hopeless = np.zeros((self.M, self.N), dtype=bool)
        self.n_at = np.zeros(self.N, dtype=int)
        # coupons0: coupons already spent before testing (e.g. a pilot plate).
        self.coupons = coupons0
        self.history = []
        self.log_thresh = -np.log(alpha)

    # -- testing --------------------------------------------------------------

    def _grid(self, v):
        return v.reshape(self.shape)

    def evidence(self):
        """S (M, N): the statistic compared with 1/alpha for each (mode, setting)."""
        wk = self.w * np.exp(np.minimum(self.ep.log_wealth(), 700.0))
        if self.rule == "none":
            return wk
        out = np.empty_like(wk)
        for m in range(self.M):
            g = self._grid(wk[m])
            if self.rule == "cone":
                out[m] = cone_sum(g, self.dirs[m]).ravel()
            else:   # "max": Bonferroni + spreading
                out[m] = _cone_max(g, self.dirs[m]).ravel()
        return out

    def _check(self):
        self.certified |= self.evidence() >= 1.0 / self.alpha

    # -- allocation -----------------------------------------------------------

    def _estimates(self):
        if self.oracle:
            return self.truth
        w = self.ep.n + self.ep.prior_weight
        p = (self.ep.s1 + self.ep.prior_weight * self.prior) / w
        if not self.smooth:
            return p
        out = np.empty_like(p)
        for m in range(self.M):
            d_p, d_v = self.dirs[m]
            out[m] = _isotonic_2d(self._grid(p[m]), self._grid(w[m]), -d_p, -d_v).ravel()
        return out

    def _need(self):
        """Log-wealth still missing at each (m, x) for x to certify itself,
        given the evidence already in its cone."""
        S = self.evidence()
        own = self.w * np.exp(np.minimum(self.ep.log_wealth(), 700.0))
        rest = S - own
        with np.errstate(divide="ignore", invalid="ignore"):
            k_req = (1.0 / self.alpha - rest) / self.w
            need = np.log(np.maximum(k_req, 1e-300)) - self.ep.log_wealth()
        need = np.where(self.w > 0, np.maximum(need, 0.0), np.inf)
        return need

    def _optimistic(self, p_hat):
        if self.oracle or self.optimism <= 0:
            return p_hat
        w = self.ep.n + self.ep.prior_weight
        se = np.sqrt(np.maximum(p_hat * (1 - p_hat), self.eps * (1 - self.eps) / 4) / w)
        return np.clip(p_hat - self.optimism * se, 1e-6, 1.0)

    def choose_plate(self):
        p_hat = self._estimates()
        if self.alloc == "frontier":
            return self._frontier_plate(self._optimistic(p_hat))
        plate = self._edge_plate(p_hat)
        return plate if plate else self._recheck_plate(p_hat)

    def _fill(self, remaining):
        plate = []
        for x, r in sorted(remaining.items(), key=lambda kv: kv[1]):
            plate += [x] * int(min(np.ceil(r), self.batch - len(plate)))
            if len(plate) >= self.batch:
                break
        if not plate:
            return []
        reps = int(np.ceil(self.batch / len(plate)))
        return list(np.tile(plate, reps)[: self.batch])

    def _edge_plate(self, p_hat):
        target = (p_hat < self.target_q * self.eps).all(axis=0)
        need = self._need()
        rate = _kl_vec(p_hat, self.eps)
        remaining = {}
        for m in range(self.M):
            u = target & ~self.certified[m] & ~self.hopeless[m]
            if not u.any():
                continue
            if self.rule == "none":
                minimal = u
            else:
                count = cone_sum(self._grid(u.astype(float)), self.dirs[m]).ravel()
                minimal = u & (count < 1.5)        # nothing else of u is riskier
            for x in np.flatnonzero(minimal & (rate[m] > 0) & np.isfinite(need[m])):
                r = need[m, x] / rate[m, x] + 1.0
                remaining[x] = max(remaining.get(x, 0.0), r)
        return self._fill(remaining)

    def _recheck_plate(self, p_hat, per_point=4):
        w = self.ep.n + self.ep.prior_weight
        lcb = (p_hat - 2.0 * np.sqrt(p_hat * (1 - p_hat) / w)) / self.eps
        open_ = ~self.certified & ~self.hopeless & (self.w > 0)
        risk = np.where(open_, lcb, np.inf).max(axis=0, initial=-np.inf, where=open_)
        cand = np.flatnonzero(open_.any(axis=0))
        if len(cand) == 0:
            return []
        order = cand[np.argsort(risk[cand], kind="stable")][: max(1, self.batch // per_point)]
        reps = int(np.ceil(self.batch / len(order)))
        return list(np.tile(np.repeat(order, per_point), reps)[: self.batch])

    def _frontier_plate(self, p_hat):
        looks_safe = (p_hat < self.target_q * self.eps).all(axis=0)
        need = self._need()
        rate = _kl_vec(p_hat, self.eps)
        score = np.zeros(self.N)
        for m in range(self.M):
            tgt = (looks_safe & ~self.certified[m]).astype(float)
            if self.rule == "none":
                gain = tgt
            else:
                gain = cone_sum(self._grid(tgt), self.dirs[m], riskier=False).ravel()
            ok = ~self.certified[m] & ~self.hopeless[m] & (rate[m] > 0) & np.isfinite(need[m])
            score += np.where(ok, gain / (need[m] / np.maximum(rate[m], 1e-4) + 1.0), 0.0)
        cand = np.flatnonzero(score > 0)
        if len(cand) == 0:
            return self._recheck_plate(p_hat)
        order = cand[np.argsort(-score[cand], kind="stable")][: self.batch]
        reps = int(np.ceil(self.batch / len(order)))
        return list(np.tile(order, reps)[: self.batch])

    # -- one build plate ----------------------------------------------------------

    def run_plate(self):
        plate = self.choose_plate()
        if not plate:
            return False
        for x in plate:
            y = (self.rng.random(self.M) < self.truth[:, x]).astype(float)
            self.ep.update_at((slice(None), x), y)
            self.n_at[x] += 1
            self.coupons += 1
        # Checking once per plate is valid (anytime validity covers any times).
        self._check()
        self._futility()
        self._record()
        return True

    def _futility(self):
        """Mark (mode, setting) pairs that are confidently unsafe so allocation
        stops spending on them. Never certifies anything."""
        n = self.ep.n
        p = np.divide(self.ep.s1, n, out=np.zeros_like(self.ep.s1), where=n > 0)
        se = np.sqrt(np.maximum(p * (1 - p), 1.0 / np.maximum(n, 1)) / np.maximum(n, 1))
        self.hopeless |= (n >= self.futility_n) & (p - 2 * se > self.eps)

    # -- results --------------------------------------------------------------------

    def window(self):
        return self.certified.all(axis=0).reshape(self.shape)

    def _record(self):
        win = self.window().ravel()
        bad = (self.truth >= self.eps).any(axis=0)
        self.history.append(dict(coupons=self.coupons, area=int(win.sum()),
                                 errors=int((win & bad).sum())))

    def run(self, budget):
        while self.coupons < budget and self.run_plate():
            pass
        return self.history

    def run_until(self, target, budget):
        """Run until every setting in the boolean mask `target` is certified
        for every mode, or the budget runs out. Returns coupons used or inf."""
        target = np.asarray(target, dtype=bool).ravel()
        while self.coupons < budget and self.run_plate():
            if (self.window().ravel() >= target).all():
                return self.coupons
        return self.coupons if (self.window().ravel() >= target).all() else np.inf


def _cone_max(v, direction):
    """Max of v over each setting's riskier cone (Bonferroni + spreading)."""
    s_p, s_v = direction
    z = v[::s_p, ::s_v]
    z = np.maximum.accumulate(np.maximum.accumulate(z, axis=0), axis=1)
    return z[::s_p, ::s_v]
