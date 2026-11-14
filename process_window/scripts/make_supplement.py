"""Build the anonymous supplementary-material archive for submission.

Copies the code, tests, requirements and the result files the paper's
tables and figures are built from (CSV, NPZ, JSON; no logs, which contain
local paths), writes an anonymized README and a LICENSE, then refuses to
finish if any identifying string is left in a text file.

Left out: ROADMAP.md, notes/ (study notes), paper drafts, early exploratory
scripts (experiments/exp0*.py) and their results, logs.

Run from process_window/:  python3 scripts/make_supplement.py [--out dist]
Output: <out>/supplement/ and <out>/supplement.zip
"""

import argparse
import glob
import os
import re
import shutil
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

EXPERIMENTS = ["exp_lm.py", "exp_search.py", "final.py", "lm_figure.py", "lm_live.py",
               "lm_sensitivity.py", "lm_surface.py", "paper_figs.py", "physics_sensitivity.py",
               "violation.py"]
RESULT_GLOBS = ["results/final/*.csv", "results/lm/*.csv", "results/lm/*.npz", "results/lm/*.json"]

# Case-insensitive patterns that must not appear anywhere in the archive.
FORBIDDEN = [r"amit", r"\bjain\b", r"sj3006", r"claude", r"anthropic", r"/home/", r"/root/",
             r"[\w.+-]+@[\w-]+\.[\w.]+", r"session_0", r"lime"]

LICENSE = """MIT License

Copyright (c) 2026 Anonymous authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# (old, new) edits that turn the repository README into the archive README.
# Each must apply exactly once, so a README change that breaks one is caught.
README_EDITS = [
    ("Code for the ICML 2027 submission. The paper itself is\n"
     "`paper/latex/main.tex` (compiled: `paper/latex/main.pdf`); the proofs in\n"
     "plain text are `paper/appendix_theory.md`.\n",
     "Code for the submission \"Certifying Safe Operating Regions under Monotone\n"
     "Failure Modes\". Section and theorem numbers in code comments refer to\n"
     "the paper.\n"),
    ("\nIndependent of the LIME/RUL work elsewhere in this repository.\n", ""),
    ("results/          CSVs, logs and figures written by the experiments\n",
     "results/          CSVs and measured surfaces the paper is built from\n"),
    ("notes/            study notes and earlier proof drafts\n", ""),
    ("\n## Status\n\nSee the log at the bottom of `ROADMAP.md`.\n", ""),
]


def copy(rel, out):
    dst = os.path.join(out, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(os.path.join(ROOT, rel), dst)


def build(out):
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    files = []
    files += sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "pwcert", "*.py")))
    files += sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "tests", "*.py")))
    files += [os.path.join("experiments", f) for f in EXPERIMENTS]
    files += ["requirements.txt", "requirements-lm.txt"]
    for g in RESULT_GLOBS:
        files += sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, g)))
    for rel in files:
        copy(rel, out)

    readme = open(os.path.join(ROOT, "README.md")).read()
    for old, new in README_EDITS:
        if readme.count(old) != 1:
            raise SystemExit(f"README edit does not apply exactly once: {old[:60]!r}")
        readme = readme.replace(old, new)
    with open(os.path.join(out, "README.md"), "w") as f:
        f.write(readme)
    with open(os.path.join(out, "LICENSE"), "w") as f:
        f.write(LICENSE)
    return files + ["README.md", "LICENSE"]


def scan(out):
    """Return (file, pattern, line) for every forbidden match in a text file."""
    hits = []
    pats = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN]
    for dirpath, _, names in os.walk(out):
        for name in names:
            path = os.path.join(dirpath, name)
            if name.endswith(".npz"):
                continue                      # numeric arrays only
            try:
                text = open(path, encoding="utf-8").read()
            except UnicodeDecodeError:
                hits.append((path, "binary file", ""))
                continue
            for i, line in enumerate(text.splitlines(), 1):
                for p in pats:
                    if p.search(line):
                        hits.append((os.path.relpath(path, out), p.pattern, f"{i}: {line.strip()[:80]}"))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
    args = ap.parse_args()
    out = os.path.join(args.out, "supplement")
    files = build(out)
    hits = scan(out)
    if hits:
        for h in hits:
            print("FORBIDDEN:", *h)
        raise SystemExit(f"{len(hits)} identifying strings found; archive not written")
    zpath = os.path.join(args.out, "supplement.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in sorted(files):
            z.write(os.path.join(out, rel), os.path.join("supplement", rel))
    print(f"{len(files)} files, {os.path.getsize(zpath) / 1e6:.1f} MB -> {zpath}")


if __name__ == "__main__":
    main()
