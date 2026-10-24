import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.certify import WindowCertifier  # noqa: E402
from pwcert.physics import (check_monotone_directions, defect_rates,  # noqa: E402
                            make_physics_scenario, melt_pool)


def test_melt_pool_grows_with_power_and_shrinks_with_speed():
    w1, _, _ = melt_pool(150.0, 0.8)
    w2, _, _ = melt_pool(250.0, 0.8)
    w3, _, _ = melt_pool(250.0, 1.6)
    assert w2 > w1 > 0 and w3 < w2


def test_physics_rates_are_monotone():
    r = defect_rates(np.linspace(80, 400, 10), np.linspace(300, 2400, 10))
    for mode, (sp, sv, frac) in check_monotone_directions(r).items():
        assert frac == 1.0, mode
    d = check_monotone_directions(r)
    assert d["lof"][:2] == (-1, 1)        # less LoF with power, more with speed
    assert d["keyhole"][:2] == (1, -1)


def test_physics_scenario_certifies_only_safe_settings():
    sc = make_physics_scenario(10, 10, simulator="biased")
    wc = WindowCertifier(sc, structure="hybrid", alloc="frontier", rng=np.random.default_rng(0))
    wc.run(budget=6000)
    assert not (wc.window() & ~sc.true_window()).any()
