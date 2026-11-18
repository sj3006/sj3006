"""Every claim in this package, checked by measurement rather than asserted.

Exits non-zero if any check fails, so it can gate a commit.

    python3.13 verify.py
    python3.13 verify.py --draws 400000      # tighter Monte Carlo error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.stats import chi2

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import theory as th                                               # noqa: E402

RESULTS: list[tuple[bool, str, str]] = []


def record(ok: bool, name: str, detail: str) -> None:
    RESULTS.append((bool(ok), name, detail))
    print(f"   [{'pass' if ok else 'FAIL'}] {name}: {detail}")


def _random_unit(S: int, rng) -> np.ndarray:
    v = rng.standard_normal(S)
    return v / np.linalg.norm(v)


def _rotate_by(u: np.ndarray, delta_deg: float, rng) -> np.ndarray:
    """A unit vector at exactly `delta_deg` from `u`, in a random plane."""
    w = rng.standard_normal(len(u))
    w -= (w @ u) * u
    w /= np.linalg.norm(w)
    d = np.radians(delta_deg)
    return np.cos(d) * u + np.sin(d) * w


# ---------------------------------------------------------------------------
def check_theorem1(rng) -> None:
    """Scaling any column by any nonzero factor leaves every residual unchanged."""
    print("\nTheorem 1, magnitude invariance")
    worst = 0.0
    for S in (3, 15):
        for _ in range(200):
            J = rng.standard_normal((S, 5))
            a = rng.choice([-1.0, 1.0], 5) * 10.0 ** rng.uniform(-3, 3, 5)
            Z = rng.standard_normal((50, S)) * rng.uniform(1, 100)
            R0 = th.residuals(Z, J)
            R1 = th.residuals(Z, J * a)
            worst = max(worst, float(np.abs(R0 - R1).max() / (np.abs(R0).max() + 1e-300)))
    record(worst < 1e-11, "residuals unchanged by column scaling, sign included",
           f"worst relative change {worst:.1e} over scale factors spanning 1e-3 to 1e3")


def check_theorem2(draws: int, rng) -> None:
    """Monte Carlo coverage against the noncentral chi-squared closed form."""
    print("\nTheorem 2, coverage under directional error")
    tol = 4.0 * np.sqrt(0.25 / draws)
    worst = 0.0
    cases = 0
    for S in (3, 15):
        q = chi2.ppf(0.95, S - 1)
        for rho in (14.0, 28.0, 120.0):
            for delta in (0.0, 0.5, 1.6, 4.0, 10.0):
                u = _random_unit(S, rng)
                v = _rotate_by(u, delta, rng)
                Z = rho * u + rng.standard_normal((draws, S))
                R = (Z * Z).sum(1) - (Z @ v) ** 2
                mc = float((R <= q).mean())
                exact = th.coverage_directional(delta, rho, S)
                worst = max(worst, abs(mc - exact))
                cases += 1
    record(worst <= tol, "Monte Carlo coverage matches the closed form",
           f"worst gap {worst:.4f} over {cases} (S, rho, delta) cases, tolerance {tol:.4f}")


def check_corollary(draws: int, rng) -> None:
    """At delta_max the measured coverage equals the target, and delta_max ~ 1/rho."""
    print("\nCorollary, the admissible error shrinks as 1/rho")
    tol = 4.0 * np.sqrt(0.09 / draws)
    S, target = 3, 0.90
    q = chi2.ppf(0.95, S - 1)
    gaps, products = [], []
    for rho in (14.0, 28.0, 56.0, 120.0):
        dm = th.delta_max(rho, S, target)
        products.append(rho * np.sin(np.radians(dm)))
        u = _random_unit(S, rng)
        v = _rotate_by(u, dm, rng)
        Z = rho * u + rng.standard_normal((draws, S))
        R = (Z * Z).sum(1) - (Z @ v) ** 2
        gaps.append(abs(float((R <= q).mean()) - target))
    record(max(gaps) <= tol, "measured coverage at delta_max equals the target",
           f"worst gap {max(gaps):.4f}, tolerance {tol:.4f}")
    spread = float(np.ptp(products) / np.mean(products))
    record(spread < 1e-9, "rho sin(delta_max) is the same at every rho",
           f"value {np.mean(products):.6f}, relative spread {spread:.1e}")


def check_proposition3(rng) -> None:
    """The folded angle obeys the triangle inequality, and the bound is tight."""
    print("\nProposition 3, verdict stability")
    violations, n = 0, 0
    for S in (3, 15):
        for _ in range(20000):
            a, b, c = (rng.standard_normal(S) for _ in range(3))
            if th.folded_angle(a, c) > th.folded_angle(a, b) + th.folded_angle(b, c) + 1e-9:
                violations += 1
            n += 1
    record(violations == 0, "folded angle satisfies the triangle inequality",
           f"{violations} violations in {n} random triples of lines")

    # the bound on the pairwise angle error, on random perturbations
    worst_ratio, n = 0.0, 0
    for S in (3, 15):
        for _ in range(5000):
            uk, ul = _random_unit(S, rng), _random_unit(S, rng)
            dk, dl = rng.uniform(0, 8, 2)
            vk, vl = _rotate_by(uk, dk, rng), _rotate_by(ul, dl, rng)
            err = abs(th.folded_angle(vk, vl) - th.folded_angle(uk, ul))
            worst_ratio = max(worst_ratio, err / (dk + dl))
            n += 1
    record(worst_ratio <= 1.0 + 1e-9, "pairwise angle error never exceeds delta_k + delta_l",
           f"largest ratio of error to bound {worst_ratio:.4f} over {n} cases")

    # tightness: coplanar errors in the same rotational sense attain the bound
    e1, e2 = np.eye(3)[0], np.eye(3)[1]
    th_kl, dk, dl = 30.0, 3.0, 4.0

    def at(deg):
        r = np.radians(deg)
        return np.cos(r) * e1 + np.sin(r) * e2

    err = abs(th.folded_angle(at(0 - dk), at(th_kl + dl)) - th_kl)
    record(abs(err - (dk + dl)) < 1e-9, "the bound is attained by coplanar errors",
           f"error {err:.6f} deg against bound {dk + dl:.1f} deg")


def check_proposition4(draws: int, rng) -> None:
    """Imhof against Monte Carlo, the scalar case, and independence from rho."""
    print("\nProposition 4, noise-model misspecification")
    # scalar case: closed form
    worst = 0.0
    for S in (3, 15):
        q = chi2.ppf(0.95, S - 1)
        for c in (0.8, 1.0, 1.25, 1.5):
            got = th.generalised_chi2_cdf(q, [c ** 2] * (S - 1))
            worst = max(worst, abs(got - chi2.cdf(q / c ** 2, S - 1)))
    record(worst < 1e-9, "Imhof reproduces the scalar case exactly",
           f"worst difference {worst:.1e}")

    # general case against simulation, and no dependence on rho
    tol = 4.0 * np.sqrt(0.25 / draws)
    worst_mc, worst_rho = 0.0, 0.0
    for _ in range(6):
        S = 3
        sig_true = rng.uniform(0.1, 1.5, S)
        sig_twin = sig_true * rng.uniform(0.6, 1.6, S)
        u = _random_unit(S, rng)
        exact = th.coverage_noise_model(u, sig_true, sig_twin)
        D = np.diag(sig_true / sig_twin)
        v = D @ u
        v /= np.linalg.norm(v)
        q = chi2.ppf(0.95, S - 1)
        covs = []
        for rho in (10.0, 100.0):
            Z = (rho * u + rng.standard_normal((draws, S))) @ D.T
            R = (Z * Z).sum(1) - (Z @ v) ** 2
            covs.append(float((R <= q).mean()))
        worst_mc = max(worst_mc, max(abs(cv - exact) for cv in covs))
        worst_rho = max(worst_rho, abs(covs[0] - covs[1]))
    record(worst_mc <= tol, "Imhof coverage matches simulation for ratio errors",
           f"worst gap {worst_mc:.4f}, tolerance {tol:.4f}")
    record(worst_rho <= 2 * tol, "coverage under noise error does not depend on rho",
           f"largest difference between rho = 10 and 100 is {worst_rho:.4f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=200_000)
    args = ap.parse_args()
    rng = np.random.default_rng(20261118)
    print("Checks on the fidelity package")
    print("=" * 74)
    print(f"Monte Carlo draws per cell: {args.draws}")
    check_theorem1(rng)
    check_theorem2(args.draws, rng)
    check_corollary(args.draws, rng)
    check_proposition3(rng)
    check_proposition4(args.draws, rng)

    failed = [r for r in RESULTS if not r[0]]
    print("\n" + "=" * 74)
    print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks passed")
    for _, name, detail in failed:
        print(f"   FAILED  {name}: {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
