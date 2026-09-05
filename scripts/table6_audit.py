"""Recompute Table 7 from the ranks the paper itself prints in Table 6."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import RESULTS as P, DATA, load_frame, load_xy, get_model
import itertools, numpy as np

# Table 6 as printed: feature -> {run: rank}
T6 = {
 'Time':      {1:1, 2:1, 3:1, 4:1, 5:1},
 'Sensor 15': {1:2, 2:2, 3:2, 4:2, 5:2},
 'Sensor 11': {1:3, 2:3, 3:3, 4:3, 5:3},
 'Sensor 4':  {1:4, 2:4, 3:4, 4:4, 5:4},
 'Sensor 13': {1:5, 2:5, 3:5, 4:5, 5:5},
 'Sensor 3':  {1:6, 2:6, 3:7, 4:6, 5:6},
 'Sensor 2':  {4:7, 5:7},
 'Sensor 8':  {1:8, 5:8},
 'Sensor 7':  {2:7, 3:6, 4:8},
 'Sensor 14': {1:7, 3:8},
 'Sensor 12': {2:8},
}
runs = {r: {f: d[r] for f, d in T6.items() if r in d} for r in range(1, 6)}

print("="*84)
print("AUDIT OF TABLE 6 (recomputing Table 7 from the paper's own printed ranks)")
print("="*84)
for r in range(1, 6):
    ordered = sorted(runs[r], key=runs[r].get)
    print(f"  run {r}: |A|={len(ordered)}  {ordered}")

A = [set(runs[r]) for r in range(1, 6)]
J = [len(A[i] & A[j]) / len(A[i] | A[j]) for i, j in itertools.combinations(range(5), 2)]

rhos = []
for i, j in itertools.combinations(range(5), 2):
    inter = A[i] & A[j]; q = len(inter)
    if q <= 1: continue
    ri = sorted(inter, key=lambda f: runs[i+1][f]); rj = sorted(inter, key=lambda f: runs[j+1][f])
    rk_i = {f: k for k, f in enumerate(ri)}; rk_j = {f: k for k, f in enumerate(rj)}
    d2 = sum((rk_i[f] - rk_j[f])**2 for f in inter)
    rhos.append(1 - 6*d2 / (q*(q*q - 1)))

union = set().union(*A)
allruns = {f for f in union if all(f in a for a in A)}

print()
print("  pairwise Jaccard values:", [round(x, 4) for x in J])
print()
print("  %-44s %-10s %s" % ("metric", "paper", "Table 6 implies"))
print("  " + "-"*76)
print("  %-44s %-10s %.4f" % ("Mean pairwise Jaccard", "0.636", np.mean(J)))
print("  %-44s %-10s %.4f" % ("Mean pairwise Spearman (intersection)", "1.000", np.mean(rhos)))
print("  %-44s %-10s %d" % ("Total unique features ever in top-8", "14", len(union)))
print("  %-44s %-10s %d" % ("Features in top-8 in all 5 runs", "6", len(allruns)))
print("  %-44s %-10s %d" % ("Features appearing in <5 runs", "8", len(union)-len(allruns)))
print()
print("  features in all 5 runs:", sorted(allruns))
print("  features in <5 runs   :", sorted(union - allruns))
print()
print("  paper's prose names these 8 as the unstable ones:")
print("    Sensors 2, 7, 9, 12, 17, 18, 19, and Operational Setting 3")
print("  Table 6 actually contains:", sorted(union - allruns))
print("  named in prose but ABSENT from Table 6 : Sensors 9, 17, 18, 19, Operational Setting 3")
print("  in Table 6 but MISSING from the prose  : Sensors 8, 14")
print()
print("  pairs whose Spearman < 1 (contradicting the 'exactly 1.000' claim):")
for (i, j), r in zip(itertools.combinations(range(1, 6), 2), rhos):
    if r < 0.9999:
        print(f"    runs {i} vs {j}: rho = {r:.4f}   (Sensor 3 / Sensor 7 swap at ranks 6-7)")
