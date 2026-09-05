"""Shared machinery for the paper pipeline.

Everything the stages need: data, model, explanations, metrics, output writing.
All randomness flows from config seeds so a run is exactly reproducible.
"""
import itertools
import json
import os
import sys
import warnings

import numpy as np
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(PROJECT, "scripts"))

import config as CFG                      # noqa: E402
from _common import load_frame, load_xy   # noqa: E402  (dataset loading only)

OUT = os.path.join(PROJECT, CFG.OUT_DIR) + os.sep
os.makedirs(OUT, exist_ok=True)

SHORT = lambda c: (c.replace("sensor measurement ", "S")
                    .replace("operational setting ", "OS"))


# ------------------------------------------------------------------ model
def build_model(split=None):
    """Fit the GBRM. Returns (gb, X_train, X_test, y_train, y_test, groups_test).

    split="random"  : row-level 80/20, the conventional protocol
    split="grouped" : engine-level, so no engine appears on both sides
    """
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import GroupShuffleSplit, train_test_split

    split = split or CFG.SPLIT
    df, X, y = load_xy()
    groups = df["unit number"].values

    if split == "grouped":
        gss = GroupShuffleSplit(n_splits=1, test_size=CFG.TEST_SIZE,
                                random_state=CFG.SPLIT_SEED)
        tr, te = next(gss.split(X, y, groups))
        X_train, X_test = X.iloc[tr], X.iloc[te]
        y_train, y_test = y.iloc[tr], y.iloc[te]
        g_test = groups[te]
    elif split == "random":
        idx = np.arange(len(X))
        tr, te = train_test_split(idx, test_size=CFG.TEST_SIZE,
                                  random_state=CFG.SPLIT_SEED)
        X_train, X_test = X.iloc[tr], X.iloc[te]
        y_train, y_test = y.iloc[tr], y.iloc[te]
        g_test = groups[te]
    else:
        raise ValueError(f"unknown split {split!r}")

    gb = GradientBoostingRegressor(random_state=CFG.MODEL_SEED)
    gb.fit(X_train, y_train)
    return gb, X_train, X_test, y_train, y_test, g_test


def pick_instances(X_test, y_test):
    """Instances to explain, stratified across the RUL range.

    One instance is an anecdote. Spreading them over early/mid/late life means
    the stability result is a property of the model, not of one lucky cycle.
    """
    rng = np.random.RandomState(CFG.INSTANCE_SEED)
    y = y_test.values
    edges = np.quantile(y, np.linspace(0, 1, CFG.N_INSTANCES + 1))
    picks = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        pool = np.where((y >= lo) & (y <= hi))[0]
        if len(pool):
            picks.append(int(rng.choice(pool)))
    # de-duplicate while keeping order
    seen, out = set(), []
    for p in picks:
        if p not in seen:
            seen.add(p); out.append(p)
    return out


# ------------------------------------------------------- explanation engines
def _explainer(X_train, cols, seed):
    from lime.lime_tabular import LimeTabularExplainer
    return LimeTabularExplainer(
        X_train.values, feature_names=cols, mode="regression",
        discretize_continuous=False, random_state=int(seed),
    )


def lime_weights(gb, X_train, cols, row, seed, n_perturb=None, k=None):
    """One LIME explanation as a dense SIGNED weight vector over all features.

    k defaults to all features on purpose: LIME's num_features does feature
    selection and then REFITS the surrogate on that subset, so a truncated call
    changes the model being explained, not just what is displayed. Truncate for
    display, never before computing a metric.

    Regression mode stores the sign-correct weights under local_exp[1]
    (Explanation.dummy_label == 1); local_exp[0] is their negation.
    """
    n_perturb = n_perturb or CFG.N_PERTURB
    k = k or len(cols)
    e = _explainer(X_train, cols, seed).explain_instance(
        row, gb.predict, num_features=k, num_samples=n_perturb)
    w = np.zeros(len(cols))
    for i, v in e.local_exp[1]:
        w[i] = v
    return w, float(e.score)


def wa_lime_weights(gb, X_train, cols, row, seed, B=None, signed=False,
                    n_perturb=None):
    """WA-LIME: mean of B independent LIME runs.

    signed=False averages |w| (ranks features). signed=True keeps direction,
    which is what a maintenance engineer needs. Report both.
    """
    B = B or CFG.B_AGG
    acc = np.zeros(len(cols))
    scores = []
    for b in range(B):
        w, sc = lime_weights(gb, X_train, cols, row, seed * 1000 + b,
                             n_perturb=n_perturb)
        acc += (w if signed else np.abs(w)) / B
        scores.append(sc)
    return acc, float(np.mean(scores))


# ------------------------------------------------------------------ metrics
def jaccard_topk(a, b, k):
    """|A n B| / |A u B| on the top-k features by |weight|."""
    sa = set(np.argsort(-np.abs(a))[:k])
    sb = set(np.argsort(-np.abs(b))[:k])
    return len(sa & sb) / len(sa | sb)


def spearman_full(a, b):
    """Spearman on the FULL feature ranking by |weight|.

    Computing it on the intersection of two top-k sets instead is close to
    guaranteed to return ~1: the surviving features are the high-SNR ones whose
    order is stable by construction, so the statistic discards exactly the
    features whose ordering is in doubt.
    """
    return float(spearmanr(np.abs(a), np.abs(b)).statistic)


def pairwise_stability(W, k_list=None):
    """W: (R, n_features). Mean over all R(R-1)/2 pairs, with a 95% CI."""
    k_list = k_list or CFG.K_LIST
    R = len(W)
    out = {}
    for k in k_list:
        v = [jaccard_topk(W[i], W[j], k) for i, j in itertools.combinations(range(R), 2)]
        out[f"jaccard@{k}"] = _summ(v)
    v = [spearman_full(W[i], W[j]) for i, j in itertools.combinations(range(R), 2)]
    out["spearman"] = _summ(v)
    out["n_pairs"] = R * (R - 1) // 2
    return out


def _summ(v):
    v = np.asarray(v, dtype=float)
    m, sd, n = v.mean(), v.std(ddof=1), len(v)
    # pairwise values are dependent, so this is a descriptive interval, not an
    # exact CI -- stage 04 also reports a bootstrap-over-runs interval.
    return {"mean": float(m), "sd": float(sd),
            "lo": float(m - 1.96 * sd / np.sqrt(n)),
            "hi": float(m + 1.96 * sd / np.sqrt(n))}


def bootstrap_over_runs(W, k, n_boot=2000, seed=0):
    """Resample RUNS (not pairs) to get an honest interval on mean Jaccard."""
    rng = np.random.RandomState(seed)
    R = len(W)
    stats = []
    for _ in range(n_boot):
        idx = rng.choice(R, R, replace=True)
        v = [jaccard_topk(W[i], W[j], k)
             for i, j in itertools.combinations(idx, 2) if i != j]
        if v:
            stats.append(np.mean(v))
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


# ------------------------------------------------------------------- output
def write_csv(name, rows, header):
    import csv
    p = OUT + name
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  -> {CFG.OUT_DIR}/{name}")
    return p


def write_json(name, obj):
    p = OUT + name
    json.dump(obj, open(p, "w"), indent=2, default=float)
    print(f"  -> {CFG.OUT_DIR}/{name}")
    return p


def banner(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)
