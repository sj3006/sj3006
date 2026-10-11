"""Parametric noise study: what the sensor suite can resolve, as a function of
how good the sensors are.

Why parametric rather than a single matrix
------------------------------------------
No defensible in-process noise figures exist for these three sensors. The one
published number that looks usable - NIST AMS 100-35's 10 uV resolution on a
35 mV scale - comes from a bench multimeter reading a static blackbody, and
applying it to a sensor running at tens of kilohertz against a melt pool with
plume and spatter in view would flatter the hardware and bias every conclusion
towards "separable". It is not used.

The structural point that shapes this study
-------------------------------------------
Isolability and detectability depend on *different* things.

Whitening divides each sensor row by its own noise. If all three noise levels
scale together, that is a uniform rescaling of the whole Jacobian, and the
angles between fault signatures do not move at all. So:

    isolability (angles, collinearity)  <- depends on noise RATIOS between sensors
    detectability (minimum fault size)  <- depends on ABSOLUTE noise level

A single sweep over "sensor quality" would therefore say nothing about
isolability. The two questions need two different sweeps, which is the main
reason this module exists rather than a one-line loop.
"""

from __future__ import annotations

import numpy as np

from diagnosability import (FAULT_NAMES, SENSOR_NAMES, angles, collinearity_index,
                            detectability, jacobian, whiten)

# Conventional cutoff from the identifiability literature (Brun et al. use 20;
# tighter applications use 10). Below this a subset is considered identifiable.
COLLINEARITY_CUTOFF = 10.0


def isolability_vs_pyrometer_quality(J, ratios) -> None:
    """How good must the pyrometer be, relative to the other two?

    Photodiode and camera both essentially report how large and hot the pool is,
    so they are held at equal noise. The pyrometer asks a different question but
    answers it faintly (responses around 1-3 % of the others), so the live
    question is how precise it must be before that faint answer counts.
    """
    print("ISOLABILITY vs pyrometer noise, relative to photodiode and camera")
    print("ratio = sigma_pyrometer / sigma_photodiode. Small = precise pyrometer.\n")
    pairs = [(a, b) for i, a in enumerate(FAULT_NAMES)
             for j, b in enumerate(FAULT_NAMES) if i < j]
    print(f"   {'ratio':>9s}" + "".join(f"{a[:4]+'/'+b[:4]:>11s}" for a, b in pairs))
    for r in ratios:
        sig = np.array([1.0, 1.0, r])
        Jw = whiten(J, sig)
        ang = angles(Jw)
        print(f"   {r:>9.3g}" + "".join(f"{ang[(a, b)]:>11.2f}" for a, b in pairs))
    print("\n   (degrees, folded to 0-90; small = confounded)")


def rank_limit_note() -> None:
    """Why subsets larger than the sensor count cannot be resolved at any noise."""
    print(f"\nRANK LIMIT: {len(SENSOR_NAMES)} sensors, {len(FAULT_NAMES)} faults")
    print("   A suite of m sensors spans at most m independent directions, so no")
    print("   more than m faults can ever be told apart simultaneously, whatever")
    print("   the noise. With three sensors and five faults, two fault directions")
    print("   are unresolvable by construction before noise is even considered.")
    print("   The collinearity index is therefore only meaningful for subsets of")
    print("   size three or fewer; larger subsets are exactly singular and the")
    print("   index diverges, which is a statement about the hardware, not a bug.")


def collinearity_vs_pyrometer(J, ratios) -> None:
    """Collinearity index for pairs and triples, with the degenerate pair flagged."""
    import itertools
    print("\nCOLLINEARITY INDEX (higher = closer to linearly dependent)")
    print(f"conventional cutoff {COLLINEARITY_CUTOFF:.0f}; above it a subset is not")
    print("practically identifiable. Reported as the worst finite case, with the")
    print("exactly-degenerate power/gas pair excluded since it is infinite at any")
    print("noise and would mask everything else.\n")
    pairs = [s for s in itertools.combinations(range(5), 2)]
    deg = (FAULT_NAMES.index("power"), FAULT_NAMES.index("gas"))
    finite_pairs = [s for s in pairs if set(s) != set(deg)]
    triples = [s for s in itertools.combinations(range(5), 3) if not set(deg) <= set(s)]

    print(f"   {'ratio':>9s}{'worst pair':>13s}{'  (which)':>22s}{'worst triple':>15s}")
    for r in ratios:
        Jw = whiten(J, np.array([1.0, 1.0, r]))
        pv = [(collinearity_index(Jw, s), s) for s in finite_pairs]
        tv = [collinearity_index(Jw, s) for s in triples]
        worst_p, which = max(pv)
        label = f"{FAULT_NAMES[which[0]]}/{FAULT_NAMES[which[1]]}"
        wt = max(tv) if tv else float("inf")
        wt_s = f"{wt:,.0f}" if np.isfinite(wt) and wt < 1e12 else "singular"
        print(f"   {r:>9.3g}{worst_p:>13,.0f}{label:>22s}{wt_s:>15s}")


def detectability_vs_absolute_noise(J, levels) -> None:
    """Minimum detectable fault magnitude against absolute noise.

    Unlike isolability, this does scale with the overall noise level. All three
    sensors held at the same relative noise so the axis means something simple.
    """
    print("\nDETECTABILITY: smallest fault seen at 3 sigma, as a fraction of nominal")
    print("(all sensors at the same relative noise)\n")
    print(f"   {'noise':>8s}" + "".join(f"{n:>11s}" for n in FAULT_NAMES))
    for s in levels:
        Jw = whiten(J, np.array([s, s, s]))
        d = detectability(Jw)
        print(f"   {s:>7.2%}" + "".join(f"{d[n]:>10.2%} " for n in FAULT_NAMES))


if __name__ == "__main__":
    J, _ = jacobian()
    ratios = [1e-3, 1e-2, 3e-2, 1e-1, 3e-1, 1.0, 3.0, 10.0]
    isolability_vs_pyrometer_quality(J, ratios)
    rank_limit_note()
    collinearity_vs_pyrometer(J, ratios)
    detectability_vs_absolute_noise(J, [0.001, 0.003, 0.01, 0.023, 0.05, 0.10])
