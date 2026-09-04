import os
DATA = os.environ.get('AIRCRAFT_XLSX', 'Full_Dataset.xlsx')
import numpy as np, itertools, warnings, pandas as pd
warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from lime.lime_tabular import LimeTabularExplainer

print("="*86)
print("IS TABLE 7 SELF-CONSISTENT?  (can union=14, 6-in-all, 8-unstable give J=0.636?)")
print("="*86)
# 5 runs x 8 slots = 40; 6 core features occupy 30; 8 unstable features share 10 slots.
# If 2 of them appear twice and 6 appear once: 2*2 + 6*1 = 10 slots. Then exactly 2 of the
# 10 pairs share one extra feature.
J = (2*(7/9) + 8*(6/10)) / 10
print(f"  2 pairs with |intersection|=7 -> J=7/9=0.7778")
print(f"  8 pairs with |intersection|=6 -> J=6/10=0.6000")
print(f"  mean = {J:.4f}   <- matches the reported 0.636 exactly")
print("  => Table 7 IS internally self-consistent. It is Table 6 that disagrees with it.")

print()
print("="*86); print("WA-LIME RE-RUN (paper's Section 4.4 protocol)"); print("="*86)
df = pd.read_excel(DATA)
df.columns=[c.replace('Unit Number','unit number').replace('Time (Cycles)','time') for c in df.columns]
df.columns=[' '.join(c.split()).lower() if c not in ('unit number','time','RUL') else c for c in df.columns]
X=df.drop(columns=['unit number']).drop('RUL',axis=1); y=df['RUL']
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=0.2,random_state=42)
gb=GradientBoostingRegressor().fit(Xtr,ytr); cols=list(X.columns); NF=len(cols); row=Xte.iloc[10].values

def base(seed, k=8):
    ex=LimeTabularExplainer(Xtr.values,feature_names=cols,mode='regression',
                            discretize_continuous=False,random_state=seed)
    return dict(ex.explain_instance(row, gb.predict, num_features=k, num_samples=5000).local_exp[1])

def wa_run(seed0, k=8, m=2, Bmax=50):
    """Eq.18 aggregation + Eq.22/23 stopping rule: top-k unchanged for m successive iters."""
    acc=np.zeros(NF); prev=None; stable=0
    for t in range(1, Bmax+1):
        for i,w in base(seed0+t*1000, k).items(): acc[i]+=abs(w)
        cur=tuple(np.argsort(-(acc/t))[:k])
        if prev is not None and set(cur)==set(prev):
            stable+=1
            if stable>=m: return t, list(cur)
        else: stable=0
        prev=cur
    return Bmax, list(prev)

res=[wa_run(s) for s in (0, 500000, 1000000)]
for i,(t,o) in enumerate(res,1):
    print(f"  WA-LIME run {i}: converged after {t:2d} inner iterations -> "
          f"{[cols[j].replace('sensor measurement','S').replace('operational setting','OS') for j in o]}")
A=[set(o) for _,o in res]
Jw=[len(A[i]&A[j])/len(A[i]|A[j]) for i,j in itertools.combinations(range(3),2)]
union=set().union(*A); allr={f for f in union if all(f in a for a in A)}
print()
print("  %-42s %-12s %s"%("metric","paper","got"))
print("  "+"-"*72)
print("  %-42s %-12s %.4f"%("Mean pairwise Jaccard (WA-LIME)","0.778",np.mean(Jw)))
print("  %-42s %-12s %d of %d"%("Features in top-8 in all runs","7 of 10",len(allr),len(union)))
print("  %-42s %-12s %d"%("Total unique features in any top-8","10",len(union)))
print("  %-42s %-12s %d"%("Boundary-fluctuating features","3",len(union)-len(allr)))
print("  convergence iterations   paper 4, 12, 6   got", [t for t,_ in res])
print()
print("  paper's key qualitative claim: 'Sensor 7 appears in only 1 of the 5 LIME runs")
print("   (rank 6 in run 5 only) ... appears in all three WA-LIME runs'")
s7=cols.index('sensor measurement 7')
print("  -> in MY 5 seeded LIME runs, sensor 7 appears in all 5 (see paper_audit.py),")
print("     so there is no omission for WA-LIME to correct.")
print("  -> in my WA-LIME runs sensor 7 appears in %d of 3."%sum(s7 in a for a in A))
