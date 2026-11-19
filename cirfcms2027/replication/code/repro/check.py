"""Check every number the paper quotes against a fresh recomputation.

    python3 repro/check.py              # everything, using the cache
    python3 repro/check.py --no-cache   # recompute from scratch (~4 minutes)
    python3 repro/check.py --group noise --group meltpool
    python3 repro/check.py --report REPORT.md

Exits non-zero if any claim fails, so it can sit in CI. A claim fails when the
recomputed value does not round to the number the paper prints; see the
tolerance note in `claims.py`.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from claims import CLAIMS, Claim          # noqa: E402
from compute import GROUPS                # noqa: E402

CACHE = HERE / "cache"


def _load(group: str, use_cache: bool) -> dict:
    path = CACHE / f"{group}.json"
    if use_cache and path.exists():
        return {"values": json.loads(path.read_text())["values"],
                "cached": True, "seconds": 0.0}
    t = time.time()
    values = {k: (float(v) if v is not None else None)
              for k, v in GROUPS[group]().items()}
    took = time.time() - t
    CACHE.mkdir(exist_ok=True)
    path.write_text(json.dumps({"values": values, "seconds": took}, indent=1))
    return {"values": values, "cached": False, "seconds": took}


def _verdict(c: Claim, got: float | None) -> tuple[str, str]:
    """PASS / FAIL / MISSING, with the comparison spelled out."""
    if got is None:
        return "MISSING", f"no value at key {c.key}"
    tol = c.tolerance
    if c.relation in ("==", "range_lo", "range_hi"):
        ok = abs(got - c.value) <= tol
        detail = f"|{got:.6g} - {c.value:.6g}| = {abs(got - c.value):.3g} vs tol {tol:.3g}"
    elif c.relation == ">=":
        ok = got >= c.value - tol
        detail = f"{got:.6g} >= {c.value:.6g} - {tol:.3g}"
    elif c.relation == "<=":
        ok = got <= c.value + tol
        detail = f"{got:.6g} <= {c.value:.6g} + {tol:.3g}"
    else:
        raise ValueError(f"unknown relation {c.relation!r}")
    return ("PASS" if ok else "FAIL"), detail


def run(groups=None, use_cache=True, verbose=False):
    wanted = {c.key.split(".")[0] for c in CLAIMS}
    if groups:
        wanted &= set(groups)
    unknown = wanted - set(GROUPS)
    if unknown:
        raise SystemExit(f"claims reference unknown compute groups: {sorted(unknown)}")

    values: dict[str, float] = {}
    timings: dict[str, tuple[float, bool]] = {}
    for g in sorted(wanted):
        r = _load(g, use_cache)
        timings[g] = (r["seconds"], r["cached"])
        for k, v in r["values"].items():
            values[f"{g}.{k}"] = v
        if verbose:
            tag = "cached" if r["cached"] else f"{r['seconds']:.1f} s"
            print(f"  computed {g:18s} {len(r['values']):4d} values  ({tag})",
                  file=sys.stderr)

    results = []
    for c in CLAIMS:
        if c.key.split(".")[0] not in wanted:
            continue
        got = values.get(c.key)
        status, detail = _verdict(c, got)
        results.append({"claim": c, "got": got, "status": status,
                        "detail": detail})
    return results, timings


def print_table(results) -> None:
    by_section: dict[str, list] = {}
    for r in results:
        by_section.setdefault(r["claim"].section, []).append(r)

    def key(s):
        return (0, [int(x) for x in s.split(".")]) if s[0].isdigit() else (1, s)

    for section in sorted(by_section, key=key):
        rows = by_section[section]
        print(f"\n--- Section {section} "
              f"{'-' * max(0, 62 - len(section))}")
        for r in rows:
            c = r["claim"]
            got = "-" if r["got"] is None else f"{r['got']:.6g}"
            mark = {"PASS": "  ", "FAIL": "!!", "MISSING": "??"}[r["status"]]
            print(f" {mark} {c.id:30s} paper {c.quoted:22s} code {got:>12s}"
                  f"   {c.kind}")
            if r["status"] != "PASS":
                print(f"      {r['detail']}")


def write_report(results, timings, path: Path) -> None:
    n = len(results)
    bad = [r for r in results if r["status"] != "PASS"]
    lines = [
        "# Reproduction report",
        "",
        f"`{n}` claims checked, `{n - len(bad)}` reproduced, `{len(bad)}` not.",
        "",
        "Every row is a number the paper prints. **paper** is what it prints,",
        "**code** is what this repository computes, and a row passes only if the",
        "computed value rounds to the printed one (see `claims.py` for the",
        "tolerance rule and the exceptions for stated bounds).",
        "",
        "`kind` is `computed` for a number this repository derives from the",
        "forward model, `source` for a measurement or reported fit taken from a",
        "cited work - not recomputable here, so what is checked is that the",
        "paper and the code carry the same figure - and `convention` for a",
        "threshold or unit this work chose.",
        "",
    ]
    if bad:
        lines += ["## Claims that did not reproduce", ""]
        for r in bad:
            c = r["claim"]
            lines.append(f"- **{c.id}** (Section {c.section}): paper says "
                         f"`{c.quoted}`, code gives "
                         f"`{'-' if r['got'] is None else format(r['got'], '.6g')}`"
                         f" - {r['detail']}")
        lines.append("")

    by_section: dict[str, list] = {}
    for r in results:
        by_section.setdefault(r["claim"].section, []).append(r)

    def key(s):
        return (0, [int(x) for x in s.split(".")]) if s[0].isdigit() else (1, s)

    for section in sorted(by_section, key=key):
        lines += [f"## Section {section}", "",
                  "| | id | paper | code | kind | what it means |",
                  "|---|---|---|---|---|---|"]
        for r in by_section[section]:
            c = r["claim"]
            got = "-" if r["got"] is None else f"{r['got']:.6g}"
            tick = {"PASS": "ok", "FAIL": "**FAIL**", "MISSING": "**?**"}[r["status"]]
            means = c.means.replace("|", "/")
            if c.provenance:
                means += f" *(source: {c.provenance})*"
            if c.note:
                means += f" *(note: {c.note})*"
            lines.append(f"| {tick} | `{c.id}` | {c.quoted} | {got} | {c.kind} "
                         f"| {means} |")
        lines.append("")

    lines += ["## Compute groups", "",
              "| group | seconds | cached |", "|---|---|---|"]
    for g, (secs, cached) in sorted(timings.items()):
        lines.append(f"| `{g}` | {secs:.1f} | {'yes' if cached else 'no'} |")
    lines.append("")
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", action="append", default=None)
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--report", type=Path, default=HERE / "REPORT.md")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    results, timings = run(groups=a.group, use_cache=not a.no_cache,
                           verbose=not a.quiet)
    if not a.quiet:
        print_table(results)
    cached = [g for g, (_, c) in timings.items() if c]
    if cached:
        print(f"\nNOTE: {len(cached)} of {len(timings)} groups came from "
              f"repro/cache/ rather than being recomputed\n"
              f"      ({', '.join(sorted(cached))}).\n"
              f"      Run with --no-cache before trusting a pass.")

    bad = [r for r in results if r["status"] != "PASS"]
    print(f"\n{len(results)} claims checked, {len(results) - len(bad)} "
          f"reproduced, {len(bad)} not.")
    for r in bad:
        c = r["claim"]
        print(f"  {r['status']}  {c.id:30s} (Section {c.section})  "
              f"paper {c.quoted} vs code "
              f"{'-' if r['got'] is None else format(r['got'], '.6g')}")
    if a.report:
        write_report(results, timings, a.report)
        print(f"\nreport written to {a.report}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
