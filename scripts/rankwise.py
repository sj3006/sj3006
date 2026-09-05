"""Rank-position analysis: which feature occupies each rank, how often, and how
concentrated that position is. Tests the paper's bimodal-stability claim (§4.3)
with 200 runs instead of 5."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import RESULTS as P, DATA, load_frame, load_xy, get_model
import numpy as np, pandas as pd, warnings, json, math
from collections import Counter
warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from lime.lime_tabular import LimeTabularExplainer

df = load_frame()
X=df.drop(columns=['unit number']).drop('RUL',axis=1); y=df['RUL']
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=0.2,random_state=42)
gb=GradientBoostingRegressor().fit(Xtr,ytr)
cols=list(X.columns); NF=len(cols); row=Xte.iloc[10].values
short={c:c.replace('sensor measurement ','S').replace('operational setting ','OS') for c in cols}

def lime_ordered(seed, k=8):
    """Paper protocol: k=8 retained. Returns (ordered feature idxs, |weights|)."""
    ex=LimeTabularExplainer(Xtr.values,feature_names=cols,mode='regression',
                            discretize_continuous=False,random_state=int(seed))
    le=ex.explain_instance(row,gb.predict,num_features=k,num_samples=5000).local_exp[1]
    le=sorted(le,key=lambda t:-abs(t[1]))
    return [i for i,_ in le], [abs(w) for _,w in le]

def walime_ordered(seed0,B=5,k=8):
    acc=np.zeros(NF)
    for b in range(B):
        idx,w=lime_ordered(seed0*100+b,k)
        for i,v in zip(idx,w): acc[i]+=v/B
    o=np.argsort(-acc)[:k]
    return list(o),[acc[i] for i in o]

R=200
print("computing %d LIME runs ..."%R, flush=True)
L=[lime_ordered(900000+s) for s in range(R)]
RW=100
print("computing %d WA-LIME(B=5) runs ..."%RW, flush=True)
W=[walime_ordered(7000+s) for s in range(RW)]

def rank_table(runs,label,n):
    print()
    print("="*94)
    print(f"{label}   (n = {n} independent runs, instance #10, top-k = 8)")
    print("="*94)
    print(f"  {'rank':<6}{'modal feature':<16}{'share':<10}{'distinct':<10}{'H/Hmax':<9}{'runner-up':<26}{'mean |w|'}")
    print("  "+"-"*90)
    out=[]
    for r in range(8):
        c=Counter(o[r] for o,_ in runs)
        tot=sum(c.values())
        top=c.most_common()
        share=top[0][1]/tot
        H=-sum((v/tot)*math.log(v/tot) for v in c.values())
        Hmax=math.log(len(c)) if len(c)>1 else 1.0
        nh=H/math.log(NF)          # normalise against all 25 features
        ru = f"{short[cols[top[1][0]]]} {top[1][1]/tot*100:.0f}%" if len(top)>1 else "-"
        mw=np.mean([w[r] for _,w in runs])
        print(f"  {r+1:<6}{short[cols[top[0][0]]]:<16}{share*100:>5.1f}%    {len(c):<10}{nh:<9.3f}{ru:<26}{mw:>8.2f}")
        out.append(dict(rank=r+1,modal=cols[top[0][0]],share=share,distinct=len(c),
                        norm_entropy=nh,mean_abs_w=float(mw),
                        dist={cols[k_]:v/tot for k_,v in top}))
    return out

lo=rank_table(L,"LIME  — rank-position occupancy",R)
wo=rank_table(W,"WA-LIME (B = 5) — rank-position occupancy",RW)

print()
print("="*94); print("SIDE BY SIDE: how concentrated is each rank position?"); print("="*94)
print(f"  {'rank':<6}{'LIME modal share':<20}{'LIME distinct':<16}{'WA-LIME modal share':<22}{'WA-LIME distinct'}")
print("  "+"-"*90)
for a,b in zip(lo,wo):
    print(f"  {a['rank']:<6}{a['share']*100:>6.1f}%             {a['distinct']:<16}{b['share']*100:>6.1f}%               {b['distinct']}")

print()
print("full occupancy distribution, LIME (features holding each rank in >2% of runs):")
for a in lo:
    parts=[f"{short[k_]} {v*100:.0f}%" for k_,v in a['dist'].items() if v>0.02]
    print(f"   rank {a['rank']}: "+", ".join(parts))
print()
print("full occupancy distribution, WA-LIME B=5:")
for b in wo:
    parts=[f"{short[k_]} {v*100:.0f}%" for k_,v in b['dist'].items() if v>0.02]
    print(f"   rank {b['rank']}: "+", ".join(parts))
json.dump({'lime':lo,'walime':wo,'R_lime':R,'R_walime':RW}, open(P+'rankwise.json','w'), indent=2, default=float)
