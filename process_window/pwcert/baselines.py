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

from .synthetic import MODES


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
    truth = np.stack([scenario.truth[m] for m in MODES])           # (M, nP, nV)
    eps = np.array([scenario.eps[m] for m in MODES])[:, None, None]
    n_tests = truth.size
    level = alpha / n_tests if correction == "bonferroni" else alpha
    k = rng.binomial(n_per_point, truth)
    cert = np.stack([cp_certifies(k[m], n_per_point, float(eps[m, 0, 0]), level)
                     for m in range(len(MODES))])
    window = cert.all(axis=0)
    unsafe = (truth >= eps).any(axis=0)
    return window, n_per_point * truth[0].size, int((window & unsafe).sum())
