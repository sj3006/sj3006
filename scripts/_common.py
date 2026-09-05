"""Shared setup for every verification script.

Resolves the dataset and the trained GBRM the same way regardless of where the
script is invoked from, so `python scripts/anything.py` works from any cwd.
"""
import os
import warnings

warnings.filterwarnings("ignore")

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(PROJECT, "results") + os.sep
os.makedirs(RESULTS, exist_ok=True)

# Override with AIRCRAFT_XLSX=/path/to/your.xlsx if the file lives elsewhere.
DATA = os.environ.get("AIRCRAFT_XLSX", os.path.join(PROJECT, "Full_Dataset.xlsx"))


def load_frame():
    """Read the dataset and normalise the exported column names back to the
    notebook's names, so downstream code matches full_aircraft_XAI.ipynb."""
    import pandas as pd

    if not os.path.exists(DATA):
        raise SystemExit(
            f"Dataset not found at {DATA}\n"
            "Put Full_Dataset.xlsx in the project root, or set AIRCRAFT_XLSX "
            "to its path."
        )
    df = pd.read_excel(DATA)
    df.columns = [
        c.replace("Unit Number", "unit number").replace("Time (Cycles)", "time")
        for c in df.columns
    ]
    df.columns = [
        " ".join(c.split()).lower() if c not in ("unit number", "time", "RUL") else c
        for c in df.columns
    ]
    return df


def load_xy():
    """Features and target exactly as the notebook builds them: drop
    'unit number', keep time + 3 operational settings + 21 sensors."""
    df = load_frame()
    X = df.drop(columns=["unit number"]).drop("RUL", axis=1)
    y = df["RUL"].copy()
    return df, X, y


def get_model(rebuild=False):
    """Train (or reuse) the GBRM on the notebook's split.

    Cached in results/model.joblib so the LIME-heavy scripts don't refit on
    every run. Returns (gb, X_train, X_test, y_train, y_test).
    """
    import joblib
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import train_test_split

    cache = RESULTS + "model.joblib"
    if os.path.exists(cache) and not rebuild:
        return joblib.load(cache)

    _, X, y = load_xy()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    # random_state=0 is set here purely so the cache is byte-identical whichever
    # script builds it first. It changes nothing measurable: seeded and unseeded
    # fits agree to 10 decimal places on MSE, R2 and MAE (see repro_gbrm.py,
    # which deliberately keeps the notebook's unseeded default).
    gb = GradientBoostingRegressor(random_state=0).fit(X_train, y_train)
    joblib.dump((gb, X_train, X_test, y_train, y_test), cache)
    return gb, X_train, X_test, y_train, y_test
