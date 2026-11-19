#!/usr/bin/env bash
# Rented GPU (RunPod, Lambda, Vast.ai, a cloud VM, a lab workstation):
# install, then run in the background so closing the terminal does not stop it.
#
#   unzip gpu_bundle.zip && cd gpu_bundle
#   bash rented_gpu.sh                 # the three 7B models
#   bash rented_gpu.sh --dry-run       # a 3-minute test first (recommended)
#
# Watch progress:   tail -f ~/pw_out/logs/run_gpu.log
# When it says "results packed", download ~/pw_out/gpu_results.zip
# (scp, or the provider's file browser) and switch the machine off.
set -e
cd "$(dirname "$0")"
python3 -m pip install -q -r requirements-gpu.txt
OUT="${PW_OUT:-$HOME/pw_out}"
mkdir -p "$OUT"
nohup python3 run_gpu.py --out "$OUT" --hf-cache "${HF_CACHE:-$HOME/hf_cache}" "$@" > "$OUT/console.log" 2>&1 &
echo "started (process $!). Progress: tail -f $OUT/logs/run_gpu.log"
