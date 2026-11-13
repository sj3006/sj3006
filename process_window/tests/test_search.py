import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.dose import make_dose_scenario  # noqa: E402
from pwcert.search import SearchCertifier  # noqa: E402
from pwcert.synthetic import MODES, Scenario, make_scenario  # noqa: E402


@pytest.mark.parametrize("warm", ["both", "sim", False])
def test_search_stops_complete_and_valid(warm):
    sc = make_scenario(8, 8, simulator="biased")
    T = np.all([sc.truth[m] <= 0.5 * sc.eps[m] for m in sc.modes], axis=0)
    c = SearchCertifier(sc, q=0.5, batch=16, warm_start=warm, rng=np.random.default_rng(0))
    while c.coupons < 200_000 and c.run_plate():
        pass
    assert c.coupons < 200_000                      # stopped on its own
    assert (c.window() >= T).all()                  # complete
    assert not (c.window() & ~sc.true_window()).any()


def test_search_two_modes():
    sc = make_dose_scenario(8, 8)
    c = SearchCertifier(sc, q=0.5, batch=16, rng=np.random.default_rng(1))
    while c.coupons < 200_000 and c.run_plate():
        pass
    assert not (c.window() & ~sc.true_window()).any()


def test_search_worst_case_null():
    base = make_scenario(6, 6, simulator="adversarial")
    truth = {m: np.full((6, 6), 0.05) for m in MODES}
    sc = Scenario(base.power, base.speed, base.eps, truth, base.sim)
    errors = 0
    for r in range(10):
        c = SearchCertifier(sc, q=0.5, batch=12, rng=np.random.default_rng(r))
        while c.coupons < 20_000 and c.run_plate():
            pass
        errors += int(c.certified.any())
    assert errors <= 2
