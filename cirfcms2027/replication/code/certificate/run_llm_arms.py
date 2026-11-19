#!/usr/bin/env python3
"""Run the language-model arms of the certificate paper (its Section 4.7).

Everything else in the paper is computed by `results.py`. This script runs the
part that needs a language-model service: the unconstrained model under the two
prompt styles, and the certified model, on the same cases as the deterministic
arms, and scores all of them together.

    export ANTHROPIC_API_KEY=...              # your own key; never commit it
    python3 run_llm_arms.py --model MODEL_NAME --n-per-cell 10
    python3 run_llm_arms.py --dry-run         # no network: checks the pipeline

`MODEL_NAME` is the identifier of the model to test, as the provider names it.
Each case costs one call per arm; there are `n_per_cell x 4 signal levels x 5
faults` cases, so `--n-per-cell 10` is 200 cases and 600 calls for three arms.
Start small and check the cost with your provider before a full run; the paper's
deterministic arms use 300 per cell.

Every raw reply is saved in `llm_replies.json`, so the run can be rescored later
without paying again (`--rescore`), and the scores go to `llm_results.json`.
Other providers: write a `Backend` subclass in `agents.py` with a `complete`
method (prompt in, text out), following `AnthropicBackend`, and add it to
`BACKENDS` below.

The build-context regime is not offered: whether it needs its own prompt is an
open decision in `ROADMAP.md`, because its coefficient matrix does not read
naturally as prose.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import agents as agent_mod                                 # noqa: E402
import benchmark as bench                                  # noqa: E402
import cases as case_mod                                   # noqa: E402
import inference as inf                                    # noqa: E402
import observables as obs                                  # noqa: E402

SNRS = (14.0, 28.0, 56.0, 120.0)
REPLIES = HERE / "llm_replies.json"
OUT = HERE / "llm_results.json"
BACKENDS = {"anthropic": agent_mod.AnthropicBackend}


class Recording(agent_mod.Backend):
    """Wraps a backend and keeps every reply, keyed by arm and case."""

    def __init__(self, inner, store: dict, arm: str):
        self.inner, self.store, self.arm = inner, store, arm
        self.case_id = None

    @property
    def name(self) -> str:
        return self.inner.name

    def complete(self, prompt: str) -> str:
        text = self.inner.complete(prompt)
        self.store.setdefault(self.arm, {})[str(self.case_id)] = text
        return text


def _arms(backend_for):
    return [agent_mod.LanguageModel(backend_for("neutral"), style="neutral"),
            agent_mod.LanguageModel(backend_for("operator"), style="operator"),
            agent_mod.CertifiedLanguageModel(backend_for("certified"))]


class _CaseTracking(agent_mod.Agent):
    """Tells a recording backend which case it is answering."""

    def __init__(self, arm):
        self.arm = arm

    @property
    def name(self) -> str:
        return self.arm.name

    def diagnose(self, case, table, regime):
        if isinstance(self.arm.backend, Recording):
            self.arm.backend.case_id = case.case_id
        return self.arm.diagnose(case, table, regime)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="model identifier, as the provider names it")
    ap.add_argument("--provider", default="anthropic", choices=sorted(BACKENDS))
    ap.add_argument("--n-per-cell", type=int, default=10)
    ap.add_argument("--seed", type=int, default=9)
    ap.add_argument("--dry-run", action="store_true",
                    help="no network; every arm replies with the certificate")
    ap.add_argument("--rescore", action="store_true",
                    help="score the replies saved in llm_replies.json, no calls")
    a = ap.parse_args()

    regime = inf.instantaneous()
    response = case_mod.ExactResponse()
    table = case_mod.SignatureTable(regime, response, plan=obs.scan_plan())
    cs = case_mod.generate(n_per_cell=a.n_per_cell, snrs=SNRS,
                           regime_name="instantaneous", response=response, seed=a.seed)
    print(f"{len(cs)} cases, instantaneous regime")

    store: dict = {}
    if a.dry_run:
        canned = {str(c.case_id): json.dumps({"causes": list(c.certificate),
                                              "confidence": 0.5, "reasoning": "dry run"})
                  for c in cs}
        backend_for = lambda style: agent_mod.ScriptedBackend(
            {int(k): v for k, v in canned.items()}, "dry-run")
    elif a.rescore:
        saved = json.loads(REPLIES.read_text())
        backend_for = lambda style: agent_mod.ScriptedBackend(
            {int(k): v for k, v in saved["replies"][style].items()}, saved["model"])
    else:
        if not a.model:
            ap.error("--model is required for a live run")
        cls = BACKENDS[a.provider]
        backend_for = lambda style: Recording(cls(model=a.model), store, style)
    arms = _arms(backend_for)
    arms = [_CaseTracking(x) for x in arms] + agent_mod.deterministic_agents(seed=5)

    try:
        scores, verdicts = bench.run(cs, arms, regime, table)
    finally:
        if not (a.dry_run or a.rescore):
            REPLIES.write_text(json.dumps({"model": a.model, "provider": a.provider,
                                           "n_per_cell": a.n_per_cell, "seed": a.seed,
                                           "replies": store}, indent=1))
            print(f"raw replies saved to {REPLIES.name}")

    print("\n   " + bench.Score.header())
    for s in scores:
        print("   " + s.row())
    out = {"model": "dry-run" if a.dry_run else a.model, "n_cases": len(cs),
           "n_per_cell": a.n_per_cell, "seed": a.seed,
           "arms": {s.agent: {k: (None if isinstance(v, float) and np.isnan(v) else v)
                              for k, v in s.__dict__.items() if k != "agent"}
                    for s in scores}}
    if not a.dry_run:
        OUT.write_text(json.dumps(out, indent=1))
        print(f"\nscores written to {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
