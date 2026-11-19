"""One command for every GPU machine: measure the language-model surfaces for
the paper's larger models, run the live checks and the analyses, and pack
everything into one zip to bring back.

The same command works on a rented GPU, on Kaggle and on an HPC cluster:

    python run_gpu.py --out OUT_DIR [options]

What it does, for each model in turn (default: Mistral-7B-v0.3, OLMo-2-7B,
Qwen2.5-7B):
  1. download the model (or use the local cache; --offline for no internet),
  2. pick the precision (bfloat16 on A100/H100/L4/A10-class cards, float16 on
     T4/V100/P100) and whether to split the model over several GPUs,
  3. a 2-setting test: measures the speed, prints a time estimate, and
     catches float16 overflow (then retries in float32 if it fits, else
     skips the model) and out-of-memory errors (then halves the batch),
  4. the 12 x 12 surface, the nested 23 x 23 surface, live runs (the
     certifier querying the model) and the 12 x 12 analyses.
Every step saves after each setting and resumes where it stopped, so a
session that ends early loses at most a few minutes: run the same command
again (with --resume-from pointing at the old output if the output folder
is new, as on Kaggle).

At the end (or when --time-limit is reached) it writes OUT_DIR/gpu_results.zip
with the measured surfaces, live runs, analysis tables, logs and a run
summary. That zip is all that needs to come back.

Try it first with --dry-run (a 135M model, a few minutes, works on CPU too).
"""

import argparse
import glob
import json
import os
import platform
import queue
import shutil
import subprocess
import sys
import threading
import time
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE if os.path.isdir(os.path.join(HERE, "experiments")) else os.path.dirname(HERE)
EXP = os.path.join(ROOT, "experiments")

MODELS = {   # tag: Hugging Face repository (all open, no account needed)
    "mistral7b": "mistralai/Mistral-7B-v0.3",
    "olmo7b": "allenai/OLMo-2-1124-7B",
    "qwen7b": "Qwen/Qwen2.5-7B",
    "qwen3b": "Qwen/Qwen2.5-3B",
    "qwen14b": "Qwen/Qwen2.5-14B",
    "dryrun": "HuggingFaceTB/SmolLM2-135M",
}
DEFAULT_MODELS = "mistral7b,olmo7b,qwen7b"
ALLOW = ["*.json", "*.safetensors", "*.model", "*.txt", "*.tiktoken", "tokenizer*"]
IGNORE = ["consolidated*", "original/*", "*.bin", "*.pth", "*.pt", "*.gguf", "*.msgpack", "*.h5"]
BYTES = {"float32": 4, "bfloat16": 2, "float16": 2, None: 2}
ANALYSIS_PARTS = ["cost", "confidence", "check,budget", "gp"]


# -- small helpers ----------------------------------------------------------------

class Run:
    def __init__(self, args):
        self.args = args
        self.out = os.path.abspath(args.out)
        self.res = os.path.join(self.out, "results", "lm")
        self.logs = os.path.join(self.out, "logs")
        os.makedirs(self.res, exist_ok=True)
        os.makedirs(self.logs, exist_ok=True)
        self.t0 = time.time()
        self.deadline = None
        if args.time_limit:
            self.deadline = self.t0 + args.time_limit * 3600 - args.margin * 60
        self.info = dict(started=time.strftime("%Y-%m-%d %H:%M:%S"), command=" ".join(sys.argv),
                         platform=platform.platform(), python=sys.version.split()[0], models={})
        self.main_log = open(os.path.join(self.logs, "run_gpu.log"), "a")

    def say(self, msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        self.main_log.write(line + "\n")
        self.main_log.flush()

    def remaining(self):
        return None if self.deadline is None else self.deadline - time.time()

    def env(self, threads=4):
        e = dict(os.environ)
        e["PWCERT_LM_RESULTS"] = self.res
        e["OMP_NUM_THREADS"] = str(threads)
        e["TOKENIZERS_PARALLELISM"] = "false"
        e.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        return e

    def run(self, cmd, logname, threads=4):
        """Run one step as a subprocess, streaming its output to the console
        and to logs/<logname>. Returns 'ok', 'timeout', 'nonfinite', 'oom',
        'access', 'disk' or 'error'."""
        path = os.path.join(self.logs, logname)
        self.say("$ " + " ".join(cmd))
        with open(path, "a") as log:
            log.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(cmd)}\n")
            log.flush()
            p = subprocess.Popen(cmd, cwd=ROOT, env=self.env(threads), stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True, bufsize=1)
            q = queue.Queue()
            reader = threading.Thread(target=lambda: [q.put(x) for x in p.stdout] and None, daemon=True)
            reader.start()
            tail = []
            killed = False
            while True:
                try:
                    line = q.get(timeout=5)
                except queue.Empty:
                    line = None
                if line:
                    log.write(line)
                    log.flush()
                    tail = (tail + [line])[-300:]
                    if "Loading weights" not in line and "it/s]" not in line:
                        print("   " + line.rstrip(), flush=True)
                elif p.poll() is not None and not reader.is_alive() and q.empty():
                    break
                if self.deadline and time.time() > self.deadline and p.poll() is None:
                    p.kill()
                    killed = True
                    break
            p.wait()
        if killed:
            self.say("time limit reached: stopped this step (finished settings are saved)")
            return "timeout"
        if p.returncode == 0:
            return "ok"
        text = "".join(tail)
        if "NONFINITE" in text or "probability tensor contains" in text:
            return "nonfinite"
        if "out of memory" in text.lower() or "OutOfMemoryError" in text:
            return "oom"
        if "No space left" in text:
            return "disk"
        if "gated" in text.lower() or "401 Client Error" in text or "403 Client Error" in text:
            return "access"
        return "error"


def gpu_info():
    """GPU names, memory (GB) and compute capability, read in a child
    process so this process never holds GPU memory."""
    code = ("import json, torch\n"
            "g=[dict(name=torch.cuda.get_device_name(i),"
            "mem=torch.cuda.get_device_properties(i).total_memory/1e9,"
            "cc=list(torch.cuda.get_device_capability(i))) for i in range(torch.cuda.device_count())]\n"
            "import transformers\n"
            "print(json.dumps(dict(gpus=g, torch=torch.__version__, transformers=transformers.__version__,"
            "cuda=torch.version.cuda)))")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("Could not import torch/transformers:\n" + r.stderr[-2000:] +
                         "\nInstall them: pip install -r requirements-gpu.txt")
    return json.loads(r.stdout.strip().splitlines()[-1])


def param_count(snapshot):
    """Number of parameters, from the safetensors headers (no loading)."""
    n = 0
    for f in glob.glob(os.path.join(snapshot, "*.safetensors")):
        with open(f, "rb") as fh:
            size = int.from_bytes(fh.read(8), "little")
            header = json.loads(fh.read(size))
        for k, v in header.items():
            if k != "__metadata__":
                c = 1
                for d in v["shape"]:
                    c *= d
                n += c
    return n


def download(run, repo):
    from huggingface_hub import snapshot_download
    kw = dict(allow_patterns=ALLOW, ignore_patterns=IGNORE)
    if run.args.offline:
        return snapshot_download(repo, local_files_only=True, **kw)
    free = shutil.disk_usage(os.environ.get("HF_HOME", os.path.expanduser("~"))).free / 1e9
    run.say(f"downloading {repo} (free disk: {free:.0f} GB; 7B models need 15-30 GB)")
    return snapshot_download(repo, **kw)


def delete_model(repo):
    hub = os.path.join(os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface")), "hub")
    d = os.path.join(hub, "models--" + repo.replace("/", "--"))
    if os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)


def n_settings(path):
    if not os.path.exists(path):
        return 0
    import numpy as np
    with np.load(path, allow_pickle=True) as z:
        return len([k for k in z.files if k[0].isdigit()])


def seconds_per_setting(logpath):
    """From the last two progress lines '[k/N] ... (XXs)' of a surface log."""
    import re
    times = []
    with open(logpath) as f:
        for line in f:
            m = re.search(r"^\[\d+/\d+\].*\((\d+)s\)\s*$", line.strip())
            if m:
                times.append(int(m.group(1)))
    return times[-1] - times[-2] if len(times) >= 2 and times[-1] > times[-2] else None


# -- one model ----------------------------------------------------------------------

def plan(run, hw, n_params, meta):
    """Choose dtype, device placement and batch sizes for this machine."""
    a = run.args
    gpus = hw["gpus"]
    if not gpus:
        return dict(dtype=a.dtype, device="cpu", batch=a.batch or 32, score_batch=a.score_batch or 32)
    if a.dtype:
        dtype = a.dtype
    elif meta.get("dtype"):
        dtype = meta["dtype"]              # keep a resumed model in the precision it started in
    else:
        dtype = "bfloat16" if min(g["cc"][0] for g in gpus) >= 8 else "float16"
    if dtype == "bfloat16" and min(g["cc"][0] for g in gpus) < 8:
        raise RuntimeError("this model was started in bfloat16, which these GPUs do not support; continue "
                           "on an A100/H100/L4/A10-class GPU, or delete its files to restart in float16")
    w = n_params * BYTES[dtype] / 1e9
    one, total = min(g["mem"] for g in gpus), sum(g["mem"] for g in gpus)
    if a.device:
        device = a.device
    elif w + 5 <= 0.9 * one:
        device = "cuda"
    elif len(gpus) > 1 and w + 4 * len(gpus) <= 0.85 * total:
        device = "auto"
    else:
        raise RuntimeError(f"the model needs about {w:.0f} GB of GPU memory in {dtype} plus room to "
                           f"work; these GPUs have {total:.0f} GB in total")
    batch = a.batch or 160
    score_batch = a.score_batch or (32 if one >= 40 else 16)
    return dict(dtype=dtype, device=device, batch=batch, score_batch=score_batch, weights_gb=round(w, 1))


def surface_cmd(repo, tag, n, p, per_setting, max_settings=0):
    cmd = [sys.executable, "-u", os.path.join(EXP, "lm_surface.py"), "--model", repo, "--tag", tag,
           "--n", str(n), "--device", p["device"], "--batch", str(min(p["batch"], per_setting)),
           "--score-batch", str(p["score_batch"]), "--per-setting", str(per_setting), "--threads", "4"]
    if p["dtype"]:
        cmd += ["--dtype", p["dtype"]]
    if max_settings:
        cmd += ["--max-settings", str(max_settings)]
    return cmd


def do_model(run, tag, hw):
    a = run.args
    repo = MODELS.get(tag, tag)
    if "/" in tag:                          # a raw repository name was given
        tag = tag.split("/")[-1].lower().replace(".", "").replace("-", "")
    st = run.info["models"].setdefault(tag, dict(repo=repo, stages={}))
    s12 = os.path.join(run.res, f"surface_scores_{tag}.npz")
    s23 = os.path.join(run.res, f"surface_scores_{tag}_23.npz")
    meta_path = os.path.join(run.res, f"surface_scores_{tag}.meta.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    per_setting = 20 if a.dry_run else 160

    try:
        snap = download(run, repo)
    except Exception as e:                  # noqa: BLE001 (report and move on)
        msg = str(e)
        st["status"] = "download failed: " + msg[:300]
        run.say(f"{tag}: download failed ({msg[:200]}); skipping. If it says gated or 401, set HF_TOKEN.")
        return
    n_params = param_count(snap)
    try:
        p = plan(run, hw, n_params, meta)
    except RuntimeError as e:
        st["status"] = "skipped: " + str(e)
        run.say(f"{tag}: {e}; skipping")
        return
    run.say(f"{tag}: {n_params / 1e9:.2f}B parameters; plan {p}")

    # 1. test on 2 settings: speed, overflow, memory
    tries = 0
    while n_settings(s12) < 144:
        before = n_settings(s12)
        if before >= 2 and tries == 0 and meta:
            break                                       # resumed and already tested
        status = run.run(surface_cmd(repo, tag, 12, p, per_setting, max_settings=2), f"{tag}_surface12.log")
        tries += 1
        if status == "ok":
            break
        if status == "timeout":
            st["status"] = "paused (time limit)"
            return "timeout"
        if status == "oom" and tries <= 3 and p["batch"] > 20:
            p["batch"], p["score_batch"] = max(20, p["batch"] // 2), max(4, p["score_batch"] // 2)
            run.say(f"{tag}: out of GPU memory; retrying with batch {p['batch']}, score batch {p['score_batch']}")
            continue
        if status == "nonfinite" and p["dtype"] == "float16" and not a.dtype:
            hwmem = sum(g["mem"] for g in hw["gpus"])
            if n_params * 4 / 1e9 + 4 * len(hw["gpus"]) <= 0.85 * hwmem:
                run.say(f"{tag}: float16 overflow (NaN); restarting in float32")
                for f in glob.glob(os.path.join(run.res, f"surface_scores_{tag}*.npz")):
                    os.replace(f, f + ".float16-partial")
                p["dtype"] = "float32"
                p["device"] = "cuda" if n_params * 4 / 1e9 + 5 <= 0.9 * min(g["mem"] for g in hw["gpus"]) else "auto"
                continue
            st["status"] = "skipped: float16 overflow (NaN) and float32 does not fit on these GPUs"
            run.say(f"{tag}: {st['status']}. Use a bfloat16-capable GPU (A100, H100, L4, A10) "
                    f"or try --models qwen3b")
            return
        st["status"] = f"failed in the test ({status}); see logs/{tag}_surface12.log"
        run.say(f"{tag}: {st['status']}")
        return
    if not meta:
        meta = dict(repo=repo, dtype=p["dtype"], device=p["device"], gpus=hw["gpus"], torch=hw["torch"],
                    transformers=hw["transformers"], per_setting=per_setting,
                    date=time.strftime("%Y-%m-%d"))
        json.dump(meta, open(meta_path, "w"), indent=1)
    st["plan"] = p
    sps = seconds_per_setting(os.path.join(run.logs, f"{tag}_surface12.log"))
    if sps:
        left12 = 144 - n_settings(s12)
        left23 = 0 if "surface23" not in a.stages else 529 - max(n_settings(s23), 144)
        live = len(a.live_seeds) * 60 if "live" in a.stages else 0   # a live run costs about 60 settings
        if a.dry_run:
            left23, live = 2, 5
        est = sps * (left12 + left23 + live) / 3600
        st["seconds_per_setting"] = sps
        run.say(f"{tag}: {sps} s per setting; about {est:.1f} h left for this model")

    # 2. the full 12 x 12 surface
    if n_settings(s12) < 144:
        status = run.run(surface_cmd(repo, tag, 12, p, per_setting), f"{tag}_surface12.log")
        if status != "ok":
            st["status"] = "paused (time limit)" if status == "timeout" else f"surface12 {status}"
            if status == "nonfinite":
                st["status"] += (" (float16 overflow at some setting; the settings measured so far are kept. "
                                 "Continue on a bfloat16 GPU, or delete this model's files and rerun with "
                                 "--dtype float32 on larger GPUs)")
            run.say(f"{tag}: {st['status']}")
            return status
    if n_settings(s12) < 144:
        st["status"] = f"surface12 incomplete: {s12} has {n_settings(s12)} of 144 settings"
        run.say(f"{tag}: {st['status']}")
        return "error"
    st["stages"]["surface12"] = "done"

    # 3. the 23 x 23 surface (contains the 12 x 12 one)
    if "surface23" in a.stages and n_settings(s23) < 529:
        cmd = surface_cmd(repo, tag, 23, p, per_setting, max_settings=2 if a.dry_run else 0)
        status = run.run(cmd, f"{tag}_surface23.log")
        if status != "ok":
            st["status"] = "paused (time limit)" if status == "timeout" else f"surface23 {status}"
            run.say(f"{tag}: {st['status']}")
            return status
    if "surface23" in a.stages:
        st["stages"]["surface23"] = "done" if n_settings(s23) >= 529 else f"{n_settings(s23)}/529"
        if not a.dry_run and n_settings(s23) < 529:
            st["status"] = f"surface23 incomplete: {s23} has {n_settings(s23)} of 529 settings"
            run.say(f"{tag}: {st['status']}")
            return "error"

    # 4. live runs: the certifier queries the model directly
    if "live" in a.stages:
        for seed in a.live_seeds:
            js = os.path.join(run.res, f"lm_live_{tag}_seed{seed}.json")
            if os.path.exists(js):
                continue
            cmd = [sys.executable, "-u", os.path.join(EXP, "lm_live.py"), "--model", repo, "--surface", s12,
                   "--seed", str(seed), "--budget", str(2600 if a.dry_run else 8000), "--device", p["device"],
                   "--gen-batch", str(min(p["batch"], 64)), "--score-batch", str(p["score_batch"]),
                   "--threads", "4"]
            if p["dtype"]:
                cmd += ["--dtype", p["dtype"]]
            status = run.run(cmd, f"{tag}_live.log")
            if status == "ok" and not os.path.exists(js):
                status = "error"
            if status != "ok":
                st["status"] = "paused (time limit)" if status == "timeout" else f"live seed {seed} {status}"
                run.say(f"{tag}: {st['status']}")
                return status
        st["stages"]["live"] = "done"

    # 5. analyses of the 12 x 12 surface (CPU; the four parts run in parallel)
    if "analyze" in a.stages:
        parts = ["check,budget"] if a.dry_run else ANALYSIS_PARTS
        procs = []
        for part in parts:
            name = part.split(",")[0]
            if not a.dry_run and glob.glob(os.path.join(run.res, f"lm_*{name}*_{tag}.csv")) and name != "check":
                continue
            cmd = [sys.executable, "-u", os.path.join(EXP, "exp_lm.py"), "--parts", part, "--surface", s12]
            log = open(os.path.join(run.logs, f"{tag}_analysis_{name}.log"), "a")
            run.say("$ " + " ".join(cmd))
            procs.append((part, subprocess.Popen(cmd, cwd=ROOT, env=run.env(1), stdout=log,
                                                 stderr=subprocess.STDOUT)))
        bad = [part for part, pr in procs if pr.wait() != 0]
        st["stages"]["analyze"] = "done" if not bad else f"failed: {bad} (see logs)"
    st["status"] = "done"
    run.say(f"{tag}: done")


# -- packaging ----------------------------------------------------------------------

def pack(run):
    run.info["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    run.info["hours"] = round((time.time() - run.t0) / 3600, 2)
    with open(os.path.join(run.out, "run_info.json"), "w") as f:
        json.dump(run.info, f, indent=1)
    z = os.path.join(run.out, "gpu_results.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in glob.glob(os.path.join(run.res, "*")) + glob.glob(os.path.join(run.logs, "*")):
            if f.endswith(".float16-partial"):
                continue
            zf.write(f, os.path.relpath(f, run.out))
        zf.write(os.path.join(run.out, "run_info.json"), "run_info.json")
    run.say(f"results packed: {z} ({os.path.getsize(z) / 1e6:.1f} MB). Bring this file back.")


def resume_from(run, src):
    """Copy earlier results (surfaces, live runs, tables, meta) into this run's
    output, so a new session continues where the old one stopped."""
    n = 0
    pats = ["surface_scores_*.npz", "surface_scores_*.meta.json", "lm_live_*_seed*.json", "lm_*.csv"]
    for pat in pats:
        for f in glob.glob(os.path.join(src, "**", pat), recursive=True):
            dst = os.path.join(run.res, os.path.basename(f))
            if os.path.abspath(f) == os.path.abspath(dst):
                continue
            if f.endswith(".npz") and os.path.exists(dst) and n_settings(dst) >= n_settings(f):
                continue
            if not f.endswith(".npz") and os.path.exists(dst):
                continue
            shutil.copy2(f, dst)
            n += 1
    for zf in glob.glob(os.path.join(src, "**", "gpu_results.zip"), recursive=True):
        tmp = os.path.join(run.out, "_resume_tmp")
        with zipfile.ZipFile(zf) as z:
            z.extractall(tmp)
        n += resume_from(run, tmp) or 0
        shutil.rmtree(tmp, ignore_errors=True)
    if n:
        run.say(f"resumed: copied {n} earlier result files from {src}")
    return n


def slurm_time_left():
    jid = os.environ.get("SLURM_JOB_ID")
    if not jid:
        return None
    try:
        s = subprocess.run(["squeue", "-h", "-j", jid, "-o", "%L"], capture_output=True, text=True).stdout.strip()
        d, _, hms = s.rpartition("-")
        parts = [int(x) for x in hms.split(":")]
        while len(parts) < 3:
            parts.insert(0, 0)
        return (int(d or 0) * 86400 + parts[0] * 3600 + parts[1] * 60 + parts[2]) / 3600
    except Exception:                       # noqa: BLE001
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="gpu_out", help="output folder (results, logs, gpu_results.zip)")
    ap.add_argument("--models", default=DEFAULT_MODELS,
                    help=f"comma-separated tags ({', '.join(MODELS)}) or Hugging Face names")
    ap.add_argument("--stages", default="surface12,surface23,live,analyze")
    ap.add_argument("--live-seeds", default="0,1", help="seeds of the live runs per model")
    ap.add_argument("--hf-cache", default=None, help="where to keep downloaded models (sets HF_HOME)")
    ap.add_argument("--offline", action="store_true", help="no internet: use models already in the cache")
    ap.add_argument("--download-only", action="store_true", help="download the models and stop (HPC login node)")
    ap.add_argument("--resume-from", default=None, help="folder or zip with results of an earlier session")
    ap.add_argument("--time-limit", type=float, default=None,
                    help="hours this session may run (e.g. 11.5 on Kaggle); read from Slurm if not given")
    ap.add_argument("--margin", type=float, default=15, help="minutes kept free at the end for packing")
    ap.add_argument("--delete-models-after", action="store_true", help="free disk after each model")
    ap.add_argument("--dry-run", action="store_true", help="quick test of the whole pipeline with a 135M model")
    ap.add_argument("--dtype", default=None, help="force a precision: bfloat16, float16 or float32")
    ap.add_argument("--device", default=None, help="force placement: cuda, auto (split) or cpu")
    ap.add_argument("--batch", type=int, default=None, help="generations per model call (default 160 on GPU)")
    ap.add_argument("--score-batch", type=int, default=None, help="sequences per NLL pass")
    a = ap.parse_args()
    a.stages = a.stages.split(",")
    a.live_seeds = [int(s) for s in a.live_seeds.split(",") if s != ""]
    if a.dry_run:
        a.models = "dryrun"
        a.live_seeds = [0]
    if a.hf_cache:
        os.environ["HF_HOME"] = os.path.abspath(a.hf_cache)
        os.makedirs(os.environ["HF_HOME"], exist_ok=True)
    if a.offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
    if a.time_limit is None:
        a.time_limit = slurm_time_left()

    run = Run(a)
    run.say(f"output: {run.out}")
    if a.resume_from:
        if os.path.isfile(a.resume_from) and a.resume_from.endswith(".zip"):
            tmp = os.path.join(run.out, "_resume_zip")
            with zipfile.ZipFile(a.resume_from) as z:
                z.extractall(tmp)
            resume_from(run, tmp)
            shutil.rmtree(tmp, ignore_errors=True)
        elif os.path.isdir(a.resume_from):
            resume_from(run, a.resume_from)
    models = [m.strip() for m in a.models.split(",") if m.strip()]

    if a.download_only:
        for m in models:
            snap = download(run, MODELS.get(m, m))
            run.say(f"{m}: in the cache ({param_count(snap) / 1e9:.2f}B parameters)")
        run.say("all models downloaded; now run the job with --offline")
        return

    hw = gpu_info()
    run.info.update(gpus=hw["gpus"], torch=hw["torch"], transformers=hw["transformers"], cuda=hw["cuda"])
    if hw["gpus"]:
        run.say("GPUs: " + "; ".join(f"{g['name']} {g['mem']:.0f} GB (cc {g['cc'][0]}.{g['cc'][1]})"
                                     for g in hw["gpus"]))
    else:
        run.say("no GPU found: running on CPU (fine for --dry-run, far too slow for 7B models)")
    if a.time_limit:
        run.say(f"time limit: {a.time_limit:.1f} h (stops {a.margin:.0f} min before to pack the results)")
    try:
        for i, m in enumerate(models):
            r = do_model(run, m, hw)
            if a.delete_models_after:
                delete_model(MODELS.get(m, m))
            if r == "timeout":
                run.say("stopping: time limit. Run again with --resume-from <this output> to continue.")
                break
            if i < len(models) - 1:
                pack(run)                       # pack after every model, so nothing is lost
    finally:
        pack(run)
    run.say("summary: " + "; ".join(f"{k}: {v.get('status')}" for k, v in run.info["models"].items()))


if __name__ == "__main__":
    main()
