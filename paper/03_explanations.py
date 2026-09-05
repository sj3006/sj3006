"""Stage 03 - the reference explanation for each study instance.

Gives the paper: the single-explanation figure material, the local fidelity of
the surrogate, and the aggregated (WA-LIME) explanation with BOTH the signed
weights and the magnitudes.
"""
from _lib import (CFG, SHORT, banner, build_model, lime_weights, pick_instances,
                  wa_lime_weights, write_csv, write_json)
import numpy as np

banner("STAGE 03  REFERENCE EXPLANATIONS")
gb, Xtr, Xte, ytr, yte, _ = build_model()
cols = list(Xtr.columns)
inst = pick_instances(Xte, yte)
print(f"  split={CFG.SPLIT}  instances={inst}")

rows, agg_rows, meta = [], [], []
for n, i in enumerate(inst):
    row = Xte.iloc[i].values
    pred, actual = float(gb.predict(row.reshape(1, -1))[0]), float(yte.iloc[i])
    w, fid = lime_weights(gb, Xtr, cols, row, seed=1000 + i)
    wa_mag, _ = wa_lime_weights(gb, Xtr, cols, row, seed=2000 + i, signed=False)
    wa_sgn, _ = wa_lime_weights(gb, Xtr, cols, row, seed=2000 + i, signed=True)

    print(f"\n  instance #{i}  predicted RUL {pred:7.2f}   actual {actual:6.1f} "
          f"  residual {pred-actual:+7.2f}   R2_local {fid:.4f}")
    order = np.argsort(-np.abs(w))[:CFG.K_DISPLAY]
    for r, j in enumerate(order, 1):
        print(f"     {r}. {SHORT(cols[j]):<8} {w[j]:+9.3f}  "
              f"({'raises' if w[j] > 0 else 'lowers'} predicted RUL)")
        rows.append((i, r, SHORT(cols[j]), f"{w[j]:+.4f}",
                     "raises" if w[j] > 0 else "lowers"))

    for r, j in enumerate(np.argsort(-wa_mag)[:CFG.K_DISPLAY], 1):
        agg_rows.append((i, r, SHORT(cols[j]), f"{wa_mag[j]:.4f}",
                         f"{wa_sgn[j]:+.4f}",
                         "raises" if wa_sgn[j] > 0 else "lowers"))

    meta.append(dict(instance=i, predicted=pred, actual=actual,
                     residual=pred - actual, r2_local=fid))

write_csv("t03_single_explanation.csv", rows,
          ["instance", "rank", "feature", "weight", "direction"])
write_csv("t03_walime_explanation.csv", agg_rows,
          ["instance", "rank", "feature", "mean_abs_weight", "mean_signed_weight",
           "direction"])
write_json("s03_instances.json", {"split": CFG.SPLIT, "instances": meta,
                                  "mean_r2_local": float(np.mean([m["r2_local"] for m in meta]))})
print(f"\n  mean local fidelity across instances: "
      f"{np.mean([m['r2_local'] for m in meta]):.4f}")
