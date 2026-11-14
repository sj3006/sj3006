"""Search allocation: find each row's edge by noisy galloping + bisection.

Goal: certify every setting of the target T = {all rates <= q eps}, where
settings with rates between q eps and eps may also be certified (slack).

For each mode m and each row (a chain of settings along axis 0, ordered from
safest to riskiest for m) the target's edge is a single position, because
rates are monotone along the row. We locate it with a two-sided test at one
probe setting at a time:

- CERTIFY: the cone rule certifies the probe for m (wealth in its riskier
  cone reaches 1/alpha). Everything safer is then certified too.
- REJECT: a second betting e-process, testing "rate <= q eps" (it bets on
  defects), reaches 1/delta. The probe is then confidently outside the
  target for m, and by monotonicity so is everything riskier.

The slack between q eps and eps makes this cheap at every rate p: if
p <= q eps, certification needs about ln(1/(alpha w)) / KL(p || eps) coupons
and p is far from eps; if p >= eps, rejection needs about
ln(1/delta) / KL(p || q eps) and p is far from q eps; in between, whichever
finishes first. So no probe is ever stuck near a threshold.

Probes per row: start at the simulator's predicted edge (if any), gallop
(steps 1, 2, 4, ...) toward the side the outcome points to until the edge is
bracketed, then bisect. That is O(log distance) probes with a good
simulator and O(log n) without. Certificates and rejections from every row
spread through the 2D ordering, so other rows' searches shrink too.

Validity of certificates is unchanged (cone rule, paper Theorem 1): allocation and
rejections never certify anything. Rejections can only make the procedure
miss target settings, with probability at most beta overall (they use level
beta / (M N) each).
"""

import numpy as np

from .cone import ConeCertifier, cone_sum

REJECT_FRACTIONS = np.array([0.025, 0.05, 0.1, 0.2, 0.4])   # bets as fractions of 1/(q eps)


class SearchCertifier(ConeCertifier):
    def __init__(self, scenario, q=0.5, beta=0.05, per_probe=8, warm_start="sim",
                 concurrent_rows=2, timeout=2.0, bracket_probe="mid", **kw):
        kw.setdefault("alloc", "edge")       # parent's allocation is not used
        kw.setdefault("target_q", q)
        super().__init__(scenario, **kw)
        self.q, self.per_probe, self.warm_start = q, per_probe, warm_start
        # Where to probe once a row's edge is bracketed: "mid" (bisection),
        # "walk" (the safest undecided setting, next to the certified ones)
        # or "quarter" (a quarter of the way from the certified side).
        if bracket_probe not in ("mid", "walk", "quarter"):
            raise ValueError("bracket_probe must be 'mid', 'walk' or 'quarter'")
        self.bracket_probe = bracket_probe
        # Rows are searched riskiest first (in the across-row direction), a
        # few at a time per mode: a certificate in a risky row covers a
        # quadrant that spans the safer rows, so searching them later is
        # often unnecessary.
        self.concurrent_rows = concurrent_rows
        # Time-boxed probes: a probe whose rate sits between q eps and eps is
        # slow to certify AND slow to reject. After `timeout` times the
        # expected cost of certifying a setting at exactly q eps, call it
        # "too close to call", treat it as outside the target, and move the
        # search safer. Never certifies anything (validity unaffected); a
        # true target setting times out only with small probability
        # (completeness risk, measured in the experiments). timeout=None
        # disables it.
        self.timeout = timeout
        self.timed_out = np.zeros((self.M, self.N), dtype=bool)
        self._probe_start = {}
        self.reject_level = np.log(self.M * self.N / beta)
        lam = REJECT_FRACTIONS[None, None, :] / (q * self.eps[:, :, None])   # (M, N, K)
        self._rej_lam = lam
        self._rej_logk = np.zeros(lam.shape)
        self.rejected = np.zeros((self.M, self.N), dtype=bool)
        nP, nV = self.shape
        self.nP, self.nV = nP, nV
        # Per (mode, row): galloping state.
        self.state = {}
        sim = np.stack([scenario.sim[m].ravel() for m in self.modes])
        self._sim = sim
        self._sim_informative = np.ptp(sim) > 0
        self.probes = 0

    def _probe_budget(self, m, x):
        from .certify import _kl_vec
        kl = float(_kl_vec(np.array(self.q * self.eps[m, x]), np.array(self.eps[m, x])))
        need = np.log(16.0 / (self.alpha * max(self.w[m, x], 1e-300)))
        return self.timeout * need / kl

    # -- rows ------------------------------------------------------------------

    def _row(self, m, j):
        """Flat indices of row j (fixed axis-1 index), safest first for mode m."""
        idx = np.arange(self.nP) * self.nV + j
        d_p = self.dirs[m][0]
        return idx[::-1] if d_p > 0 else idx

    # -- evidence updates ------------------------------------------------------

    def _update_reject(self, x, y):
        eps_q = (self.q * self.eps[:, x])[:, None]
        self._rej_logk[:, x, :] += np.log1p(self._rej_lam[:, x, :] * (y[:, None] - eps_q))
        top = self._rej_logk[:, x, :].max(axis=1)
        mix = top + np.log(np.mean(np.exp(self._rej_logk[:, x, :] - top[:, None]), axis=1))
        newly = mix >= self.reject_level
        if newly.any():
            for m in np.flatnonzero(newly):
                if not self.certified[m, x]:
                    self.rejected[m, x] = True

    def _spread_rejections(self):
        for m in range(self.M):
            g = self._grid(self.rejected[m].astype(float))
            # y is rejected if some rejected x is at least as safe as y.
            self.rejected[m] |= (cone_sum(g, self.dirs[m], riskier=False) > 0.5).ravel()
            self.rejected[m] &= ~self.certified[m]

    # -- allocation ---------------------------------------------------------------

    def _undecided(self, m, row, excluded):
        return [x for x in row if not (self.certified[m, x] or self.rejected[m, x] or excluded[x])]

    def _apply_timeouts(self):
        if self.timeout is None:
            return
        for (m, j), st in self.state.items():
            x = st["probe"]
            if self.certified[m, x] or self.rejected[m, x]:
                continue
            spent = self.n_at[x] - self._probe_start.get((m, j, x), 0)
            if spent >= self._probe_budget(m, x):
                self.timed_out[m, x] = True
                self.rejected[m, x] = True          # for the search: move safer

    def _neighbor_edge(self, m, j):
        """Position (row index along axis 0) of the edge found in an adjacent,
        already-searched row for mode m, or None."""
        for jj in (j - 1, j + 1):
            if 0 <= jj < self.nV and (m, jj) in self.state:
                row = list(self._row(m, jj))
                cert = [k for k, x in enumerate(row) if self.certified[m, x]]
                if cert:
                    return row[max(cert)] // self.nV      # power index of riskiest certified
        return None

    def _first_probe(self, m, row, und):
        if self.warm_start in ("neighbor", "both"):
            j = row[0] % self.nV
            e = self._neighbor_edge(m, j)
            if e is not None:
                # undecided setting in this row closest in power to the neighbour's edge
                return min(und, key=lambda x: abs(x // self.nV - e))
        if self.warm_start in (True, "sim", "both") and self._sim_informative:
            g = self._sim[m, row]
            ok = [x for x, gx in zip(row, g) if gx <= self.q * self.eps[m, x] and x in und]
            if ok:
                return ok[-1]                   # riskiest predicted-in-target setting
            return und[0]
        return und[len(und) // 2]
    # warm_start: True / "sim" (simulator's predicted edge; the default),
    # "neighbor" (edge found in an adjacent row), "both" (neighbour if
    # available, else simulator), False (middle of the row). On the synthetic
    # window "sim" is 6-14% cheaper than "both" with good side information
    # (16x16 to 48x48) and costs the same with optimistic side information,
    # where "both" needs fewer probes.

    def _bracket_choice(self, und):
        """Probe inside a bracket; und is ordered safest first."""
        if self.bracket_probe == "walk":
            return und[0]
        if self.bracket_probe == "quarter":
            return und[len(und) // 4]
        return und[len(und) // 2]

    def choose_plate(self):
        excluded = self.rejected.any(axis=0)
        probes = []
        for m in range(self.M):
            d_v = self.dirs[m][1]
            rows_risky_first = range(self.nV - 1, -1, -1) if d_v < 0 else range(self.nV)
            active = 0
            for j in rows_risky_first:
                if active >= self.concurrent_rows:
                    break
                row = list(self._row(m, j))
                und = self._undecided(m, row, excluded)
                if not und:
                    continue
                active += 1
                st = self.state.get((m, j))
                if st is not None and st["probe"] in und:
                    probes.append(st["probe"])              # keep testing current probe
                    continue
                if st is None:
                    x = self._first_probe(m, row, und)
                    self.state[(m, j)] = dict(probe=x, step=1, dir=0, bracketed=False)
                    self._probe_start[(m, j, x)] = self.n_at[x]
                    probes.append(x)
                    self.probes += 1
                    continue
                # The previous probe was decided: certified -> look riskier, else safer.
                last = st["probe"]
                went = +1 if self.certified[m, last] else -1
                pos = {x: k for k, x in enumerate(row)}
                und_pos = [pos[x] for x in und]
                if st["dir"] not in (0, went):
                    st["bracketed"] = True
                if not st["bracketed"]:
                    target = pos[last] + went * st["step"]
                    st["step"] *= 2
                    st["dir"] = went
                    if und_pos[0] <= target <= und_pos[-1]:
                        x = row[min(und_pos, key=lambda k: abs(k - target))]
                    else:
                        st["bracketed"] = True
                        x = self._bracket_choice(und)
                else:
                    x = self._bracket_choice(und)
                st["probe"] = x
                self._probe_start[(m, j, x)] = self.n_at[x]
                probes.append(x)
                self.probes += 1
        if not probes:
            return []
        uniq = list(dict.fromkeys(probes))
        per = max(self.per_probe, int(np.ceil(self.batch / len(uniq))))
        plate = [x for x in uniq for _ in range(per)]
        return plate

    # -- one build plate -------------------------------------------------------------

    def run_plate(self):
        plate = self.choose_plate()
        if not plate:
            return False
        for x in plate:
            y = (self.rng.random(self.M) < self.truth[:, x]).astype(float)
            self.ep.update_at((slice(None), x), y)
            self._update_reject(x, y)
            self.n_at[x] += 1
            self.coupons += 1
        self._check()
        self.rejected &= ~self.certified
        self._apply_timeouts()
        self._spread_rejections()
        self._record()
        return True
