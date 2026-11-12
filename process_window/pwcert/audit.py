"""Audit: a falsification test for the monotonicity assumption.

The cone rule certifies settings it never tested directly, by spreading from
riskier certified settings. That is only valid if Assumption A holds. If it
fails somewhere (say a pocket of spatter defects inside an otherwise good
region), spreading can certify unsafe settings.

The audit spends an extra, separate budget on settings that were certified
without being tested much, and at each runs the *opposite* betting test:

    K_audit = average over a fixed grid of bets lam of prod (1 + lam (Y - eps)),
    with every lam in (0, 1/eps),

which is a nonnegative supermartingale when the rate is at most eps (the
setting is safe). A mixture over bets matters: a single large bet has
negative drift even at clearly unsafe rates (lam = 10 at eps = 5% loses
wealth at a true rate of 15%; the best bet there is about 2).

If it reaches 1 / alpha_audit (Bonferroni over audited pairs), the setting
is confidently unsafe although certified, so either
Assumption A fails there or the certification was one of the alpha-rare
false ones. Under Assumption A and correct certifications, P(any flag) <=
alpha_audit.
"""

import numpy as np


AUDIT_FRACTIONS = np.array([0.025, 0.05, 0.1, 0.2, 0.4])   # bets as fractions of 1/eps


def audit(cert, n_settings, per_setting, alpha_audit=0.05, rng=None):
    """Audit a finished ConeCertifier.

    Picks n_settings certified settings at random among those with the fewest
    test coupons, builds per_setting fresh coupons at each, and runs a
    defect-betting e-process for every mode. Returns (flagged (mode, setting)
    pairs, audit coupons used).
    """
    rng = np.random.default_rng() if rng is None else rng
    win = cert.window().ravel()
    cand = np.flatnonzero(win)
    if len(cand) == 0:
        return [], 0
    order = cand[np.lexsort((rng.random(len(cand)), cert.n_at[cand]))]
    chosen = order[:n_settings]
    level = -np.log(alpha_audit / (len(chosen) * cert.M))
    flagged = []
    for x in chosen:
        eps = cert.eps[:, x][:, None]
        lam = AUDIT_FRACTIONS[None, :] / eps                      # (M, bets)
        logk = np.zeros(lam.shape)
        mix = np.zeros(cert.M)
        for _ in range(per_setting):
            y = (rng.random(cert.M) < cert.truth[:, x]).astype(float)[:, None]
            logk += np.log1p(lam * (y - eps))
            top = logk.max(axis=1, keepdims=True)
            mix = (top + np.log(np.mean(np.exp(logk - top), axis=1, keepdims=True))).ravel()
            if (mix >= level).any():
                break
        flagged += [(m, int(x)) for m in np.flatnonzero(mix >= level)]
    return flagged, len(chosen) * per_setting
