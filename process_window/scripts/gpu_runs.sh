#!/bin/bash
# Language-model runs for a GPU machine. See COMPUTE_PLAN.md for what each
# step is for and what it costs. Run from process_window/ after
#   pip install -r requirements.txt -r requirements-lm.txt
# Every step is resumable: re-running the script skips finished settings.
#
#   bash scripts/gpu_runs.sh            # tier A: three 7B base models
#   TIER=B bash scripts/gpu_runs.sh     # adds Qwen2.5-14B
#
# Outputs go to results/lm/ (surface_scores_<tag>.npz, ..._<tag>_23.npz,
# lm_live_<tag>_seed<k>.json). Copy that folder back; the analysis below runs
# on any CPU.
set -euo pipefail
export HF_HOME=${HF_HOME:-$HOME/.cache/huggingface}
GPU="--device cuda --dtype bfloat16 --batch 160 --threads 8"

MODELS=("qwen7b Qwen/Qwen2.5-7B" "olmo7b allenai/OLMo-2-1124-7B" "mistral7b mistralai/Mistral-7B-v0.3")
if [ "${TIER:-A}" = "B" ]; then
  MODELS+=("qwen14b Qwen/Qwen2.5-14B")
fi

for entry in "${MODELS[@]}"; do
  read -r tag name <<< "$entry"
  echo "== $name ($tag)"
  # 1. measured surface, 12 x 12 grid (144 settings x 160 generations)
  python3 experiments/lm_surface.py --model "$name" --tag "$tag" $GPU
  # 2. nested 23 x 23 grid (385 new settings; reuses the 12 x 12 ones)
  python3 experiments/lm_surface.py --model "$name" --tag "$tag" --n 23 $GPU
  # 3. live runs: the certifier queries the model directly (5 seeds, 10k generations each)
  for seed in 0 1 2 3 4; do
    python3 experiments/lm_live.py --model "$name" --surface "results/lm/surface_scores_$tag.npz" \
      --budget 10000 --seed "$seed" --device cuda --dtype bfloat16
  done
done

# CPU analysis (here or after copying results/lm/ back), per tag:
#   python3 experiments/exp_lm.py --parts cost,confidence,check,budget,gp --surface results/lm/surface_scores_<tag>.npz
#   python3 experiments/exp_lm.py --parts cost,confidence --surface results/lm/surface_scores_<tag>_23.npz \
#       --pilot-stride 2 --budget 150000
