#!/usr/bin/env bash
# Quick verification of the whole package, about ten minutes on a laptop.
#
#   1. every file matches MANIFEST.tsv
#   2. the shipped generated data is put where the code reads it
#   3. the theory of the certificate and fidelity papers is checked by simulation
#   4. every number printed in each of the three papers is checked against the
#      code: the conference paper by full recomputation, the other two against
#      the shipped results files
#
# Exits non-zero at the first failure. Set PYTHON to choose the interpreter.
set -euo pipefail
PY="${PYTHON:-python3}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

step() { printf '\n=== %s\n' "$1"; }

step "1/6 manifest"
"$PY" scripts/verify_manifest.py

step "2/6 shipped data into place"
"$PY" scripts/use_shipped_data.py

step "3/6 conference paper: 234 printed numbers, recomputed from scratch (about 4 min)"
( cd code && "$PY" repro/check.py --no-cache )

step "4/6 certificate paper: theory checks"
( cd code/certificate && "$PY" verify.py )

step "5/6 certificate paper: printed numbers against results.json"
( cd code/certificate && "$PY" claims.py )

step "6/6 fidelity paper: theory checks and printed numbers"
( cd code/fidelity && "$PY" verify.py && PYTHONPATH=../src "$PY" claims.py )

printf '\nAll checks passed.\n'
