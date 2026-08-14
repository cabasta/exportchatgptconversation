#!/usr/bin/env python3
"""Convert ChatGPT export conversation JSON into Markdown files."""
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def slugify(value: str, max_len: int = 90) -> str:
    value = re.sub(r"\s+", " ", value or "Untitled").strip()
    value = re.sub(r"[^\w\-. ]+", "", value, flags=re.UNICODE)
    value = value.replace(" ", "-").strip("-.") or "untitled"
    return value[:max_len].rstrip("-.")


def load_conversations(path: Path) -> list[dict[str, Any]]:
    files = [path] if path.is_file() else sorted(path.rglob("*.json"))
    result: list[dict[str, Any]] = []
    for file in files:
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, list):
            result.extend(x for x in data if isinstance(x, dict) and ("mapping" in x or "title" in x))
        elif isinstance(data, dict):
            if "mapping" in data or "title" in data:
                result.append(data)
            elif isinstance(data.get("conversations"), list):
                result.extend(x for x in data["conversations"] if isinstance(x, dict))
    unique: dict[str, dict[str, Any]] = {}
    for c in result:
        key = str(c.get("conversation_id") or c.get("id") or hash(json.dumps(c, sort_keys=True, ensure_ascii=False)))
        unique[key] = c
    return list(unique.values())


def dt(value: Any) -> str:
    if not value:
        return ""
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()
    except (ValueError, TypeError, OverflowError):
        return str(value)


def message_text(message: dict[str, Any]) -> str:
    content = message.get("content") or {}
    if isinstance(content, str):
        return content
    parts = content.get("parts") if isinstance(content, dict) else None
    if isinstance(parts, list):
        out = []
        for part in parts:
            if isinstance(part, str):
                out.append(part)
            elif isinstance(part, dict):
                out.append(str(part.get("text") or part.get("content") or ""))
        return "\n\n".join(x for x in out if x)
    if isinstance(content, dict):
        return str(content.get("text") or "")
    return str(content)


def messages(conversation: dict[str, Any]) -> Iterable[tuple[str, str, str]]:
    mapping = conversation.get("mapping") or {}
    nodes = list(mapping.values()) if isinstance(mapping, dict) else []
    nodes.sort(key=lambda n: ((n.get("message") or {}).get("create_time") or 0, str(n.get("id") or "")))
    seen: set[str] = set()
    for node in nodes:
        msg = node.get("message") or {}
        mid = str(msg.get("id") or node.get("id") or "")
        if not msg or mid in seen:
            continue
        seen.add(mid)
        role = str(msg.get("author", {}).get("role") or "unknown")
        if role == "system":
            continue
        text = message_text(msg).strip()
        if text:
            yield role, dt(msg.get("create_time")), text


def convert(input_path: Path, output: Path) -> int:
    conversations = load_conversations(input_path)
    conv_dir = output / "conversations"
    conv_dir.mkdir(parents=True, exist_ok=True)
    index_rows = []
    for c in sorted(conversations, key=lambda x: x.get("create_time") or 0):
        cid = str(c.get("conversation_id") or c.get("id") or "unknown")
        title = str(c.get("title") or "Untitled conversation").strip()
        created = dt(c.get("create_time"))
        date = created[:10] if created else "unknown-date"
        filename = f"{date}-{slugify(title)}--{slugify(cid, 40)}.md"
        lines = [f"# {title}", "", f"- **Conversation ID:** `{cid}`", f"- **Created:** {created or 'unknown'}"]
        if c.get("update_time"):
            lines.append(f"- **Updated:** {dt(c.get('update_time'))}")
        lines += ["", "---", ""]
        for role, timestamp, text in messages(c):
            lines += [f"## {role.title()}", ""]
            if timestamp:
                lines += [f"*{timestamp}*", ""]
            lines += [text, "", "---", ""]
        (conv_dir / filename).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        index_rows.append((date, title, cid, f"conversations/{filename}"))
    index = ["# ChatGPT conversation archive", "", f"Generated from `{input_path}`.", "", "| Date | Title | Conversation ID | File |", "|---|---|---|---|"]
    for date, title, cid, file_ref in index_rows:
        safe_title = title.replace("|", "\\|")
        index.append(f"| {date} | {safe_title} | `{cid}` | [{Path(file_ref).name}]({file_ref}) |")
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"Converted {len(conversations)} conversations to {output}")
    return len(conversations)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path, help="conversations.json or directory of JSON files")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    raise SystemExit(0 if convert(args.input, args.output) >= 0 else 1)
