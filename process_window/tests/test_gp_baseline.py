import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.gp_baseline import GPLevelSet  # noqa: E402
from pwcert.synthetic import make_scenario  # noqa: E402


def test_monotone_closure_is_a_safer_closed_superset():
    """The closure keeps every certified setting and is closed under a step
    in the mode's safer direction; it adds nothing that is not safer than
    some certified setting."""
    sc = make_scenario(8, 9)
    g = GPLevelSet(sc, rng=np.random.default_rng(0), monotone=True)
    rng = np.random.default_rng(1)
    before = rng.random(g.certified.shape) < 0.05
    g.certified = before.copy()
    g._close()
    for m, mode in enumerate(sc.modes):
        c = g.certified[m].reshape(g.shape)
        b = before[m].reshape(g.shape)
        assert (c >= b).all()
        s_p, s_v = sc.directions[mode]
        for i in range(c.shape[0]):
            for j in range(c.shape[1]):
                safer_than_some = any(b[a, d] and (i - a) * s_p >= 0 and (j - d) * s_v >= 0
                                      for a in range(c.shape[0]) for d in range(c.shape[1]))
                assert c[i, j] == safer_than_some


def test_monotone_gp_runs():
    sc = make_scenario(8, 8)
    h = GPLevelSet(sc, beta=2.0, batch=16, rng=np.random.default_rng(0), monotone=True).run(2000)
    assert h[-1]["coupons"] >= 2000 and h[-1]["area"] > 0


def test_latin_hypercube_hits_distinct_strata():
    sc = make_scenario(12, 12)
    g = GPLevelSet(sc, rng=np.random.default_rng(3), acquisition="active_search")
    idx = g._latin_hypercube(6)
    r, c = np.unravel_index(idx, g.shape)
    assert len(set(r // 2)) == 6 and len(set(c // 2)) == 6     # one per stratum of 2 rows / 2 cols


def test_active_search_runs_and_starts_with_lhs():
    sc = make_scenario(8, 8)
    g = GPLevelSet(sc, beta=2.0, batch=16, rng=np.random.default_rng(0), acquisition="active_search")
    g.run_plate()
    assert (g.n > 0).sum() == 4          # first batch: 4 LHS settings x 4 trials
    h = g.run(2000)
    assert h[-1]["coupons"] >= 2000


def test_safe_expand_samples_only_inside_the_safe_set():
    """Every trial goes to the seed or to a setting certified before the batch."""
    sc = make_scenario(8, 8)
    g = GPLevelSet(sc, beta=2.0, batch=16, rng=np.random.default_rng(0), acquisition="safe_expand",
                   monotone=True)
    seed = g._seed()
    for _ in range(30):
        allowed = g.certified.all(axis=0).copy()
        allowed[seed] = True
        n_before = g.n.copy()
        g.run_plate()
        assert allowed[g.n > n_before].all()
