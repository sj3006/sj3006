"""ML-native application: certifying safe text-generation settings.

Settings are (temperature, top-p) pairs for sampling from a language model.
Each "coupon" is one generated continuation of a random prompt, judged for
two failure modes that move in opposite directions:

- degenerate: the continuation repeats itself. Measured by seq-rep-4, the
  fraction of 4-grams that repeat an earlier 4-gram in the same continuation
  (Welleck et al. 2020). Gets worse at LOW temperature / top-p.
- incoherent: the continuation is text the model itself finds very
  unlikely. Measured by the mean per-token negative log-likelihood under the
  model's own unmodified distribution (temperature 1, no truncation). Gets
  worse at HIGH temperature / top-p.

A setting fails a mode when the score passes a threshold; the per-mode
failure rate at a setting is the probability over prompts and sampling.
This module generates and scores; the certification code is unchanged.
"""

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "HuggingFaceTB/SmolLM2-135M"


def load(name=MODEL, threads=4, device="cpu", dtype=None):
    """Tokenizer and model. dtype=None keeps the checkpoint's precision
    (bfloat16 for the models we use); on a GPU pass device="cuda". Scores
    are always computed in float32."""
    torch.set_num_threads(threads)
    tok = AutoTokenizer.from_pretrained(name)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    kw = {} if dtype is None else {"dtype": getattr(torch, dtype)}
    model = AutoModelForCausalLM.from_pretrained(name, **kw).to(device)
    model.eval()
    return tok, model


def wikitext_prompts(n=400, words=12, seed=0):
    """Short prompts: the first `words` words of WikiText-2 paragraphs."""
    from datasets import load_dataset
    ds = load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1", split="test")
    paras = [t.strip() for t in ds["text"] if len(t.split()) > 40 and not t.strip().startswith("=")]
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(paras), size=min(n, len(paras)), replace=False)
    return [" ".join(paras[i].split()[:words]) for i in pick]


def seq_rep_n(ids, n=4):
    grams = [tuple(ids[i:i + n]) for i in range(len(ids) - n + 1)]
    if not grams:
        return 0.0
    return 1.0 - len(set(grams)) / len(grams)


@torch.no_grad()
def generate_and_score(tok, model, prompts, temperature, top_p, max_new_tokens=48, score_batch=32):
    """Return (seq-rep-4, mean NLL) for one continuation per prompt. The NLL
    pass runs `score_batch` sequences at a time (the float32 log-probabilities
    over a large vocabulary dominate memory on a GPU)."""
    enc = tok(prompts, return_tensors="pt", padding=True).to(model.device)
    out = model.generate(**enc, do_sample=True, temperature=float(temperature), top_p=float(top_p),
                         max_new_tokens=max_new_tokens, pad_token_id=tok.pad_token_id)
    cont = out[:, enc["input_ids"].shape[1]:]
    # NLL of the continuation under the unmodified model.
    attn = torch.cat([enc["attention_mask"], torch.ones_like(cont)], dim=1)
    start = enc["input_ids"].shape[1] - 1
    nll = []
    for s in range(0, out.shape[0], score_batch):
        sl = slice(s, s + score_batch)
        logits = model(input_ids=out[sl], attention_mask=attn[sl]).logits[:, :-1, :]
        logp = torch.log_softmax(logits.float(), dim=-1)
        tok_lp = logp.gather(-1, out[sl, 1:].unsqueeze(-1)).squeeze(-1)
        cont_lp = tok_lp[:, start:]
        valid = cont[sl] != tok.pad_token_id
        nll.append(-(cont_lp * valid).sum(1) / valid.sum(1).clamp(min=1))
    nll = torch.cat(nll)
    reps = [seq_rep_n([t for t in row.tolist() if t != tok.pad_token_id]) for row in cont]
    return np.array(reps), nll.float().cpu().numpy()
