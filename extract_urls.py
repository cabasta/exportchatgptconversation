#!/usr/bin/env python3
"""Extract URLs from ChatGPT export JSON into CSV and Markdown."""
from __future__ import annotations
import argparse, csv, re
from pathlib import Path
from chatgpt_to_markdown import load_conversations, messages

URL_RE = re.compile(r"https?://[^\s<>()\[\]{}\"']+", re.I)

def clean(url: str) -> str:
    return url.rstrip(".,;:!?)]}")

def extract(input_path: Path, output: Path) -> int:
    rows = {}
    for c in load_conversations(input_path):
        cid = str(c.get("conversation_id") or c.get("id") or "unknown")
        title = str(c.get("title") or "Untitled conversation")
        for role, timestamp, text in messages(c):
            for url in URL_RE.findall(text):
                url = clean(url)
                key = (url, cid)
                rows[key] = {"url": url, "conversation_id": cid, "title": title, "role": role, "timestamp": timestamp}
    output.mkdir(parents=True, exist_ok=True)
    fields = ["url", "conversation_id", "title", "role", "timestamp"]
    with (output / "urls.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(sorted(rows.values(), key=lambda r: (r["url"].lower(), r["title"].lower())))
    md = ["# URLs found in ChatGPT export", "", f"Unique URL/conversation occurrences: **{len(rows)}**", "", "| URL | Conversation | Role | Timestamp |", "|---|---|---|---|"]
    for r in sorted(rows.values(), key=lambda x: x["url"].lower()):
        url = r["url"].replace("|", "%7C")
        title = r["title"].replace("|", "\\|")
        md.append(f"| [{url}]({url}) | {title} (`{r['conversation_id']}`) | {r['role']} | {r['timestamp']} |")
    (output / "urls.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Extracted {len(rows)} URL occurrences to {output}")
    return len(rows)

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--input", required=True, type=Path); p.add_argument("--output", required=True, type=Path)
    args = p.parse_args(); raise SystemExit(0 if extract(args.input, args.output) >= 0 else 1)
