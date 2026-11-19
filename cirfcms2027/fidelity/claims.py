"""Every number the fidelity paper prints, checked against what the code computes.

Same mechanism as `../certificate/claims.py`. Each claim records the string as
printed in `paper/paper.tex` and the value it should equal. The runner checks
that the string still occurs in the paper (a number edited in the text and
nowhere else) and that the value still rounds to it (a number that moved in the
code and was never carried into the text). The tolerance is the printed
precision: `22.5` passes only while the value rounds to `22.5`.

    python3.13 results.py        # first; writes _results.json
    python3.13 claims.py         # check, exit non-zero on failure
    python3.13 claims.py --list  # what is registered
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "_results.json"
PAPER = HERE / "paper" / "paper.tex"


@dataclass
class Claim:
    cid: str
    section: str
    quoted: str                 # as it appears in the paper
    value: float                # what it should be
    getter: str                 # where the value comes from
    means: str                  # plain language
    places: int | None = None   # decimal places printed; inferred if None
    skip_text: bool = False


def _places(quoted: str) -> int:
    m = re.search(r"\.(\d+)", quoted)
    return len(m.group(1)) if m else 0


def _rounds_to(value: float, quoted: str, places: int | None) -> bool:
    p = _places(quoted) if places is None else places
    return f"{float(value):.{p}f}" == f"{float(quoted):.{p}f}"


def _present(paper: str, quoted: str) -> bool:
    """The quoted number occurs as a whole number, not inside a longer one."""
    pat = r"(?<![\d.])" + re.escape(quoted) + r"(?![\d])"
    return re.search(pat, paper) is not None


def _fam(R: dict, name: str) -> dict:
    return next(r for r in R["table"] if r["family"] == name)


def build(R: dict) -> list[Claim]:
    """Registered claims. Filled in with the results text; see paper.tex."""
    from claims_registry import claims            # noqa: E402
    return claims(R, Claim, _fam)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if not RESULTS.exists():
        print(f"{RESULTS} not found; run `python3.13 results.py` first")
        return 2
    R = json.loads(RESULTS.read_text())
    claims = build(R)
    paper = PAPER.read_text() if PAPER.exists() else ""
    if args.list:
        for c in claims:
            print(f"{c.cid:26s} §{c.section:5s} {c.quoted:>9s}  {c.means}")
        return 0
    print(f"Checking {len(claims)} claims against _results.json and paper.tex")
    print("=" * 78)
    bad_v, bad_t = [], []
    for c in claims:
        ok_v = _rounds_to(c.value, c.quoted, c.places)
        ok_t = c.skip_text or _present(paper, c.quoted)
        if not ok_v:
            bad_v.append(c)
        if not ok_t:
            bad_t.append(c)
        if not (ok_v and ok_t):
            p = _places(c.quoted) if c.places is None else c.places
            why = []
            if not ok_v:
                why.append(f"value {float(c.value):.{p + 3}f} prints as "
                           f"{float(c.value):.{p}f}, not {c.quoted}")
            if not ok_t:
                why.append(f"'{c.quoted}' not found in paper.tex")
            print(f"  [FAIL] {c.cid:26s} §{c.section:5s} {'; '.join(why)}")
            print(f"         from {c.getter}; means: {c.means}")
    print(f"\n{len(claims)} claims checked; {len(bad_v)} value mismatches, "
          f"{len(bad_t)} missing from the text")
    return 1 if (bad_v or bad_t) else 0


if __name__ == "__main__":
    raise SystemExit(main())
