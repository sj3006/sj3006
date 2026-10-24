import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.certify import WindowCertifier  # noqa: E402
from pwcert.synthetic import MODES, Scenario, make_scenario  # noqa: E402


def test_upset_is_the_safe_quadrant():
    wc = WindowCertifier(make_scenario(5, 5), rng=np.random.default_rng(0))
    m = MODES.index("lof")          # safer at higher power, lower speed
    up = wc._upset(m, wc._flat(2, 2)).reshape(5, 5)
    expected = np.zeros((5, 5), dtype=bool)
    expected[2:, :3] = True
    assert (up == expected).all()


@pytest.mark.parametrize("start", ["sim", "middle", "pilot"])
def test_chains_get_less_safe(start):
    """Theorem 1 needs every chain to walk toward riskier settings."""
    sc = make_scenario(8, 8)
    wc = WindowCertifier(sc, start=start, rng=np.random.default_rng(0))
    for m in range(wc.M):
        for chain in wc.chains[m]:
            rates = wc.truth[m, chain]
            assert np.all(np.diff(rates) >= -1e-12)


def test_spreading_never_certifies_unsafe_from_safe():
    """If z is truly safe, everything spread from it must be truly safe (Assumption A)."""
    sc = make_scenario(10, 10)
    wc = WindowCertifier(sc, rng=np.random.default_rng(0))
    for m in range(wc.M):
        for z in np.flatnonzero(wc.truth[m] < wc.eps[m]):
            assert np.all(wc.truth[m, wc._upset(m, z)] < wc.eps[m, 0])


def test_no_certification_when_everything_is_at_threshold():
    """Worst-case null: every certification would be an error. Over a few
    seeds, errors should be rare (the full estimate is experiment 2A)."""
    base = make_scenario(6, 6, simulator="adversarial")
    truth = {m: np.full((6, 6), 0.05) for m in MODES}
    sc = Scenario(base.power, base.speed, base.eps, truth, base.sim)
    errors = 0
    for r in range(10):
        wc = WindowCertifier(sc, rng=np.random.default_rng(r), batch=12)
        wc.run(budget=3000)
        errors += int(wc.certified.any())
    assert errors <= 2


def test_finds_part_of_the_window():
    sc = make_scenario(8, 8)
    wc = WindowCertifier(sc, rng=np.random.default_rng(3))
    wc.run(budget=6000)
    win = wc.window()
    assert win.sum() > 0
    assert not (win & ~sc.true_window()).any()


@pytest.mark.parametrize("structure", ["spread", "hybrid"])
def test_new_structures_respect_the_worst_case_null(structure):
    base = make_scenario(6, 6, simulator="adversarial")
    truth = {m: np.full((6, 6), 0.05) for m in MODES}
    sc = Scenario(base.power, base.speed, base.eps, truth, base.sim)
    errors = 0
    for r in range(10):
        wc = WindowCertifier(sc, structure=structure, alloc="frontier",
                             rng=np.random.default_rng(r), batch=12)
        wc.run(budget=3000)
        errors += int(wc.certified.any())
    assert errors <= 2


@pytest.mark.parametrize("structure", ["monotone", "spread", "hybrid"])
def test_frontier_allocation_finds_window_without_errors(structure):
    sc = make_scenario(8, 8)
    wc = WindowCertifier(sc, structure=structure, alloc="frontier", rng=np.random.default_rng(4))
    wc.run(budget=8000)
    win = wc.window()
    assert win.sum() > 0
    assert not (win & ~sc.true_window()).any()
