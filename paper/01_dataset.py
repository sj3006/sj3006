"""Stage 01 - dataset descriptives.  Produces the Dataset table."""
from _lib import CFG, banner, load_frame, load_xy, write_csv, write_json
import numpy as np

banner("STAGE 01  DATASET DESCRIPTIVES")
df = load_frame()
life = df.groupby("unit number")["time"].max()

# RUL is defined per engine as (last cycle) - (current cycle); verify the
# column in the file actually matches that before quoting anything from it.
rul_from_max = df.groupby("unit number")["time"].transform("max") - df["time"]
rul_ok = bool((rul_from_max == df["RUL"]).all())

rows = [
    ("Total aircraft engines",  f"{df['unit number'].nunique()}",      "run-to-failure"),
    ("Total operational cycles", f"{len(df):,}",                        "across all engines"),
    ("Min engine lifetime",     f"{life.min()} cycles",                f"engine {life.idxmin()}"),
    ("Max engine lifetime",     f"{life.max()} cycles",                f"engine {life.idxmax()}"),
    ("Mean engine lifetime",    f"{life.mean():.2f} cycles",           f"sd = {life.std(ddof=1):.2f} (sample)"),
    ("RUL range",               f"{df['RUL'].min()} - {df['RUL'].max()} cycles", "0 = failure point"),
    ("Features used",           f"{df.shape[1] - 2}",                  "time + 3 op. settings + 21 sensors"),
    ("RUL label verified",      "yes" if rul_ok else "NO - CHECK",     "RUL == max(time) - time, per engine"),
]
for a, b, c in rows:
    print(f"  {a:<26} {b:<22} {c}")
if not rul_ok:
    raise SystemExit("RUL column does not match its definition - stop and investigate")

write_csv("t01_dataset.csv", rows, ["statistic", "value", "remark"])

# per-sensor descriptives, for the sensor-overview table
_, X, y = load_xy()
srows = []
for c in X.columns:
    if not c.startswith("sensor measurement"):
        continue
    v = X[c]
    srows.append((c.replace("sensor measurement ", ""),
                  f"{v.mean():.2f} +- {v.std(ddof=1):.2f}",
                  f"{v.min():.2f} - {v.max():.2f}",
                  f"{np.corrcoef(v, y)[0, 1]:+.3f}"))
write_csv("t01_sensors.csv", srows,
          ["sensor", "mean +- sd", "range", "corr with RUL"])
write_json("s01_meta.json", {"n_rows": int(len(df)),
                             "n_engines": int(df["unit number"].nunique()),
                             "rul_verified": rul_ok})
