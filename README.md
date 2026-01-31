# clawdbot-skill-xhs

English | [简体中文](README.zh-CN.md)

An OpenClaw skill to capture and archive Xiaohongshu (小红书 / RED) posts from a shared link into a clean **notes + media + metadata** structure, with optional Gemini video analysis.

> Note: OpenClaw was previously known as **Clawdbot** (and earlier iterations such as **moltbot**).

## Features

- Extract title / description / tags / comments (when available)
- Download video + images locally
- Save raw metadata JSON for future-proof reference
- Optional Gemini-based video understanding (summary / key points / transcript / visuals)
- Portable: no hardcoded paths; output fully configurable via env vars

## Requirements

- Python 3.9+ (Python 3.10+ recommended)
- Playwright (Chromium)
- A logged-in Xiaohongshu cookie (provided by the user)
- Optional: Gemini API key (video analysis)

## Install

```bash
pip install playwright requests google-generativeai
playwright install chromium
```

## Setup

**Tip**: You can create a file named `.env` inside `skills/xhs/` with these variables, then run `source skills/xhs/.env` before usage.

**Working directory**: Commands below assume you run them from a directory where `skills/xhs/` exists (i.e., `ls skills/xhs` works).

### 1) Provide XHS cookie (required)

```bash
export XHS_COOKIE="your_cookie_string_here"
```

### 2) Output directories (optional)

Default output is `./xhs_captures/`.

```bash
export XHS_OUTPUT_DIR="./xhs_captures"
```

Advanced (separate folders):

```bash
export XHS_NOTES_DIR="./xhs_captures/notes"
export XHS_MEDIA_DIR="./xhs_captures/media"
```

### 3) Enable video analysis (optional)

```bash
export GEMINI_API_KEY="your_gemini_api_key"
```

## Usage

### Extract

```bash
python3 skills/xhs/scripts/xhs_bridge.py "https://www.xiaohongshu.com/discovery/item/..."
```

This writes `xhs_last_run.json` to the current working directory.

### Archive

```bash
python3 skills/xhs/scripts/xhs_archive.py xhs_last_run.json
```

### Archive + analyze video (Gemini)

```bash
python3 skills/xhs/scripts/xhs_archive.py xhs_last_run.json --analyze
# or higher quality
python3 skills/xhs/scripts/xhs_archive.py xhs_last_run.json --analyze pro
```

## Security / Privacy

- Never commit cookies, API keys, or captured media.
- See `SECURITY.md`.

## Disclaimer / Compliance

This project is provided **for educational and research purposes only**. It uses non-official techniques (e.g., browser automation and user-provided cookies) and **is not affiliated with Xiaohongshu/RED**.

By using this project, you agree to:
- Use it **at your own risk**.
- Respect Xiaohongshu/RED’s Terms of Service and applicable laws.
- Avoid abusive behavior (high-frequency crawling, scraping at scale, or causing pressure to the service).
- Never share or commit sensitive data such as cookies or API keys.

The authors/contributors provide **no warranty** and are not responsible for account restrictions, bans, or any damage caused by misuse.

## License

MIT (see `LICENSE`).
