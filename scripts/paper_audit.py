"""Audit every number in Tolu_Revamped_V10.pdf against a re-run."""
import os
DATA = os.environ.get('AIRCRAFT_XLSX', 'Full_Dataset.xlsx')
import numpy as np, pandas as pd, itertools, warnings, joblib
warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from lime.lime_tabular import LimeTabularExplainer


df = pd.read_excel(DATA)
df.columns=[c.replace('Unit Number','unit number').replace('Time (Cycles)','time') for c in df.columns]
df.columns=[' '.join(c.split()).lower() if c not in ('unit number','time','RUL') else c for c in df.columns]

print("#"*90); print("TABLE 2(b)  DATASET DESCRIPTIVE STATISTICS"); print("#"*90)
life = df.groupby('unit number')['time'].max()
print(f"  total engines            paper 218        got {df['unit number'].nunique()}")
print(f"  total cycles             paper 45,918     got {len(df):,}")
print(f"  min engine lifetime      paper 128 (#76)  got {life.min()} (#{life.idxmin()})")
print(f"  max engine lifetime      paper 357 (#5)   got {life.max()} (#{life.idxmax()})")
print(f"  mean engine lifetime     paper 210.63     got {life.mean():.2f}")
print(f"  sigma engine lifetime    paper 43.50      got {life.std():.2f}  (ddof=1) / {life.std(ddof=0):.2f} (ddof=0)")
print(f"  RUL range                paper 0-356      got {df['RUL'].min()}-{df['RUL'].max()}")

X = df.drop(columns=['unit number']).drop('RUL',axis=1); y = df['RUL'].copy()
Xtr,Xte,ytr,yte = train_test_split(X,y,test_size=0.2,random_state=42)
print(f"  training set size        paper 36,734     got {len(Xtr):,}")
print(f"  test set size            paper 9,184      got {len(Xte):,}")

print()
print("#"*90); print("TABLE 5  GBRM PERFORMANCE"); print("#"*90)
gb = GradientBoostingRegressor().fit(Xtr,ytr); yp = gb.predict(Xte)
mse=mean_squared_error(yte,yp); mae=mean_absolute_error(yte,yp); r2=r2_score(yte,yp)
print(f"  MSE   paper 1248.52   got {mse:.4f}")
print(f"  RMSE  paper 35.33     got {np.sqrt(mse):.4f}")
print(f"  MAE   paper 26.96     got {mae:.4f}")
print(f"  R2    paper 0.733     got {r2:.4f}")
print(f"  RMSE/MAE ratio  paper 1.31   got {np.sqrt(mse)/mae:.4f}")
print(f"  hyperparams: lr={gb.learning_rate} n_estimators={gb.n_estimators} max_depth={gb.max_depth} "
      f"min_samples_split={gb.min_samples_split} min_samples_leaf={gb.min_samples_leaf} max_features={gb.max_features}")

print()
print("#"*90); print("SECTION 4.2  TEST INSTANCE #10"); print("#"*90)
row = Xte.iloc[10]
print(f"  GBRM predicted RUL   paper 175.54   got {gb.predict(row.values.reshape(1,-1))[0]:.4f}")
print(f"  actual RUL of that instance: {yte.iloc[10]}")

cols=list(X.columns)
def run(seed, k=8, rank_by='beta'):
    ex=LimeTabularExplainer(Xtr.values, feature_names=cols, mode='regression',
                            discretize_continuous=False, random_state=seed)
    e=ex.explain_instance(row.values, gb.predict, num_features=k, num_samples=5000)
    w=dict(e.local_exp[1])
    if rank_by=='beta_x':
        mu,sc = ex.scaler.mean_, ex.scaler.scale_
        w={i: v*((row.values[i]-mu[i])/sc[i]) for i,v in w.items()}
    order=sorted(w, key=lambda i:-abs(w[i]))
    return order, e.score

seeds=[17*i+3 for i in range(1,6)]
print(f"  paper's seeds s_i = 17i+3, i=1..5  ->  {seeds}")

for rank_by in ('beta','beta_x'):
    print()
    print("="*90)
    print(f"TABLE 6 / 7  LIME ACROSS 5 SEEDED RUNS   (top-8 ranked by |{'beta' if rank_by=='beta' else 'beta * x_tilde'}|)")
    print("="*90)
    sets=[]; scores=[]
    for s in seeds:
        o,sc = run(s, 8, rank_by); sets.append(o); scores.append(sc)
        print("   seed %-3d R2_local=%.4f : %s" % (s, sc, [cols[i].replace('sensor measurement','S').replace('operational setting','OS') for i in o]))
    A=[set(o) for o in sets]
    J=[len(A[i]&A[j])/len(A[i]|A[j]) for i,j in itertools.combinations(range(5),2)]
    # Spearman ON THE INTERSECTION, re-ranked (paper Eq. 16)
    rhos=[]; qs=[]
    for i,j in itertools.combinations(range(5),2):
        inter=A[i]&A[j]; q=len(inter); qs.append(q)
        if q<=1: continue
        ri=[f for f in sets[i] if f in inter]; rj=[f for f in sets[j] if f in inter]
        rk_i={f:r for r,f in enumerate(ri)}; rk_j={f:r for r,f in enumerate(rj)}
        d2=sum((rk_i[f]-rk_j[f])**2 for f in inter)
        rhos.append(1-6*d2/(q*(q*q-1)))
    union=set().union(*A); allruns={f for f in union if all(f in a for a in A)}
    print()
    print("   %-42s %-14s %s" % ("metric","paper","got"))
    print("   %-42s %-14s %.4f" % ("Mean pairwise Jaccard","0.636",np.mean(J)))
    print("   %-42s %-14s %.4f" % ("Mean pairwise Spearman (intersection)","1.000",np.mean(rhos)))
    print("   %-42s %-14s %.4f" % ("Mean local fidelity R2_local","0.843",np.mean(scores)))
    print("   %-42s %-14s %d" % ("Total unique features ever in top-8","14",len(union)))
    print("   %-42s %-14s %d" % ("Features in top-8 in all 5 runs","6",len(allruns)))
    print("   %-42s %-14s %d" % ("Features appearing in <5 runs","8",len(union)-len(allruns)))
    print("   intersection sizes q per pair:", qs)
    print("   always-present:", sorted(cols[i] for i in allruns))
