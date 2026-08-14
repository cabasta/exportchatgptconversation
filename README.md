# exportchatgptconversation

Utilities for turning an OpenAI/ChatGPT data export into a durable, searchable local archive.

## What this repository does

The official ChatGPT export is delivered as a ZIP containing chat history and other account data. Depending on export size, conversations may be in `conversations.json` or in numbered conversation JSON files. See the [OpenAI export documentation](https://help.openai.com/de-de/articles/7260999-wie-exportiere-ich-meinen-chatgpt-verlauf-und-meine-daten).

This project provides:

- `chatgpt_to_markdown.py` — convert ChatGPT conversation JSON into one Markdown file per conversation plus an index.
- `extract_urls.py` — extract URLs from conversations into CSV and Markdown tables.
- `render_conversations.py` — render conversation JSON to HTML and optionally PDF.

The scripts are deliberately local/offline-first: the exported conversation data is not uploaded anywhere.

## Quick start

```bash
python chatgpt_to_markdown.py --input /path/to/conversations.json --output ./archive
python extract_urls.py --input /path/to/conversations.json --output ./archive/urls
python render_conversations.py --input /path/to/conversations.json --output ./archive/rendered --format both
```

For PDF output install ReportLab:

```bash
python -m pip install reportlab
```

## Expected output

```text
archive/
  index.md
  conversations/
    2026-08-14-llm-agent-architecture--<id>.md
    ...
  urls/
    urls.csv
    urls.md
  rendered/
    <conversation-id>.html
    <conversation-id>.pdf
```

The scripts accept both the common single `conversations.json` export and a directory containing JSON files. They try to preserve the original message order and content while tolerating different export variants.

## Privacy

Treat the export as sensitive personal data. Do not commit your real ChatGPT export to this public repository. The `.gitignore` excludes common export/archive paths.
