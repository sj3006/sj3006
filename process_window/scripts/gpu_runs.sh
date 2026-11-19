#!/usr/bin/env bash
# Superseded by gpu/run_gpu.py: one script for rented GPUs, Kaggle and HPC
# clusters (instructions in gpu/RUN_ME.md; the upload-ready package is
# gpu/gpu_bundle.zip). Kept so the old command still works:
#   bash scripts/gpu_runs.sh             # Mistral-7B, OLMo-2-7B, Qwen2.5-7B
#   TIER=B bash scripts/gpu_runs.sh      # adds Qwen2.5-14B
set -e
cd "$(dirname "$0")/.."
MODELS="mistral7b,olmo7b,qwen7b"
if [ "${TIER:-A}" = "B" ]; then MODELS="$MODELS,qwen14b"; fi
exec python3 gpu/run_gpu.py --out gpu_out --models "$MODELS" "$@"
