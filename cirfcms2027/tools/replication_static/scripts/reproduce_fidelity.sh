#!/usr/bin/env bash
# Reproduce the fidelity paper's results from scratch.
#
# Time on four cores: region sampling ~7 min, twin study ~45 min, grid
# convergence ~5 min, floor check ~10 min, the rest ~2 min. The study uses four
# worker processes; set OMP_NUM_THREADS=1 (done below) so they do not
# oversubscribe the cores.
#
# The local linearised analysis (sloppy.py) failed and is not used in the paper;
# its shipped output is copied in unchanged unless --with-sloppy is given
# (about 15 min more).
#
# Each regenerated output is compared with the shipped copy in
# data/generated/fidelity/. fill_tables.py rewrites the data tables inside
# code/fidelity/paper/paper.tex from the new results, so that file will differ
# from the manifest afterwards only if the results differ.
set -euo pipefail
PY="${PYTHON:-python3}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHIP="$ROOT/data/generated/fidelity"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=../src
cd "$ROOT/code/fidelity"
rm -f _region.json _study.json _results.json _grid.json _floor.json _jacobians.json

"$PY" verify.py
"$PY" twins.py
"$PY" study.py
"$PY" grid_convergence.py
"$PY" floor_check.py
if [[ "${1:-}" == "--with-sloppy" ]]; then
  "$PY" sloppy.py
else
  cp "$SHIP/_sloppy.json" _sloppy.json
fi
"$PY" results.py
"$PY" fill_tables.py
"$PY" fig_fidelity.py
"$PY" fig_theory.py
"$PY" fig_region.py
"$PY" claims.py

status=0
for f in _region.json _study.json _grid.json _floor.json _results.json; do
  "$PY" "$ROOT/scripts/compare_outputs.py" "$f" "$SHIP/$f" || status=1
done
exit $status
