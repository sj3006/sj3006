"""Score every twin on both kinds of fidelity.

For each `(truth, twin)` case:

prediction
    `pred_rms`: root-mean-square relative difference between what the twin and
    the truth predict for a healthy build, at the seven AM-Bench conditions and
    the production operating point. This is what validation against healthy
    data can see. Also the twin's own error against the measured AM-Bench
    dimensions, `amb_mape`, for reference to real data.

direction
    `delta[k]`: the folded angle between the twin's and the truth's signature
    for fault `k`, measured in the truth's whitened space. This is the quantity
    Theorem 2 charges for.

geometry and verdicts
    The ten pairwise angles the twin would report, in its own whitened space,
    against the truth's; and the number of pairs whose verdict at the ten degree
    floor differs, instantaneously and with build context.

certificate
    Coverage of the twin's nominally 95 % certificate when the truth generates
    the observation. For twins whose noise model is right, Theorem 2 gives it
    exactly from `delta`; for twins whose Jacobian is right but whose noise
    model is not, Proposition 4 does. Build-context coverage is at matched
    fault severity: the magnitude that gives `rho` instantaneously gives
    `gain_k * rho` in build context, where `gain_k` is the norm of fault `k`'s
    whitened profile loading, and by Proposition 5 the directional error is the
    same.

Observations are generated from the truth's linearisation, which isolates the
twin's error from the truth's own curvature. That curvature was the subject of
the certificate paper; mixing it in here would attribute to the twin an error
that is the truth's.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import theory as th                                               # noqa: E402
import twins as tw_mod                                            # noqa: E402
import observables as obs                                         # noqa: E402
from faults import FAULT_NAMES                                    # noqa: E402
from twin import TRUTH, Twin                                      # noqa: E402

__all__ = ["Scorer", "score_case", "run", "RHOS", "FLOOR"]

RHOS = (14.0, 28.0, 56.0, 120.0)
FLOOR = 10.0
JCACHE = HERE / "_jacobians.json"


def _jkey(t: Twin) -> str:
    """Everything the Jacobian depends on; not the keyhole term or the noise."""
    c = t.couplings
    return json.dumps([round(t.absorptivity, 12), round(t.k, 12), round(t.cp, 12),
                       round(t.power, 12), round(t.speed, 12),
                       c.layer_to_absorptivity, c.layer_to_powder_enthalpy,
                       c.layer_to_conductivity, c.geometry_preheat_kelvin,
                       round(t.scattering_k, 12), int(t.n_grid)])


class Scorer:
    """Holds the build plan and a Jacobian cache shared across cases."""

    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self.cache: dict[str, list] = {}
        if use_cache and JCACHE.exists():
            self.cache = json.loads(JCACHE.read_text())
        plan = obs.scan_plan()
        G = obs.regressors(plan)
        self.GtGinv = np.linalg.inv(G.T @ G)
        self.LG = np.linalg.inv(np.linalg.cholesky(self.GtGinv))
        self.B = obs.projection_matrix(plan)
        # gain of each fault's whitened profile: build-context rho per unit
        # instantaneous rho at the same magnitude (Proposition 5)
        self.gain = np.linalg.norm(self.LG @ self.B, axis=0)

    def J(self, t: Twin) -> np.ndarray:
        key = _jkey(t)
        if key not in self.cache:
            self.cache[key] = t.jacobian().tolist()
        return np.asarray(self.cache[key], float)

    def save(self) -> None:
        if self.use_cache:
            JCACHE.write_text(json.dumps(self.cache))

    def big_whitened(self, J: np.ndarray, sig) -> np.ndarray:
        sig = np.asarray(sig, float)
        Linv = np.kron(np.diag(1.0 / sig), self.LG)
        rows = [J[s, :] * self.B[j, :] for s in range(J.shape[0])
                for j in range(self.B.shape[0])]
        return Linv @ np.vstack(rows)


def _pair_angles(Jw: np.ndarray) -> dict:
    out = {}
    for i in range(5):
        for j in range(i + 1, 5):
            out[f"{FAULT_NAMES[i]}|{FAULT_NAMES[j]}"] = th.folded_angle(Jw[:, i], Jw[:, j])
    return out


def score_case(case: tw_mod.Case, sc: Scorer) -> dict:
    truth, twin = case.truth, case.twin
    Jt, Jm = sc.J(truth), sc.J(twin)
    st = np.asarray(truth.sigmas, float)
    sm = np.asarray(twin.sigmas, float)

    # prediction
    ht, hm = truth.healthy(), twin.healthy()
    rel = (hm - ht) / ht
    pred_rms = 100.0 * float(np.sqrt(np.mean(rel ** 2)))
    pred_max = 100.0 * float(np.max(np.abs(rel)))
    amb = twin.amb_errors()

    # direction, in the truth's whitened space
    Ut = Jt / st[:, None]
    delta = [th.folded_angle(Ut[:, k], Jm[:, k] / st) for k in range(5)]

    # what each would report, each in its own whitened space
    at = _pair_angles(Jt / st[:, None])
    am = _pair_angles(Jm / sm[:, None])
    bt = _pair_angles(sc.big_whitened(Jt, st))
    bm = _pair_angles(sc.big_whitened(Jm, sm))
    dtheta = {p: am[p] - at[p] for p in at}
    flips_inst = sum((am[p] > FLOOR) != (at[p] > FLOOR) for p in at)
    flips_big = sum((bm[p] > FLOOR) != (bt[p] > FLOOR) for p in bt)
    false_sep_inst = sum((am[p] > FLOOR) and not (at[p] > FLOOR) for p in at)
    false_sep_big = sum((bm[p] > FLOOR) and not (bt[p] > FLOOR) for p in bt)

    # certificate coverage
    noise_only = bool(np.allclose(Jm, Jt) and not np.allclose(sm, st))
    cov_inst, cov_big = {}, {}
    for rho in RHOS:
        ci, cb = [], []
        for k in range(5):
            if noise_only:
                u = Ut[:, k] / np.linalg.norm(Ut[:, k])
                ci.append(th.coverage_noise_model(u, st, sm))
                cb.append(float("nan"))     # noise error in build context: not computed
            else:
                ci.append(float(th.coverage_directional(delta[k], rho, 3)))
                cb.append(float(th.coverage_directional(delta[k], sc.gain[k] * rho, 15)))
        cov_inst[f"{rho:.0f}"] = ci
        cov_big[f"{rho:.0f}"] = cb

    return {
        "family": case.family, "name": case.name, "note": case.note,
        "truth": truth.name,
        "twin": {"absorptivity": twin.absorptivity, "k": twin.k, "cp": twin.cp,
                 "keyhole_c": twin.keyhole_c, "power": twin.power,
                 "speed": twin.speed, "sigmas": list(sm),
                 "scattering_k": twin.scattering_k,
                 "couplings": vars(twin.couplings) if hasattr(twin.couplings, "__dict__")
                 else str(twin.couplings)},
        "pred_rms": pred_rms, "pred_max": pred_max,
        "amb_mape": amb["mape"], "amb_width": amb["width_mape"],
        "amb_depth": amb["depth_mape"],
        "delta": delta, "delta_max": max(delta),
        "dtheta": dtheta,
        "dtheta_max": max(abs(v) for v in dtheta.values()),
        "flips_inst": flips_inst, "flips_big": flips_big,
        "false_sep_inst": false_sep_inst, "false_sep_big": false_sep_big,
        "noise_only": noise_only,
        "cov_inst": cov_inst, "cov_big": cov_big,
        "cov_inst_min28": min(cov_inst["28"]),
        "cov_big_min28": (min(cov_big["28"]) if not noise_only else float("nan")),
    }


def _jac_worker(t: Twin):
    return _jkey(t), t.jacobian().tolist()


def precompute(cases, sc: Scorer, workers: int = 4) -> None:
    """Fill the Jacobian cache in parallel; scoring is then cheap."""
    from concurrent.futures import ProcessPoolExecutor
    todo, seen = [], set(sc.cache)
    for c in cases:
        for t in (c.truth, c.twin):
            k = _jkey(t)
            if k not in seen:
                seen.add(k)
                todo.append(t)
    t0 = time.time()
    with ProcessPoolExecutor(workers) as ex:
        for i, (k, J) in enumerate(ex.map(_jac_worker, todo, chunksize=2)):
            sc.cache[k] = J
            if (i + 1) % 20 == 0:
                sc.save()
                print(f"   {i + 1}/{len(todo)} Jacobians, {time.time() - t0:.0f}s",
                      flush=True)
    sc.save()


def run(region_max_each: int = 120, out: Path = HERE / "_study.json") -> dict:
    t0 = time.time()
    sc = Scorer()
    region = tw_mod.sample_region()
    cases = tw_mod.named_cases() + tw_mod.region_cases(region, region_max_each)
    precompute(cases, sc)
    rows = []
    for i, c in enumerate(cases):
        rows.append(score_case(c, sc))
        if (i + 1) % 40 == 0:
            sc.save()
            print(f"   {i + 1}/{len(cases)} cases, {time.time() - t0:.0f}s", flush=True)
    sc.save()
    result = {"rows": rows, "gain": sc.gain.tolist(),
              "region": {k: region[k] for k in ("ssr_truth", "ssr_min",
                                               "threshold", "C_truth_profiled")},
              "n_region_accepted": int(sum(r[4] <= region["threshold"]
                                           for r in region["rows"])),
              "n_region": len(region["rows"]),
              "study_grid": tw_mod.STUDY_GRID,
              "seconds": time.time() - t0}
    out.write_text(json.dumps(result, indent=1, default=float))
    return result


if __name__ == "__main__":
    res = run()
    print(f"\n{len(res['rows'])} cases in {res['seconds']:.0f}s")
