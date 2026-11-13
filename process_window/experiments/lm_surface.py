"""Measure the language-model failure-rate surface on a (temperature, top-p) grid.

For each setting, generate `per_setting` continuations of random WikiText-2
prompts with SmolLM2-135M and store each continuation's scores (seq-rep-4 and
mean NLL; see pwcert/lm.py). Scores rather than pass/fail are stored, so the
thresholds can be changed later. Resumable: settings already in the output
file are skipped.

Run from process_window/:
    HF_HOME=<cache> python3 experiments/lm_surface.py [--per-setting 160]
"""

import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.lm import generate_and_score, load, wikitext_prompts  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "lm")
TEMPS = np.round(np.linspace(0.2, 2.0, 12), 3)
TOPS = np.round(np.linspace(0.5, 1.0, 12), 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-setting", type=int, default=160)
    ap.add_argument("--batch", type=int, default=32)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "surface_scores.npz")
    done = dict(np.load(path, allow_pickle=True)) if os.path.exists(path) else {}
    tok, model = load()
    prompts = wikitext_prompts(400)
    t0 = time.time()
    for i, T in enumerate(TEMPS):
        for j, p in enumerate(TOPS):
            key = f"{i}_{j}"
            if key in done:
                continue
            rng = np.random.default_rng(1000 * i + j)
            reps, nlls = [], []
            for _ in range(int(np.ceil(args.per_setting / args.batch))):
                batch = list(rng.choice(prompts, args.batch))
                r, n = generate_and_score(tok, model, batch, T, p)
                reps.append(r)
                nlls.append(n)
            done[key] = np.stack([np.concatenate(reps)[: args.per_setting],
                                  np.concatenate(nlls)[: args.per_setting]])
            np.savez(path, **done, temps=TEMPS, tops=TOPS)
            print(f"[{len(done)}/{len(TEMPS) * len(TOPS)}] T={T} top_p={p} "
                  f"rep4>0.2: {np.mean(done[key][0] > 0.2):.3f}  NLL>3.5: {np.mean(done[key][1] > 3.5):.3f}"
                  f"  ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
