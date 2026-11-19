"""The literature counts quoted in paper Section 5.1.

The paper reports that of 19 works extracted - in-situ LPBF monitoring with a
stated input signal and output, 2019-2025 - seven classify outcomes and only
three estimate a process input from an in-situ signal, one of those a lumped
energy-density class.

Those are counts over a table, so they are checkable rather than assertable.
This module parses `07-literature-extraction.md` and recomputes them from the
Class column, so an edit to the table cannot silently contradict the paper.

The classification itself is a judgement recorded in that file, with each row's
verification status (A = read from abstract and metadata, F = read in full) in
the last column. This module checks the arithmetic, not the judgement.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

__all__ = ["TABLE", "OUTCOME_CLASSES", "INPUT_ESTIMATE_CLASSES", "rows",
           "counts", "report"]

TABLE = Path(__file__).resolve().parent.parent / "07-literature-extraction.md"

# Class labels that count as classifying an outcome: a defect, a property or a
# surface state, as opposed to a process input.
OUTCOME_CLASSES = {"outcome", "outcome; added hardware"}
# Class labels that count as estimating a process input from an in-situ signal.
# "cause-level physics" is excluded: those are offline characterisations, not
# estimators. "cause, separate" on a calibration study is excluded by the
# in-situ requirement, which is applied per row below.
INPUT_ESTIMATE_CLASSES = {"cause, separate", "cause, but **lumped**"}
# Rows whose output is a cause but which are not in-situ estimators: offline
# Bayesian calibration of a thermal model against cross-sections.
NOT_IN_SITU = {16}
# Rows recorded to close a rejected candidate rather than as monitoring studies.
NOT_MONITORING = {18}


def rows() -> list[dict]:
    """Parse the markdown table into one dict per work."""
    out = []
    for line in TABLE.read_text().split("\n"):
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 7 or not re.fullmatch(r"\**\d+\**", cells[0]):
            continue
        out.append({
            "n": int(cells[0].strip("*")),
            "work": cells[1], "input": cells[2], "output": cells[3],
            "klass": cells[4], "separation": cells[5], "verified": cells[6],
        })
    return out


def counts() -> dict:
    rs = rows()
    outcome = [r["n"] for r in rs if r["klass"] in OUTCOME_CLASSES]
    inputs = [r["n"] for r in rs
              if r["klass"] in INPUT_ESTIMATE_CLASSES and r["n"] not in NOT_IN_SITU]
    lumped = [r["n"] for r in rs if "lumped" in r["klass"]]
    read_in_full = [r["n"] for r in rs if r["verified"].strip("* ").startswith("F")]
    years = sorted({int(y) for r in rs
                    for y in re.findall(r"\b(19|20)\d{2}\b|\b(\d{4})\b", "")} or
                   {int(m.group()) for r in rs
                    for m in re.finditer(r"\b(?:19|20)\d{2}\b", r["work"])})
    return {"n_works": len(rs),
            "n_monitoring": len([r for r in rs if r["n"] not in NOT_MONITORING]),
            "n_outcome": len(outcome), "outcome": outcome,
            "n_input_estimators": len(inputs), "input_estimators": inputs,
            "n_lumped": len(lumped), "lumped": lumped,
            "n_read_in_full": len(read_in_full), "read_in_full": read_in_full,
            "year_range": (years[0], years[-1]) if years else None,
            "n_analysing_separation": sum(
                1 for r in rs if r["separation"].lower().startswith("yes"))}


def report() -> None:
    c = counts()
    print("LITERATURE CENSUS, from 07-literature-extraction.md\n")
    print(f"   rows in the table                    {c['n_works']}")
    print(f"   of those, monitoring studies         {c['n_monitoring']}")
    print(f"   span of publication years            "
          f"{c['year_range'][0]}-{c['year_range'][1]}")
    print(f"   classify an outcome                  {c['n_outcome']}   "
          f"rows {c['outcome']}")
    print(f"   estimate a process input in situ     {c['n_input_estimators']}   "
          f"rows {c['input_estimators']}")
    print(f"      of which a lumped group           {c['n_lumped']}   "
          f"rows {c['lumped']}")
    print(f"   analyse whether two causes separate  "
          f"{c['n_analysing_separation']}")
    print(f"   read in full rather than by abstract {c['n_read_in_full']}   "
          f"rows {c['read_in_full']}")
    print("\n   The remaining rows are offline cause-level physics, nuisance "
          "correction,\n   feature engineering, forward optimisation, "
          "instrumentation calibration, or\n   recorded to close a rejected "
          "candidate. Row 16 is a cause-level estimator but\n   an offline "
          "calibration against cross-sections, so it fails the in-situ test.")


if __name__ == "__main__":
    report()
