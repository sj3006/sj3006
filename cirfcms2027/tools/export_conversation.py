#!/usr/bin/env python3
"""Turn a Claude Code session transcript into a readable conversation record.

    python3 tools/export_conversation.py TRANSCRIPT.jsonl [--out conversations/]

Writes one Markdown file per day and an index. What is kept:

* every message the author typed, verbatim, including those sent while a reply
  was in progress;
* the automatic summaries written when the conversation outgrew the context
  window, verbatim, since they are the only record of what came before them;
* every reply written to the author, verbatim;
* every action taken (a command run, a file read, written or edited, a web
  search), as one line each, so the record shows what was done without
  reproducing every file's contents, which are in the repository anyway.

What is left out: tool output, text injected by the software rather than typed
by the author (reminders, skill instructions, task notices), and the model's
internal reasoning. Personal contact details are redacted.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REDACT = [
    (re.compile(r"[A-Za-z0-9._%+-]+@gmail\.com"), "[email redacted]"),
    (re.compile(r"\b(sk-ant-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,})"),
     "[token redacted]"),
]
REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)


def clean(text: str) -> str:
    text = REMINDER.sub("", text)
    for pat, rep in REDACT:
        text = pat.sub(rep, text)
    return text.strip()


def action_line(name: str, inp: dict) -> str:
    def short(s, n=160):
        s = " ".join(str(s).split())
        return s if len(s) <= n else s[: n - 3] + "..."
    rel = lambda p: str(p).replace("/home/user/sj3006/", "")
    if name == "Bash":
        return f"ran a command: {short(inp.get('description') or inp.get('command', ''))}"
    if name in ("Read",):
        return f"read `{rel(inp.get('file_path', ''))}`"
    if name == "Write":
        return f"wrote `{rel(inp.get('file_path', ''))}`"
    if name == "Edit":
        return f"edited `{rel(inp.get('file_path', ''))}`"
    if name == "WebSearch":
        return f"web search: {short(inp.get('query', ''))}"
    if name == "WebFetch":
        return f"web fetch: {inp.get('url', '')}"
    if name in ("Grep", "Glob"):
        return f"searched files for `{short(inp.get('pattern', ''), 80)}`"
    if name == "SendUserFile":
        return "sent files: " + ", ".join(f"`{rel(f)}`" for f in inp.get("files", []))
    if name == "Skill":
        return f"loaded the `{inp.get('skill')}` skill"
    if name in ("TaskCreate", "TaskUpdate", "TaskList", "TaskGet"):
        return None
    if name == "ToolSearch":
        return None
    if name == "Monitor":
        return f"watched a background job: {short(inp.get('description', ''))}"
    if name.startswith("mcp__github__"):
        return f"GitHub: {name.split('__')[-1]}"
    if name.startswith("mcp__"):
        return f"{name.split('__')[-1]}"
    return f"{name}"


def load(path: Path):
    events = []
    for line in open(path):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = d.get("timestamp", "")
        t = d.get("type")
        if t == "user":
            c = d["message"].get("content")
            if isinstance(c, str) and not d.get("isMeta"):
                if d.get("isCompactSummary"):
                    events.append((ts, "summary", clean(c)))
                elif (d.get("origin") or {}).get("kind") == "human":
                    events.append((ts, "user", clean(c)))
                elif "<command-name>/model" in c:
                    events.append((ts, "note", "The author changed the model setting."))
        elif t == "attachment":
            a = d.get("attachment", {})
            if a.get("type") == "queued_command":
                p = a.get("prompt", "")
                if isinstance(p, str) and not p.lstrip().startswith("<task-notification>"):
                    events.append((ts, "user", clean(p) + "\n\n*(sent while a reply was in progress)*"))
        elif t == "assistant":
            for b in d["message"].get("content", []):
                if b.get("type") == "text" and b.get("text", "").strip():
                    events.append((ts, "claude", clean(b["text"])))
                elif b.get("type") == "tool_use":
                    line_ = action_line(b.get("name", ""), b.get("input", {}))
                    if line_:
                        events.append((ts, "action", clean(line_)))
    return events


def render(events, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    days = OrderedDict()
    for e in events:
        days.setdefault(e[0][:10], []).append(e)
    index = ["# Conversation record", "",
             "The conversation between the authors and Claude Code in which the",
             "certificate and fidelity papers were built and the conference paper was",
             "finished, from 10 to 19 November 2026. Exported from the session",
             "transcript by `tools/export_conversation.py`. Each day is one file.", "",
             "Kept verbatim: every message typed by the author, the automatic summaries",
             "written when the conversation outgrew the context window (the only record",
             "of the work before 10 November that this transcript holds; that earlier",
             "work is also documented in the repository itself), and every reply. Each",
             "action taken is listed in one line. Tool output, software-injected text",
             "and internal reasoning are omitted; the author's email address is",
             "redacted. Times are UTC.", "",
             "| day | file | author messages |", "|---|---|---|"]
    msgs = ["", "## Every message from the author", ""]
    for day, evs in days.items():
        name = f"{day}.md"
        n_user = sum(1 for e in evs if e[1] == "user")
        index.append(f"| {day} | [{name}]({name}) | {n_user} |")
        L = [f"# Conversation, {day}", ""]
        actions = []

        def flush():
            if actions:
                L.append("<details><summary>" + f"{len(actions)} action"
                         + ("s" if len(actions) != 1 else "") + "</summary>\n")
                L.extend(f"- {a}" for a in actions)
                L.append("\n</details>\n")
                actions.clear()
        for ts, kind, text in evs:
            hhmm = ts[11:16]
            if kind == "action":
                actions.append(text)
                continue
            flush()
            if kind == "user":
                L += [f"## Author, {hhmm}", "", text, ""]
                first = " ".join(text.split())[:140]
                msgs.append(f"- {day} {hhmm}: [{first}{'...' if len(' '.join(text.split())) > 140 else ''}]({name})")
            elif kind == "summary":
                L += [f"## Automatic summary of the conversation so far, {hhmm}", "",
                      "> Written by the software when the conversation outgrew the context "
                      "window. It is the record of the earlier part of the conversation.", "",
                      text, ""]
            elif kind == "claude":
                L += [f"### Claude, {hhmm}", "", text, ""]
            elif kind == "note":
                L += [f"*{hhmm}: {text}*", ""]
        flush()
        (out / name).write_text("\n".join(L) + "\n")
    (out / "README.md").write_text("\n".join(index + msgs) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("transcript")
    ap.add_argument("--out", default=str(ROOT / "conversations"))
    a = ap.parse_args()
    ev = load(Path(a.transcript))
    render(ev, Path(a.out))
    print(f"{len(ev)} events; {sum(e[1] == 'user' for e in ev)} author messages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
