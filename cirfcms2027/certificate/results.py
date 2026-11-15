"""Compute every number the paper quotes, once, into `results.json`.

The conference paper's hardest lesson was that numbers computed in scratch
scripts drift away from the prose that quotes them. So nothing here is
recomputed anywhere else: the figures read this file, the claim registry checks
against this file, and the paper quotes what the registry has checked.

    python3 results.py            # recompute, about four minutes
    python3 results.py --quick    # fewer draws, for a smoke test
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import agents as agent_mod                                 # noqa: E402
import benchmark as bench                                  # noqa: E402
import cases as case_mod                                   # noqa: E402
import classes                                             # noqa: E402
import inference as inf                                    # noqa: E402
import noise                                               # noqa: E402
import observables as obs                                  # noqa: E402
import probe                                               # noqa: E402
from faults import FAULT_NAMES                             # noqa: E402
from sensors import SENSOR_NAMES                           # noqa: E402

OUT = HERE / "results.json"
SNRS = (14.0, 28.0, 56.0, 120.0)


def _angles(Jw) -> dict:
    return {f"{a}|{b}": float(v) for (a, b), v in obs._angles(Jw).items()}


def compute(draws: int, per_cell: int) -> dict:
    t0 = time.time()
    out: dict = {"meta": {"draws": draws, "cases_per_cell": per_cell,
                          "alpha": inf.ALPHA, "eps": inf.EPSILON_REFERENCE,
                          "snrs": list(SNRS), "faults": list(FAULT_NAMES),
                          "sensors": list(SENSOR_NAMES)}}

    inst = inf.instantaneous()
    ctx = inf.build_context(whitening="full")
    ctx_d = inf.build_context(whitening="diagonal")

    # ---- geometry ---------------------------------------------------------
    out["geometry"] = {
        "sigmas": {n: float(v) for n, v in zip(SENSOR_NAMES, noise.SIGMAS)},
        "instantaneous": {
            "jacobian": inst.J.tolist(),
            "whitened_norms": {n: float(v) for n, v in zip(FAULT_NAMES, inst.norms)},
            "angles": _angles(inst.Jw),
            "dof": inst.dof, "n_obs": inst.n_obs,
            "condition": float(np.linalg.cond(inst.Jw)),
        },
        "build_context_full": {
            "whitened_norms": {n: float(v) for n, v in zip(FAULT_NAMES, ctx.norms)},
            "angles": _angles(ctx.Jw), "dof": ctx.dof, "n_obs": ctx.n_obs,
        },
        "build_context_diagonal": {"angles": _angles(ctx_d.Jw)},
    }

    # ---- the floor, derived ----------------------------------------------
    floor = {}
    for reg, key in ((inst, "instantaneous"), (ctx, "build_context")):
        floor[key] = {
            "q": float(inf.chi2_threshold(reg.dof)),
            "snr_for_10deg": float(inf.snr_for_floor(10.0, reg.dof)),
            "cone": {str(r): float(inf.cone_half_angle(r, reg.dof))
                     for r in (10, 15, 20, 25, 28.08, 30, 50, 100, 300)},
            "required_snr": {
                f"{a}|{b}": (None if np.isinf(inf.resolving_snr(v, reg.dof))
                             else float(inf.resolving_snr(v, reg.dof)))
                for (a, b), v in obs._angles(reg.Jw).items()},
        }
        floor[key]["required_magnitudes"] = {}
        for (a, b), v in obs._angles(reg.Jw).items():
            r = inf.resolving_snr(v, reg.dof)
            floor[key]["required_magnitudes"][f"{a}|{b}"] = (
                None if np.isinf(r) else
                {a: float(inf.magnitude_for_snr(r, a, reg)),
                 b: float(inf.magnitude_for_snr(r, b, reg))})
    out["floor"] = floor
    print(f"   geometry and floor               {time.time() - t0:6.1f}s")

    # ---- the channel factorisation and the probe ceiling ------------------
    C = probe.channel_matrix()
    M = probe.observation_matrix()
    c = probe.ceiling()
    out["channels"] = {
        "names": list(probe.CHANNEL_NAMES),
        "C": C.tolist(), "M": M.tolist(),
        "factorisation_error": probe.verify_factorisation(),
        "rank_C": c["rank"],
        "power_gas_exact": c["power_gas_exact"],
        "null_direction": {k: float(v) for k, v in c["null_direction"].items()},
        "preheat_weakness": float(np.abs(M[:, 3]).max() / np.abs(M[:, 0]).max()),
    }
    out["probing"] = {label: s for label, s in probe.compare()}
    best = probe.search_two_point()
    out["probing_best"] = {"operating_point": best["operating_point"],
                           "second_worst": best["best"]["second"],
                           "clears_floor": best["clears_floor"]}
    print(f"   channels and probing             {time.time() - t0:6.1f}s")

    # ---- exact signatures, linearisation error ----------------------------
    response = case_mod.ExactResponse()
    plan = obs.scan_plan()
    dep = {}
    for n in FAULT_NAMES:
        k = FAULT_NAMES.index(n)
        u = inst.Jw[:, k] / inst.norms[k]
        for snr in SNRS:
            f = inf.magnitude_for_snr(snr, n, inst)
            zw = inst.whiten(response.instantaneous(n, f)[0])
            along = float(zw @ u)
            dep[f"{n}|{snr:.0f}"] = {
                "magnitude": float(f), "along": along,
                "perpendicular": float(np.linalg.norm(zw - along * u))}
    out["linearisation"] = {"departure": dep,
                            "q_instantaneous": float(inf.chi2_threshold(inst.dof))}

    # ---- certificates and the benchmark -----------------------------------
    out["certificates"] = {}
    out["benchmark"] = {}
    for label, regime in (("instantaneous", inst), ("build_context", ctx)):
        table = case_mod.SignatureTable(regime, response, plan=plan)
        cs = case_mod.generate(n_per_cell=per_cell, snrs=SNRS,
                               regime_name=("instantaneous" if label == "instantaneous"
                                            else "build context"),
                               response=response, seed=9)
        per_snr = {}
        for snr in SNRS:
            sub = [x for x in cs if x.target_snr == snr]
            per_snr[f"{snr:.0f}"] = {
                "coverage": float(np.mean([x.covered for x in sub])),
                "linear_coverage": float(np.mean(
                    [x.truth in x.linear_certificate for x in sub])),
                "mean_size": float(np.mean([len(x.certificate) for x in sub])),
                "unique": float(np.mean([len(x.certificate) == 1 for x in sub])),
                "empty": float(np.mean([len(x.certificate) == 0 for x in sub])),
                "by_fault": {n: float(np.mean(
                    [len(x.certificate) == 1 for x in sub if x.truth == n]))
                    for n in FAULT_NAMES},
            }
        out["certificates"][label] = per_snr

        arms = agent_mod.deterministic_agents(seed=5)
        scores, _ = bench.run(cs, arms, regime, table)
        out["benchmark"][label] = {
            "n": len(cs), "n_ambiguous": scores[0].n_ambiguous,
            "arms": {s.agent: {k: (None if isinstance(v, float) and np.isnan(v)
                                   else v)
                               for k, v in s.__dict__.items() if k != "agent"}
                     for s in scores}}
        print(f"   certificates, {label:14s}   {time.time() - t0:6.1f}s")

        # admissibility, for the heat maps
        mats = {}
        for snr in SNRS:
            A = classes.admissibility(regime, table, snr,
                                      draws=min(draws, 3000), seed=17)
            mats[f"{snr:.0f}"] = {"matrix": A.tolist(),
                                  "components": classes.components(A),
                                  "cliques": classes.cliques(A)}
        out.setdefault("admissibility", {})[label] = mats
        print(f"   admissibility, {label:13s}   {time.time() - t0:6.1f}s")

    out["meta"]["seconds"] = time.time() - t0
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    draws = 400 if args.quick else 3000
    per_cell = 40 if args.quick else 300
    print(f"Computing results ({'quick' if args.quick else 'full'})")
    res = compute(draws, per_cell)
    OUT.write_text(json.dumps(res, indent=1))
    print(f"\nwritten to {OUT} ({OUT.stat().st_size / 1024:.0f} kB, "
          f"{res['meta']['seconds']:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
