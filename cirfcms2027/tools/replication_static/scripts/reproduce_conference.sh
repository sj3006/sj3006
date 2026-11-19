#!/usr/bin/env bash
# Reproduce the conference paper from the forward model.
#
#   repro/check.py --no-cache   recomputes every printed number (about 4 min)
#                               and writes code/repro/REPORT.md
#   run_all.py                  optional, with --full: every analysis stage in
#                               the order of the paper's argument (about 15 min)
#
# The shipped report for comparison is data/generated/conference/REPORT.md.
set -euo pipefail
PY="${PYTHON:-python3}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/code"
"$PY" repro/check.py --no-cache
if [[ "${1:-}" == "--full" ]]; then
  "$PY" run_all.py --save
fi
echo "Report: code/repro/REPORT.md (compare with data/generated/conference/REPORT.md)"
