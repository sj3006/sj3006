"""Stage 04 - the headline result: explanation stability.

Three things the paper needs and a 5-run point estimate cannot give:
  1. Jaccard AND Spearman with intervals, over R repetitions per instance,
     pooled across instances.
  2. The B-vs-stability curve, so the aggregation depth is a reported choice
     rather than an arbitrary one.
  3. A COMPUTE-MATCHED control: plain LIME given B x num_samples perturbations.
     WA-LIME with B=5 spends 5x the budget of one LIME call, so without this
     control a reviewer cannot tell aggregation from extra sampling. This is
     the single most likely objection to the contribution.
"""
from _lib import (CFG, banner, bootstrap_over_runs, build_model, lime_weights,
                  pairwise_stability, pick_instances, wa_lime_weights,
                  write_csv, write_json)
import numpy as np

banner("STAGE 04  EXPLANATION STABILITY")
gb, Xtr, Xte, ytr, yte, _ = build_model()
cols = list(Xtr.columns)
inst = pick_instances(Xte, yte)
R, B = CFG.R_REPEATS, CFG.B_AGG
print(f"  split={CFG.SPLIT}  instances={len(inst)}  R={R} reps  "
      f"({R*(R-1)//2} pairs per instance per method)")

METHODS = [("LIME", lambda row, s: lime_weights(gb, Xtr, cols, row, s)[0], 1)]
for b in CFG.B_SWEEP:
    METHODS.append((f"WA-LIME B={b}",
                    (lambda b_: lambda row, s: wa_lime_weights(
                        gb, Xtr, cols, row, s, B=b_)[0])(b), b))
if CFG.RUN_COMPUTE_MATCHED:
    METHODS.append((f"LIME n={B*CFG.N_PERTURB} (compute-matched to B={B})",
                    lambda row, s: lime_weights(gb, Xtr, cols, row, s,
                                                n_perturb=B*CFG.N_PERTURB)[0], B))

rows, per_inst_rows, detail = [], [], {}
for name, fn, cost in METHODS:
    pooled = {m: [] for m in [f"jaccard@{k}" for k in CFG.K_LIST] + ["spearman"]}
    boots = []
    for i in inst:
        row = Xte.iloc[i].values
        W = np.array([fn(row, 7000 + i * 100 + r) for r in range(R)])
        st = pairwise_stability(W)
        for m in pooled:
            pooled[m].append(st[m]["mean"])
        lo, hi = bootstrap_over_runs(W, CFG.K_DISPLAY, n_boot=400, seed=i)
        boots.append((lo, hi))
        per_inst_rows.append((name, i,
                              *[f"{st[f'jaccard@{k}']['mean']:.4f}" for k in CFG.K_LIST],
                              f"{st['spearman']['mean']:.4f}"))
    means = {m: float(np.mean(v)) for m, v in pooled.items()}
    sds = {m: float(np.std(v, ddof=1)) for m, v in pooled.items()}
    lo = float(np.mean([b[0] for b in boots])); hi = float(np.mean([b[1] for b in boots]))
    detail[name] = dict(mean=means, sd_across_instances=sds,
                        boot95_jaccard=[lo, hi],
                        perturbations=cost * CFG.N_PERTURB)
    rows.append((name, f"{cost*CFG.N_PERTURB:,}",
                 *[f"{means[f'jaccard@{k}']:.4f} ({sds[f'jaccard@{k}']:.4f})"
                   for k in CFG.K_LIST],
                 f"{means['spearman']:.4f} ({sds['spearman']:.4f})",
                 f"[{lo:.3f}, {hi:.3f}]"))
    print(f"  {name:<44} J@{CFG.K_DISPLAY}={means[f'jaccard@{CFG.K_DISPLAY}']:.4f}  "
          f"rho={means['spearman']:.4f}  perturb={cost*CFG.N_PERTURB:,}")

hdr = (["method", "perturbations"] +
       [f"Jaccard@{k} (sd across instances)" for k in CFG.K_LIST] +
       ["Spearman (sd across instances)", f"95pct bootstrap CI on Jaccard@{CFG.K_DISPLAY}"])
write_csv("t04_stability.csv", rows, hdr)
write_csv("t04_stability_per_instance.csv", per_inst_rows,
          ["method", "instance"] + [f"jaccard@{k}" for k in CFG.K_LIST] + ["spearman"])
write_json("s04_stability.json", {"R": R, "instances": inst, "split": CFG.SPLIT,
                                  "results": detail})

# the comparison the reviewer will make
if CFG.RUN_COMPUTE_MATCHED:
    wa = detail[f"WA-LIME B={B}"]["mean"]
    cm = detail[f"LIME n={B*CFG.N_PERTURB} (compute-matched to B={B})"]["mean"]
    k = CFG.K_DISPLAY
    banner("COMPUTE-MATCHED VERDICT")
    print(f"  at {B*CFG.N_PERTURB:,} perturbations:")
    print(f"    WA-LIME B={B}          Jaccard@{k} = {wa[f'jaccard@{k}']:.4f}   "
          f"Spearman = {wa['spearman']:.4f}")
    print(f"    plain LIME, same cost  Jaccard@{k} = {cm[f'jaccard@{k}']:.4f}   "
          f"Spearman = {cm['spearman']:.4f}")
    dj = wa[f'jaccard@{k}'] - cm[f'jaccard@{k}']
    ds = wa['spearman'] - cm['spearman']
    print(f"    difference (WA - LIME) dJ = {dj:+.4f}   drho = {ds:+.4f}")
    if dj <= 0 and ds <= 0:
        print("\n  WA-LIME does NOT beat the compute-matched baseline on either metric.")
        print("  Do not claim aggregation is the source of the gain. Either re-frame")
        print("  the contribution (simplicity / budget curve) or find a regime where")
        print("  aggregation wins -- robustness to background choice is the candidate.")
    elif dj > 0 and ds > 0:
        print("\n  WA-LIME beats the compute-matched baseline on both metrics.")
        print("  This is the result to lead with -- quote both rows together.")
    else:
        print("\n  Mixed: WA-LIME wins on one metric, loses on the other. Report both.")
