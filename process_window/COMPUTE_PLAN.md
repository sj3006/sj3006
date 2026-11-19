# Compute plan

What extra compute would buy for the paper, how much it needs, and how to
run it. Nothing here is required for submission. The paper already has
three measured language-model surfaces done on a 4-core CPU: SmolLM2-135M
(12x12 and 23x23 grids), Qwen2.5-0.5B and Qwen2.5-1.5B (both 12x12).
The obvious reviewer question is "does this hold for a model people
actually deploy?" A GPU answers it.

## What to run

All models below are open (Apache-2.0), ungated on Hugging Face, and need
no account or token.

| Tier | Runs | Why it matters | GPU time | Rough cost |
|---|---|---|---|---|
| A | Three 7B base models from three families: Qwen2.5-7B, OLMo-2-7B, Mistral-7B-v0.3. For each: the 12x12 surface, the nested 23x23 surface, and 5 live runs of 10k generations | 7B rows in Tables 1-2 on both grids (does the edge-vs-area gap hold on a deployable model?); live runs where the certifier queries a large model directly; a model-size trend (0.1B to 7B) | about 10 GPU-hours on one 80 GB A100 or H100 | about $15-40 |
| B | Adds Qwen2.5-14B (same runs) | A second size point in one family above 7B | about 5 more GPU-hours (80 GB GPU) | about $10-20 more |
| C (later, optional) | An instruction-tuned model on chat prompts, with a task-level failure such as format violations or an LLM judge | Closer to a real deployment check | 20-40 GPU-hours plus a few days of code | $50-150 |

Recommended: tier A, then B if it went smoothly. Tier C is a follow-up paper
more than a fix for this one.

Prices are typical on-demand rates for GPU clouds (A100 80 GB about
$1.2-2.5/h, H100 about $2-3.5/h); check current prices. A 24 GB card (L4,
A10G) also works for the 7B models in bfloat16 but takes about 2-3 times
longer; it cannot hold the 14B model.

Free routes, slower to arrange: a university cluster; an NSF ACCESS
"Explore" allocation (free for US researchers, a few days to approve);
Kaggle notebooks (about 30 free GPU-hours a week on 16 GB T4/P100 cards,
enough for 1.5B-3B models; 7B would need a small change to split the
model over two cards).

## How the numbers were estimated

These are estimates, not measurements, with about a 2x margin.
- Per 7B model: 144 x 160 = 23,040 generations (12x12), 385 x 160 = 61,600
  more (23x23), and up to 5 x 7,700 live generations (the 2.3k pilot comes
  from the measured surface). That is about 123k generations of 48 tokens,
  each scored once more for its NLL: roughly 8M tokens generated and 8M
  scored.
- On an A100 a batch of 160 generations plus scoring takes a few seconds
  for a 7B model in bfloat16, so the surfaces take about 20-40 minutes and
  the live runs (smaller batches) about 30 minutes. Downloading and loading
  add about 10 minutes. That gives 1-1.5 h per model, or 3-4.5 h for three;
  the 10 h budget includes the margin.
- For comparison, measured on this 4-core CPU per setting of 160
  generations: SmolLM2-135M 40 s, Qwen2.5-0.5B 78 s, Qwen2.5-1.5B 183 s. A
  7B model would take about 15 minutes per setting, or days per grid, which
  is why the GPU is needed.
- Disk: about 15 GB per 7B model and 30 GB for the 14B; 80 GB in total.

## How to run it

On any Linux machine with an NVIDIA GPU, CUDA and Python 3.10+:

```
git clone <this repository>; cd <repo>/process_window
pip install -r requirements.txt -r requirements-lm.txt
bash scripts/gpu_runs.sh             # tier A
TIER=B bash scripts/gpu_runs.sh      # tier A + B (skips what is done)
```

Every step can be resumed, so a preempted or spot instance is fine: run the
script again. The outputs (results/lm/surface_scores_<tag>*.npz and
lm_live_<tag>_seed*.json, a few MB) are all that needs to come back; commit
them or copy them over. The analysis then runs on any CPU (commands at the
end of scripts/gpu_runs.sh), and I add the rows, the size trend and the
live-run results to the paper.

If the GPU machine runs the Claude desktop app or Claude Code with Remote
Control, it can also be attached to a session so the runs are driven from
there directly.

## What it changes in the paper

- Tables 1-2: 7B (and 14B) rows on the 12x12 and 23x23 grids.
- Section 6: a model-size trend (safe-region size and certification cost
  from 0.1B to 7B or 14B) and live runs on a 7B model. With these, the
  certification cost can also be reported in GPU-minutes against the
  full-grid baseline.
- Limitations: "three small models (0.1B-1.5B)" becomes "models from 0.1B to 7B (14B)".
