# Running the 7B language-model measurements on a GPU

This folder is everything a GPU machine needs: the code, the exact prompts,
and one script, `run_gpu.py`. The same script runs on a rented GPU, on
Kaggle and on an HPC cluster; only the way you start it differs. It
downloads the models itself (about 15 GB each, no account needed), chooses
the precision and the GPU layout for the machine, tests before the long
run, saves after every step, and at the end writes **one file to bring
back: `gpu_results.zip`**.

## What it runs

By default it runs three 7B base models: Mistral-7B-v0.3, OLMo-2-7B and
Qwen2.5-7B. Each model goes through these steps:

| Step | What | Rough time on one A100 | On Kaggle's 2 x T4 |
|---|---|---|---|
| test | 2 settings: speed, memory, numerical check | 2 min | 5 min |
| surface12 | 12 x 12 settings x 160 generations | 15-30 min | 40-80 min |
| surface23 | 385 more settings (23 x 23 grid) | 40-80 min | 2-3.5 h |
| live | 2 live runs (the certifier queries the model) | 20-40 min | 1-2 h |
| analyze | the paper's 12 x 12 analyses (CPU) | 5 min | 5 min |

These are estimates. After the test, the script prints the real per-model
estimate for your machine. In total, expect about 3-6 h on one A100 or
H100, and 10-20 h on Kaggle (one to two weeks of the free quota, in 12-hour
sessions).

## Start with a dry run

A dry run checks the whole pipeline in a few minutes, with a tiny model:
```
python run_gpu.py --dry-run --out test_out
```
If it ends with `results packed: .../gpu_results.zip`, everything works.

## A. Rented GPU (RunPod, Lambda, Vast.ai, any cloud VM)

Pick an image with PyTorch and CUDA, and one 40-80 GB GPU (A100, H100,
L40S). A 24 GB card (L4, A10G) also works, at a smaller batch size. You
need about 60 GB of disk. Upload `gpu_bundle.zip`, then:
```
unzip gpu_bundle.zip && cd gpu_bundle
bash rented_gpu.sh --dry-run          # 3 minutes; check it says "results packed"
bash rented_gpu.sh                    # the real run, in the background
tail -f ~/pw_out/logs/run_gpu.log     # watch; Ctrl-C only stops watching
```
When the log says `results packed` for the last model, download
`~/pw_out/gpu_results.zip` and stop the machine.

## B. Kaggle (free; about 30 GPU-hours a week)

1. Kaggle → Datasets → New Dataset → upload `gpu_bundle.zip` (keep it
   private).
2. Kaggle → Code → New Notebook → File → Import Notebook →
   `kaggle_notebook.ipynb` (it is in this folder).
3. In the session options, set:
   - Accelerator: **GPU T4 x2**;
   - Internet: **on**;
   - Add Input: your `gpu_bundle` dataset.
4. Save Version → **Save & Run All (Commit)**. It runs for up to 12 h with
   the browser closed.
5. Open the version → Output → download `out/gpu_results.zip`.
6. If the log says `paused (time limit)`, continue the run:
   - Add Input → Your Work → this notebook (its output);
   - Save & Run All again.

   It continues where it stopped.

T4 cards have no bfloat16, so the script uses float16 on Kaggle.
- If a model overflows in float16 (Qwen models sometimes do), the script
  reports it and moves on to the next model.
- That model can then be run on a bfloat16 GPU (A100, H100, L4, A10), or
  replaced with `qwen3b` in the notebook's `MODELS` line.

## C. HPC cluster (Slurm)

Compute nodes often have no internet, so download first on the login
node:
```
unzip gpu_bundle.zip && cd gpu_bundle
python3 -m pip install --user -r requirements-gpu.txt
python3 run_gpu.py --download-only --hf-cache $SCRATCH/hf_cache
```
Then edit the `#SBATCH` lines in `slurm_job.sh` for your cluster
(partition, account, time) and submit it:
```
sbatch slurm_job.sh
```
If the job hits its time limit, run `sbatch slurm_job.sh` again; it
continues. The script reads the remaining job time from Slurm and packs the
results before the end. Copy `$SCRATCH/pw_out/gpu_results.zip` back.

On a cluster without Slurm, run the step-2 command directly:
```
python3 run_gpu.py --offline --hf-cache <cache> --out <out>
```

## Options you may want

- `--models mistral7b,olmo7b,qwen7b`: which models. Also available:
  `qwen3b`, `qwen14b` (needs 40 GB or more), or any Hugging Face name.
- `--stages surface12,surface23,live,analyze`: drop steps to save time.
  The 12 x 12 surface alone already gives the Table 1-2 rows.
- `--live-seeds 0,1`: how many live runs per model.
- `--time-limit 11.5`: stop in time and pack.
- `--resume-from <folder or zip>`: continue an earlier run in a new output
  folder.
- `--delete-models-after`: free disk after each model.
- Force settings: `--dtype bfloat16|float16|float32`, `--device
  cuda|auto|cpu`, `--batch 80` (if memory runs out repeatedly).

## What comes back

`gpu_results.zip` contains:
- `results/lm/surface_scores_<model>.npz` and `..._23.npz`: the measured
  surfaces;
- `lm_live_<model>_seed*.json`: the live runs;
- `lm_*_<model>.csv`: the analysis tables;
- `surface_scores_<model>.meta.json`: GPU, precision and versions used;
- `logs/`: everything printed;
- `run_info.json`: a summary.

Put the files from `results/lm/` into `process_window/results/lm/` in the
repository and commit them. Then follow "Add a new language model to the
paper" in PROJECT_RECORD.md, section 9.
