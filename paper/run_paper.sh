#!/usr/bin/env bash
# Regenerate every number for the paper, from scratch.
# Edit paper/config.py first; whatever it says is what gets produced.
set -uo pipefail
cd "$(dirname "$0")"
STAGES=(01_dataset 02_model 03_explanations 04_stability 05_rank_snr)
fail=0
for s in "${STAGES[@]}"; do
  echo; echo "########## $s ##########"
  if python3 "$s.py" 2>&1 | tee "../paper_outputs/${s}.log"; then :; else
    echo "!!! $s FAILED"; fail=1; break
  fi
done
echo
if [ "$fail" -eq 0 ]; then
  echo "Done. Tables (t*.csv) and metadata (s*.json) are in paper_outputs/."
else
  echo "Stopped on failure - later stages not run."
fi
exit $fail
