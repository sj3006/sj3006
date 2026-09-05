"""
Stability evaluation for LIME vs WA-LIME on the CMAPSS RUL GBRM.
Implements the two metrics missing from the notebook:
  - Jaccard Index on top-k feature SETS   (which features are selected)
  - Spearman rho on feature RANKINGS      (the order of importance)
Both are computed PAIRWISE over R independent repetitions of the same method
on the same instance -- that is what "explanation stability" means.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import RESULTS as P, DATA, load_frame, load_xy, get_model
import numpy as np, pandas as pd, joblib, warnings, itertools, json, sys
warnings.filterwarnings('ignore')
from scipy.stats import spearmanr
from lime.lime_tabular import LimeTabularExplainer

gb, X_train, X_test, y_train, y_test = get_model()
cols = list(X_train.columns); NF = len(cols)
Xtr_np = X_train.values

# ---------------------------------------------------------------- explainers
def weights_full_bg(row, num_features):
    """Plain LIME: full training set as background. Only LIME's own
    perturbation sampling varies between calls."""
    ex = LimeTabularExplainer(Xtr_np, feature_names=cols, mode='regression',
                              discretize_continuous=False)
    e = ex.explain_instance(row, gb.predict, num_features=num_features)
    w = np.zeros(NF)
    for fi, wt in e.local_exp[1]:
        w[fi] = wt
    return w

def weights_boot_bg(row, num_features, n_bg=100):
    """Notebook cell-32 protocol: bootstrap n_bg training rows first, then
    rebuild the explainer. Background resampling + LIME sampling both vary."""
    idx = np.random.choice(len(Xtr_np), size=n_bg, replace=True)
    ex = LimeTabularExplainer(Xtr_np[idx], feature_names=cols, mode='regression',
                              discretize_continuous=False)
    e = ex.explain_instance(row, gb.predict, num_features=num_features)
    w = np.zeros(NF)
    for fi, wt in e.local_exp[1]:
        w[fi] = wt
    return w

def wa_lime(row, B, base, num_features):
    """WA-LIME: mean of |w| over B base explanations (notebook cell 35)."""
    acc = np.zeros(NF)
    for _ in range(B):
        acc += np.abs(base(row, num_features)) / B
    return acc

# ---------------------------------------------------------------- metrics
def jaccard_topk(a, b, k):
    sa = set(np.argsort(-np.abs(a))[:k]); sb = set(np.argsort(-np.abs(b))[:k])
    return len(sa & sb) / len(sa | sb)

def pairwise(mat, k_list):
    """mat: (R, NF) weight vectors from R independent repetitions."""
    R = mat.shape[0]
    out = {f'jaccard@{k}': [] for k in k_list}
    out['spearman_abs'] = []
    for i, j in itertools.combinations(range(R), 2):
        for k in k_list:
            out[f'jaccard@{k}'].append(jaccard_topk(mat[i], mat[j], k))
        rho = spearmanr(np.abs(mat[i]), np.abs(mat[j])).statistic
        out['spearman_abs'].append(rho)
    return {m: (float(np.mean(v)), float(np.std(v))) for m, v in out.items()}

# ---------------------------------------------------------------- experiment
R = 30
K_LIST = [5, 8, 10]
rng = np.random.RandomState(12345)
inst_ids = [10] + list(rng.choice(len(X_test), 9, replace=False))
rows = [X_test.iloc[i].values for i in inst_ids]

CONFIGS = [
    # name,                       base fn,          B,  num_features
    ('LIME (single, full bg)',    weights_full_bg,  1,  NF),
    ('LIME (single, boot-100 bg)',weights_boot_bg,  1,  NF),
    ('WA-LIME B=3  (boot bg)',    weights_boot_bg,  3,  NF),
    ('WA-LIME B=5  (boot bg)',    weights_boot_bg,  5,  NF),
    ('WA-LIME B=10 (boot bg)',    weights_boot_bg, 10,  NF),
    ('WA-LIME B=20 (boot bg)',    weights_boot_bg, 20,  NF),
    ('WA-LIME B=5  (full bg)',    weights_full_bg,  5,  NF),
]
# the notebook as literally written: truncate each base explanation to top-8
CONFIGS_TRUNC = [
    ('LIME as-coded (top-8 trunc)',      weights_boot_bg, 1, 8),
    ('WA-LIME as-coded (B=5, top-8)',    weights_boot_bg, 5, 8),
]

def run(configs, tag):
    print("\n" + "=" * 92)
    print(tag + f"   [R={R} repetitions per instance, {len(rows)} instances, pairwise agreement]")
    print("=" * 92)
    hdr = f"{'method':<30}" + "".join(f"{'J@'+str(k):>14}" for k in K_LIST) + f"{'Spearman':>16}"
    print(hdr); print("-" * len(hdr))
    results = {}
    for name, base, B, nf in configs:
        per_inst = []
        for r in rows:
            mat = np.array([wa_lime(r, B, base, nf) if B > 1 else base(r, nf)
                            for _ in range(R)])
            per_inst.append(pairwise(mat, K_LIST))
        agg = {}
        for m in per_inst[0]:
            agg[m] = (float(np.mean([p[m][0] for p in per_inst])),
                      float(np.mean([p[m][1] for p in per_inst])))
        results[name] = agg
        line = f"{name:<30}"
        for k in K_LIST:
            mu, sd = agg[f'jaccard@{k}']; line += f"  {mu:.3f}±{sd:.3f}"
        mu, sd = agg['spearman_abs']; line += f"    {mu:.4f}±{sd:.4f}"
        print(line)
    return results

r1 = run(CONFIGS, "A. STABILITY OF LIME vs WA-LIME (full 25-feature weight vectors)")
r2 = run(CONFIGS_TRUNC, "B. THE NOTEBOOK'S CODE AS LITERALLY WRITTEN (num_features=8)")

json.dump({'full': r1, 'trunc': r2, 'R': R, 'instances': [int(i) for i in inst_ids]},
          open(P + 'stability_results.json', 'w'), indent=2)
print("\nsaved -> stability_results.json")
