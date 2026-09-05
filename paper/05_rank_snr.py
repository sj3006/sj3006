"""Stage 05 - rank-position occupancy and per-feature signal-to-noise.

Rank occupancy answers "which feature sits at rank r, and how often", which is
a sharper claim than a single averaged Jaccard: it shows WHERE instability
lives and where aggregation helps.

The SNR table measures the mechanism rather than asserting it: if each run is a
noisy estimate b_hat = b* + eps, rank stability should track |mean w| / sd(w).
"""
from _lib import (CFG, SHORT, banner, build_model, lime_weights, pick_instances,
                  wa_lime_weights, write_csv, write_json)
from collections import Counter
import numpy as np

banner("STAGE 05  RANK OCCUPANCY AND SIGNAL-TO-NOISE")
gb, Xtr, Xte, ytr, yte, _ = build_model()
cols = list(Xtr.columns)
inst = pick_instances(Xte, yte)
R, K = CFG.R_RANK, CFG.K_DISPLAY
print(f"  split={CFG.SPLIT}  instances={len(inst)}  R={R} reps")

occ_rows, full_rows, snr_rows = [], [], []
for i in inst:
    row = Xte.iloc[i].values
    Wl = np.array([lime_weights(gb, Xtr, cols, row, 31000 + i * 100 + r)[0]
                   for r in range(R)])
    Ww = np.array([wa_lime_weights(gb, Xtr, cols, row, 41000 + i * 100 + r)[0]
                   for r in range(R)])

    for label, W in (("LIME", Wl), (f"WA-LIME B={CFG.B_AGG}", Ww)):
        order = np.argsort(-np.abs(W), axis=1)
        for r in range(K):
            c = Counter(order[:, r])
            tot = sum(c.values())
            top = c.most_common()
            occ_rows.append((label, i, r + 1, SHORT(cols[top[0][0]]),
                             f"{top[0][1]/tot:.4f}", len(c),
                             f"{np.mean(np.abs(W)[np.arange(len(W)), order[:, r]]):.4f}"))
            for feat, n in top:
                if n / tot >= 0.02:
                    full_rows.append((label, i, r + 1, SHORT(cols[feat]),
                                      f"{n/tot:.4f}"))

    # SNR from the untruncated LIME runs
    mu, sd = Wl.mean(0), Wl.std(0, ddof=1)
    ranks = np.argsort(np.argsort(-np.abs(Wl), axis=1), axis=1) + 1
    for j in np.argsort(-np.abs(mu)):
        snr_rows.append((i, SHORT(cols[j]), f"{mu[j]:+.4f}", f"{sd[j]:.4f}",
                         f"{abs(mu[j])/sd[j]:.2f}" if sd[j] else "inf",
                         f"{ranks[:, j].mean():.2f}", f"{ranks[:, j].std(ddof=1):.2f}",
                         f"{(ranks[:, j] <= K).mean():.4f}"))

write_csv("t05_rank_occupancy.csv", occ_rows,
          ["method", "instance", "rank", "modal_feature", "modal_share",
           "n_distinct", "mean_abs_weight"])
write_csv("t05_rank_occupancy_full.csv", full_rows,
          ["method", "instance", "rank", "feature", "share"])
write_csv("t05_feature_snr.csv", snr_rows,
          ["instance", "feature", "mean_weight", "sd_weight", "snr",
           "mean_rank", "rank_sd", f"top{K}_rate"])

# pooled view across instances - what actually goes in the paper
banner("POOLED RANK STABILITY (mean modal share across instances)")
print(f"  {'rank':<6}{'LIME share':>13}{'LIME distinct':>16}"
      f"{'WA-LIME share':>16}{'WA-LIME distinct':>18}")
print("  " + "-" * 68)
pooled = []
for r in range(1, K + 1):
    a = [float(x[4]) for x in occ_rows if x[0] == "LIME" and x[2] == r]
    an = [x[5] for x in occ_rows if x[0] == "LIME" and x[2] == r]
    b = [float(x[4]) for x in occ_rows if x[0].startswith("WA-LIME") and x[2] == r]
    bn = [x[5] for x in occ_rows if x[0].startswith("WA-LIME") and x[2] == r]
    print(f"  {r:<6}{np.mean(a)*100:>11.1f}%{np.mean(an):>16.1f}"
          f"{np.mean(b)*100:>15.1f}%{np.mean(bn):>18.1f}")
    pooled.append((r, f"{np.mean(a):.4f}", f"{np.mean(an):.2f}",
                   f"{np.mean(b):.4f}", f"{np.mean(bn):.2f}"))
write_csv("t05_rank_pooled.csv", pooled,
          ["rank", "LIME_modal_share", "LIME_n_distinct",
           "WALIME_modal_share", "WALIME_n_distinct"])
write_json("s05_meta.json", {"R": R, "instances": inst, "k": K, "split": CFG.SPLIT})
