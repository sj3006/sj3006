"""Check that docs/measured-inputs.md still matches the data in the code.

`docs/measured-inputs.md` tabulates every measurement this work takes from
somebody else's article. A prose table is exactly the kind of thing that drifts
away from the code beside it, so this module parses the two tables that have a
machine-readable counterpart and compares them entry by entry.

What it cannot check is whether either matches the article. That still needs a
person and a copy of the paper.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import numpy as np

from calibrate import WEAVER_POINTS
from weaver_pads import (X_PAD_CONTROL_CHANGES, Y_PAD_ANTIPARALLEL,
                         Y_PAD_PARALLEL, Y_PAD_SD_RANGE_UM)

__all__ = ["DOC", "single_track_rows", "pad_rows", "compare", "report"]

DOC = Path(__file__).resolve().parent.parent / "docs" / "measured-inputs.md"


def _tables() -> list[list[list[str]]]:
    """Every markdown table in the document, as lists of cell lists."""
    tables, current = [], []
    for line in DOC.read_text().split("\n"):
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                continue                     # the header rule
            current.append(cells)
        elif current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


def _num(cell: str) -> float:
    return float(re.sub(r"[^0-9.\-+]", "", cell))


def single_track_rows() -> list[dict]:
    for t in _tables():
        if t[0][:2] == ["condition", "P, W"]:
            return [{"power": _num(r[1]), "speed": _num(r[2]) / 1e3,
                     "spot": _num(r[3]) * 1e-6, "width": _num(r[4]) * 1e-6,
                     "depth": _num(r[5]) * 1e-6,
                     "U_width": _num(r[6]), "U_depth": _num(r[7])}
                    for r in t[1:]]
    raise RuntimeError("single-track table not found in docs/measured-inputs.md")


def pad_rows() -> list[dict]:
    for t in _tables():
        if t[0][0].startswith("Y-pad cross-section"):
            rows = []
            for r in t[1:]:
                if r[0].strip() in ("", "|") or not r[1].strip():
                    continue                 # the mean row
                rows.append({"anti": _num(r[1]), "para": _num(r[2])})
            return rows
    raise RuntimeError("pad table not found in docs/measured-inputs.md")


def compare() -> dict:
    """Largest absolute disagreement between the document and the code."""
    doc = single_track_rows()
    worst = 0.0
    details = []
    if len(doc) != len(WEAVER_POINTS):
        raise AssertionError(f"document lists {len(doc)} single tracks, "
                             f"calibrate.py holds {len(WEAVER_POINTS)}")
    for d, p in zip(doc, WEAVER_POINTS):
        for key, got in (("power", p.power), ("speed", p.speed),
                         ("spot", p.spot_diameter), ("width", p.width),
                         ("depth", p.depth)):
            scale = max(abs(got), 1e-9)
            rel = abs(d[key] - got) / scale
            worst = max(worst, rel)
            if rel > 1e-6:
                details.append(f"{p.label} {key}: doc {d[key]!r} vs code {got!r}")

    pads = pad_rows()
    if len(pads) != len(Y_PAD_ANTIPARALLEL):
        raise AssertionError(f"document lists {len(pads)} pad cross-sections, "
                             f"weaver_pads.py holds {len(Y_PAD_ANTIPARALLEL)}")
    for d, a, b in zip(pads, Y_PAD_ANTIPARALLEL, Y_PAD_PARALLEL):
        for key, got in (("anti", a), ("para", b)):
            rel = abs(d[key] - got) / abs(got)
            worst = max(worst, rel)
            if rel > 1e-6:
                details.append(f"pad {key}: doc {d[key]!r} vs code {got!r}")

    # the uncertainties the document tabulates against the comment in calibrate.py
    text = (Path(__file__).resolve().parent / "calibrate.py").read_text()
    quoted = {}
    for m in re.finditer(r"#\s+case\s+([\d.]+)\s+width\s+([\d.]+)\s+depth\s+([\d.]+)",
                         text):
        quoted[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    if len(quoted) == len(doc):
        for d, (_, (uw, ud)) in zip(doc, sorted(quoted.items())):
            for key, got in (("U_width", uw), ("U_depth", ud)):
                rel = abs(d[key] - got) / abs(got)
                worst = max(worst, rel)
                if rel > 1e-6:
                    details.append(f"uncertainty {key}: doc {d[key]} vs "
                                   f"code comment {got}")
    return {"worst_relative_disagreement": worst,
            "n_single_tracks": len(doc), "n_pad_sections": len(pads),
            "n_uncertainties_checked": len(quoted),
            "details": details}


def report() -> None:
    r = compare()
    print("PROVENANCE CHECK: docs/measured-inputs.md against the code\n")
    print(f"   single-track conditions compared   {r['n_single_tracks']}")
    print(f"   pad cross-sections compared        {r['n_pad_sections']}")
    print(f"   uncertainty pairs compared         {r['n_uncertainties_checked']}")
    print(f"   worst relative disagreement        "
          f"{r['worst_relative_disagreement']:.2e}")
    if r["details"]:
        print("\n   DISAGREEMENTS:")
        for d in r["details"]:
            print(f"      {d}")
    else:
        print("\n   The document and the code carry the same numbers.")
    print("\n   What this does not check: whether either matches the article. "
          "That\n   still needs a person and a copy of the paper.")


if __name__ == "__main__":
    report()
