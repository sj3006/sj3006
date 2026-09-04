import os
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results') + os.sep
os.makedirs(P, exist_ok=True)
DATA = os.environ.get('AIRCRAFT_XLSX', os.path.join(os.path.dirname(P.rstrip(os.sep)), 'Full_Dataset.xlsx'))
import pandas as pd, numpy as np, joblib
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.dummy import DummyRegressor
df = pd.read_pickle(P+'data.pkl')
df.columns = [c.replace('Unit Number','unit number').replace('Time (Cycles)','time') for c in df.columns]
df.columns = [' '.join(c.split()).lower() if c not in ('unit number','time','RUL') else c for c in df.columns]
groups = df['unit number'].values
X = df.drop(columns=['unit number']).drop('RUL', axis=1); y = df['RUL'].copy()

# A) run-to-run variance of the *unseeded* GBR on the fixed split
Xtr,Xte,ytr,yte = train_test_split(X,y,test_size=0.2,random_state=42)
ms=[]
for i in range(5):
    m=GradientBoostingRegressor().fit(Xtr,ytr); p=m.predict(Xte)
    ms.append((mean_squared_error(yte,p), r2_score(yte,p)))
ms=np.array(ms)
print("A) Unseeded GBR, fixed split=42, 5 refits:")
for a,b in ms: print("     MSE=%.6f  R2=%.8f"%(a,b))
print("   spread: MSE range=%.4f, R2 range=%.2e"%(np.ptp(ms[:,0]), np.ptp(ms[:,1])))

# B) sensitivity to the split seed
print("\nB) Sensitivity to train_test_split random_state (GBR seeded=0):")
r=[]
for s in [0,1,42,2024,7]:
    a,b,c,d = train_test_split(X,y,test_size=0.2,random_state=s)
    m=GradientBoostingRegressor(random_state=0).fit(a,c); p=m.predict(b)
    r.append((s, mean_squared_error(d,p), r2_score(d,p)))
    print("     seed=%-5d MSE=%9.2f  R2=%.4f"%r[-1])
arr=np.array([x[2] for x in r]); print("   R2 mean=%.4f sd=%.4f"%(arr.mean(),arr.std()))

# C) LEAKAGE: random row split vs engine-wise (group) split
print("\nC) Random-row split vs engine-grouped split (GBR seeded=0):")
gss=GroupShuffleSplit(n_splits=1,test_size=0.2,random_state=42)
tr,te=next(gss.split(X,y,groups))
m=GradientBoostingRegressor(random_state=0).fit(X.iloc[tr],y.iloc[tr]); p=m.predict(X.iloc[te])
print("     GROUPED (no engine in both sides): MSE=%9.2f  R2=%.4f"%(mean_squared_error(y.iloc[te],p), r2_score(y.iloc[te],p)))
print("     RANDOM  (notebook's protocol)    : MSE=%9.2f  R2=%.4f"%(ms[0][0], ms[0][1]))
# how many test engines also appear in train under the notebook split?
tr_idx,te_idx = train_test_split(np.arange(len(X)),test_size=0.2,random_state=42)
ov=len(set(groups[te_idx])&set(groups[tr_idx]))
print("     engines appearing in BOTH train and test (notebook split): %d / %d"%(ov, df['unit number'].nunique()))

# D) 'time' feature contribution
print("\nD) Role of the 'time' feature:")
m=GradientBoostingRegressor(random_state=0).fit(Xtr,ytr)
imp=pd.Series(m.feature_importances_, index=X.columns).sort_values(ascending=False)
print(imp.head(8).to_string())
Xtr2,Xte2 = Xtr.drop(columns=['time']), Xte.drop(columns=['time'])
m2=GradientBoostingRegressor(random_state=0).fit(Xtr2,ytr); p2=m2.predict(Xte2)
print("     WITHOUT 'time': MSE=%9.2f  R2=%.4f"%(mean_squared_error(yte,p2), r2_score(yte,p2)))
# baseline
d=DummyRegressor().fit(Xtr,ytr)
print("     mean baseline : MSE=%9.2f  R2=%.4f"%(mean_squared_error(yte,d.predict(Xte)), r2_score(yte,d.predict(Xte))))
