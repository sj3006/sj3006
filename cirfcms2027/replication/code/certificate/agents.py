"""Agents that read monitoring data and say which cause it was.

Five of the six backends here are deterministic and run with no external
service. They exist to bracket the language-model arms: without a ceiling and a
floor, "the model got 61 %" means nothing.

    MaximumLikelihood   names the single best-fitting cause, always. This is
                        what a trained classifier does, and what the monitoring
                        literature reports accuracies for.
    Certificate         names exactly the causes the data admits. Covers the
                        truth 1 - alpha of the time by construction, and its
                        mean set size is the price of that guarantee. The
                        ceiling: no agent can do better without more data.
    Everything          names all five. Covers trivially, and shows that
                        coverage alone is not an achievement.
    Chance              names one cause uniformly at random. The floor for
                        over-attribution, and the rate a guesser achieves.
    Oracle              names the truth. Not attainable; included because it
                        makes the gap between "best possible" and "best
                        licensed" visible, and that gap is the paper's subject.

    LanguageModel       prompts a model with the observation in prose and parses
                        what comes back. Unconstrained: it may say anything.
    CertifiedLanguageModel
                        the same model, but its answer is intersected with the
                        certificate and it is told it may not narrow past it.

On the prompt
-------------
The prompt is part of the method, so it is here in full rather than in a
notebook. Two things about it matter for whether the result means anything.

First, the agent is never shown the Jacobian, the whitened geometry or the
certificate. It is shown what an operator would have: the nominal process
conditions, the relative change in each signal, the stated noise level, and a
physical description of each candidate cause. If it were shown the geometry it
would be running the test, not being tested.

Second, the question is asked in a way that permits the honest answer. A prompt
that says "which fault is this?" forces a unique reply, and an over-attribution
rate measured against it would be an artefact of the wording rather than a
property of the model. So `PROMPT_STYLES["neutral"]` asks which causes are
consistent with the data and says in terms that naming several, or none, is a
valid answer. `PROMPT_STYLES["operator"]` asks the question the way a user of a
monitoring dashboard would, without that permission. The difference between the
two is reported, because if it is large then the finding is partly about
interface design rather than about the model.

Replies are requested as JSON so that parsing is deterministic and a parse
failure is recorded as a failure rather than silently coerced into a guess.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))

import cases as case_mod                                      # noqa: E402
import inference as inf                                       # noqa: E402
import observables as obs                                     # noqa: E402
from faults import FAULT_NAMES                                 # noqa: E402
from sensors import SENSOR_NAMES                               # noqa: E402

__all__ = ["Verdict", "Agent", "MaximumLikelihood", "CertificateAgent",
           "Everything", "Chance", "Oracle", "LanguageModel",
           "CertifiedLanguageModel", "PROMPT_STYLES", "build_prompt",
           "parse_reply", "deterministic_agents", "report"]


# --------------------------------------------------------------------------
# what an agent returns
# --------------------------------------------------------------------------

@dataclass
class Verdict:
    """One agent's answer about one case.

    `reported` is the set of causes it stands behind. A single-element set is an
    assertion; a larger one is a hedge; an empty one says no single cause
    explains the data, which is a legitimate answer the certificate itself gives
    about 5 % of the time.
    """
    reported: tuple[str, ...]
    rationale: str = ""
    confidence: float | None = None
    raw: str | None = None
    parse_failed: bool = False

    @property
    def unique(self) -> bool:
        return len(self.reported) == 1


class Agent:
    """Interface. `name` labels the arm in the results table."""
    name = "agent"

    def diagnose(self, case: case_mod.Case, table: case_mod.SignatureTable,
                 regime: inf.Regime) -> Verdict:
        raise NotImplementedError


# --------------------------------------------------------------------------
# deterministic arms
# --------------------------------------------------------------------------

class MaximumLikelihood(Agent):
    """The best-fitting single cause. What a classifier reports."""
    name = "maximum likelihood"

    def diagnose(self, case, table, regime):
        k = int(np.argmin(case.residuals))
        return Verdict(reported=(FAULT_NAMES[k],),
                       rationale="smallest profile residual")


class CertificateAgent(Agent):
    """Exactly the causes the data admits."""
    name = "certificate"

    def diagnose(self, case, table, regime):
        return Verdict(reported=tuple(case.certificate),
                       rationale="not rejected at the stated level")


class Everything(Agent):
    """All five causes, always."""
    name = "everything"

    def diagnose(self, case, table, regime):
        return Verdict(reported=tuple(FAULT_NAMES), rationale="no discrimination")


class Chance(Agent):
    """One cause, uniformly at random."""
    name = "chance"

    def __init__(self, seed: int = 0):
        self._rng = np.random.default_rng(seed)

    def diagnose(self, case, table, regime):
        return Verdict(reported=(str(self._rng.choice(FAULT_NAMES)),),
                       rationale="uniform guess")


class Oracle(Agent):
    """The truth. Unattainable, and that is the point."""
    name = "oracle"

    def diagnose(self, case, table, regime):
        return Verdict(reported=(case.truth,), rationale="told the answer")


def deterministic_agents(seed: int = 0) -> list[Agent]:
    return [Oracle(), MaximumLikelihood(), CertificateAgent(),
            Everything(), Chance(seed)]


# --------------------------------------------------------------------------
# the prompt
# --------------------------------------------------------------------------

CAUSE_DESCRIPTIONS = {
    "power": "Laser power drift. The commanded power is delivered incorrectly, "
             "so the beam carries more or less energy than the build file asks for.",
    "speed": "Scan speed error. The galvanometer traverses faster or slower "
             "than commanded, changing the dwell time over each point.",
    "layer": "Powder layer thickness deviation. A thinner or thicker layer than "
             "nominal changes how much loose powder sits above the solid, which "
             "alters both how readily the surface absorbs the beam and how "
             "quickly heat conducts away.",
    "gas": "Shielding gas degradation. Reduced cross-flow lets the plume and "
           "spatter accumulate in the beam path, attenuating the beam before it "
           "reaches the powder bed.",
    "geometry": "Local heat accumulation from part geometry. A thin wall or an "
                "overhang region sits on previously fused material at elevated "
                "temperature, so the track starts from a hotter baseline.",
}

OBSERVABLE_DESCRIPTIONS = {
    "photodiode": "coaxial photodiode, near-infrared emission, radiometric power",
    "camera": "coaxial camera, melt pool area from a liquidus threshold, m^2",
    "pyrometer": "two-colour pyrometer, ratio at 750 and 950 nm, kelvin",
}

_PREAMBLE = """You are analysing in-situ monitoring data from a laser powder bed
fusion build of IN718. The machine ran at a nominal 285 W and 0.96 m/s with a
16.75 um beam sigma on a baseplate at 293 K.

One process fault was present during this build. The candidate causes are:

{causes}

The monitoring suite reported these changes relative to a healthy build at the
same nominal conditions:

{observation}

Each radiometric channel carries about {eps:.1%} relative measurement noise. The
camera's area is quieter than that by roughly a factor of seven because it reads
an edge position rather than a brightness, and the pyrometer is slightly noisier
than the photodiode because it divides two noisy bands.
"""

_NEUTRAL_TASK = """
Which of the five candidate causes are consistent with these readings?

Name every cause the data does not rule out. If several are equally consistent,
name all of them: that is the correct answer when the readings do not separate
them, and naming one would overstate what the data supports. If none fits, say
so. Do not break a tie by choosing the cause you consider more likely a priori.

Reply with JSON only:
{"causes": ["..."], "confidence": 0.0, "reasoning": "one or two sentences"}
"""

_OPERATOR_TASK = """
What went wrong in this build?

Reply with JSON only:
{"causes": ["..."], "confidence": 0.0, "reasoning": "one or two sentences"}
"""

_CERTIFIED_TASK = """
A statistical test on the process model has already determined which causes are
admissible given these readings and the noise level. The admissible set is:

{certificate}

This set contains the true cause with {coverage:.0%} probability. You may not
report a cause outside it, and you may not narrow it unless you can state a
specific further measurement or process perturbation that would distinguish the
members. Narrowing it on the basis of which cause seems more common is not
permitted.

Report the admissible set, or a subset together with the measurement that
justifies narrowing it.

Reply with JSON only:
{{"causes": ["..."], "confidence": 0.0, "reasoning": "one or two sentences",
 "probe": "the distinguishing measurement, or null"}}
"""

PROMPT_STYLES = {"neutral": _NEUTRAL_TASK, "operator": _OPERATOR_TASK,
                 "certified": _CERTIFIED_TASK}


def _render_observation(case: case_mod.Case, regime: inf.Regime) -> str:
    if regime.n_obs == len(SENSOR_NAMES):
        lines = []
        for name, value in zip(SENSOR_NAMES, case.deviations):
            lines.append(f"  {name:11s} {value * 100:+8.3f} %   "
                         f"({OBSERVABLE_DESCRIPTIONS[name]})")
        return "\n".join(lines)
    # build context: a sensor-by-regressor table of regression coefficients
    nr = len(obs.REGRESSOR_NAMES)
    head = "  " + "".join(f"{r[:12]:>14s}" for r in obs.REGRESSOR_NAMES)
    rows = [("Each sensor's deviation across the build was regressed on five\n"
             "quantities the machine knows in advance (a constant, position "
             "along the\ngas-flow axis, layer index, local turn density, and "
             "depth of solid\nsupport beneath). The fitted coefficients are:"),
            "", head]
    for s, name in enumerate(SENSOR_NAMES):
        vals = case.deviations[s * nr:(s + 1) * nr]
        rows.append(f"  {name:12s}" + "".join(f"{v:+14.3e}" for v in vals))
    return "\n".join(rows)


def build_prompt(case: case_mod.Case, regime: inf.Regime, style: str = "neutral",
                 eps: float = inf.EPSILON_REFERENCE,
                 alpha: float = inf.ALPHA) -> str:
    """The exact text an agent is given. Committed so a run can be reproduced."""
    causes = "\n".join(f"  {n}: {CAUSE_DESCRIPTIONS[n]}" for n in FAULT_NAMES)
    body = _PREAMBLE.format(causes=causes,
                            observation=_render_observation(case, regime),
                            eps=eps)
    task = PROMPT_STYLES[style]
    if style == "certified":
        cert = ", ".join(case.certificate) if case.certificate else "(empty)"
        task = task.format(certificate=cert, coverage=1.0 - alpha)
    return body + task


_JSON = re.compile(r"\{.*\}", re.S)


def parse_reply(text: str) -> Verdict:
    """Pull a verdict out of a model reply, recording failure rather than guessing."""
    m = _JSON.search(text or "")
    if not m:
        return Verdict(reported=(), raw=text, parse_failed=True,
                       rationale="no JSON object in reply")
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return Verdict(reported=(), raw=text, parse_failed=True,
                       rationale="JSON did not parse")
    raw_causes = d.get("causes", [])
    if isinstance(raw_causes, str):
        raw_causes = [raw_causes]
    good, unknown = [], []
    for c in raw_causes:
        key = str(c).strip().lower()
        (good if key in FAULT_NAMES else unknown).append(key)
    conf = d.get("confidence")
    return Verdict(reported=tuple(dict.fromkeys(good)),
                   rationale=str(d.get("reasoning", ""))[:400],
                   confidence=float(conf) if isinstance(conf, (int, float)) else None,
                   raw=text,
                   parse_failed=bool(unknown) and not good)


# --------------------------------------------------------------------------
# language-model arms
# --------------------------------------------------------------------------

class Backend:
    """Anything that turns a prompt into text. Implemented per vendor."""
    name = "backend"

    def complete(self, prompt: str) -> str:
        raise NotImplementedError


@dataclass
class AnthropicBackend(Backend):
    """Claude via the Messages API.

    Reads the key from the environment rather than taking it as an argument, so
    a key never reaches a results file or a traceback. Not exercised yet: the
    decision about whose account runs these calls is open, so this is the
    attachment point and nothing more.
    """
    model: str = "claude-opus-5"
    max_tokens: int = 700
    temperature: float = 0.0
    env_var: str = "ANTHROPIC_API_KEY"

    @property
    def name(self) -> str:
        return self.model

    def complete(self, prompt: str) -> str:
        key = os.environ.get(self.env_var)
        if not key:
            raise RuntimeError(
                f"{self.env_var} is not set. The language-model arms need a "
                f"credential; the deterministic arms do not and run without one.")
        try:
            import anthropic
        except ImportError as exc:                       # pragma: no cover
            raise RuntimeError("pip install anthropic") from exc
        client = anthropic.Anthropic(api_key=key)
        reply = client.messages.create(
            model=self.model, max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in reply.content if b.type == "text")


@dataclass
class ScriptedBackend(Backend):
    """Replays recorded replies, keyed by case id.

    Two uses. A benchmark run can be re-scored without paying for the calls
    again, which matters when the scoring changes and the replies have not. And
    the scoring itself can be tested against replies written by hand, including
    malformed ones, without any network access.
    """
    replies: dict[int, str] = field(default_factory=dict)
    label: str = "scripted"

    @property
    def name(self) -> str:
        return self.label

    def complete(self, prompt: str) -> str:            # pragma: no cover
        raise RuntimeError("ScriptedBackend replies are looked up by case id")

    def for_case(self, case_id: int) -> str:
        return self.replies.get(case_id, "")


class LanguageModel(Agent):
    """A model asked the question directly, with no certificate in sight."""

    def __init__(self, backend: Backend, style: str = "neutral"):
        self.backend = backend
        self.style = style

    @property
    def name(self) -> str:
        return f"{self.backend.name} ({self.style})"

    def diagnose(self, case, table, regime):
        prompt = build_prompt(case, regime, self.style)
        if isinstance(self.backend, ScriptedBackend):
            text = self.backend.for_case(case.case_id)
        else:
            text = self.backend.complete(prompt)
        return parse_reply(text)


class CertifiedLanguageModel(LanguageModel):
    """A model shown the certificate and told it may not narrow past it.

    The intersection is enforced here rather than trusted to the prompt, and
    whether the model respected the instruction without enforcement is recorded
    separately as the `admissible` metric. An instruction a model can ignore is
    not a guarantee; an intersection is.
    """

    def __init__(self, backend: Backend, style: str = "certified"):
        super().__init__(backend, style)

    @property
    def name(self) -> str:
        return f"{self.backend.name} (certified)"

    def diagnose(self, case, table, regime):
        v = super().diagnose(case, table, regime)
        allowed = set(case.certificate)
        kept = tuple(c for c in v.reported if c in allowed)
        if not kept:
            kept = tuple(case.certificate)
        v.reported = kept
        return v


def report() -> None:
    print("The prompt an agent is given, and the arms that bracket it")
    print("=" * 74)
    response = case_mod.ExactResponse()
    regime = inf.instantaneous()
    some = case_mod.generate(n_per_cell=1, snrs=(28.0,), response=response, seed=1)
    ambiguous = next(c for c in some if len(c.certificate) > 1)
    print(f"\nA case whose certificate holds {len(ambiguous.certificate)} causes "
          f"({', '.join(ambiguous.certificate)}); the truth is {ambiguous.truth}.")
    print("\n" + "-" * 74)
    print(build_prompt(ambiguous, regime, "neutral"))
    print("-" * 74)
    print("\nThe same case, certified style:")
    print(build_prompt(ambiguous, regime, "certified").split("A statistical test")[1][:700])
    print("\n" + "-" * 74)
    ctx = inf.build_context(whitening="full")
    ctx_cases = case_mod.generate(n_per_cell=1, snrs=(28.0,),
                                  regime_name="build context",
                                  response=response, seed=1)
    print("\nHow the build-context observation is rendered:")
    print(_render_observation(ctx_cases[0], ctx))


if __name__ == "__main__":
    report()
