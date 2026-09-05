"""Is WA-LIME's stability gain due to aggregation, or just 5x the compute?
Compare WA-LIME(B=5, num_samples=5000) against plain LIME with num_samples=25000."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import RESULTS as P, DATA, load_frame, load_xy, get_model
import numpy as np, joblib, warnings, itertools; warnings.filterwarnings('ignore')
from scipy.stats import spearmanr
from lime.lime_tabular import LimeTabularExplainer
gb,Xtr,Xte,ytr,yte=get_model(); cols=list(Xtr.columns); NF=len(cols)

def lime_w(row, ns=5000, bg=None):
    b = Xtr.values if bg is None else bg
    ex=LimeTabularExplainer(b,feature_names=cols,mode='regression',discretize_continuous=False)
    e=ex.explain_instance(row, gb.predict, num_features=NF, num_samples=ns)
    w=np.zeros(NF)
    for fi,wt in e.local_exp[1]: w[fi]=wt
    return w

def wa(row,B=5,ns=5000):
    a=np.zeros(NF)
    for _ in range(B):
        idx=np.random.choice(len(Xtr),100,replace=True)
        a+=np.abs(lime_w(row,ns,Xtr.values[idx]))/B
    return a

def jac(a,b,k):
    sa=set(np.argsort(-np.abs(a))[:k]); sb=set(np.argsort(-np.abs(b))[:k])
    return len(sa&sb)/len(sa|sb)

def stab(mat):
    js8=[];js10=[];sp=[]
    for i,j in itertools.combinations(range(len(mat)),2):
        js8.append(jac(mat[i],mat[j],8)); js10.append(jac(mat[i],mat[j],10))
        sp.append(spearmanr(np.abs(mat[i]),np.abs(mat[j])).statistic)
    return np.mean(js8), np.mean(js10), np.mean(sp)

np.random.seed(0)
R=20
rng=np.random.RandomState(12345)
insts=[10]+list(rng.choice(len(Xte),4,replace=False))
CFG=[("LIME  num_samples=5000  (1x)",  lambda r: lime_w(r,5000)),
     ("LIME  num_samples=25000 (5x)",  lambda r: lime_w(r,25000)),
     ("WA-LIME B=5 x 5000      (5x)",  lambda r: wa(r,5,5000))]
print(f"COMPUTE-MATCHED COMPARISON  (R={R} reps, {len(insts)} instances)")
print(f"{'method':<32}{'J@8':>10}{'J@10':>10}{'Spearman':>12}{'perturbations':>16}")
print("-"*80)
for name,fn in CFG:
    res=[]
    for i in insts:
        row=Xte.iloc[i].values
        res.append(stab(np.array([fn(row) for _ in range(R)])))
    m=np.mean(res,axis=0)
    ns = "5,000" if "5000  (1x)" in name else "25,000"
    print(f"{name:<32}{m[0]:>10.3f}{m[1]:>10.3f}{m[2]:>12.4f}{ns:>16}")
