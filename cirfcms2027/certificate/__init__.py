"""Certified diagnosis: what a monitoring agent is entitled to conclude.

Journal extension of the conference paper. `ROADMAP.md` has the plan and the
open decisions, `FINDINGS.md` the results so far.

    inference.py   the statistical core. Profiles out the fault magnitude,
                   leaving a chi-squared residual per candidate cause, and
                   derives the conference paper's separation floor from it.
    cases.py       observations from the exact forward model, and the exact
                   profile certificate the linearised one is not good enough
                   to replace.
    classes.py     the admissibility matrix and the equivalence structure:
                   which causes travel together, and how that coarsens as the
                   signal weakens.
    agents.py      seven arms, five of them deterministic, plus the committed
                   prompt text and the reply parser.
    benchmark.py   scoring, defined against the certificate rather than the
                   truth, because accuracy is the measure that creates the
                   problem.
    probe.py       the channel factorisation J = M C, and the proof that no
                   probe at any operating point separates power from gas.
    verify.py      every claim above, measured rather than asserted. Exits
                   non-zero on failure.

Run `python3 verify.py` first: it is the fastest way to see whether the whole
chain still holds after a change.
"""
