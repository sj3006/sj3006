"""Model-based baseline: Gaussian-process level-set certification.

The standard model-based way to find a feasible region (GP level-set
estimation, Gotovos et al. 2013; safe Bayesian optimization, Sui et al. 2015)
fits a GP to the observations and declares a setting safe when the GP's upper
confidence bound is below the threshold:

    certify x for mode m  if  mu_m(x) + beta * sd_m(x) < eps_m.

Its guarantee holds only if the GP model is right (the true rate surface is
a draw from, or has bounded norm in, the kernel's function space, with a
correct noise model). We use the usual choices: one GP per mode on the
empirical rates, RBF kernel on normalized coordinates, binomial noise
variance, prior mean eps. Sampling follows the LSE "straddle" rule: build at
settings with the largest beta * sd - |mu - eps|, i.e. most ambiguous.

With monotone=True the baseline also uses the ordering, in the spirit of
monotone safe exploration (Losalka and Scarlett 2023): a setting certified
for a mode certifies every setting that is safer for that mode. This is the
strongest fair model-based competitor: same structure as ours, but the
certificate rests on the GP model instead of a test.

This exists to measure how often a model-based certificate is wrong when
the model is misspecified (here: defect rates with sharp transitions).
"""

import numpy as np

from .cone import cone_sum


class GPLevelSet:
    def __init__(self, scenario, beta=2.0, lengthscale=0.2, signal_sd=0.15, batch=24, rng=None,
                 monotone=False):
        self.sc = scenario
        self.monotone = monotone
        self.dirs = [scenario.directions[m] for m in scenario.modes]
        self.modes = scenario.modes
        self.M = len(self.modes)
        self.shape = scenario.truth[self.modes[0]].shape
        self.N = int(np.prod(self.shape))
        self.truth = np.stack([scenario.truth[m].ravel() for m in self.modes])
        self.eps = np.array([scenario.eps[m] for m in self.modes])
        self.beta, self.batch = beta, batch
        self.rng = np.random.default_rng() if rng is None else rng
        ii, jj = np.meshgrid(np.linspace(0, 1, self.shape[0]), np.linspace(0, 1, self.shape[1]),
                             indexing="ij")
        X = np.stack([ii.ravel(), jj.ravel()], axis=1)
        d2 = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
        self.Kfull = signal_sd ** 2 * np.exp(-d2 / (2 * lengthscale ** 2))
        self.n = np.zeros(self.N)
        self.k = np.zeros((self.M, self.N))
        self.certified = np.zeros((self.M, self.N), dtype=bool)
        self.coupons = 0
        self.history = []

    def posterior(self):
        """Posterior mean and sd per mode (exact GP regression)."""
        obs = np.flatnonzero(self.n > 0)
        mu = np.tile(self.eps[:, None], (1, self.N)).astype(float)
        sd = np.tile(np.sqrt(np.diag(self.Kfull))[None, :], (self.M, 1))
        if len(obs) == 0:
            return mu, sd
        Koo = self.Kfull[np.ix_(obs, obs)]
        Kxo = self.Kfull[:, obs]
        for m in range(self.M):
            r = self.k[m, obs] / self.n[obs]
            var = np.maximum(r * (1 - r), self.eps[m] * (1 - self.eps[m]) / 4) / self.n[obs]
            L = np.linalg.cholesky(Koo + np.diag(var) + 1e-10 * np.eye(len(obs)))
            a = np.linalg.solve(L.T, np.linalg.solve(L, r - self.eps[m]))
            mu[m] = self.eps[m] + Kxo @ a
            v = np.linalg.solve(L, Kxo.T)
            sd[m] = np.sqrt(np.maximum(np.diag(self.Kfull) - (v ** 2).sum(0), 1e-12))
        return mu, sd

    def run_plate(self):
        if not hasattr(self, "_post"):
            self._post = self.posterior()
        mu, sd = self._post
        ambiguity = (self.beta * sd - np.abs(mu - self.eps[:, None]))
        ambiguity = np.where(self.certified, -np.inf, ambiguity).max(axis=0)
        order = np.argsort(-ambiguity)[: max(1, self.batch // 4)]
        for x in np.repeat(order, 4)[: self.batch]:
            y = self.rng.random(self.M) < self.truth[:, x]
            self.n[x] += 1
            self.k[:, x] += y
            self.coupons += 1
        mu, sd = self._post = self.posterior()      # one refit per plate
        self.certified |= mu + self.beta * sd < self.eps[:, None]
        if self.monotone:
            self._close()
        win = self.certified.all(axis=0)
        bad = (self.truth >= self.eps[:, None]).any(axis=0)
        self.history.append(dict(coupons=self.coupons, area=int(win.sum()),
                                 errors=int((win & bad).sum())))
        return True

    def _close(self):
        """Certified for mode m at x => certified at every setting safer than x."""
        for m in range(self.M):
            c = self.certified[m].reshape(self.shape).astype(float)
            self.certified[m] = (cone_sum(c, self.dirs[m], riskier=True) > 0.5).ravel()

    def run(self, budget):
        while self.coupons < budget:
            self.run_plate()
        return self.history

    def window(self):
        return self.certified.all(axis=0).reshape(self.shape)
