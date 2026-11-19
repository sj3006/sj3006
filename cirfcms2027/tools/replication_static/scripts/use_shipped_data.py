#!/usr/bin/env python3
"""Copy the shipped generated data from `data/generated/` into `code/`.

The programs in `code/` read and write their outputs next to themselves. The
package keeps the canonical copies of those outputs separately, in
`data/generated/`, so that `code/` starts clean. This script puts the shipped
copies where the programs expect them, which lets the claim checks run in
minutes instead of rerunning the studies.

    python3 scripts/use_shipped_data.py          # copy, overwriting
    python3 scripts/use_shipped_data.py --list   # show the mapping only
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: shipped file -> where the code reads it
MAPPING = {
    "data/generated/certificate/results.json": "code/certificate/results.json",
    "data/generated/fidelity/_region.json": "code/fidelity/_region.json",
    "data/generated/fidelity/_study.json": "code/fidelity/_study.json",
    "data/generated/fidelity/_results.json": "code/fidelity/_results.json",
    "data/generated/fidelity/_grid.json": "code/fidelity/_grid.json",
    "data/generated/fidelity/_floor.json": "code/fidelity/_floor.json",
    "data/generated/fidelity/_sloppy.json": "code/fidelity/_sloppy.json",
    "data/generated/fidelity/caches/_jacobians.json": "code/fidelity/_jacobians.json",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    for src, dst in MAPPING.items():
        print(f"{src}  ->  {dst}")
        if not a.list:
            (ROOT / dst).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / src, ROOT / dst)
    if not a.list:
        print(f"copied {len(MAPPING)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
