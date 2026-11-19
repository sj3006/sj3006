"""Write the paper's two data tables from `_results.json`.

Replaces the rows between the `%%TABLEROWS%%`/`%%FAMILYROWS%%` markers on the
first run, and between `% rows:<name>` comment fences on later runs, so the
tables can be regenerated after any rerun without hand editing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE / "paper" / "paper.tex"

CLASS = {"validation-equivalent": "shared", "region-rejected": "shared",
         "structural": "shared, structure", "prediction only": "prediction only",
         "one parameter": "shared", "operating point": "shared",
         "numerical resolution": "diagnosis only", "couplings": "diagnosis only",
         "couplings control": "diagnosis only", "noise model": "diagnosis only",
         "noise level": "diagnosis only", "missing channel": "diagnosis only",
         "spurious channel": "diagnosis only"}


def _f(x, p=1):
    if x is None or x != x:
        return "--"
    return f"{x:.{p}f}"


def _cov(x):
    return "--" if x is None or x != x else f"{100 * x:.1f}"


def result_rows(R):
    out = []
    for r in R["table"]:
        out.append(f"{r['family']} & {r['n']} & {_f(r['pred_rms_median'])} & "
                   f"{_f(r['delta_max_median'], 2)} & {_f(r['delta_max_max'], 2)} & "
                   f"{_f(r['frac_over_budget'], 2)} & {_cov(r['cov_inst_min28_median'])} & "
                   f"{_cov(r['cov_big_min28_median'])} & {_f(r['flips_inst_any'], 2)} \\\\")
    return "\n".join(out)


def family_rows(R):
    return "\n".join(f"{r['family']} & {CLASS[r['family']]} & {r['n']} \\\\"
                     for r in R["table"])


def grid_rows(R):
    g = R.get("grid")
    if not g:
        return "% grid table: run grid_convergence.py"
    out = []
    for n in g["grids"]:
        d = g["rows"][str(n)]["delta"]
        out.append(f"${n}\\times{n}$ & " + " & ".join(f"{x:.2f}" for x in d) + " \\\\")
    return "\n".join(out)


def put(s: str, name: str, rows: str) -> str:
    fence = f"% rows:{name}\n{rows}\n% end rows:{name}"
    marker = f"%%{name.upper()}%%"
    if marker in s:
        return s.replace(marker, fence)
    pat = re.compile(rf"% rows:{name}\n.*?\n% end rows:{name}", re.S)
    return pat.sub(lambda m: fence, s)


def main():
    R = json.loads((HERE / "_results.json").read_text())
    s = PAPER.read_text()
    s = put(s, "tablerows", result_rows(R))
    s = put(s, "familyrows", family_rows(R))
    s = put(s, "gridrows", grid_rows(R))
    PAPER.write_text(s)
    print("tables written")


if __name__ == "__main__":
    main()
