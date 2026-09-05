#!/usr/bin/env bash
# Run every verification check, fastest first. Logs land in results/.
# Usage:  ./run_all.sh          all checks
#         ./run_all.sh quick    skip the three long-running studies
set -uo pipefail
cd "$(dirname "$0")"
mkdir -p results

QUICK=${1:-full}

FAST=(
  table6_audit      # instant  - arithmetic only, no data needed
  repro_gbrm        # ~1 min   - GBRM metrics, writes results/model.joblib
  diagnostics       # ~3 min   - split leakage, seed sensitivity, 'time' feature
  paper_audit       # ~2 min   - every printed number vs the re-run
  lime_verify       # ~1 min   - local_exp[1] semantics, cell 32/35 reproduction
  agg_issues        # ~2 min   - the three WA-LIME aggregation issues
  walime_audit      # ~2 min   - WA-LIME convergence protocol from S4.4
)
SLOW=(
  stability_study   # ~25 min  - LIME vs WA-LIME across B, 10 instances
  compute_matched   # ~15 min  - the compute-matched LIME baseline
  seed_distribution # ~10 min  - sampling distribution of the 5-run Jaccard
  true_effect       # ~20 min  - well-powered comparison on instance #10
  rankwise          # ~10 min  - rank-position occupancy
  snr               # ~10 min  - per-feature signal-to-noise
)

run() {
  printf '\n=== %s ===\n' "$1"
  if python3 "scripts/$1.py" 2>&1 | tee "results/$1.log"; then
    echo "--- $1 ok"
  else
    echo "!!! $1 FAILED (see results/$1.log)"; return 1
  fi
}

fail=0
for s in "${FAST[@]}"; do run "$s" || fail=1; done
if [ "$QUICK" != "quick" ]; then
  for s in "${SLOW[@]}"; do run "$s" || fail=1; done
else
  echo -e "\n(skipping the long studies; drop 'quick' to run them)"
fi

echo
[ "$fail" -eq 0 ] && echo "All checks completed. Logs in results/." \
                  || echo "Some checks failed - see the !!! lines above."
exit $fail
