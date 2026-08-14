#!/usr/bin/env python3
"""Render ChatGPT conversation JSON as standalone HTML and PDF."""
from __future__ import annotations
import argparse, html
from pathlib import Path
from chatgpt_to_markdown import load_conversations, messages, slugify

CSS = """body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:1000px;margin:40px auto;padding:0 24px;color:#222;line-height:1.55}h1{margin-bottom:.2em}.meta{color:#666;margin-bottom:2em}.message{border-top:1px solid #ddd;padding:1.2em 0}.role{font-weight:700;font-size:1.05em}pre{overflow:auto;background:#f5f5f5;padding:12px;border-radius:6px}code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}a{overflow-wrap:anywhere}@media print{body{margin:0;max-width:none}.message{break-inside:avoid}}"""

def render_text(text: str) -> str:
    # Preserve code-like content safely; the export itself is not interpreted as HTML.
    return html.escape(text).replace("\n", "<br>\n")

def render(c: dict, output: Path, formats: set[str]) -> None:
    cid = str(c.get("conversation_id") or c.get("id") or "unknown")
    title = str(c.get("title") or "Untitled conversation")
    body = ["<!doctype html><html><head><meta charset='utf-8'>", f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>", f"<h1>{html.escape(title)}</h1>", f"<div class='meta'>Conversation ID: <code>{html.escape(cid)}</code></div>"]
    for role, timestamp, text in messages(c):
        body.append("<section class='message'>")
        body.append(f"<div class='role'>{html.escape(role.title())}</div>")
        if timestamp: body.append(f"<div class='meta'>{html.escape(timestamp)}</div>")
        body.append(f"<div>{render_text(text)}</div></section>")
    body.append("</body></html>")
    document = "\n".join(body)
    output.mkdir(parents=True, exist_ok=True)
    base = output / f"{slugify(title)}--{slugify(cid,40)}"
    if "html" in formats or "both" in formats:
        (base.with_suffix(".html")).write_text(document, encoding="utf-8")
    if "pdf" in formats or "both" in formats:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_LEFT
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        except ImportError as e:
            raise SystemExit("PDF output requires: python -m pip install reportlab") from e
        styles = getSampleStyleSheet(); normal = ParagraphStyle("ChatNormal", parent=styles["BodyText"], leading=15, alignment=TA_LEFT)
        doc = SimpleDocTemplate(str(base.with_suffix(".pdf")), pagesize=A4, rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=40)
        story = [Paragraph(html.escape(title), styles["Title"]), Spacer(1, 12)]
        for role, timestamp, text in messages(c):
            story += [Paragraph(html.escape(role.title()), styles["Heading3"])]
            if timestamp: story.append(Paragraph(html.escape(timestamp), styles["Italic"]))
            for para in text.split("\n\n"):
                # Paragraph supports basic XML; escape everything from the export.
                story.append(Paragraph(html.escape(para).replace("\n", "<br/>"), normal)); story.append(Spacer(1, 8))
        doc.build(story)

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--input", required=True, type=Path); p.add_argument("--output", required=True, type=Path); p.add_argument("--format", choices=["html","pdf","both"], default="both")
    args=p.parse_args(); conversations=load_conversations(args.input)
    for c in conversations: render(c,args.output,{args.format})
    print(f"Rendered {len(conversations)} conversations to {args.output}"); return 0
if __name__ == "__main__": raise SystemExit(main())
