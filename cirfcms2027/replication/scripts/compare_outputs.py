#!/usr/bin/env python3
"""Compare a regenerated JSON output with the shipped one, number by number.

    python3 scripts/compare_outputs.py NEW.json SHIPPED.json [--rtol 1e-6] [--atol 1e-9]

Walks both structures together. Numbers agree if
`|a - b| <= atol + rtol * |b|`; NaN agrees with NaN; strings and booleans must
be equal; lists must have the same length; dictionaries the same keys. Keys
that record run time (`seconds`, `timings`) are ignored. Prints every
disagreement with its path and exits non-zero if there is any.

A rerun on the machine that produced the shipped data reproduces it exactly.
On other hardware or library versions, floating-point summation order can move
the last digits; the default tolerance absorbs that without hiding a real
change, and the claim checks, which compare at the printed precision, are the
test that matters for the papers.
"""

from __future__ import annotations

import argparse
import json
import math
import sys

IGNORE = {"seconds", "timings"}


def walk(a, b, path, rtol, atol, out):
    if isinstance(b, dict):
        if not isinstance(a, dict):
            out.append((path, "type differs"))
            return
        ka, kb = set(a) - IGNORE, set(b) - IGNORE
        for k in sorted(ka ^ kb):
            out.append((f"{path}/{k}", "key present in only one file"))
        for k in sorted(ka & kb):
            walk(a[k], b[k], f"{path}/{k}", rtol, atol, out)
    elif isinstance(b, list):
        if not isinstance(a, list) or len(a) != len(b):
            out.append((path, f"list length {len(a) if isinstance(a, list) else '-'} vs {len(b)}"))
            return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", rtol, atol, out)
    elif isinstance(b, bool) or isinstance(b, str) or b is None:
        if a != b:
            out.append((path, f"{a!r} vs {b!r}"))
    elif isinstance(b, (int, float)):
        if not isinstance(a, (int, float)) or isinstance(a, bool):
            out.append((path, f"{a!r} vs {b!r}"))
        elif math.isnan(b) or math.isnan(a):
            if not (math.isnan(a) and math.isnan(b)):
                out.append((path, f"{a!r} vs {b!r}"))
        elif abs(a - b) > atol + rtol * abs(b):
            out.append((path, f"{a!r} vs {b!r}"))
    else:
        if a != b:
            out.append((path, f"{a!r} vs {b!r}"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("new")
    ap.add_argument("shipped")
    ap.add_argument("--rtol", type=float, default=1e-6)
    ap.add_argument("--atol", type=float, default=1e-9)
    a = ap.parse_args()
    A = json.load(open(a.new))
    B = json.load(open(a.shipped))
    out = []
    walk(A, B, "", a.rtol, a.atol, out)
    if out:
        print(f"{a.new}: {len(out)} disagreements with {a.shipped}")
        for p, why in out[:40]:
            print(f"   {p or '/'}: {why}")
        if len(out) > 40:
            print(f"   ... and {len(out) - 40} more")
        return 1
    print(f"{a.new}: agrees with {a.shipped} (rtol {a.rtol:g}, atol {a.atol:g})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
