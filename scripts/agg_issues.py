import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import RESULTS as P, DATA, load_frame, load_xy, get_model
import numpy as np, joblib, warnings; warnings.filterwarnings('ignore')
from lime.lime_tabular import LimeTabularExplainer
gb,Xtr,Xte,ytr,yte=get_model(); cols=list(Xtr.columns); NF=len(cols)
row=Xte.iloc[10].values

print("="*80); print("ISSUE 1: np.abs() discards direction -> explanation loses its meaning"); print("="*80)
ex=LimeTabularExplainer(Xtr.values,feature_names=cols,mode='regression',discretize_continuous=False,random_state=1)
e=ex.explain_instance(row, gb.predict, num_features=8)
print("  A single LIME explanation for X_test.iloc[10] (signed):")
for f,w in e.as_list(): print("     %-24s %+9.4f  (%s RUL)"%(f,w,'increases' if w>0 else 'decreases'))
print("\n  After np.abs() the aggregated bar chart in cells 37/38 can no longer say")
print("  whether a sensor pushes predicted RUL UP or DOWN. For a prognostics paper")
print("  that is the whole actionable content of the explanation.")

print()
print("="*80); print("ISSUE 2: sign cancellation is NOT the reason to use abs -- check it"); print("="*80)
np.random.seed(3)
signs=np.zeros((20,NF)); mags=np.zeros((20,NF))
for t in range(20):
    idx=np.random.choice(len(Xtr),100,replace=True)
    ee=LimeTabularExplainer(Xtr.values[idx],feature_names=cols,mode='regression',discretize_continuous=False)
    ex2=ee.explain_instance(row, gb.predict, num_features=NF)
    for fi,w in ex2.local_exp[1]: signs[t,fi]=np.sign(w); mags[t,fi]=w
flip=[(cols[j], float(np.mean(signs[:,j]>0))) for j in range(NF)]
print("  fraction of 20 runs where the weight is POSITIVE (0 or 1 => stable sign):")
for n,f in sorted(flip,key=lambda x:-abs(x[1]-.5))[:6]: print("     %-24s %.2f"%(n,f))
unstable=[n for n,f in flip if 0.15<f<0.85]
print("  features with UNSTABLE sign across runs: %d / %d -> %s"%(len(unstable),NF,unstable[:6]))
print("  => signed averaging would be safe for the top features; abs() is not needed")
print("     for them, and it destroys interpretability. Report signed mean + the")
print("     magnitude separately.")

print()
print("="*80); print("ISSUE 3: truncation-to-8 shrinks the aggregate (cell 35 vs untruncated)"); print("="*80)
def agg(nf,B=5,seed=7):
    np.random.seed(seed); a=np.zeros(NF)
    for _ in range(B):
        idx=np.random.choice(len(Xtr),100,replace=True)
        ee=LimeTabularExplainer(Xtr.values[idx],feature_names=cols,mode='regression',discretize_continuous=False)
        for fi,w in ee.explain_instance(row,gb.predict,num_features=nf).local_exp[1]: a[fi]+=abs(w)/B
    return a
a8, a25 = agg(8), agg(25)
print("  %-24s %12s %12s %10s"%("feature","agg(top-8)","agg(all 25)","shrinkage"))
for j in np.argsort(-a25)[:10]:
    sh = "-" if a25[j]==0 else "%.1f%%"%(100*(1-a8[j]/a25[j]))
    print("  %-24s %12.4f %12.4f %10s"%(cols[j],a8[j],a25[j],sh))
print("  nonzero: top-8 protocol=%d, untruncated=%d"%((a8>0).sum(),(a25>0).sum()))
