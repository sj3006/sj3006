#!/usr/bin/env python3
"""Check every file in the package against `MANIFEST.tsv`.

    python3 scripts/verify_manifest.py

Reports files that are missing, changed (SHA-256 differs) or not listed.
Files created by running the code (outputs copied into `code/`, caches,
LaTeX by-products, Python bytecode) are not part of the package and are
ignored. Exits non-zero on any discrepancy.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {"__pycache__", "cache", "output"}
SKIP_SUFFIX = {".pyc", ".aux", ".log", ".out", ".bbl", ".blg", ".spl", ".npz"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ignorable(rel: str) -> bool:
    p = Path(rel)
    if set(p.parts) & SKIP_PARTS or p.suffix in SKIP_SUFFIX:
        return True
    # outputs the programs write into code/ when run
    if rel.startswith("code/") and (p.name.startswith("_") and p.suffix == ".json"):
        return True
    if rel in {"code/certificate/results.json", "code/repro/REPORT.md"}:
        return True
    if rel.startswith(("code/paper/", "code/figures/", "code/certificate/figures/",
                       "code/fidelity/paper/figures/")) and p.suffix in {".png", ".pdf"}:
        return True
    return rel == "MANIFEST.tsv"


def main() -> int:
    listed = {}
    for line in (ROOT / "MANIFEST.tsv").read_text().splitlines()[1:]:
        path, size, digest, _ = line.split("\t", 3)
        listed[path] = digest
    bad = 0
    for path, digest in listed.items():
        p = ROOT / path
        if not p.exists():
            print(f"missing   {path}")
            bad += 1
        elif sha256(p) != digest:
            print(f"changed   {path}")
            bad += 1
    for p in sorted(ROOT.rglob("*")):
        if p.is_file():
            rel = p.relative_to(ROOT).as_posix()
            if rel not in listed and not ignorable(rel):
                print(f"unlisted  {rel}")
                bad += 1
    print(f"{len(listed)} files listed; {bad} discrepancies")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
