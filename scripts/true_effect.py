"""Well-powered estimate of the LIME vs WA-LIME effect on the paper's own
instance #10, plus the compute-matched baseline."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import RESULTS as P, DATA, load_frame, load_xy, get_model
import numpy as np, itertools, warnings, pandas as pd
warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from lime.lime_tabular import LimeTabularExplainer

df = load_frame()
X=df.drop(columns=['unit number']).drop('RUL',axis=1); y=df['RUL']
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=0.2,random_state=42)
gb=GradientBoostingRegressor().fit(Xtr,ytr); cols=list(X.columns); NF=len(cols); row=Xte.iloc[10].values
SEED=[0]
def weights(k=NF, ns=5000):
    SEED[0]+=1
    ex=LimeTabularExplainer(Xtr.values,feature_names=cols,mode='regression',
                            discretize_continuous=False,random_state=SEED[0])
    w=np.zeros(NF)
    for i,v in ex.explain_instance(row,gb.predict,num_features=k,num_samples=ns).local_exp[1].__iter__():
        pass
    return w
def wvec(k=NF, ns=5000):
    SEED[0]+=1
    ex=LimeTabularExplainer(Xtr.values,feature_names=cols,mode='regression',
                            discretize_continuous=False,random_state=SEED[0])
    e=ex.explain_instance(row,gb.predict,num_features=k,num_samples=ns)
    w=np.zeros(NF)
    for i,v in e.local_exp[1]: w[i]=v
    return w
def wa(B=5, ns=5000):
    a=np.zeros(NF)
    for _ in range(B): a+=np.abs(wvec(NF,ns))/B
    return a
def top8(w): return set(np.argsort(-np.abs(w))[:8])
def jbar(ws):
    S=[top8(w) for w in ws]
    return np.mean([len(S[i]&S[j])/len(S[i]|S[j]) for i,j in itertools.combinations(range(len(S)),2)])
from scipy.stats import spearmanr
def sbar(ws):
    return np.mean([spearmanr(np.abs(ws[i]),np.abs(ws[j])).statistic
                    for i,j in itertools.combinations(range(len(ws)),2)])

R=100
print("="*88)
print(f"WELL-POWERED COMPARISON ON THE PAPER'S OWN INSTANCE #10  (R={R} runs, {R*(R-1)//2:,} pairs)")
print("="*88)
print(f"{'method':<40}{'J@8':>10}{'Spearman(all 25)':>20}{'perturbations':>16}")
print("-"*88)
for name,fn,ns in [("LIME (1x budget, n=5000)", lambda: wvec(NF,5000), "5,000"),
                   ("WA-LIME B=5 (5x budget)",  lambda: wa(5,5000),    "25,000"),
                   ("LIME (5x budget, n=25000)",lambda: wvec(NF,25000),"25,000")]:
    ws=[fn() for _ in range(R)]
    print(f"{name:<40}{jbar(ws):>10.4f}{sbar(ws):>20.4f}{ns:>16}")
