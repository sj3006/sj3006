"""The twins: one truth, and models that differ from it in one controlled way.

Every case is a `(truth, twin)` pair. For most families truth is the calibrated
model of the earlier papers, `twin.TRUTH`; for the missing-channel family the
roles reverse, because the question there is what a twin loses by omitting
physics the process has.

Families
--------
validation-equivalent
    Absorptivity, conductivity and heat capacity drawn from the region the
    AM-Bench data cannot rule out, with the keyhole coefficient profiled out.
    Twins that any validation against these data would pass equally well.

region-rejected
    Draws from the same box that the data does rule out, for contrast: twins a
    validation would correctly reject.

structural
    The conduction-only refit and the uncalibrated literature-property fit of
    `conduction_baseline`. Real alternative twins, not perturbations.

couplings
    The fault-to-channel constants varied around their derived values. The
    layer constants rotate the layer column; the geometry constant only scales
    its column, so Theorem 1 predicts it is free. The control.

operating point
    The power or speed the twin believes the machine runs at, offset.

noise model
    The four noise sets of the conference paper. Diagnosis-only, through
    whitening.

missing channel
    Plume scattering present in the truth and absent from the twin, and the
    reverse.

The validation region
---------------------
With relative residuals `r_i(theta)` against the seven measured widths and
depths, `n = 14` and four fitted parameters, the set of parameters the data
cannot reject at 95 % is the classical nonlinear-regression region

    ( SSR(theta) - SSR_min ) / p   /   ( SSR_min / (n - 4) )  <=  F_{p, n-4, 0.95}

with `p = 3`, the dimension of the region in (absorptivity, conductivity, heat
capacity). Dividing by the residual variance rather than the measurement
uncertainty keeps the region meaningful when the model is misspecified, as this
one is. The keyhole coefficient enters every depth linearly, so for each sample
its least-squares value is found in closed form and clipped to the calibration's
bounds, which is the exact constrained optimum of a one-dimensional quadratic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import f as f_dist
from scipy.stats import qmc

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

from twin import TRUTH, Twin                                      # noqa: E402
from calibrate import BOUNDS_HI, BOUNDS_LO, WEAVER_POINTS         # noqa: E402
from conduction_baseline import (PROVISIONAL, conduction_only_fit,  # noqa: E402
                                 historical_one_parameter_fit)
from faults import FaultCouplings                                  # noqa: E402
from route_b import RATIO_SETS                                     # noqa: E402
from sensors import SENSOR_NAMES                                   # noqa: E402

__all__ = ["ssr_profiled", "region_threshold", "sample_region", "Case",
           "named_cases", "region_cases", "REGION_CACHE"]

REGION_CACHE = HERE / "_region.json"

#: The box sampled for the validation region: the calibration's own bounds.
BOX_LO = np.array(BOUNDS_LO[:3], float)
BOX_HI = np.array(BOUNDS_HI[:3], float)
C_LO, C_HI = BOUNDS_LO[3], BOUNDS_HI[3]


# ---------------------------------------------------------------------------
# the validation region
# ---------------------------------------------------------------------------
def ssr_profiled(mu: float, k: float, cp: float) -> tuple[float, float]:
    """Sum of squared relative residuals, keyhole coefficient profiled out.

    Width residuals do not involve C. Each depth residual is
    `(d_cond + C h - d_meas) / d_meas`, linear in C, so the optimum is a
    weighted least-squares slope, clipped to the calibration bounds.
    """
    tw = TRUTH.but("probe", absorptivity=mu, k=k, cp=cp, keyhole_c=0.0)
    rw, a, b = [], [], []
    for p in WEAVER_POINTS:
        d = tw.predict_point(p)
        rw.append((d["width"] - p.width) / p.width)
        a.append((d["depth_conduction"] - p.depth) / p.depth)
        b.append(d["keyhole"] / p.depth)
    rw, a, b = (np.asarray(v, float) for v in (rw, a, b))
    C = float(np.clip(-(a @ b) / (b @ b), C_LO, C_HI)) if b @ b > 0 else C_LO
    rd = a + C * b
    return float(rw @ rw + rd @ rd), C


def region_threshold(ssr_min: float, n: int = 14, p: int = 3,
                     n_fit: int = 4, level: float = 0.95) -> float:
    """Largest SSR inside the nonlinear-regression confidence region."""
    F = float(f_dist.ppf(level, p, n - n_fit))
    return ssr_min * (1.0 + p * F / (n - n_fit))


def sample_region(n_samples: int = 2048, seed: int = 0,
                  use_cache: bool = True) -> dict:
    """Sobol points over the calibration box, each with its profiled SSR."""
    if use_cache and REGION_CACHE.exists():
        cached = json.loads(REGION_CACHE.read_text())
        if cached.get("n") == n_samples and cached.get("seed") == seed:
            return cached
    sampler = qmc.Sobol(d=3, scramble=True, seed=seed)
    U = sampler.random(n_samples)
    X = qmc.scale(U, BOX_LO, BOX_HI)
    rows = []
    for mu, k, cp in X:
        ssr, C = ssr_profiled(float(mu), float(k), float(cp))
        rows.append([float(mu), float(k), float(cp), C, ssr])
    ssr_star, C_star = ssr_profiled(TRUTH.absorptivity, TRUTH.k, TRUTH.cp)
    ssr_min = min(ssr_star, min(r[4] for r in rows))
    out = {"n": n_samples, "seed": seed, "rows": rows,
           "ssr_truth": ssr_star, "C_truth_profiled": C_star,
           "ssr_min": ssr_min, "threshold": region_threshold(ssr_min)}
    if use_cache:
        REGION_CACHE.write_text(json.dumps(out))
    return out


# ---------------------------------------------------------------------------
# cases
# ---------------------------------------------------------------------------
class Case:
    """A truth, a twin, and the family the comparison belongs to."""

    def __init__(self, family: str, twin: Twin, truth: Twin = TRUTH,
                 note: str = ""):
        self.family = family
        self.twin = twin
        self.truth = truth
        self.note = note

    @property
    def name(self) -> str:
        return self.twin.name

    def __repr__(self) -> str:
        return f"Case({self.family!r}, {self.name!r})"


def named_cases() -> list[Case]:
    """Every family except the sampled region."""
    cases: list[Case] = []

    # structural alternatives
    c = conduction_only_fit()
    cases.append(Case("structural", TRUTH.but(
        "conduction-only refit", absorptivity=c["absorptivity"],
        k=c["conductivity"], cp=c["heat_capacity"], keyhole_c=0.0),
        note="same three parameters refitted without the keyhole term"))
    h = historical_one_parameter_fit()
    cases.append(Case("structural", TRUTH.but(
        "uncalibrated, one-parameter", absorptivity=h["absorptivity"],
        k=PROVISIONAL.k, cp=PROVISIONAL.cp, keyhole_c=0.0),
        note="literature properties, absorptivity fitted alone"))

    # couplings: the layer constants rotate a column, the geometry one scales it
    base = FaultCouplings()
    for v in (0.0, 0.25, 0.75, 1.0, 1.5):
        cases.append(Case("couplings", TRUTH.but(
            f"layer-to-conductivity {v:g}",
            couplings=FaultCouplings(layer_to_absorptivity=base.layer_to_absorptivity,
                                     layer_to_powder_enthalpy=base.layer_to_powder_enthalpy,
                                     layer_to_conductivity=v,
                                     geometry_preheat_kelvin=base.geometry_preheat_kelvin))))
    for v in (-0.46, -0.115, 0.0):
        cases.append(Case("couplings", TRUTH.but(
            f"layer-to-absorptivity {v:g}",
            couplings=FaultCouplings(layer_to_absorptivity=v,
                                     layer_to_powder_enthalpy=base.layer_to_powder_enthalpy,
                                     layer_to_conductivity=base.layer_to_conductivity,
                                     geometry_preheat_kelvin=base.geometry_preheat_kelvin))))
    for v in (25.0, 50.0, 200.0, 400.0):
        cases.append(Case("couplings control", TRUTH.but(
            f"geometry preheat {v:g} K",
            couplings=FaultCouplings(layer_to_absorptivity=base.layer_to_absorptivity,
                                     layer_to_powder_enthalpy=base.layer_to_powder_enthalpy,
                                     layer_to_conductivity=base.layer_to_conductivity,
                                     geometry_preheat_kelvin=v)),
            note="Theorem 1 predicts no effect on the certificate"))

    # operating point
    for s in (0.90, 0.95, 1.05, 1.10):
        cases.append(Case("operating point", TRUTH.but(
            f"power x{s:.2f}", power=TRUTH.power * s)))
        cases.append(Case("operating point", TRUTH.but(
            f"speed x{s:.2f}", speed=TRUTH.speed * s)))

    # noise model
    for name, ratios in RATIO_SETS.items():
        if name == "derived":
            continue
        cases.append(Case("noise model", TRUTH.but(
            f"noise: {name}", sigmas=tuple(float(ratios[n]) for n in SENSOR_NAMES))))
    for c in (0.8, 0.9, 1.1, 1.25):
        cases.append(Case("noise level", TRUTH.but(
            f"noise level x{c:g}",
            sigmas=tuple(float(s) * c for s in TRUTH.sigmas)),
            note="a common error in the assumed noise; c < 1 underestimates it"))

    # missing or spurious physics
    for k in (0.25, 0.75, 1.0):
        scatter = TRUTH.but(f"scattering k={k:g}", scattering_k=k)
        cases.append(Case("missing channel", TRUTH.but(f"twin omits scattering k={k:g}"),
                          truth=scatter,
                          note="the process broadens the beam; the twin does not"))
        cases.append(Case("spurious channel", scatter,
                          note="the twin broadens the beam; the process does not"))
    return cases


def region_cases(region: dict, max_each: int = 120,
                 seed: int = 1) -> list[Case]:
    """Twins from the sampled box, accepted and rejected by the data."""
    rng = np.random.default_rng(seed)
    rows = np.asarray(region["rows"], float)
    acc = rows[rows[:, 4] <= region["threshold"]]
    rej = rows[rows[:, 4] > region["threshold"]]
    pick = lambda R: R[rng.choice(len(R), size=min(max_each, len(R)),
                                  replace=False)] if len(R) else R
    out = []
    for fam, R in (("validation-equivalent", pick(acc)),
                   ("region-rejected", pick(rej))):
        for i, (mu, k, cp, C, ssr) in enumerate(R):
            out.append(Case(fam, TRUTH.but(
                f"{fam} {i}", absorptivity=float(mu), k=float(k), cp=float(cp),
                keyhole_c=float(C)), note=f"SSR {ssr:.4f}"))
    return out


if __name__ == "__main__":
    import time
    t = time.time()
    reg = sample_region()
    rows = np.asarray(reg["rows"])
    acc = rows[:, 4] <= reg["threshold"]
    print(f"sampled {len(rows)} points in {time.time() - t:.0f}s")
    print(f"SSR at the calibrated point {reg['ssr_truth']:.5f} "
          f"(keyhole coefficient profiled to {reg['C_truth_profiled']:.3f})")
    print(f"SSR minimum over the samples and truth {reg['ssr_min']:.5f}")
    print(f"region threshold {reg['threshold']:.5f}; {acc.sum()} of {len(rows)} "
          f"samples inside ({acc.mean():.1%})")
    A = rows[acc]
    for j, nm in enumerate(("absorptivity", "conductivity", "heat capacity")):
        print(f"   {nm:14s} accepted range {A[:, j].min():8.3f} to {A[:, j].max():8.3f}"
              f"   box {BOX_LO[j]:g} to {BOX_HI[j]:g}")
    print(f"\n{len(named_cases())} named cases")
