import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments"))
from am_monotone_check import check_study, formula_like  # noqa: E402


def _grid(noise, seed=0):
    rng = np.random.default_rng(seed)
    P, V = np.meshgrid([100, 150, 200, 250, 300], [400, 600, 800, 1000], indexing="ij")
    P, V = P.ravel().astype(float), V.ravel().astype(float)
    depth = 50 * (P / 100) ** 1.4 * (V / 400) ** -1.0 * np.exp(noise * rng.standard_normal(P.size))
    width = 90 * (P / 100) ** 0.5 * (V / 400) ** -0.4 * np.exp(noise * rng.standard_normal(P.size))
    return pd.DataFrame({"Power": P, "Velocity": V, "depth of meltpool": depth, "width of melt pool": width})


def test_noiseless_monotone_grid_has_no_reversals_and_right_exponents():
    t = _grid(0.0)
    r = check_study(t, "depth of meltpool")
    assert r["settings"] == 20 and r["pairs"] == 5 * 3 + 4 * 4
    assert r["reversed"] == 0 and r["reversed_2se"] == 0
    assert abs(r["exp_power"] - 1.4) < 1e-6 and abs(r["exp_speed"] + 1.0) < 1e-6


def test_formula_like_flags_exact_power_laws_and_depth_equal_width():
    t = _grid(0.0)
    assert formula_like(t, "depth of meltpool")
    t2 = _grid(0.2)
    assert not formula_like(t2, "depth of meltpool")
    t2["width of melt pool"] = t2["depth of meltpool"]
    assert formula_like(t2, "width of melt pool")


def test_a_planted_large_reversal_is_counted_beyond_two_se():
    t = _grid(0.02, seed=1)
    i = t.index[(t.Power == 200) & (t.Velocity == 600)][0]
    t.loc[i, "depth of meltpool"] *= 0.3          # a deep dip inside the grid
    r = check_study(t, "depth of meltpool")
    assert r["reversed"] >= 2 and r["reversed_2se"] >= 1
