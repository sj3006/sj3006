"""Second application: certifying a therapeutic window for a two-drug combination.

Setting: a combination screen (for example, cell-line or animal studies) over
a grid of dose pairs (dose A x dose B). Each replicate ("coupon") at a dose
pair gives two binary outcomes:

- toxicity: an adverse event. Its rate increases with BOTH doses, so it is
  safer at lower doses: safer direction (-1, -1).
- non-response: no therapeutic response. Its rate decreases with both doses,
  so it is safer at higher doses: safer direction (+1, +1).

The therapeutic window is the set of dose pairs with toxicity rate below
eps_tox and non-response rate below eps_nr. Same structure as a process
window: a partial order per failure mode, opposing directions.

Ground truth: logistic dose-response surfaces in log dose with an
interaction term (synergy / antagonism). Simulator: Bliss independence,
which predicts a combination from single-agent curves alone and ignores the
interaction. This is the standard textbook prediction, so it is a realistic
misspecified simulator.

Bliss independence for a "probability of effect" with single-agent
probabilities pA, pB is 1 - (1 - pA)(1 - pB). Toxicity combines that way;
non-response is the complement of response, so it is the product of the
single-agent non-response rates.
"""

import numpy as np

from .synthetic import Scenario

DOSE_MODES = ("toxicity", "nonresponse")
DOSE_DIRECTIONS = {"toxicity": (-1, -1), "nonresponse": (+1, +1)}


def _sig(z):
    return 1.0 / (1.0 + np.exp(-z))


def single_agent(dose, ec50, slope):
    """Probability of effect for one agent (log-logistic)."""
    return _sig(slope * (np.log(dose) - np.log(ec50)))


def make_dose_scenario(n_a=12, n_b=12, eps_tox=0.30, eps_nr=0.50, simulator="bliss",
                       synergy_resp=1.2, synergy_tox=0.6, dose_range=(0.05, 20.0)):
    """Build a dose-combination scenario.

    simulator: "bliss" (single-agent curves + independence, ignores the
    interaction), "good" (true model with interactions shrunk by half),
    "none" (flat prior at eps) or "adversarial" (says everything is safe).

    synergy_resp > 0 makes the drugs better together than Bliss predicts
    (more response); synergy_tox > 0 makes them more toxic together.
    """
    a = np.geomspace(*dose_range, n_a)
    b = np.geomspace(*dose_range, n_b)
    A, B = np.meshgrid(a, b, indexing="ij")

    def truth_rates(s_resp, s_tox):
        # Single-agent curves.
        tox_a, tox_b = single_agent(A, 8.0, 1.6), single_agent(B, 12.0, 1.4)
        resp_a, resp_b = single_agent(A, 1.5, 1.2), single_agent(B, 2.5, 1.0)
        # Bliss combination on the logit scale, plus an interaction that grows
        # with both doses (zero when either dose is tiny).
        inter = np.log1p(A) * np.log1p(B) / np.log1p(dose_range[1]) ** 2 * 4.0
        tox = 1 - (1 - tox_a) * (1 - tox_b)
        resp = 1 - (1 - resp_a) * (1 - resp_b)
        tox = _sig(np.log(tox / (1 - tox)) + s_tox * inter)
        resp = _sig(np.log(resp / (1 - resp)) + s_resp * inter)
        return {"toxicity": np.clip(tox, 1e-4, 1 - 1e-4),
                "nonresponse": np.clip(1 - resp, 1e-4, 1 - 1e-4)}

    truth = truth_rates(synergy_resp, synergy_tox)
    eps = {"toxicity": eps_tox, "nonresponse": eps_nr}
    if simulator == "bliss":
        sim = truth_rates(0.0, 0.0)
    elif simulator == "good":
        sim = truth_rates(synergy_resp / 2, synergy_tox / 2)
    elif simulator == "none":
        sim = {m: np.full_like(truth[m], eps[m]) for m in DOSE_MODES}
    elif simulator == "adversarial":
        sim = {m: np.full_like(truth[m], 0.01) for m in DOSE_MODES}
    else:
        raise ValueError(f"unknown simulator {simulator!r}")
    return Scenario(a, b, eps, truth, sim, name=f"dose/{simulator}",
                    directions=dict(DOSE_DIRECTIONS))
