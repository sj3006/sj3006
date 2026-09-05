"""Verify notebook cells 30/32/35: LIME + WA-LIME weight aggregation."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import RESULTS as P, DATA, load_frame, load_xy, get_model
import numpy as np, pandas as pd, joblib, warnings
warnings.filterwarnings('ignore')
from lime.lime_tabular import LimeTabularExplainer
gb, X_train, X_test, y_train, y_test = get_model()
cols = list(X_train.columns)

print("="*78)
print("1. local_exp key semantics in LIME regression mode (notebook uses local_exp[1])")
print("="*78)
ex = LimeTabularExplainer(X_train.values, feature_names=cols, mode='regression',
                          discretize_continuous=False, random_state=0)
e = ex.explain_instance(X_test.iloc[10].values, gb.predict, num_features=8)
k0 = dict(e.local_exp[0]); k1 = dict(e.local_exp[1])
print("   keys present          :", sorted(e.local_exp.keys()))
print("   local_exp[0] == -local_exp[1] :", all(np.isclose(k0[i], -k1[i]) for i in k0))
al = dict((cols.index(n), w) for n, w in e.as_list())
print("   as_list()/show_in_notebook() agrees with local_exp[1]:",
      all(np.isclose(al[i], k1[i]) for i in al))
print("   -> local_exp[1] is the SIGN-CORRECT one (dummy_label=1). Notebook is RIGHT.")

print()
print("="*78)
print("2. What cell 32 actually varies (num_samples=100 resamples the BACKGROUND set)")
print("="*78)
row = X_test.iloc[10]

def explain_notebook_style(seed=None):
    """Exact cell-32 protocol: bootstrap 100 training rows, rebuild explainer."""
    idx = np.random.choice(len(X_train), size=100, replace=True)
    sx = X_train.iloc[idx]
    exp = LimeTabularExplainer(sx.values, mode='regression', feature_names=cols,
                               discretize_continuous=False)
    return exp.explain_instance(row.values, gb.predict, num_features=8)

def explain_full_background():
    """LIME sampling variance only: full X_train as background, fresh RNG."""
    exp = LimeTabularExplainer(X_train.values, mode='regression', feature_names=cols,
                               discretize_continuous=False)
    return exp.explain_instance(row.values, gb.predict, num_features=8)

np.random.seed(0)
nb_exps = [explain_notebook_style() for _ in range(5)]
print("   cell-32 style, 5 runs, top-8 feature sets:")
for i, e in enumerate(nb_exps):
    print("     run%d: %s" % (i, [cols[j] for j, _ in e.local_exp[1]]))

print()
print("   LIME default num_samples used for the surrogate:",
      "5000 (explain_instance default) -- NOT the 100 in the notebook variable")
print("   The notebook's `num_samples=100` sizes the bootstrap of the training")
print("   background set; `num_iterations=5` is the number of explanations.")

print()
print("="*78)
print("3. Reproduce cell 35 aggregation (WA-LIME)")
print("="*78)
def aggregate(exps, n=len(cols)):
    w = np.zeros(n)
    for e in exps:
        for fi, wt in e.local_exp[1]:
            w[fi] += np.abs(wt) / len(exps)
    return w

agg = aggregate(nb_exps)
order = np.argsort(agg)[::-1]
print("   top-10 by aggregated |weight|:")
for r, i in enumerate(order[:10]):
    print("     %2d. %-24s %.4f" % (r+1, cols[i], agg[i]))
print("   non-zero features: %d / %d" % ((agg > 0).sum(), len(agg)))
print("   sum of aggregated weights: %.4f" % agg.sum())

# Check: is the divide-by-len correct given truncation to 8?
print()
print("   NOTE ON THE ESTIMATOR: each run contributes only its top-8 features;")
print("   absent features are implicitly counted as 0. So agg[j] is")
print("   mean over 5 runs of (|w_j| if j in top-8 else 0)  --  a *shrunk* mean,")
print("   not the mean |w_j|. Features that are strong-but-inconsistent are")
print("   penalised twice (once by truncation, once by the /5).")
np.save(P+'agg_notebook.npy', agg)
joblib.dump((cols, row), P+'ctx.joblib')
