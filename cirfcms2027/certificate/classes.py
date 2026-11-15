"""Which causes travel together, and whether they do so by noise or by algebra.

The certificate is data-dependent: two runs of the same fault at the same
severity can license different sets, because the noise differs. That is correct
behaviour for a run-time object, but a machine designer needs a design-time one,
and a paper needs a figure. So the certificate is summarised by its sampling
distribution.

The admissibility matrix
------------------------
    A[k, l] = P( l is in the certificate | the true cause is k )

Its diagonal is the coverage, `1 - alpha` by construction, so the diagonal is a
check rather than a result. Its off-diagonal entries are the result: `A[k, l]`
is how often cause `l` survives a build whose actual cause was `k`. An entry
near `1 - alpha` means `l` is admissible essentially whenever `k` is, so the two
are interchangeable on this evidence. An entry near zero means the data tells
them apart.

The matrix need not be symmetric and generally is not. A fault with a short
whitened signature, geometry here, produces a weak observation that lies close
to the origin, where every signature direction passes; a fault with a long one
produces an observation far out along its own direction, where only nearby
directions reach. So a weak cause admits strong ones more readily than the
reverse. Reporting the asymmetry is more honest than symmetrising it.

Equivalence classes, and why the graph is the real object
---------------------------------------------------------
Thresholding `A` at some `beta` gives a graph: an edge wherever one of the two
causes is admissible under the other at least a `beta` fraction of the time.
Grouping by connected components gives something that reads like equivalence
classes, and that is how the result is usually wanted.

But admissibility is not transitive. `k` can be confusable with `l`, and `l`
with `m`, while `k` and `m` are far apart, and merging all three then overstates
the ambiguity. Connected components are therefore the conservative summary, and
the maximal cliques are the optimistic one. Both are reported, and where they
disagree the graph itself is what the paper should print.

Noise-limited against structural
--------------------------------
An entry that falls towards zero as the signal grows is noise-limited: enough
signal resolves it. An entry that does not is structural, and no instrument
improvement or longer averaging touches it. Power against gas is the second
kind, because the two Jacobian columns are proportional, so its entry sits at
`1 - alpha` at every signal level. Sweeping the signal and reporting which
entries move is how the paper separates the two, and it is the claim that
survives any objection about noise figures.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import cases                                      # noqa: E402
import inference as inf                           # noqa: E402
import observables as obs                         # noqa: E402
from faults import FAULT_NAMES                    # noqa: E402

__all__ = ["admissibility", "components", "cliques", "structural_entries", "report"]

#: An entry at or above this counts as "these two travel together".
BETA = 0.5


def admissibility(regime: inf.Regime, table: cases.SignatureTable, rho: float,
                  draws: int = 4000, alpha: float = inf.ALPHA,
                  seed: int = 0) -> np.ndarray:
    """`A[k, l] = P(l in certificate | truth = k)` at signal-to-noise `rho`.

    Observations come from the exact signature at the magnitude giving `rho`,
    so the matrix inherits the model's curvature rather than assuming it away.
    """
    rng = np.random.default_rng(seed)
    q = inf.chi2_threshold(regime.dof, alpha)
    A = np.empty((len(FAULT_NAMES), len(FAULT_NAMES)))
    for k, truth in enumerate(FAULT_NAMES):
        f = inf.magnitude_for_snr(rho, truth, regime)
        grid = table.magnitudes[truth]
        if not grid[0] <= f <= grid[-1]:
            raise ValueError(
                f"rho={rho} needs {truth} magnitude {f:.4g}, outside the cached "
                f"response grid [{grid[0]:.4g}, {grid[-1]:.4g}]. Raise "
                f"cases.GRID_SNR and clear cases.CACHE, or sweep lower. Reading "
                f"a clipped table shows up as the diagonal falling below 1-alpha.")
        # the exact whitened signature at that magnitude, read off the table
        idx = int(np.argmin(np.abs(grid - f)))
        mean = table.points[truth][idx]
        Z = mean + rng.standard_normal((draws, regime.n_obs))
        A[k, :] = (table.residuals(Z) <= q).mean(0)
    return A


def _edges(A: np.ndarray, beta: float = BETA) -> set[frozenset[int]]:
    n = A.shape[0]
    return {frozenset((i, j)) for i in range(n) for j in range(n)
            if i != j and max(A[i, j], A[j, i]) >= beta}


def components(A: np.ndarray, beta: float = BETA) -> list[list[str]]:
    """Connected components of the ambiguity graph: the conservative summary."""
    edges = _edges(A, beta)
    parent = list(range(A.shape[0]))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for e in edges:
        a, b = tuple(e)
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    groups: dict[int, list[str]] = {}
    for i, n in enumerate(FAULT_NAMES):
        groups.setdefault(find(i), []).append(n)
    return sorted(groups.values(), key=lambda g: (-len(g), g[0]))


def cliques(A: np.ndarray, beta: float = BETA) -> list[list[str]]:
    """Maximal cliques of the ambiguity graph: the optimistic summary.

    A clique is a set every member of which is confusable with every other, so
    it is a set that genuinely cannot be taken apart, rather than one merged
    through a chain.
    """
    n = A.shape[0]
    adj = {i: {j for j in range(n) if i != j and
               max(A[i, j], A[j, i]) >= beta} for i in range(n)}
    found: list[set[int]] = []

    def extend(R: set[int], P: set[int], X: set[int]) -> None:
        if not P and not X:
            found.append(set(R))
            return
        for v in list(P):
            extend(R | {v}, P & adj[v], X & adj[v])
            P = P - {v}
            X = X | {v}

    extend(set(), set(range(n)), set())
    out = [sorted(FAULT_NAMES[i] for i in c) for c in found if len(c) > 1]
    return sorted(out, key=lambda g: (-len(g), g[0]))


def structural_entries(regime: inf.Regime, alpha: float = inf.ALPHA
                       ) -> dict[tuple[str, str], float]:
    """Each pair's required signal-to-noise, and infinity where it is degenerate.

    Deciding structural against noise-limited by simulation would mean sweeping
    the signal until the admissibility entry falls away, and the signal needed
    is reached only at fault magnitudes the forward model has no business being
    evaluated at: separating power from layer wants a 99 % power deviation, and
    layer from gas wants a severity index of 2.7 where 1.0 is the convention for
    "severe". Those are not faults, they are different processes.

    So the question is settled on the geometry instead, where it is exact. A
    pair is noise-limited if its whitened angle is non-zero, with the required
    ratio given by the resolvability inequality, and structural if the two
    Jacobian columns are proportional, in which case no ratio suffices.
    """
    out = {}
    for pair, angle in obs._angles(regime.Jw).items():
        out[pair] = inf.resolving_snr(angle, regime.dof, alpha)
    return out


def report() -> None:
    print("Which causes travel together")
    print("=" * 74)
    response = cases.ExactResponse()
    plan = obs.scan_plan()
    # capped so every required magnitude stays inside the cached response
    # grid, which reaches rho = 240; see the guard in `admissibility`.
    rhos = (14.0, 28.0, 56.0, 120.0)

    for name in ("instantaneous", "build context"):
        regime = (inf.instantaneous() if name == "instantaneous"
                  else inf.build_context(whitening="full", plan=plan))
        table = cases.SignatureTable(regime, response, plan=plan)
        mats = {}
        print(f"\n{name}")
        for rho in rhos:
            A = admissibility(regime, table, rho, draws=3000, seed=17)
            mats[rho] = A
            print(f"\n   admissibility at rho = {rho:.0f}, "
                  f"rows are the truth, columns what survives")
            print("      " + "".join(f"{n[:4]:>9s}" for n in FAULT_NAMES))
            for i, n in enumerate(FAULT_NAMES):
                print(f"      {n:9s}" + "".join(f"{A[i, j]:9.3f}" for j in range(5)))
            comp = components(A)
            clq = cliques(A)
            print(f"      components: " +
                  " | ".join("+".join(g) for g in comp))
            print(f"      cliques:    " +
                  (" | ".join("+".join(g) for g in clq) if clq else "none"))
        need = structural_entries(regime)
        print(f"\n   required signal-to-noise, and the magnitudes it implies")
        for (a, b), r in sorted(need.items(), key=lambda x: x[1]):
            if r == float("inf"):
                print(f"      {a + ' / ' + b:22s} degenerate, no ratio resolves it")
            else:
                fa = inf.magnitude_for_snr(r, a, regime)
                fb = inf.magnitude_for_snr(r, b, regime)
                mark = "  <- within the swept range" if r <= max(rhos) else ""
                print(f"      {a + ' / ' + b:22s} rho {r:9.1f}   "
                      f"{a} f={fa:7.3f}, {b} f={fb:7.3f}{mark}")

    print("\nNote on the diagonal: it is the coverage, fixed at 0.95 by the test's")
    print("construction, so it is a check on the implementation and not a result.")


if __name__ == "__main__":
    report()
