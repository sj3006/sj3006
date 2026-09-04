"""How much does the paper's J-bar move if you just pick different seeds?
The paper estimates it from 5 runs (10 pairs) -- a very small sample."""
import os
DATA = os.environ.get('AIRCRAFT_XLSX', 'Full_Dataset.xlsx')
import numpy as np, itertools, warnings, pandas as pd
warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from lime.lime_tabular import LimeTabularExplainer

df = pd.read_excel(DATA)
df.columns=[c.replace('Unit Number','unit number').replace('Time (Cycles)','time') for c in df.columns]
df.columns=[' '.join(c.split()).lower() if c not in ('unit number','time','RUL') else c for c in df.columns]
X=df.drop(columns=['unit number']).drop('RUL',axis=1); y=df['RUL']
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=0.2,random_state=42)
gb=GradientBoostingRegressor().fit(Xtr,ytr); cols=list(X.columns); NF=len(cols); row=Xte.iloc[10].values

def top8(seed):
    ex=LimeTabularExplainer(Xtr.values,feature_names=cols,mode='regression',
                            discretize_continuous=False,random_state=int(seed))
    return set(dict(ex.explain_instance(row,gb.predict,num_features=8,num_samples=5000).local_exp[1]))

# 250 independent LIME runs, then resample groups of 5 to get the sampling distribution of J-bar
POOL=250
sets=[top8(s) for s in range(10000,10000+POOL)]
def jbar(idx):
    return np.mean([len(sets[i]&sets[j])/len(sets[i]|sets[j]) for i,j in itertools.combinations(idx,2)])

rng=np.random.RandomState(0)
draws=[jbar(rng.choice(POOL,5,replace=False)) for _ in range(2000)]
draws=np.array(draws)
print("="*80)
print("SAMPLING DISTRIBUTION OF THE PAPER'S J-bar (5 runs, 10 pairs, instance #10)")
print("="*80)
print(f"  based on {POOL} independent LIME runs, 2000 resamples of 5")
print(f"  mean            {draws.mean():.4f}")
print(f"  std             {draws.std():.4f}")
print(f"  min .. max      {draws.min():.4f} .. {draws.max():.4f}")
for p in (1,5,25,50,75,95,99):
    print(f"  {p:3d}th pct       {np.percentile(draws,p):.4f}")
print(f"  fraction of 5-run draws at or below the paper's 0.636: {(draws<=0.636).mean()*100:.2f}%")
print(f"  fraction at or below 0.707 (Table 6's implied value)  : {(draws<=0.7067).mean()*100:.2f}%")

# all-pairs estimate from the full pool
allJ=[len(sets[i]&sets[j])/len(sets[i]|sets[j]) for i,j in itertools.combinations(range(POOL),2)]
print(f"\n  best estimate of LIME's true J-bar (all {len(allJ):,} pairs): {np.mean(allJ):.4f} "
      f"+- {np.std(allJ):.4f}")
# how often is each feature present
from collections import Counter
c=Counter(f for s in sets for f in s)
print("\n  feature presence across the 250 runs:")
for f,n in c.most_common():
    print(f"    {cols[f]:<26} {n:3d}/{POOL}  ({100*n/POOL:.1f}%)")
