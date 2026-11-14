"""Measure the language-model failure-rate surface on a (temperature, top-p) grid.

For each setting, generate `per_setting` continuations of random WikiText-2
prompts with SmolLM2-135M and store each continuation's scores (seq-rep-4 and
mean NLL; see pwcert/lm.py). Scores rather than pass/fail are stored, so the
thresholds can be changed later. Resumable: settings already in the output
file are skipped.

Run from process_window/:
    HF_HOME=<cache> python3 experiments/lm_surface.py [--per-setting 160] [--n 12]

--n 23 measures the finer grid linspace(.., 23), which contains the 12 x 12
grid at even indices; those 144 settings are copied from surface_scores.npz
instead of being generated again (output: surface_scores_23.npz).

--model NAME --tag TAG measures another model on the 12 x 12 grid (output:
surface_scores_TAG.npz); the NLL judge is then that model's own NLL.
"""

import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.lm import MODEL, generate_and_score, load, wikitext_prompts  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "lm")


def grid(n):
    return np.round(np.linspace(0.2, 2.0, n), 3), np.round(np.linspace(0.5, 1.0, n), 3)


TEMPS, TOPS = grid(12)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-setting", type=int, default=160)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--tag", default=None, help="output suffix for a model other than the default")
    ap.add_argument("--threads", type=int, default=4, help="torch threads (leave cores for other jobs)")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    temps, tops = grid(args.n)
    if args.model != MODEL:
        assert args.tag and args.n == 12, "another model needs --tag and the 12 x 12 grid"
        path = os.path.join(OUT, f"surface_scores_{args.tag}.npz")
    else:
        path = os.path.join(OUT, "surface_scores.npz" if args.n == 12 else f"surface_scores_{args.n}.npz")
    done = dict(np.load(path, allow_pickle=True)) if os.path.exists(path) else {}
    done.pop("temps", None)
    done.pop("tops", None)
    if args.n == 23:
        base = np.load(os.path.join(OUT, "surface_scores.npz"), allow_pickle=True)
        assert np.allclose(base["temps"], temps[::2]) and np.allclose(base["tops"], tops[::2])
        for i in range(12):
            for j in range(12):
                done.setdefault(f"{2 * i}_{2 * j}", base[f"{i}_{j}"])
    tok, model = load(args.model, threads=args.threads)
    prompts = wikitext_prompts(400)
    t0 = time.time()
    for i, T in enumerate(temps):
        for j, p in enumerate(tops):
            key = f"{i}_{j}"
            if key in done:
                continue
            rng = np.random.default_rng(1000 * i + j + (0 if args.n == 12 else 10 ** 6))
            reps, nlls = [], []
            for _ in range(int(np.ceil(args.per_setting / args.batch))):
                batch = list(rng.choice(prompts, args.batch))
                r, n = generate_and_score(tok, model, batch, T, p)
                reps.append(r)
                nlls.append(n)
            done[key] = np.stack([np.concatenate(reps)[: args.per_setting],
                                  np.concatenate(nlls)[: args.per_setting]])
            np.savez(path, **done, temps=temps, tops=tops)
            print(f"[{len(done)}/{len(temps) * len(tops)}] T={T} top_p={p} "
                  f"rep4>0.2: {np.mean(done[key][0] > 0.2):.3f}  NLL>3.5: {np.mean(done[key][1] > 3.5):.3f}"
                  f"  ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
