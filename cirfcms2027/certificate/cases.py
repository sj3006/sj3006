"""Observations from the exact forward model, and the exact certificate.

Why not the Jacobian
--------------------
`inference.py` builds its test on the tangent to the forward model at the
healthy point. That is enough to derive the geometry, and it is what the
conference paper's angles are, but it is not enough to test with. The exact
response to a fault curves away from its own tangent, and the departure is a
fixed bias rather than noise, so it enters the residual squared and consumes the
test's budget. Measured at a 1 % channel noise, a power fault's perpendicular
departure is 0.19 at rho = 28 but 1.72 at rho = 120, against a threshold of
5.99, and the coverage of the nominally 95 % certificate falls to 0.68. Under-
coverage means the test throws out the true cause, which is the one failure a
certificate may not have.

So the magnitude is profiled through the model itself:

    R_k(z) = min over f of || z_w - g_k(f) / (sigma eps) ||^2

where `g_k(f)` is the exact relative sensor deviation under a fault of type `k`
and magnitude `f`. This is a profile likelihood with one nuisance parameter, so
it keeps the same chi-squared reference distribution on `S - 1` degrees of
freedom. That reference is exact when the signature is a straight line and
approximate when it is a curve; `verify.py` measures the error rather than
assuming it is small, and finds coverage within Monte Carlo noise of 0.95 at
every signal-to-noise ratio tested.

What a signature is, in each regime
-----------------------------------
Instantaneous: `g_k(f)` is the three relative deviations of photodiode, camera
area and pyrometer temperature, read once. One forward evaluation per magnitude.

Build context: the observation is not a reading but 15 regression coefficients,
three sensors onto five build regressors, estimated across all 84 segments of
the plan. Fault `k` modulates along the build with a known profile `m_k`, so in
segment `t` its local magnitude is `f * m_k(t)` and that segment's deviation is
`g_k_instant(f * m_k(t))`. Regressing those 84 deviations onto the regressors
gives the signature. Nothing here is linear in `f`: the per-segment response
curves and so does the coefficient vector, which is exactly the point.

Cost
----
49 forward evaluations per fault, once, cached as monotone cubic interpolants.
Monotone cubics are used rather than splines because the responses are smooth
but the camera's extent comes from thresholding, so an interpolant that can
overshoot would invent features the model does not have. After that a signature
at any magnitude is a table lookup, and a case costs nothing.

Choosing magnitudes
-------------------
Not by a common `f`. The five fault magnitudes are severity indices on different
scales, and `faults.py` is explicit that f = 1 means "severe" by convention
rather than by calibration, so drawing all five at the same `f` would compare
unequal severities and the benchmark would measure the convention. Cases are
drawn at a target whitened signal-to-noise ratio instead, `f_k = rho eps /
||Jw[:,k]||`, which is the quantity the test actually responds to. Every pair of
a magnitude and a noise level giving the same rho behaves identically, so this
claims no absolute noise figure.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import inference as inf                                        # noqa: E402
import noise                                                   # noqa: E402
import observables as obs                                      # noqa: E402
from faults import (FAULT_NAMES, FaultCouplings, FaultState,    # noqa: E402
                    apply_faults)
from sensors import SENSOR_NAMES, sensor_readings               # noqa: E402

__all__ = ["ExactResponse", "SignatureTable", "Case", "generate", "save", "load",
           "profile_residuals", "certify", "report"]

#: Magnitudes are gridded out to this signal-to-noise ratio, well past anything
#: a case is drawn at, so that a noise excursion cannot push the best fit off
#: the end of the table.
GRID_SNR = 200.0

#: Forward evaluations per fault when building a response curve.
GRID_POINTS = 49

#: Points in the fine table the profile minimisation searches.
FINE_POINTS = 4001

CACHE = HERE / "_response_cache.npz"


def _readings(state: FaultState) -> np.ndarray:
    beam, material = apply_faults(state, FaultCouplings())
    r = sensor_readings(beam, material)
    return np.array([r[s] for s in SENSOR_NAMES], dtype=float)


class ExactResponse:
    """Relative sensor deviation against fault magnitude, from the real model.

    `self.curve[fault]` is a list of three monotone cubic interpolants, one per
    sensor, each mapping a magnitude to a relative deviation from the healthy
    reading. Evaluating all three at `f` gives `g_k(f)`.
    """

    def __init__(self, use_cache: bool = True):
        self.nominal = _readings(FaultState())
        regime = inf.instantaneous()
        self.fmax = {n: inf.magnitude_for_snr(GRID_SNR, n, regime)
                     for n in FAULT_NAMES}
        self.grid: dict[str, np.ndarray] = {}
        self.table: dict[str, np.ndarray] = {}
        if use_cache and CACHE.exists():
            z = np.load(CACHE)
            if int(z["points"]) == GRID_POINTS and float(z["snr"]) == GRID_SNR:
                for n in FAULT_NAMES:
                    self.grid[n] = z[f"grid_{n}"]
                    self.table[n] = z[f"resp_{n}"]
        if not self.table:
            for n in FAULT_NAMES:
                g = np.linspace(-1.2 * self.fmax[n], 1.2 * self.fmax[n], GRID_POINTS)
                self.grid[n] = g
                self.table[n] = np.array(
                    [(_readings(FaultState(**{n: float(f)})) - self.nominal)
                     / self.nominal for f in g])
            if use_cache:
                np.savez(CACHE, points=GRID_POINTS, snr=GRID_SNR,
                         **{f"grid_{n}": self.grid[n] for n in FAULT_NAMES},
                         **{f"resp_{n}": self.table[n] for n in FAULT_NAMES})
        self.curve = {
            n: [PchipInterpolator(self.grid[n], self.table[n][:, i])
                for i in range(len(SENSOR_NAMES))]
            for n in FAULT_NAMES
        }

    def instantaneous(self, fault: str, f) -> np.ndarray:
        """Relative deviation of the three sensors, shape (..., 3)."""
        f = np.atleast_1d(np.asarray(f, float))
        out = np.column_stack([c(f) for c in self.curve[fault]])
        return out

    def build_context(self, fault: str, f, plan) -> np.ndarray:
        """The 15 regression coefficients, shape (..., 15).

        Segment `t` sees local magnitude `f * m_k(t)`, its deviation is read off
        the same response curve, and the 84 deviations are regressed onto the
        build regressors exactly as the enlarged observation is defined.
        """
        f = np.atleast_1d(np.asarray(f, float))
        G = obs.regressors(plan)
        hat = np.linalg.inv(G.T @ G) @ G.T
        m = obs.modulations(plan)[:, FAULT_NAMES.index(fault)]
        rows = []
        for value in f:
            local = value * m                                   # 84 magnitudes
            seg = self.instantaneous(fault, local)              # 84 x 3
            coef = hat @ seg                                    # 5 x 3
            rows.append(coef.T.ravel())                         # sensor-major
        return np.array(rows)


class SignatureTable:
    """Whitened exact signatures on a fine magnitude grid, for one regime.

    `self.points[fault]` is a `FINE_POINTS x n_obs` array of whitened
    signatures, so the profile residual of an observation against cause `k` is
    the squared distance to the nearest row of `self.points[k]`.
    """

    def __init__(self, regime: inf.Regime, response: ExactResponse,
                 plan=None, eps: float = inf.EPSILON_REFERENCE):
        self.regime = regime
        self.eps = eps
        self.points: dict[str, np.ndarray] = {}
        self.magnitudes: dict[str, np.ndarray] = {}
        for n in FAULT_NAMES:
            lo, hi = response.grid[n][0], response.grid[n][-1]
            f = np.linspace(lo, hi, FINE_POINTS)
            if regime.n_obs == len(SENSOR_NAMES):
                raw = response.instantaneous(n, f)
            else:
                raw = response.build_context(n, f, plan)
            self.magnitudes[n] = f
            self.points[n] = np.array([regime.whiten(r, eps) for r in raw])

    def residuals(self, Zw: np.ndarray, chunk: int = 2000) -> np.ndarray:
        """Profile residual of each observation against each cause.

        The nearest point on a signature curve is found as
        `||z||^2 - 2 z.p + ||p||^2` minimised over the table, which is one
        matrix product rather than an N x grid x dimension difference array.
        Chunked over observations so memory stays bounded whatever N is.
        """
        Zw = np.atleast_2d(np.asarray(Zw, float))
        out = np.empty((Zw.shape[0], len(FAULT_NAMES)))
        for k, n in enumerate(FAULT_NAMES):
            P = self.points[n]
            pn = (P * P).sum(1)
            for a in range(0, Zw.shape[0], chunk):
                Z = Zw[a:a + chunk]
                d = (Z * Z).sum(1)[:, None] - 2.0 * (Z @ P.T) + pn[None, :]
                out[a:a + chunk, k] = np.maximum(d.min(1), 0.0)
        return out

    def best_magnitude(self, Zw: np.ndarray, chunk: int = 2000) -> np.ndarray:
        """Profiled magnitude under each cause, for reporting."""
        Zw = np.atleast_2d(np.asarray(Zw, float))
        out = np.empty((Zw.shape[0], len(FAULT_NAMES)))
        for k, n in enumerate(FAULT_NAMES):
            P = self.points[n]
            pn = (P * P).sum(1)
            for a in range(0, Zw.shape[0], chunk):
                Z = Zw[a:a + chunk]
                d = (Z * Z).sum(1)[:, None] - 2.0 * (Z @ P.T) + pn[None, :]
                out[a:a + chunk, k] = self.magnitudes[n][d.argmin(1)]
        return out


def profile_residuals(Zw, table: SignatureTable) -> np.ndarray:
    return table.residuals(Zw)


def certify(Zw, table: SignatureTable, alpha: float = inf.ALPHA) -> list[tuple[str, ...]]:
    """Causes not rejected at level `alpha`, one tuple per observation."""
    q = inf.chi2_threshold(table.regime.dof, alpha)
    R = table.residuals(Zw)
    return [tuple(n for n, r in zip(FAULT_NAMES, row) if r <= q) for row in R]


@dataclass
class Case:
    """One synthetic build with one fault, and what the data licenses about it."""
    case_id: int
    regime: str
    truth: str
    magnitude: float
    target_snr: float
    observed_snr: float
    deviations: list[float]          # raw relative deviations, as an agent sees
    certificate: list[str]
    residuals: list[float]
    fitted_magnitudes: list[float]
    linear_certificate: list[str]

    @property
    def ambiguous(self) -> bool:
        return len(self.certificate) != 1

    @property
    def covered(self) -> bool:
        return self.truth in self.certificate


def generate(n_per_cell: int = 20,
             snrs=(14.0, 28.0, 56.0, 120.0),
             regime_name: str = "instantaneous",
             alpha: float = inf.ALPHA,
             eps: float = inf.EPSILON_REFERENCE,
             seed: int = 0,
             response: ExactResponse | None = None) -> list[Case]:
    """Cases stratified by fault and target signal-to-noise ratio."""
    rng = np.random.default_rng(seed)
    plan = obs.scan_plan()
    if regime_name == "instantaneous":
        regime = inf.instantaneous()
    else:
        regime = inf.build_context(whitening="full", plan=plan)
    response = response or ExactResponse()
    table = SignatureTable(regime, response, plan=plan, eps=eps)
    q = inf.chi2_threshold(regime.dof, alpha)

    cases: list[Case] = []
    cid = 0
    for snr in snrs:
        for truth in FAULT_NAMES:
            f = inf.magnitude_for_snr(snr, truth, regime, eps)
            if regime.n_obs == len(SENSOR_NAMES):
                mean_raw = response.instantaneous(truth, f)[0]
            else:
                mean_raw = response.build_context(truth, f, plan)[0]
            mean_w = regime.whiten(mean_raw, eps)
            for _ in range(n_per_cell):
                zw = mean_w + rng.standard_normal(regime.n_obs)
                # the raw deviations an agent would be shown, recovered by
                # undoing the whitening: zw = L^-1 (z/eps), so z = eps L zw
                raw = regime.unwhiten(zw, eps)
                R = table.residuals(zw)[0]
                fhat = table.best_magnitude(zw)[0]
                lin = inf.certificate(zw, regime, alpha)
                cases.append(Case(
                    case_id=cid, regime=regime.name, truth=truth,
                    magnitude=float(f), target_snr=float(snr),
                    observed_snr=float(np.linalg.norm(zw)),
                    deviations=[float(x) for x in raw],
                    certificate=[n for n, r in zip(FAULT_NAMES, R) if r <= q],
                    residuals=[float(x) for x in R],
                    fitted_magnitudes=[float(x) for x in fhat],
                    linear_certificate=list(lin)))
                cid += 1
    return cases


def save(cases: list[Case], path: Path) -> None:
    Path(path).write_text(json.dumps([asdict(c) for c in cases], indent=1))


def load(path: Path) -> list[Case]:
    return [Case(**d) for d in json.loads(Path(path).read_text())]


def report() -> None:
    print("Exact signatures and the certificate they license")
    print("=" * 74)
    response = ExactResponse()
    plan = obs.scan_plan()

    print("\nHow far the exact signature departs from its own tangent")
    regime = inf.instantaneous()
    print(f"   {'fault':9s} {'rho':>6s} {'f':>9s} {'along':>8s} "
          f"{'perpendicular':>14s} {'as a share of q':>16s}")
    q = inf.chi2_threshold(regime.dof)
    for n in FAULT_NAMES:
        u = regime.Jw[:, FAULT_NAMES.index(n)] / regime.norms[FAULT_NAMES.index(n)]
        for snr in (28.0, 56.0, 120.0):
            f = inf.magnitude_for_snr(snr, n, regime)
            zw = regime.whiten(response.instantaneous(n, f)[0])
            along = float(zw @ u)
            perp = float(np.linalg.norm(zw - along * u))
            print(f"   {n:9s} {snr:6.0f} {f:9.4f} {along:8.2f} {perp:14.3f} "
                  f"{perp ** 2 / q:15.1%}")

    for name in ("instantaneous", "build context"):
        cases = generate(n_per_cell=400, regime_name=name, response=response, seed=4)
        print(f"\n{name}: 400 cases per fault and signal level")
        print(f"   {'rho':>6s}  {'coverage':>9s} {'mean |C|':>9s} {'unique':>8s} "
              f"{'empty':>7s} {'linear coverage':>16s}")
        for snr in sorted({c.target_snr for c in cases}):
            sub = [c for c in cases if c.target_snr == snr]
            cov = np.mean([c.covered for c in sub])
            size = np.mean([len(c.certificate) for c in sub])
            uniq = np.mean([len(c.certificate) == 1 for c in sub])
            empty = np.mean([len(c.certificate) == 0 for c in sub])
            lcov = np.mean([c.truth in c.linear_certificate for c in sub])
            print(f"   {snr:6.0f}  {cov:9.3f} {size:9.2f} {uniq:8.3f} "
                  f"{empty:7.3f} {lcov:15.3f}")

        print(f"   by fault at rho = 56:")
        for n in FAULT_NAMES:
            sub = [c for c in cases if c.target_snr == 56.0 and c.truth == n]
            if not sub:
                continue
            uniq = np.mean([len(c.certificate) == 1 for c in sub])
            size = np.mean([len(c.certificate) for c in sub])
            print(f"      {n:9s} unique {uniq:6.3f}   mean |C| {size:5.2f}")


if __name__ == "__main__":
    report()
