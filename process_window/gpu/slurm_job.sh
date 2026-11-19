#!/usr/bin/env bash
# HPC cluster with Slurm. Two steps, because compute nodes often have no
# internet:
#
#   1. On the LOGIN node (has internet), download the models once:
#        unzip gpu_bundle.zip && cd gpu_bundle
#        python3 -m pip install --user -r requirements-gpu.txt
#        python3 run_gpu.py --download-only --hf-cache $SCRATCH/hf_cache
#
#   2. Submit this job:
#        sbatch slurm_job.sh
#      If the job runs out of time, submit it again: it continues where it
#      stopped (same --out folder).
#
# Edit the #SBATCH lines and the module line for your cluster. Any GPU with
# 40 GB or more (A100, H100, L40S) runs one 7B model per card; two 16-32 GB
# cards (V100, T4) also work (the model is split over them).
#SBATCH --job-name=pw-gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=pw-gpu-%j.log
##SBATCH --partition=gpu          # uncomment and set for your cluster
##SBATCH --account=your_account   # uncomment if your cluster needs one

set -e
# module load python/3.11 cuda/12.1     # uncomment / adjust for your cluster
cd "${SLURM_SUBMIT_DIR:-$(dirname "$0")}"
SCRATCH_DIR="${SCRATCH:-$HOME}"
python3 run_gpu.py --offline --hf-cache "$SCRATCH_DIR/hf_cache" --out "$SCRATCH_DIR/pw_out" "$@"
# Results: $SCRATCH_DIR/pw_out/gpu_results.zip (copy it back with scp or rsync).
