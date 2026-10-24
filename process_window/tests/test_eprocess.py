import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.eprocess import BettingEProcess, coupons_to_certify  # noqa: E402


@pytest.mark.parametrize("strategy", ["fixed", "agrapa", "mixture", "hedge"])
def test_wealth_never_hits_zero(strategy):
    ep = BettingEProcess(0.05, shape=1, strategy=strategy)
    for _ in range(200):
        ep.update(np.array([1.0]))      # all defects: worst case
    assert np.isfinite(ep.log_wealth()).all()


def test_update_at_matches_update():
    rng = np.random.default_rng(0)
    prior = rng.random((3, 5)) * 0.1
    a = BettingEProcess(0.05, shape=(3, 5), prior_mean=prior, prior_weight=5)
    b = BettingEProcess(0.05, shape=(3, 5), prior_mean=prior, prior_weight=5)
    for _ in range(50):
        x = rng.integers(5)
        y = (rng.random(3) < 0.04).astype(float)
        mask = np.zeros((3, 5), dtype=bool)
        mask[:, x] = True
        yy = np.zeros((3, 5))
        yy[:, x] = y
        a.update(yy, mask=mask)
        b.update_at((slice(None), x), y)
    np.testing.assert_allclose(a.log_wealth(), b.log_wealth())


@pytest.mark.parametrize("strategy,prior", [("hedge", None), ("agrapa", 0.001), ("fixed", None)])
def test_false_certification_rate_at_most_alpha(strategy, prior):
    """At the worst-case null p = eps, the error rate must not exceed alpha."""
    alpha, eps, reps = 0.1, 0.05, 3000
    stop = coupons_to_certify(eps, eps, alpha, np.random.default_rng(1), strategy=strategy,
                              prior_mean=prior, prior_weight=10, max_n=600, reps=reps)
    rate = np.isfinite(stop).mean()
    assert rate <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / reps)


def test_good_setting_gets_certified():
    stop = coupons_to_certify(0.0, 0.05, 0.05, np.random.default_rng(2), reps=50)
    assert np.isfinite(stop).all()
    # Can't beat the success-run floor ln(alpha)/ln(1-eps) ~ 58.4.
    assert stop.min() >= 58
