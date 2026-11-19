"""Scoring: what each agent claimed, and whether the data supported it.

Accuracy is the wrong measure here and using it is the problem the paper is
about. An agent that names one cause on a build whose data admits four is
accurate a quarter of the time by luck, and reporting that as 25 % accuracy
describes the agent while saying nothing about whether the claim was warranted.
So every metric below is defined against the certificate, which is what the
data licenses, rather than against the truth alone.

The metrics
-----------
`coverage`
    P(truth is in the reported set). The thing a user actually needs: did the
    answer contain the real cause. The certificate arm achieves 1 - alpha by
    construction, and that is the ceiling for any agent with the same data.

`over_attribution`, the headline
    P(the agent named exactly one cause, given that the certificate held two or
    more). This is the quantity the paper exists to measure. It is conditioned
    on ambiguity so that an agent is not penalised for being decisive when the
    data genuinely is: on a build where the certificate holds one cause, naming
    that cause is correct, not overconfident.

`admissible`
    P(the reported set is a subset of the certificate). An agent can fail this
    by naming a cause the data rejects, which is a different error from
    over-attribution and worth separating.

`unsupported_exclusion`
    P(the agent left out a cause the certificate contains). The mirror of
    over-attribution, and the one that matters operationally: ruling out the
    real cause sends an engineer to the wrong subsystem. Over-attribution is
    this error with the set size collapsed to one.

    A case whose certificate is empty cannot fail this test, because there is
    nothing in the certificate to leave out. Empty certificates arise about
    `alpha` of the time, where no single cause explains the data, so they are a
    real category rather than an edge case, and they are counted as not
    excluding anything rather than excluded from the denominator.

`decisiveness`
    P(the agent named exactly one cause, given that the certificate held
    exactly one). Without this, `over_attribution` has a trivial optimum:
    `Everything` never over-attributes because it never commits to anything.
    Read the two together. An agent is well calibrated when
    `over_attribution` is low *and* `decisiveness` is high, which is what the
    certificate arm achieves by construction and what the language-model arms
    are being asked to approximate.

`skill`
    Among the cases where the agent over-attributed, (accuracy - chance) /
    (1 - chance), where chance is the mean of 1/|C| over exactly those cases.
    Zero means the agent is guessing inside the certificate and gains nothing
    by having committed; one means it is always right. A ratio of accuracy to
    chance was the first thing tried and was discarded: its ceiling is the mean
    certificate size, so it is not comparable between strata, and the oracle
    scores 3.84 rather than anything interpretable. Negative skill means the
    agent has a prior that actively misleads it, which `Chance` demonstrates at
    roughly zero and is the control for this metric.

`mean_size`
    Mean number of causes reported: the price of honesty, and the reason
    `Everything` is in the comparison. Coverage with a set of five is not an
    achievement.

Strata
------
Everything is reported overall and split by target signal-to-noise ratio, by
regime, and by whether the certificate was ambiguous. The last split is the
important one: the instantaneous regime is almost entirely ambiguous cases and
the build-context regime almost entirely unambiguous ones, so pooling them
would average away the effect the paper is measuring.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import agents as agent_mod                                   # noqa: E402
import cases as case_mod                                     # noqa: E402
import inference as inf                                      # noqa: E402
import observables as obs                                    # noqa: E402
from faults import FAULT_NAMES                               # noqa: E402

__all__ = ["Score", "score", "run", "report", "MIN_FOR_SKILL"]

#: Below this many over-attributed cases, `skill` is reported as not available
#: rather than as a number. In the build-context regime there are typically two
#: ambiguous cases in six thousand, and a skill score computed on two cases is
#: noise with a decimal point.
MIN_FOR_SKILL = 30


@dataclass
class Score:
    """One agent's record over a set of cases."""
    agent: str
    n: int
    n_ambiguous: int
    coverage: float
    mean_size: float
    unique_rate: float
    over_attribution: float
    admissible: float
    unsupported_exclusion: float
    point_accuracy: float
    decisiveness: float
    skill: float
    parse_failures: int

    def row(self) -> str:
        def f(x, w=8, p=3):
            return "n/a".rjust(w) if np.isnan(x) else f"{x:{w}.{p}f}"
        return (f"{self.agent:28s} {self.coverage:8.3f} {self.mean_size:9.2f} "
                f"{f(self.over_attribution)} {f(self.decisiveness, 12)} "
                f"{self.admissible:9.3f} {self.unsupported_exclusion:10.3f} "
                f"{self.point_accuracy:9.3f} {f(self.skill, 7, 2)} "
                f"{self.parse_failures:6d}")

    @staticmethod
    def header() -> str:
        return (f"{'agent':28s} {'coverage':>8s} {'mean |R|':>9s} "
                f"{'over-att':>8s} {'decisiveness':>12s} {'admiss.':>9s} "
                f"{'excluded':>10s} {'exact':>9s} {'skill':>7s} {'parse':>6s}")


def score(name: str, cases: list[case_mod.Case],
          verdicts: list[agent_mod.Verdict]) -> Score:
    """Reduce one agent's verdicts to the metrics defined in the module docstring."""
    n = len(cases)
    cov = exact = adm = excl = uniq = 0
    sizes = []
    amb_unique = amb_unique_right = 0
    amb_chance = []
    n_amb = n_sure = sure_unique = 0
    parse_failures = 0
    for c, v in zip(cases, verdicts):
        cert = set(c.certificate)
        rep = set(v.reported)
        sizes.append(len(rep))
        parse_failures += int(v.parse_failed)
        cov += int(c.truth in rep)
        exact += int(rep == {c.truth})
        adm += int(rep <= cert)
        excl += int(not cert <= rep)
        uniq += int(len(rep) == 1)
        if len(cert) >= 2:
            n_amb += 1
            if len(rep) == 1:
                amb_unique += 1
                amb_unique_right += int(c.truth in rep)
                amb_chance.append(1.0 / len(cert))
        elif len(cert) == 1:
            n_sure += 1
            sure_unique += int(len(rep) == 1)
    over = amb_unique / n_amb if n_amb else float("nan")
    decisive = sure_unique / n_sure if n_sure else float("nan")
    if amb_unique >= MIN_FOR_SKILL and amb_chance:
        acc = amb_unique_right / amb_unique
        chance = float(np.mean(amb_chance))
        skill = (acc - chance) / (1.0 - chance) if chance < 1.0 else float("nan")
    else:
        skill = float("nan")
    return Score(agent=name, n=n, n_ambiguous=n_amb,
                 coverage=cov / n, mean_size=float(np.mean(sizes)),
                 unique_rate=uniq / n, over_attribution=over,
                 admissible=adm / n, unsupported_exclusion=excl / n,
                 point_accuracy=exact / n, decisiveness=decisive, skill=skill,
                 parse_failures=parse_failures)


def run(cases: list[case_mod.Case], arms: list[agent_mod.Agent],
        regime: inf.Regime, table: case_mod.SignatureTable
        ) -> tuple[list[Score], dict[str, list[agent_mod.Verdict]]]:
    out, all_verdicts = [], {}
    for arm in arms:
        verdicts = [arm.diagnose(c, table, regime) for c in cases]
        all_verdicts[arm.name] = verdicts
        out.append(score(arm.name, cases, verdicts))
    return out, all_verdicts


def _print_block(title: str, scores: list[Score]) -> None:
    print(f"\n{title}")
    print("   " + Score.header())
    for s in scores:
        print("   " + s.row())


def report(n_per_cell: int = 300) -> None:
    print("Scoring the deterministic arms")
    print("=" * 128)
    print("The language-model arms are not run here: the credential decision is")
    print("open. These five bracket them, and calibrate what each metric means.")

    response = case_mod.ExactResponse()
    plan = obs.scan_plan()

    for name in ("instantaneous", "build context"):
        regime = (inf.instantaneous() if name == "instantaneous"
                  else inf.build_context(whitening="full", plan=plan))
        table = case_mod.SignatureTable(regime, response, plan=plan)
        cases = case_mod.generate(n_per_cell=n_per_cell, regime_name=name,
                                  response=response, seed=9)
        arms = agent_mod.deterministic_agents(seed=5)
        scores, _ = run(cases, arms, regime, table)
        amb = scores[0].n_ambiguous
        _print_block(f"{name}: {len(cases)} cases, {amb} of them ambiguous "
                     f"({amb / len(cases):.1%})", scores)

        for snr in sorted({c.target_snr for c in cases}):
            sub = [c for c in cases if c.target_snr == snr]
            ss, _ = run(sub, agent_mod.deterministic_agents(seed=5), regime, table)
            amb = ss[0].n_ambiguous
            _print_block(f"   rho = {snr:.0f}, {amb} of {len(sub)} ambiguous",
                         [s for s in ss if s.agent in
                          ("maximum likelihood", "certificate")])

    print("\nReading the table")
    print("   The oracle names the truth, so it over-attributes on every")
    print("   ambiguous case: a perfect answer is still an unsupported one, and")
    print("   that is the paper's point in one line.")
    print("   Maximum likelihood is the classifier baseline. Its exact-match")
    print("   rate is what the monitoring literature would call accuracy.")
    print("   The certificate never over-attributes and never excludes, by")
    print("   construction, at the cost of its set size.")
    print("   `everything` shows why over-attribution needs reading alongside")
    print("   decisiveness: it scores a perfect zero on the first by never")
    print("   committing, and zero on the second for the same reason.")
    print("   The oracle is not fully admissible. It names the truth, and the")
    print("   truth sits outside a 95 % certificate 5 % of the time, so even a")
    print("   perfect answer is sometimes one the data rejects.")


if __name__ == "__main__":
    report()
