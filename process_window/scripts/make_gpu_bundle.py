"""Build gpu/gpu_bundle.zip: everything a GPU machine needs to run the
language-model measurements (see gpu/RUN_ME.md).

Run from process_window/:  python3 scripts/make_gpu_bundle.py
Re-run it after changing pwcert/, the LM experiment scripts or gpu/.
"""

import glob
import os
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "gpu", "gpu_bundle.zip")
TOP = "gpu_bundle"

FILES = {   # source (relative to process_window/) -> path inside the bundle
    "gpu/run_gpu.py": "run_gpu.py",
    "gpu/RUN_ME.md": "RUN_ME.md",
    "gpu/requirements-gpu.txt": "requirements-gpu.txt",
    "gpu/rented_gpu.sh": "rented_gpu.sh",
    "gpu/slurm_job.sh": "slurm_job.sh",
    "gpu/kaggle_notebook.ipynb": "kaggle_notebook.ipynb",
    "experiments/lm_surface.py": "experiments/lm_surface.py",
    "experiments/lm_live.py": "experiments/lm_live.py",
    "experiments/exp_lm.py": "experiments/exp_lm.py",
    "experiments/exp_search.py": "experiments/exp_search.py",
}


def main():
    files = dict(FILES)
    for f in glob.glob(os.path.join(ROOT, "pwcert", "*.py")) + glob.glob(os.path.join(ROOT, "pwcert", "data", "*")):
        rel = os.path.relpath(f, ROOT)
        files[rel] = rel
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for src, dst in sorted(files.items()):
            info = zipfile.ZipInfo(f"{TOP}/{dst}", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o755 if dst.endswith((".sh", ".py")) else 0o644) << 16
            with open(os.path.join(ROOT, src), "rb") as fh:
                z.writestr(info, fh.read())
    print(f"{len(files)} files, {os.path.getsize(OUT) / 1e3:.0f} kB -> {OUT}")


if __name__ == "__main__":
    main()
