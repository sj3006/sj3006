#!/usr/bin/env bash
# Reproduce the certificate paper's results from scratch (about 10 min).
#
#   results.py   recomputes every quoted number into code/certificate/results.json
#   figures.py   redraws the figures into code/certificate/figures/
#   claims.py    checks the paper's printed numbers against the new results
#   compare      the new results.json against the shipped one
set -euo pipefail
PY="${PYTHON:-python3}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/code/certificate"
rm -f _response_cache.npz results.json
"$PY" verify.py
"$PY" results.py
"$PY" figures.py
"$PY" claims.py
"$PY" "$ROOT/scripts/compare_outputs.py" results.json "$ROOT/data/generated/certificate/results.json"
