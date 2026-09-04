"""
Jaccard Index and Spearman rank correlation for LIME / WA-LIME explanation
stability.  Drop-in replacement for the missing evaluation in
full_aircraft_XAI.ipynb.

Stability is measured as PAIRWISE AGREEMENT between R independent repetitions
of the *same* explanation method applied to the *same* instance.  A method is
stable if repeated runs select the same features (Jaccard) and order them the
same way (Spearman).

Usage
-----
    from stability_metrics import run_stability_study
    results = run_stability_study(gb_regressor, X_train, X_test,
                                  instance_ids=[10], R=30, B=5)
"""

import itertools
import warnings

import numpy as np
from scipy.stats import spearmanr
from lime.lime_tabular import LimeTabularExplainer

warnings.filterwarnings("ignore", category=UserWarning)


# --------------------------------------------------------------------------
# Explanation generators
# --------------------------------------------------------------------------
def lime_weights(model, X_train, row, num_features=None, background=None,
                 random_state=None):
    """One LIME explanation, returned as a dense signed weight vector.

    Requesting num_features = n_features (the default) is deliberate: a
    truncated explanation leaves most features at exactly 0, which creates
    a large tie block and makes Spearman correlation meaningless.

    Note on `local_exp[1]`: in regression mode LIME stores the sign-correct
    weights under key 1 (`Explanation.dummy_label == 1`) and their negation
    under key 0.  `as_list()` and `show_in_notebook()` both use key 1, so
    local_exp[1] is the right choice.
    """
    n_features = X_train.shape[1]
    if num_features is None:
        num_features = n_features
    bg = X_train.values if background is None else background

    explainer = LimeTabularExplainer(
        bg,
        feature_names=list(X_train.columns),
        mode="regression",
        discretize_continuous=False,
        random_state=random_state,
    )
    exp = explainer.explain_instance(row, model.predict, num_features=num_features)

    w = np.zeros(n_features)
    for feature_idx, weight in exp.local_exp[1]:
        w[feature_idx] = weight
    return w


def wa_lime_weights(model, X_train, row, B=5, num_features=None,
                    n_background=100, signed=False):
    """WA-LIME: aggregate B base LIME explanations.

    signed=False reproduces the notebook (mean of |w|), which ranks features
    but cannot say whether a feature pushes RUL up or down.
    signed=True keeps the direction, which is what a prognostics reader needs.
    Report both.
    """
    n_features = X_train.shape[1]
    acc = np.zeros(n_features)
    for _ in range(B):
        idx = np.random.choice(len(X_train), size=n_background, replace=True)
        w = lime_weights(model, X_train, row, num_features=num_features,
                         background=X_train.values[idx])
        acc += (w if signed else np.abs(w)) / B
    return acc


# --------------------------------------------------------------------------
# Stability metrics
# --------------------------------------------------------------------------
def jaccard_topk(w_a, w_b, k):
    """Jaccard index of the top-k feature SETS ranked by |weight|.

    J = |A n B| / |A u B|.  Since |A| = |B| = k, this equals
    m / (2k - m) where m is the overlap, so J = 1 iff the sets coincide.
    """
    a = set(np.argsort(-np.abs(w_a))[:k])
    b = set(np.argsort(-np.abs(w_b))[:k])
    return len(a & b) / len(a | b)


def spearman_rank(w_a, w_b, use_abs=True):
    """Spearman rho between the two importance RANKINGS over all features."""
    a, b = (np.abs(w_a), np.abs(w_b)) if use_abs else (w_a, w_b)
    return spearmanr(a, b).statistic


def pairwise_stability(weight_matrix, k_list=(5, 8, 10)):
    """weight_matrix: (R, n_features) from R independent repetitions."""
    R = weight_matrix.shape[0]
    if R < 2:
        raise ValueError("need at least 2 repetitions to measure stability")

    scores = {f"jaccard@{k}": [] for k in k_list}
    scores["spearman"] = []
    for i, j in itertools.combinations(range(R), 2):
        for k in k_list:
            scores[f"jaccard@{k}"].append(
                jaccard_topk(weight_matrix[i], weight_matrix[j], k))
        scores["spearman"].append(
            spearman_rank(weight_matrix[i], weight_matrix[j]))

    return {m: {"mean": float(np.mean(v)),
                "std": float(np.std(v)),
                "n_pairs": len(v)}
            for m, v in scores.items()}


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------
def run_stability_study(model, X_train, X_test, instance_ids, R=30, B=5,
                        k_list=(5, 8, 10), seed=0, verbose=True):
    """Compare single-LIME against WA-LIME on explanation stability.

    R  repetitions per method per instance
    B  base explanations aggregated per WA-LIME repetition

    WA-LIME uses B times the compute of a single LIME.  Any honest comparison
    in the paper should say so, and ideally also compare against plain LIME
    run with B * num_samples perturbations.
    """
    np.random.seed(seed)
    methods = {
        "LIME": lambda r: lime_weights(model, X_train, r),
        f"WA-LIME (B={B})": lambda r: wa_lime_weights(model, X_train, r, B=B),
    }

    results = {}
    for name, fn in methods.items():
        per_instance = []
        for inst in instance_ids:
            row = X_test.iloc[inst].values
            mat = np.array([fn(row) for _ in range(R)])
            per_instance.append(pairwise_stability(mat, k_list))
        results[name] = {
            m: {"mean": float(np.mean([p[m]["mean"] for p in per_instance])),
                "std":  float(np.mean([p[m]["std"] for p in per_instance]))}
            for m in per_instance[0]
        }

    if verbose:
        metrics = [f"jaccard@{k}" for k in k_list] + ["spearman"]
        header = f"{'method':<22}" + "".join(f"{m:>18}" for m in metrics)
        print(f"Stability over R={R} repetitions, {len(instance_ids)} instance(s)")
        print(header)
        print("-" * len(header))
        for name, res in results.items():
            line = f"{name:<22}"
            for m in metrics:
                line += f"{res[m]['mean']:>11.3f}+-{res[m]['std']:.3f}"
            print(line)
        print("\nAll Jaccard values equal to 1.000 mean the top-k set never "
              "changed;\npick a larger k, or report Spearman, to get a metric "
              "with any resolution.")

    return results
