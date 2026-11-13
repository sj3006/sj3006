"""Live run: the certifier queries the language model directly.

Instead of drawing outcomes from the measured surface, every trial the
certifier requests is a real generation from SmolLM2-135M at that
(temperature, top-p), judged by the same two thresholds. The measured
surface is used only for the side information (the pilot fit, whose
generations are counted in the budget) and, afterwards, as the reference
for checking the certified region.

Run from process_window/ after lm_surface.py has finished:
    HF_HOME=<cache> python3 experiments/lm_live.py [--budget 8000] [--seed 0]
"""

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pwcert.cone import ConeCertifier  # noqa: E402
from pwcert.lm import generate_and_score, load, wikitext_prompts  # noqa: E402
from pwcert.lm_scenario import NLL_THRESH, REP_THRESH, make_lm_scenario  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "results", "lm")


class LiveCertifier(ConeCertifier):
    """ConeCertifier whose trials are real generations."""

    def __init__(self, sc, tok, model, prompts, gen_batch=32, **kw):
        super().__init__(sc, **kw)
        self.tok, self.model, self.prompts, self.gen_batch = tok, model, prompts, gen_batch
        self.temps, self.tops = sc.power, sc.speed
        self.shape2 = sc.truth[sc.modes[0]].shape

    def _generate(self, x, k):
        i, j = np.unravel_index(x, self.shape2)
        ys = []
        for start in range(0, k, self.gen_batch):
            m = min(self.gen_batch, k - start)
            pr = [self.prompts[t] for t in self.rng.integers(len(self.prompts), size=m)]
            rep, nll = generate_and_score(self.tok, self.model, pr, float(self.temps[i]), float(self.tops[j]))
            ys += [np.array([float(r > REP_THRESH), float(v > NLL_THRESH)]) for r, v in zip(rep, nll)]
        return ys

    def run_plate(self):
        plate = self.choose_plate()
        if not plate:
            return False
        xs, counts = np.unique(np.asarray(plate), return_counts=True)
        # Outcomes are generated per setting, then fed to the e-processes in
        # the plate's order of settings; all choices were made before any
        # outcome of this plate was seen, so predictability holds.
        for x, k in zip(xs, counts):
            for y in self._generate(int(x), int(k)):
                self.ep.update_at((slice(None), int(x)), y)
                self.n_at[x] += 1
                self.coupons += 1
        self._check()
        self._futility()
        self._record()
        return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    sc = make_lm_scenario(0.10, "pilot")
    n = sc.truth["degenerate"].shape[0]
    tok, model = load()
    prompts = wikitext_prompts(400, seed=1)      # a fresh prompt pool
    c = LiveCertifier(sc, tok, model, prompts, rule="cone", weights="ensemble", alloc="edge", target_q=0.7,
                      batch=2 * n, coupons0=sc.meta["pilot_coupons"], rng=np.random.default_rng(args.seed))
    t0 = time.time()
    W = sc.true_window()
    log = []
    while c.coupons < args.budget and c.run_plate():
        h = c.history[-1]
        log.append(dict(generations=int(h["coupons"]), certified=int(h["area"]),
                        unsafe_vs_reference=int(h["errors"]), seconds=round(time.time() - t0, 1)))
        print(log[-1], flush=True)
    C = c.window()
    res = dict(budget=args.budget, seed=args.seed, safe_reference=int(W.sum()), certified=int(C.sum()),
               certified_unsafe_vs_reference=int((C & ~W).sum()), generations=int(c.coupons),
               certified_mask=C.astype(int).tolist(), log=log)
    with open(os.path.join(OUT, f"lm_live_seed{args.seed}.json"), "w") as f:
        json.dump(res, f)
    print({k: v for k, v in res.items() if k not in ("certified_mask", "log")})


if __name__ == "__main__":
    main()
