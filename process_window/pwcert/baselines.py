"""Baselines that represent current practice.

grid_doe: build the same number of coupons at every grid setting (a full
factorial DoE), then call a setting safe for a mode when the exact
(Clopper-Pearson) one-sided upper confidence bound on its defect rate is
below eps. With correction="bonferroni" each test runs at level
alpha / (M * N), which controls the family-wise error rate. With
correction="none" each test runs at level alpha, which is what is often done
in practice and does NOT control the error rate over the whole window.

The Clopper-Pearson decision needs no interval: the upper bound is below eps
exactly when P(Bin(n, eps) <= k) < level, where k is the observed number of
defects in n coupons.
"""

from math import exp, lgamma, log

import numpy as np


def binom_cdf(k, n, p):
    """P(Bin(n, p) <= k), computed in log space. Scalars only."""
    if k >= n:
        return 1.0
    lp, lq = log(p), log1m(p)
    terms = [lgamma(n + 1) - lgamma(i + 1) - lgamma(n - i + 1) + i * lp + (n - i) * lq
             for i in range(int(k) + 1)]
    m = max(terms)
    return min(1.0, exp(m) * sum(exp(t - m) for t in terms))


def log1m(p):
    return np.log1p(-p)


def cp_certifies(k, n, eps, level):
    """True where the one-sided Clopper-Pearson upper bound is below eps."""
    k = np.asarray(k)
    out = np.zeros(k.shape, dtype=bool)
    for idx in np.ndindex(k.shape):
        out[idx] = binom_cdf(int(k[idx]), int(n), eps) < level
    return out


def grid_doe(scenario, n_per_point, alpha=0.05, correction="bonferroni", rng=None):
    """One full-factorial DoE with n_per_point coupons at every setting.

    Returns (window mask, coupons used, number of truly unsafe settings in
    the certified window).
    """
    rng = np.random.default_rng() if rng is None else rng
    modes = scenario.modes
    truth = np.stack([scenario.truth[m] for m in modes])           # (M, nP, nV)
    eps = np.array([scenario.eps[m] for m in modes])[:, None, None]
    n_tests = truth.size
    level = alpha / n_tests if correction == "bonferroni" else alpha
    k = rng.binomial(n_per_point, truth)
    cert = np.stack([cp_certifies(k[m], n_per_point, float(eps[m, 0, 0]), level)
                     for m in range(len(modes))])
    window = cert.all(axis=0)
    unsafe = (truth >= eps).any(axis=0)
    return window, n_per_point * truth[0].size, int((window & unsafe).sum())


def grid_fst(scenario, n_per_point, alpha=0.05, axis=None, rng=None):
    """Full grid + fixed-sequence testing along the ordering (Learn-then-Test
    style, Angelopoulos et al.): the strongest standard non-adaptive method
    that uses monotonicity.

    Every setting gets n_per_point trials. For each mode, the grid is split
    into chains along `axis` (one chain per index of the other axis), each
    ordered safest to riskiest for that mode. Each chain is tested in order
    with exact binomial p-values at level alpha / (M * number of chains),
    stopping at the first setting that fails. Under monotonicity the true
    nulls on a chain form its riskiest end, so fixed-sequence testing
    controls the chain's error rate; a union bound covers all chains and
    modes. Certificates then spread to every safer setting (correct whenever
    the certificate is). axis=None tries both axes' chain counts and uses
    the one with fewer chains (larger per-chain level).

    Returns (window mask, coupons used, number of truly unsafe settings in
    the certified window).
    """
    from .cone import cone_sum
    rng = np.random.default_rng() if rng is None else rng
    modes = scenario.modes
    truth = np.stack([scenario.truth[m] for m in modes])
    shape = truth.shape[1:]
    if axis is None:
        axis = 0 if shape[1] <= shape[0] else 1     # chains run along `axis`
    n_chains = shape[1 - axis]
    level = alpha / (len(modes) * n_chains)
    k = rng.binomial(n_per_point, truth)
    cert = np.zeros(truth.shape, dtype=bool)
    for m, mode in enumerate(modes):
        eps = float(scenario.eps[mode])
        d = scenario.directions[mode]
        km = k[m] if axis == 0 else k[m].T
        cm = np.zeros(km.shape, dtype=bool)
        step = d[axis]                            # +1: safer at higher index
        order = np.arange(km.shape[0])[::-1] if step > 0 else np.arange(km.shape[0])
        for c in range(km.shape[1]):
            for i in order:                       # safest first
                if binom_cdf(int(km[i, c]), int(n_per_point), eps) < level:
                    cm[i, c] = True
                else:
                    break
        cm = cm if axis == 0 else cm.T
        # spread: everything at least as safe as a certified setting
        cert[m] = cone_sum(cm.astype(float), d) > 0.5
    window = cert.all(axis=0)
    eps_arr = np.array([scenario.eps[m] for m in modes])[:, None, None]
    unsafe = (truth >= eps_arr).any(axis=0)
    return window, n_per_point * truth[0].size, int((window & unsafe).sum())
