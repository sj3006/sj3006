import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.baselines import grid_doe  # noqa: E402
from pwcert.cone import ConeCertifier, _cone_max, cone_sum, edge_probability, make_weights  # noqa: E402
from pwcert.dose import make_dose_scenario  # noqa: E402
from pwcert.pilot import pilot_simulator  # noqa: E402
from pwcert.synthetic import MODES, Scenario, make_scenario  # noqa: E402


@pytest.mark.parametrize("d", [(1, 1), (1, -1), (-1, 1), (-1, -1)])
def test_cone_sums_match_brute_force(d):
    v = np.random.default_rng(0).random((5, 6))
    for riskier in (True, False):
        got = cone_sum(v, d, riskier=riskier)
        for i in range(5):
            for j in range(6):
                sgn = 1 if riskier else -1
                mask = np.array([[(a - i) * d[0] * sgn <= 0 and (b - j) * d[1] * sgn <= 0
                                  for b in range(6)] for a in range(5)])
                assert np.isclose(got[i, j], v[mask].sum())
                if riskier:
                    assert np.isclose(_cone_max(v, d)[i, j], v[mask].max())


@pytest.mark.parametrize("kind", ["uniform", "band", "mix", "ensemble"])
def test_weights_are_a_valid_budget(kind):
    w = make_weights(make_scenario(8, 8, simulator="biased"), kind)
    assert (w >= 0).all() and w.sum() <= 1 + 1e-9


def test_cone_rule_dominates_max_rule():
    """Same e-processes and weights: the cone rule certifies a superset."""
    sc = make_scenario(8, 8)
    a = ConeCertifier(sc, rule="cone", rng=np.random.default_rng(0))
    a.run(3000)
    b = ConeCertifier(sc, rule="max", rng=np.random.default_rng(0))
    b.ep, b.w = a.ep, a.w
    assert ((a.evidence() >= b.evidence() - 1e-12)).all()


@pytest.mark.parametrize("rule", ["cone", "max", "none"])
def test_worst_case_null(rule):
    base = make_scenario(6, 6, simulator="adversarial")
    truth = {m: np.full((6, 6), 0.05) for m in MODES}
    sc = Scenario(base.power, base.speed, base.eps, truth, base.sim)
    errors = 0
    for r in range(15):
        c = ConeCertifier(sc, rule=rule, alloc="frontier", target_q=1.0, batch=12,
                          rng=np.random.default_rng(r))
        c.run(3000)
        errors += int(c.certified.any())
    assert errors <= 3


@pytest.mark.parametrize("make", [lambda: make_scenario(10, 10, simulator="biased"),
                                  lambda: make_dose_scenario(10, 10)])
def test_certifies_only_safe_settings(make):
    sc = make()
    for alloc in ("edge", "frontier"):
        c = ConeCertifier(sc, alloc=alloc, rng=np.random.default_rng(1))
        c.run(6000)
        assert c.window().sum() > 0
        assert not (c.window() & ~sc.true_window()).any()


def test_edge_probability_is_normalized():
    p = edge_probability(make_scenario(8, 8), sigma=1.0, n_draws=50)
    assert np.isclose(p.sum(), 1.0) and (p >= 0).all()


def test_pilot_simulator_is_monotone_and_counted():
    sc = make_scenario(12, 12, simulator="none")
    ps, coupons = pilot_simulator(sc, np.random.default_rng(0), per_point=4, stride=2)
    assert coupons == 36 * 4
    from pwcert.physics import check_monotone_directions
    for m, (sp, sv, frac) in check_monotone_directions(ps.sim).items():
        assert frac == 1.0, m


def test_grid_doe_handles_two_modes():
    w, c, e = grid_doe(make_dose_scenario(6, 6), 100, rng=np.random.default_rng(0))
    assert w.shape == (6, 6) and c == 3600
