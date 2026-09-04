"""Per-feature signal-to-noise: quantifies the mechanism §3.7 asserts.
The paper models each run as beta_hat = beta* + eps. If so, a feature's rank
stability should track |mean w| / sd(w) across runs."""
import numpy as np, pandas as pd, warnings, json
warnings.filterwarnings('ignore')
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from lime.lime_tabular import LimeTabularExplainer
import os
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results') + os.sep
df=pd.read_excel(os.environ.get('AIRCRAFT_XLSX','Full_Dataset.xlsx'))
df.columns=[c.replace('Unit Number','unit number').replace('Time (Cycles)','time') for c in df.columns]
df.columns=[' '.join(c.split()).lower() if c not in ('unit number','time','RUL') else c for c in df.columns]
X=df.drop(columns=['unit number']).drop('RUL',axis=1); y=df['RUL']
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=0.2,random_state=42)
gb=GradientBoostingRegressor().fit(Xtr,ytr)
cols=list(X.columns); NF=len(cols); row=Xte.iloc[10].values
short={c:c.replace('sensor measurement ','S').replace('operational setting ','OS') for c in cols}

R=200
M=np.zeros((R,NF))
for s in range(R):
    ex=LimeTabularExplainer(Xtr.values,feature_names=cols,mode='regression',
                            discretize_continuous=False,random_state=800000+s)
    for i,w in ex.explain_instance(row,gb.predict,num_features=NF,num_samples=5000).local_exp[1]:
        M[s,i]=w

mu=M.mean(0); sd=M.std(0); snr=np.abs(mu)/np.where(sd==0,np.nan,sd)
# rank of each feature within each run, by |w|
ranks=np.argsort(np.argsort(-np.abs(M),axis=1),axis=1)+1
mr=ranks.mean(0); rsd=ranks.std(0); top8rate=(ranks<=8).mean(0)

order=np.argsort(-np.abs(mu))
print("="*104)
print(f"PER-FEATURE SIGNAL-TO-NOISE AND RANK STABILITY  (instance #10, {R} untruncated LIME runs)")
print("="*104)
print(f"  {'#':<4}{'feature':<24}{'mean w':>10}{'sd |w|':>9}{'SNR':>8}{'mean rank':>11}{'rank sd':>9}{'in top-8':>10}")
print("  "+"-"*100)
for n,j in enumerate(order,1):
    print(f"  {n:<4}{short[cols[j]]:<24}{mu[j]:>10.3f}{sd[j]:>9.3f}{snr[j]:>8.1f}"
          f"{mr[j]:>11.2f}{rsd[j]:>9.2f}{top8rate[j]*100:>9.1f}%")

print()
print("="*104)
print("THE SNR CLIFF — the paper asserts this mechanism in §3.7 but never measures it")
print("="*104)
band=[("ranks 1-5 (stable core)",[j for j in order[:5]]),
      ("rank 6 (S3)",[order[5]]),
      ("ranks 7-8 (boundary)",[j for j in order[6:8]]),
      ("outside top-8",[j for j in order[8:]])]
print(f"  {'band':<28}{'mean SNR':>10}{'median rank sd':>17}")
print("  "+"-"*56)
for lbl,js in band:
    v=[snr[j] for j in js if not np.isnan(snr[j])]
    print(f"  {lbl:<28}{np.mean(v):>10.1f}{np.median([rsd[j] for j in js]):>17.2f}")
json.dump({'features':[{'feature':cols[j],'mean_w':float(mu[j]),'sd':float(sd[j]),
    'snr':float(snr[j]),'mean_rank':float(mr[j]),'rank_sd':float(rsd[j]),
    'top8_rate':float(top8rate[j])} for j in order]}, open(P+'snr.json','w'), indent=2)
