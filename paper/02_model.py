"""Stage 02 - GBRM performance under BOTH splits.  Produces the model table."""
from _lib import CFG, banner, build_model, load_frame, write_csv, write_json
import numpy as np
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score)
from sklearn.dummy import DummyRegressor

banner("STAGE 02  MODEL PERFORMANCE")

def evaluate(split):
    gb, Xtr, Xte, ytr, yte, g_te = build_model(split)
    p = gb.predict(Xte)
    mse = mean_squared_error(yte, p)
    return dict(split=split, n_train=len(Xtr), n_test=len(Xte),
                mse=mse, rmse=float(np.sqrt(mse)),
                mae=float(mean_absolute_error(yte, p)),
                r2=float(r2_score(yte, p)),
                gb=gb, Xtr=Xtr, Xte=Xte, ytr=ytr, yte=yte, g_te=g_te)

res = {s: evaluate(s) for s in ("random", "grouped")}

rows = []
for s in ("random", "grouped"):
    r = res[s]
    label = ("row-level 80/20" if s == "random" else "engine-level 80/20")
    rows.append((label, f"{r['n_train']:,}", f"{r['n_test']:,}",
                 f"{r['mse']:.2f}", f"{r['rmse']:.2f}", f"{r['mae']:.2f}",
                 f"{r['r2']:.4f}"))
    print(f"  {label:<20} MSE={r['mse']:9.2f}  RMSE={r['rmse']:6.2f}  "
          f"MAE={r['mae']:6.2f}  R2={r['r2']:.4f}")

write_csv("t02_model.csv", rows,
          ["split", "n_train", "n_test", "MSE", "RMSE", "MAE", "R2"])

# context a reviewer will want
r = res[CFG.SPLIT]
dummy = DummyRegressor().fit(r["Xtr"], r["ytr"])
base_r2 = r2_score(r["yte"], dummy.predict(r["Xte"]))
imp = dict(sorted(zip(r["Xtr"].columns, r["gb"].feature_importances_),
                  key=lambda t: -t[1]))
top = list(imp.items())[:6]

print(f"\n  mean-baseline R2            {base_r2:+.4f}")
print(f"  RUL sd on the test set      {r['yte'].std(ddof=1):.2f} cycles")
# how many engines appear on both sides of each split
df_all = load_frame()
groups_all = df_all['unit number'].values
for s_ in ('random', 'grouped'):
    te = set(res[s_]['g_te'])
    print(f"  engines in the {s_:<8} test set: {len(te)} of {df_all['unit number'].nunique()}")

print("  top feature importances:")
for k, v in top:
    print(f"     {k:<26} {v:.4f}")

# 'time' is one term of the RUL definition (RUL = T_max - time), so quantify
# how much of the fit rests on it before claiming a sensor-driven explanation.
from sklearn.ensemble import GradientBoostingRegressor
Xtr2, Xte2 = r["Xtr"].drop(columns=["time"]), r["Xte"].drop(columns=["time"])
g2 = GradientBoostingRegressor(random_state=CFG.MODEL_SEED).fit(Xtr2, r["ytr"])
r2_no_time = r2_score(r["yte"], g2.predict(Xte2))
print(f"\n  R2 with 'time'              {r['r2']:.4f}")
print(f"  R2 without 'time'           {r2_no_time:.4f}")

write_json("s02_model.json", {
    s: {k: v for k, v in res[s].items()
        if k in ("split", "n_train", "n_test", "mse", "rmse", "mae", "r2")}
    for s in res} | {
    "primary_split": CFG.SPLIT,
    "baseline_r2": float(base_r2),
    "r2_without_time": float(r2_no_time),
    "feature_importance": {k: float(v) for k, v in imp.items()},
})
