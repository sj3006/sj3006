import os
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results') + os.sep
os.makedirs(P, exist_ok=True)
DATA = os.environ.get('AIRCRAFT_XLSX', os.path.join(os.path.dirname(P.rstrip(os.sep)), 'Full_Dataset.xlsx'))
import pandas as pd, numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score

df = pd.read_excel(DATA)
# normalise the exported column names back to the notebook's names
df.columns = [c.replace('Unit Number', 'unit number').replace('Time (Cycles)', 'time')
              for c in df.columns]
df.columns = [' '.join(c.split()).lower() if c not in ('unit number','time','RUL') else c for c in df.columns]
print("cols:", list(df.columns))

# --- 1. Verify RUL == last_time - time, per engine (notebook cell 15) ---
rul_check = df.groupby('unit number')['time'].transform('last') - df['time']
print("\n[RUL] matches last()-time :", bool((rul_check == df['RUL']).all()))
rul_max = df.groupby('unit number')['time'].transform('max') - df['time']
print("[RUL] matches max()-time  :", bool((rul_max == df['RUL']).all()))
print("[RUL] engines:", df['unit number'].nunique(), " rows:", len(df))
print("[RUL] min RUL per engine all zero:", bool((df.groupby('unit number')['RUL'].min()==0).all()))

# --- 2. Reproduce split + GBR exactly as notebook ---
X = df.drop(columns=['unit number']).drop('RUL', axis=1)
y = df['RUL'].copy()
print("\n[features] n=%d ->" % X.shape[1], list(X.columns))

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
gb = GradientBoostingRegressor()
gb.fit(X_train, y_train)
y_pred = gb.predict(X_test)
print("\n[GBRM default params] MSE = %.10f" % mean_squared_error(y_test, y_pred))
print("[GBRM default params] R2  = %.10f" % r2_score(y_test, y_pred))
print("  paper/notebook:        MSE = 1248.5247554117475, R2 = 0.7331471442860311")
print("  RMSE = %.4f cycles" % np.sqrt(mean_squared_error(y_test, y_pred)))
print("  y_test std = %.4f, var = %.4f" % (y_test.std(), y_test.var()))

# determinism check: default GBR has subsample=1.0, max_features=None -> no RNG use
gb2 = GradientBoostingRegressor().fit(X_train, y_train)
print("\n[determinism] identical preds across two unseeded fits:", np.array_equal(y_pred, gb2.predict(X_test)))

import joblib, os
joblib.dump((gb, X_train, X_test, y_train, y_test), P + 'model.joblib')
