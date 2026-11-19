#!/usr/bin/env python3
"""Assemble `replication/` from the working directories.

    python3 tools/build_replication.py            # rebuild replication/ and the zip
    python3 tools/build_replication.py --no-zip   # rebuild the folder only

The package is regenerated in full on every run, so it never drifts from the
working directories: code and papers are copied from where they are developed,
the published measurements are exported from the constants in the code, the
generated data is copied from the run outputs, and the hand-written parts
(README, scripts, environment, licence notice, citation) are copied from
`tools/replication_static/`. A manifest with the SHA-256 of every file is
written last, and a zip of the folder is written next to it for sharing.

Everything under `replication/` is overwritten; edit the sources, not the copy.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # cirfcms2027/
OUT = ROOT / "replication"
STATIC = ROOT / "tools" / "replication_static"
ZIP = ROOT / "cirfcms2027-replication.zip"
VERSION = "1.0"


def copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_glob(src_dir: Path, pattern: str, dst_dir: Path) -> int:
    n = 0
    for p in sorted(src_dir.glob(pattern)):
        if p.is_file() and "__pycache__" not in p.parts:
            copy(p, dst_dir / p.name)
            n += 1
    return n


def copy_tree(src: Path, dst: Path, suffixes: set[str] | None = None) -> int:
    n = 0
    for p in sorted(src.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and (
                suffixes is None or p.suffix in suffixes):
            copy(p, dst / p.relative_to(src))
            n += 1
    return n


# ---------------------------------------------------------------------------
def build_code() -> None:
    C = OUT / "code"
    copy_glob(ROOT / "src", "*.py", C / "src")
    copy_glob(ROOT / "repro", "*.py", C / "repro")
    copy(ROOT / "repro" / "README.md", C / "repro" / "README.md")
    copy(ROOT / "repro" / ".gitignore", C / "repro" / ".gitignore")
    copy(ROOT / "run_all.py", C / "run_all.py")
    copy(ROOT / "README.md", C / "README-conference.md")
    # documents read by src/literature_census.py and src/provenance_check.py
    copy(ROOT / "07-literature-extraction.md", C / "07-literature-extraction.md")
    copy(ROOT / "docs" / "measured-inputs.md", C / "docs" / "measured-inputs.md")
    # certificate: code, and the paper source its claim check reads
    copy_glob(ROOT / "certificate", "*.py", C / "certificate")
    for f in ("paper.tex", "refs.bib", "build.sh"):
        copy(ROOT / "certificate" / "paper" / f, C / "certificate" / "paper" / f)
    # fidelity: code, README, and the paper source its claim check reads
    copy_glob(ROOT / "fidelity", "*.py", C / "fidelity")
    copy(ROOT / "fidelity" / "README.md", C / "fidelity" / "README.md")
    for f in ("paper.tex", "refs.bib"):
        copy(ROOT / "fidelity" / "paper" / f, C / "fidelity" / "paper" / f)


def build_papers() -> None:
    P = OUT / "papers"
    conf = P / "conference"
    for f in ("paper.tex", "paper.pdf", "README.md", "build.sh"):
        copy(ROOT / "paper" / f, conf / f)
    copy_glob(ROOT / "paper", "*.png", conf)
    for f in ("paper.tex", "compact-spacing.tex", "README.md"):
        copy(ROOT / "overleaf" / f, conf / "two-column-overleaf" / f)
    cert = P / "certificate"
    for f in ("paper.tex", "refs.bib", "paper.pdf", "build.sh"):
        copy(ROOT / "certificate" / "paper" / f, cert / f)
    copy_tree(ROOT / "certificate" / "figures", cert / "figures", {".png", ".pdf"})
    fid = P / "fidelity"
    for f in ("paper.tex", "refs.bib", "paper.pdf"):
        copy(ROOT / "fidelity" / "paper" / f, fid / f)
    copy_tree(ROOT / "fidelity" / "paper" / "figures", fid / "figures", {".png", ".pdf"})


def build_input_data() -> None:
    D = OUT / "data" / "input"
    D.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / "src"))
    import calibrate                                            # noqa: E402
    import weaver_pads as wp                                    # noqa: E402

    # expanded uncertainties: parsed from the comment that holds them, so the
    # code remains the single source
    text = (ROOT / "src" / "calibrate.py").read_text()
    unc = {m.group(1): (float(m.group(2)), float(m.group(3)))
           for m in re.finditer(r"#\s+case ([\d.]+)\s+width ([\d.]+)\s+depth ([\d.]+)", text)}
    with open(D / "weaver2024_table4_single_tracks.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["case", "label", "power_W", "speed_m_per_s", "spot_d4sigma_um",
                    "width_um", "depth_um", "U_width_um_k2", "U_depth_um_k2"])
        for p in calibrate.WEAVER_POINTS:
            case = p.label.split()[1]
            uw, ud = unc[case]
            w.writerow([case, p.label, p.power, p.speed, round(p.spot_diameter * 1e6, 3),
                        round(p.width * 1e6, 3), round(p.depth * 1e6, 3), uw, ud])
    with open(D / "weaver2024_table5_pads.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["y_pad_cross_section_mm", "depth_antiparallel_um", "depth_parallel_um"])
        for s, a, b in zip(wp.Y_PAD_SECTION_MM, wp.Y_PAD_ANTIPARALLEL, wp.Y_PAD_PARALLEL):
            w.writerow([s, a, b])
        f.write(f"# X-pad control depth changes: {', '.join(str(x) for x in wp.X_PAD_CONTROL_CHANGES)}\n")
        f.write(f"# standard deviations across Table 5: {wp.Y_PAD_SD_RANGE_UM[0]} to "
                f"{wp.Y_PAD_SD_RANGE_UM[1]} um; argon cross-flow {wp.CROSS_FLOW_M_S} m/s\n")
    copy(ROOT / "docs" / "measured-inputs.md", D / "measured-inputs.md")
    copy(STATIC / "data" / "input-README.md", D / "README.md")


def build_generated_data() -> None:
    G = OUT / "data" / "generated"
    copy(STATIC / "data" / "generated-README.md", G / "README.md")
    copy(ROOT / "repro" / "REPORT.md", G / "conference" / "REPORT.md")
    copy(ROOT / "certificate" / "results.json", G / "certificate" / "results.json")
    F = ROOT / "fidelity"
    for f in ("_region", "_study", "_results", "_grid", "_floor", "_sloppy"):
        copy(F / f"{f}.json", G / "fidelity" / f"{f}.json")
    copy(F / "_jacobians.json", G / "fidelity" / "caches" / "_jacobians.json")
    for f in ("_study_grid121", "_jacobians_grid121", "_study_grid481",
              "_results_grid481", "_jacobians_grid481"):
        copy(F / f"{f}.json", G / "fidelity" / "superseded" / f"{f}.json")


def build_docs() -> None:
    D = OUT / "docs"
    copy(ROOT / "RECORD.md", D / "RECORD.md")
    copy(ROOT / "INDEX.md", D / "INDEX-source-repository.md")
    copy(ROOT / "README.md", D / "findings" / "conference-README.md")
    copy(ROOT / "certificate" / "FINDINGS.md", D / "findings" / "certificate-FINDINGS.md")
    copy(ROOT / "fidelity" / "FINDINGS.md", D / "findings" / "fidelity-FINDINGS.md")
    copy(ROOT / "repro" / "README.md", D / "findings" / "conference-reproduction-harness.md")
    copy(ROOT / "fidelity" / "LABNOTEBOOK.md", D / "fidelity-labnotebook.md")
    copy(ROOT / "certificate" / "ROADMAP.md", D / "roadmaps" / "certificate-ROADMAP.md")
    copy(ROOT / "fidelity" / "ROADMAP.md", D / "roadmaps" / "fidelity-ROADMAP.md")
    copy(ROOT / "fidelity" / "literature.md", D / "literature" / "fidelity-literature.md")
    for f in ("06-literature-landscape.md", "07-literature-extraction.md"):
        copy(ROOT / f, D / "literature" / f)
    for f in ("sources-consulted.md", "web-lookups-2026-11.json",
              "measured-inputs.md", "commit-history.md"):
        copy(ROOT / "docs" / f, D / f)
    copy(ROOT / "10-errata-and-draft-2-changes.md", D / "errata-conference.md")
    copy_tree(ROOT / "explainers", D / "explainers", {".md"})
    for p in sorted(ROOT.glob("0[0-9]-*.md")):
        copy(p, D / "project-notes" / p.name)
    copy(ROOT / "CLAUDE.md", D / "project-notes" / "working-agreements.md")


def build_static() -> None:
    for f in ("LICENSE-NOTICE.md", "CITATION.md"):
        copy(STATIC / f, OUT / f)
    copy_tree(STATIC / "environment", OUT / "environment")
    copy_tree(STATIC / "scripts", OUT / "scripts")
    for p in (OUT / "scripts").iterdir():
        p.chmod(0o755)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip() or "unknown"
    readme = (STATIC / "README.md").read_text()
    readme = (readme.replace("%%VERSION%%", VERSION)
              .replace("%%BUILT%%", dt.date.today().isoformat())
              .replace("%%COMMIT%%", commit))
    (OUT / "README.md").write_text(readme)


ROLE = {"code": "code", "data": "data", "papers": "paper", "docs": "documentation",
        "scripts": "script", "environment": "environment"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest() -> int:
    rows = []
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.tsv":
            rel = p.relative_to(OUT).as_posix()
            rows.append((rel, p.stat().st_size, sha256(p),
                         ROLE.get(rel.split("/")[0], "package")))
    with open(OUT / "MANIFEST.tsv", "w") as f:
        f.write("path\tbytes\tsha256\trole\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    return len(rows)


def write_zip() -> None:
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                info = zipfile.ZipInfo(f"replication/{p.relative_to(OUT).as_posix()}",
                                       date_time=(2026, 1, 1, 0, 0, 0))
                info.external_attr = (p.stat().st_mode & 0o777) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, p.read_bytes())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-zip", action="store_true")
    a = ap.parse_args()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    build_code()
    build_papers()
    build_input_data()
    build_generated_data()
    build_docs()
    build_static()
    n = write_manifest()
    print(f"replication/ built: {n} files")
    if not a.no_zip:
        write_zip()
        print(f"wrote {ZIP.name} ({ZIP.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
