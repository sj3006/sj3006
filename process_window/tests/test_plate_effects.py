import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from plate_effects import PlateCertifier, plate_rates, run_single  # noqa: E402
from pwcert.synthetic import make_scenario  # noqa: E402


def test_plate_rates_have_the_right_mean_and_correlation():
    rng = np.random.default_rng(0)
    p, rho = 0.1, 0.2
    pb = plate_rates(p, rho, 200_000, rng)
    assert abs(pb.mean() - p) < 2e-3
    # beta-binomial: Var(p_b) = rho * p * (1 - p)
    assert abs(pb.var() / (p * (1 - p)) - rho) < 0.01
    assert np.all(plate_rates(p, 0.0, 10, rng) == p)


def test_per_plate_analysis_is_valid_at_the_tolerance_under_strong_correlation():
    hit, _ = run_single(0.10, 0.2, 24, "plate", 400, 2400, np.random.default_rng(1))
    assert hit.mean() <= 0.05


def test_plate_aware_rule_puts_at_most_one_trial_per_setting_on_a_plate():
    sc = make_scenario(8, 8, simulator="good")
    c = PlateCertifier(sc, rule="cone", weights="ensemble", alloc="edge", target_q=0.7, batch=16,
                       rng=np.random.default_rng(0), rho=0.1, design="spread")
    for _ in range(30):
        plate = c.choose_plate()
        assert len(plate) == len(set(plate)) <= 16
        if not c.run_plate():
            break
