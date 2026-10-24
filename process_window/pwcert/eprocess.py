"""Betting e-processes for "this setting is safe" claims.

For one setting and one failure mode, each coupon gives an outcome Y in [0, 1]
(1 = defect, 0 = no defect; a bounded score also works). The unknown defect
rate is p = E[Y]. We want to certify p < eps, so the null hypothesis is

    H0: p >= eps   ("the setting is bad").

The gambler's wealth after t coupons is

    K_t = prod_{s <= t} (1 + lam_s * (eps - Y_s)),

where the bet lam_s >= 0 is chosen before Y_s is seen. Under H0,
E[1 + lam_s * (eps - Y_s) | past] = 1 + lam_s * (eps - p) <= 1, so K is a
nonnegative supermartingale and Ville's inequality gives
P(K_t >= 1/alpha for some t) <= alpha. That is the whole validity argument,
and it does not care how lam_s was chosen, so a simulator can choose it.

Keeping 1 + lam * (eps - Y) > 0 for Y = 1 requires lam < 1 / (1 - eps). We use
lam_max = cap / (1 - eps) with cap < 1, so one defect can cost at most a
factor (1 - cap) of the wealth.

All state is stored in arrays so many hypotheses (settings x modes) can be
updated at once. Everything is kept in log-wealth to avoid overflow.
"""

import numpy as np

STRATEGIES = ("fixed", "agrapa", "mixture", "hedge")

# Bets in the mixture, as fractions of lam_max. Uniform weights, fixed in
# advance, so the average is itself an e-process.
MIXTURE_FRACTIONS = np.array([0.05, 0.1, 0.2, 0.35, 0.5, 0.7, 0.85, 1.0])


class BettingEProcess:
    """A batch of independent betting e-processes for H0: E[Y] >= eps.

    Parameters
    ----------
    eps : float or array
        Defect-rate threshold for each hypothesis.
    shape : int or tuple
        Number (shape) of hypotheses tracked together.
    strategy : {"fixed", "agrapa", "mixture", "hedge"}
        How bets are chosen.
        - "fixed": constant bet lam_fixed (as a fraction of lam_max).
        - "agrapa": plug-in bet lam = E[X] / E[X^2] with X = eps - Y,
          estimated from past data plus a prior (Waudby-Smith & Ramdas).
          The prior is where the simulator enters.
        - "mixture": average of fixed-bet processes over MIXTURE_FRACTIONS.
          Ignores the simulator.
        - "hedge": average of "agrapa" and "mixture". Never worse than
          half of the better of the two, so a bad simulator costs at most
          a factor 2 in wealth relative to the mixture.
    prior_mean : float or array, optional
        Prior guess of the defect rate (e.g. the simulator's prediction).
        Defaults to eps, the neutral "no information" choice.
    prior_weight : float
        How many pseudo-coupons the prior is worth. Must be > 0.
    cap : float in (0, 1)
        lam_max = cap / (1 - eps).
    lam_fixed : float in (0, 1]
        Bet for the "fixed" strategy, as a fraction of lam_max.
    """

    def __init__(self, eps, shape=1, strategy="hedge", prior_mean=None,
                 prior_weight=1.0, cap=0.8, lam_fixed=1.0):
        if strategy not in STRATEGIES:
            raise ValueError(f"strategy must be one of {STRATEGIES}")
        if not 0.0 < cap < 1.0:
            raise ValueError("cap must be in (0, 1)")
        if prior_weight <= 0:
            raise ValueError("prior_weight must be > 0")
        self.shape = (shape,) if np.isscalar(shape) else tuple(shape)
        self.eps = np.broadcast_to(np.asarray(eps, dtype=float), self.shape).copy()
        self.strategy = strategy
        pm = self.eps if prior_mean is None else prior_mean
        self.prior_mean = np.clip(np.broadcast_to(np.asarray(pm, dtype=float),
                                                  self.shape).copy(), 0.0, 1.0)
        self.prior_weight = float(prior_weight)
        self.lam_max = cap / (1.0 - self.eps)
        self.lam_fixed = lam_fixed

        self.n = np.zeros(self.shape)
        self.s1 = np.zeros(self.shape)  # sum of Y
        self.s2 = np.zeros(self.shape)  # sum of Y^2
        self.log_k_agrapa = np.zeros(self.shape)
        self.log_k_fixed = np.zeros(self.shape)
        # One log-wealth per mixture component.
        self.log_k_mix = np.zeros(self.shape + (len(MIXTURE_FRACTIONS),))

    # -- bets -------------------------------------------------------------

    def agrapa_lambda(self):
        """Plug-in bet from prior + past data. Predictable by construction."""
        w = self.n + self.prior_weight
        mean = (self.s1 + self.prior_weight * self.prior_mean) / w
        # For a Bernoulli prior, E[Y^2] = E[Y], so the prior's second moment
        # is prior_mean.
        m2 = (self.s2 + self.prior_weight * self.prior_mean) / w
        var = np.maximum(m2 - mean ** 2, 1e-6)
        gap = self.eps - mean
        lam = gap / (var + gap ** 2)
        return np.clip(lam, 0.0, self.lam_max)

    # -- updates ------------------------------------------------------------

    def update(self, y, mask=None):
        """Feed one new outcome to each hypothesis where mask is True.

        y and mask broadcast to self.shape. Hypotheses outside the mask are
        left unchanged (they placed no bet this round).
        """
        y = np.broadcast_to(np.asarray(y, dtype=float), self.shape)
        if np.any((y < 0) | (y > 1)):
            raise ValueError("outcomes must lie in [0, 1]")
        mask = (np.ones(self.shape, dtype=bool) if mask is None
                else np.broadcast_to(np.asarray(mask, dtype=bool), self.shape))
        x = self.eps - y

        lam = self.agrapa_lambda()
        self.log_k_agrapa = np.where(mask, self.log_k_agrapa + np.log1p(lam * x),
                                     self.log_k_agrapa)

        lam_f = self.lam_fixed * self.lam_max
        self.log_k_fixed = np.where(mask, self.log_k_fixed + np.log1p(lam_f * x),
                                    self.log_k_fixed)

        lams = self.lam_max[..., None] * MIXTURE_FRACTIONS
        self.log_k_mix = np.where(mask[..., None],
                                  self.log_k_mix + np.log1p(lams * x[..., None]),
                                  self.log_k_mix)

        self.n = self.n + mask
        self.s1 = self.s1 + mask * y
        self.s2 = self.s2 + mask * y ** 2

    def update_at(self, idx, y):
        """Feed outcomes y to the hypotheses at index idx only.

        Same arithmetic as update(), restricted to a slice, so a coupon at
        one setting does not touch the rest of the grid.
        """
        y = np.asarray(y, dtype=float)
        if np.any((y < 0) | (y > 1)):
            raise ValueError("outcomes must lie in [0, 1]")
        eps, lam_max = self.eps[idx], self.lam_max[idx]
        x = eps - y

        w = self.n[idx] + self.prior_weight
        pm = self.prior_mean[idx]
        mean = (self.s1[idx] + self.prior_weight * pm) / w
        m2 = (self.s2[idx] + self.prior_weight * pm) / w
        var = np.maximum(m2 - mean ** 2, 1e-6)
        gap = eps - mean
        lam = np.clip(gap / (var + gap ** 2), 0.0, lam_max)

        self.log_k_agrapa[idx] += np.log1p(lam * x)
        self.log_k_fixed[idx] += np.log1p(self.lam_fixed * lam_max * x)
        lams = lam_max[..., None] * MIXTURE_FRACTIONS
        self.log_k_mix[idx] += np.log1p(lams * x[..., None])
        self.n[idx] += 1
        self.s1[idx] += y
        self.s2[idx] += y ** 2

    # -- wealth -------------------------------------------------------------

    def log_wealth(self, idx=Ellipsis):
        if self.strategy == "fixed":
            return self.log_k_fixed[idx]
        if self.strategy == "agrapa":
            return self.log_k_agrapa[idx]
        log_mix = _log_mean_exp(self.log_k_mix[idx], axis=-1)
        if self.strategy == "mixture":
            return log_mix
        return _log_mean_exp(np.stack([self.log_k_agrapa[idx], log_mix], axis=-1), axis=-1)

    def rejects(self, alpha):
        """True where wealth has reached 1/alpha (alpha may be an array)."""
        return self.log_wealth() >= -np.log(alpha)


def _log_mean_exp(a, axis):
    m = np.max(a, axis=axis, keepdims=True)
    return np.squeeze(m, axis=axis) + np.log(np.mean(np.exp(a - m), axis=axis))


def coupons_to_certify(p, eps, alpha, rng, strategy="hedge", prior_mean=None,
                       prior_weight=1.0, cap=0.8, max_n=5000, reps=1):
    """Simulate one setting with true defect rate p; return stopping times.

    Returns an array of length reps holding the number of coupons at which
    the claim "p < eps" was certified, or np.inf where it never was within
    max_n coupons (which is what should happen most of the time when
    p >= eps).
    """
    ep = BettingEProcess(eps, shape=reps, strategy=strategy, prior_mean=prior_mean,
                         prior_weight=prior_weight, cap=cap)
    stop = np.full(reps, np.inf)
    active = np.ones(reps, dtype=bool)
    for t in range(1, max_n + 1):
        y = (rng.random(reps) < p).astype(float)
        ep.update(y, mask=active)
        newly = active & ep.rejects(alpha)
        stop[newly] = t
        active &= ~newly
        if not active.any():
            break
    return stop
