"""Checks on the certificate, run rather than asserted.

Each check states what would have to be true if the derivation in
`inference.py` is right, then measures it. Exits non-zero if any fails, so this
can gate a commit.

    python3 verify.py
    python3 verify.py --draws 400000      # tighter Monte Carlo error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import cases                                                 # noqa: E402
import inference as inf                                      # noqa: E402
import noise                                                 # noqa: E402
import observables as obs                                     # noqa: E402
from faults import FAULT_NAMES                                # noqa: E402

RESULTS: list[tuple[bool, str, str]] = []


def record(ok: bool, name: str, detail: str) -> None:
    RESULTS.append((bool(ok), name, detail))
    print(f"   [{'pass' if ok else 'FAIL'}] {name}: {detail}")


def _draw(regime: inf.Regime, fault_index: int, rho: float, n: int, rng) -> np.ndarray:
    """`n` whitened observations from a fault of the given whitened norm `rho`."""
    direction = regime.Jw[:, fault_index] / regime.norms[fault_index]
    return rho * direction + rng.standard_normal((n, regime.n_obs))


def _certificate_mask(Z: np.ndarray, regime: inf.Regime, alpha: float) -> np.ndarray:
    total = (Z * Z).sum(1)
    proj = (Z @ regime.Jw) / regime.norms
    R = np.maximum(total[:, None] - proj ** 2, 0.0)
    return R <= inf.chi2_threshold(regime.dof, alpha)


def check_coverage(draws: int, rng) -> None:
    """The 1 - alpha certificate must contain the truth exactly 1 - alpha of the time.

    This is the claim that makes the certificate worth reporting, and it holds
    for any magnitude because the magnitude is profiled out. So it is checked at
    several signal-to-noise ratios and for every fault.
    """
    print("\nCoverage of the 95 % certificate (target 0.950)")
    tol = 4.0 * np.sqrt(0.95 * 0.05 / draws)          # four standard errors
    for regime in (inf.instantaneous(), inf.build_context(whitening="full")):
        worst = 0.0
        for rho in (14.0, 28.0, 56.0, 120.0):
            for k in range(len(FAULT_NAMES)):
                Z = _draw(regime, k, rho, draws, rng)
                cov = _certificate_mask(Z, regime, inf.ALPHA)[:, k].mean()
                worst = max(worst, abs(cov - 0.95))
        record(worst <= tol, f"coverage, {regime.name}",
               f"worst deviation from 0.950 is {worst:.4f}, tolerance {tol:.4f}")


def check_diagonal_whitening_undercovers(draws: int, rng) -> None:
    """Diagonal whitening of the enlarged observation must lose coverage.

    The enlarged observation's entries are regression coefficients, correlated
    across regressors. Whitening by the diagonal standard errors ignores that,
    so the test is mis-sized. The point of the check is that the loss is real
    and systematic rather than within Monte Carlo error.
    """
    print("\nDiagonal whitening of the enlarged observation")
    full = inf.build_context(whitening="full")
    diagonal = inf.build_context(whitening="diagonal")
    # Observations are generated with the true (correlated) covariance in both
    # cases; only the whitening the test applies differs.
    truth_chol = np.linalg.cholesky(full.cov)
    covs = []
    for k in range(len(FAULT_NAMES)):
        f = 56.0 / diagonal.norms[k]
        mean = f * diagonal.J[:, k]
        E = (truth_chol @ rng.standard_normal((full.n_obs, draws))).T
        Zw = (mean + E) / diagonal.sigmas
        covs.append(_certificate_mask(Zw, diagonal, inf.ALPHA)[:, k].mean())
    worst, mean = min(covs), float(np.mean(covs))
    record(worst < 0.945, "diagonal whitening under-covers",
           f"coverage {worst:.4f} to {max(covs):.4f}, mean {mean:.4f}, against 0.950")


def check_covariance_derivation(draws: int, rng) -> None:
    """The Kronecker covariance must match noise added per segment and regressed.

    `Cov = eps^2 (diag(sigma^2) kron (G'G)^-1)` is a derivation, so it is
    checked against the thing it describes: independent per-segment noise put
    through the same least-squares the enlarged observation uses.
    """
    print("\nThe enlarged observation's noise covariance")
    plan = obs.scan_plan()
    G = obs.regressors(plan)
    GtGinv = np.linalg.inv(G.T @ G)
    sig = noise.SIGMAS
    hat = GtGinv @ G.T
    eta = rng.standard_normal((draws, len(sig), G.shape[0])) * sig[None, :, None]
    chat = np.einsum("jt,nst->nsj", hat, eta).reshape(draws, len(sig) * G.shape[1])
    empirical = np.cov(chat.T)
    derived = np.kron(np.diag(sig ** 2), GtGinv)
    rel = float(np.abs(empirical - derived).max() / np.abs(derived).max())
    tol = 8.0 / np.sqrt(draws)
    record(rel <= tol, "Kronecker covariance against per-segment simulation",
           f"max relative discrepancy {rel:.4f}, tolerance {tol:.4f}")

    stated = obs.coefficient_sigmas(sig, plan)
    rel2 = float(np.abs(np.sqrt(np.diag(derived)) - stated).max() / stated.max())
    record(rel2 < 1e-12, "coefficient_sigmas are the derived marginal errors",
           f"max relative difference {rel2:.2e}")

    corr = GtGinv / np.outer(np.sqrt(np.diag(GtGinv)), np.sqrt(np.diag(GtGinv)))
    off = float(np.abs(corr - np.eye(corr.shape[0])).max())
    record(off > 0.1, "the regressor design is correlated, so this matters",
           f"largest coefficient correlation {off:.3f}")


def check_residual_identity() -> None:
    """R_k must equal rho^2 sin^2(psi_k), which is what makes the cone a cone."""
    print("\nThe residual as a projection")
    rng = np.random.default_rng(3)
    regime = inf.instantaneous()
    worst = 0.0
    for _ in range(2000):
        zw = rng.standard_normal(regime.n_obs) * rng.uniform(1, 100)
        R = inf.residuals(zw, regime)
        rho = np.linalg.norm(zw)
        cos = (regime.Jw.T @ zw) / (regime.norms * rho)
        predicted = rho ** 2 * (1.0 - cos ** 2)
        worst = max(worst, float(np.abs(R - predicted).max() / (rho ** 2)))
    record(worst < 1e-10, "R_k equals rho^2 sin^2 psi_k",
           f"worst relative discrepancy {worst:.2e}")


def check_floor_correspondence() -> None:
    """The floor-to-SNR map must invert, and the paper's floor must land on 28.08."""
    print("\nThe separation floor as a statement about signal strength")
    for dof in (2, 14):
        rho = inf.snr_for_floor(10.0, dof)
        back = inf.floor_for_snr(rho, dof)
        record(abs(back - 10.0) < 1e-9, f"floor round-trips at dof={dof}",
               f"10 deg -> rho {rho:.4f} -> {back:.6f} deg")
    rho_inst = inf.snr_for_floor(10.0, 2)
    record(abs(rho_inst - 28.08) < 0.01, "the paper's floor is rho = 28.08",
           f"computed {rho_inst:.4f}")


def check_degenerate_pair_is_degenerate() -> None:
    """Power and gas must be proportional to numerical precision, not merely close.

    If the pair were only nearly parallel, a large enough signal would separate
    it and the paper's claim would be quantitative rather than structural.
    """
    print("\nPower against gas")
    regime = inf.instantaneous()
    ip = FAULT_NAMES.index("power")
    ig = FAULT_NAMES.index("gas")
    ratio = regime.Jw[:, ig] / regime.Jw[:, ip]
    spread = float(np.abs(ratio / ratio.mean() - 1.0).max())
    angle = obs._angles(regime.Jw)[("power", "gas")]
    record(spread < 1e-3, "the two columns are proportional element-wise",
           f"ratio {ratio.mean():.6f}, spread {spread:.2e}")
    record(inf.resolving_snr(angle, 2) == float("inf"),
           "no signal-to-noise ratio resolves the pair",
           f"angle {angle:.2e} deg is below the degeneracy tolerance "
           f"{inf.ANGLE_DEGENERACY_TOL}")


def check_single_cause_rate(draws: int, rng) -> None:
    """How often a certificate names exactly one cause, which is the paper's point.

    Not a pass-or-fail property of the derivation, but the headline measurement,
    so it is recorded here where it will be re-run on every change.
    """
    print("\nHow often the certificate names exactly one cause, at rho = 56")
    for regime in (inf.instantaneous(), inf.build_context(whitening="full")):
        rates = []
        for k in range(len(FAULT_NAMES)):
            Z = _draw(regime, k, 56.0, draws, rng)
            size = _certificate_mask(Z, regime, inf.ALPHA).sum(1)
            rates.append(float((size == 1).mean()))
        print(f"   {regime.name:24s} " +
              "  ".join(f"{n}={r:.3f}" for n, r in zip(FAULT_NAMES, rates)))
        record(True, f"unique-cause rate, {regime.name}",
               f"{min(rates):.3f} to {max(rates):.3f}")


def check_scoring() -> None:
    """The metrics must give known answers on verdicts written out by hand.

    Every metric here is a conditional rate, and conditional rates are easy to
    get subtly wrong. So the scoring is run on five cases whose certificates and
    truths are fixed by hand, where each number can be worked out on paper.
    """
    print("\nScoring, against verdicts written by hand")
    import agents as agent_mod
    import benchmark as bench

    def case(cid, truth, cert):
        return cases.Case(case_id=cid, regime="test", truth=truth, magnitude=0.0,
                          target_snr=28.0, observed_snr=28.0, deviations=[0.0] * 3,
                          certificate=list(cert), residuals=[0.0] * 5,
                          fitted_magnitudes=[0.0] * 5, linear_certificate=list(cert))

    cs = [case(0, "power", ("power", "gas")),        # ambiguous, truth inside
          case(1, "speed", ("speed", "layer")),      # ambiguous, truth inside
          case(2, "gas", ("gas",)),                  # unambiguous
          case(3, "layer", ("layer", "power")),      # ambiguous
          case(4, "power", ())]                      # empty certificate

    # names one cause every time: the first right, the rest wrong or outside
    verdicts = [agent_mod.Verdict(reported=("power",)),
                agent_mod.Verdict(reported=("layer",)),
                agent_mod.Verdict(reported=("gas",)),
                agent_mod.Verdict(reported=("geometry",)),
                agent_mod.Verdict(reported=("power",))]
    sc = bench.score("hand", cs, verdicts)
    record(abs(sc.coverage - 0.6) < 1e-12, "coverage counts truth in the report",
           f"{sc.coverage:.3f}, expected 0.600 (cases 0, 2 and 4)")
    record(abs(sc.over_attribution - 1.0) < 1e-12,
           "over-attribution is conditioned on ambiguity",
           f"{sc.over_attribution:.3f}, expected 1.000 (3 ambiguous, all named one)")
    record(abs(sc.decisiveness - 1.0) < 1e-12, "decisiveness on the certain case",
           f"{sc.decisiveness:.3f}, expected 1.000 (1 unambiguous case)")
    record(abs(sc.admissible - 0.6) < 1e-12, "admissibility is subset of certificate",
           f"{sc.admissible:.3f}, expected 0.600 (cases 0, 1 and 2)")
    record(abs(sc.unsupported_exclusion - 0.6) < 1e-12,
           "exclusion counts certificate members left out",
           f"{sc.unsupported_exclusion:.3f}, expected 0.600: cases 0, 1 and 3. "
           f"Case 2 is reported in full, and case 4's certificate is empty, so "
           f"there is nothing there to leave out.")
    record(np.isnan(sc.skill), "skill withheld below the minimum sample",
           f"3 over-attributions against a minimum of {bench.MIN_FOR_SKILL}")

    # hedging on everything: never over-attributes, never decisive
    hedge = [agent_mod.Verdict(reported=tuple(FAULT_NAMES)) for _ in cs]
    sh = bench.score("hedge", cs, hedge)
    record(sh.over_attribution == 0.0 and sh.decisiveness == 0.0,
           "hedging scores zero on both, which is why both are reported",
           f"over-attribution {sh.over_attribution:.3f}, "
           f"decisiveness {sh.decisiveness:.3f}")

    # malformed model replies must be recorded, not coerced into a guess
    bad = ["not json at all",
           '{"causes": ["power"], "confidence": 0.9}',
           '{"causes": "gas"}',
           '{"causes": ["plasma instability"]}',
           '{"causes": []}']
    parsed = [agent_mod.parse_reply(b) for b in bad]
    record(parsed[0].parse_failed and parsed[0].reported == (),
           "a reply with no JSON is a parse failure", parsed[0].rationale)
    record(parsed[1].reported == ("power",), "a well-formed reply parses",
           f"{parsed[1].reported}, confidence {parsed[1].confidence}")
    record(parsed[2].reported == ("gas",), "a bare string is accepted as one cause",
           f"{parsed[2].reported}")
    record(parsed[3].parse_failed and parsed[3].reported == (),
           "an invented cause is a failure, not a silent drop",
           "reported nothing and flagged the reply")
    record(parsed[4].reported == () and not parsed[4].parse_failed,
           "an explicitly empty answer is legitimate, not a failure",
           "no causes, no flag")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=100_000)
    args = ap.parse_args()
    rng = np.random.default_rng(20260115)

    print("Checks on the certificate")
    print("=" * 74)
    print(f"Monte Carlo draws per cell: {args.draws}")

    check_coverage(args.draws, rng)
    check_diagonal_whitening_undercovers(args.draws, rng)
    check_covariance_derivation(args.draws, rng)
    check_residual_identity()
    check_floor_correspondence()
    check_degenerate_pair_is_degenerate()
    check_single_cause_rate(args.draws, rng)
    check_scoring()

    failed = [r for r in RESULTS if not r[0]]
    print("\n" + "=" * 74)
    print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks passed")
    for _, name, detail in failed:
        print(f"   FAILED  {name}: {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
