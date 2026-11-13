import numpy as np

from pwcert.bounds import cut_constants, kl_bern, ordered_lower_bound, unordered_lower_bound
from pwcert.synthetic import make_scenario


def test_cut_constants_match_closed_form():
    a = b = 0.05
    c = cut_constants(a, b)
    # by symmetry the w = 1/2 cut is at pi = 1/2: (kl(1/2, 1-b) + kl(1/2, a)) / 2
    assert np.isclose(c[0.5], 0.5 * np.log(1 / (4 * a * (1 - a))), atol=1e-3)
    # w -> 0 recovers the "unsafe" constraint A >= kl(alpha, 1 - beta)
    assert np.isclose(c[0.01] / 0.01, kl_bern(a, 1 - b), rtol=0.02)


def test_bounds_are_ordered():
    for n in (8, 16):
        sc = make_scenario(n, n, simulator="good")
        b = ordered_lower_bound(sc, 0.5)
        assert b["lb_target_only"] <= b["lb"] + 1e-6
        assert b["lb"] <= unordered_lower_bound(sc, 0.5)
