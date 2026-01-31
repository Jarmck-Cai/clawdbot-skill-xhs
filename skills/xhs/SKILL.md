---
name: xhs
description: Capture and archive Xiaohongshu (小红书/RED) posts including videos, images, and text. Use when user shares a xiaohongshu.com link and wants to save, archive, analyze, or summarize the content. Supports video analysis via Gemini (optional). Triggers on phrases like "save this XHS link", "archive this xiaohongshu post", "analyze this video from xiaohongshu", or when a xiaohongshu.com URL is shared.
---

# Xiaohongshu (XHS) Capture Skill

Extracts and archives content from Xiaohongshu posts with a "Triple-Level Archive" strategy.

## Quick Start

```bash
# Working directory:
# Run these commands from a directory where `skills/xhs/` exists (i.e., `ls skills/xhs` works).

# 0. Load Config (Important!)
# Create a .env file with XHS_COOKIE='...' and XHS_OUTPUT_DIR='...'
# then load it:
source skills/xhs/.env

# 1. Extract data from URL
python3 skills/xhs/scripts/xhs_bridge.py "https://www.xiaohongshu.com/explore/..."

# 2. Archive (download media + create note)
python3 skills/xhs/scripts/xhs_archive.py xhs_last_run.json

# 3. With video analysis (requires GEMINI_API_KEY)
python3 skills/xhs/scripts/xhs_archive.py xhs_last_run.json --analyze
```

## Environment Variables

| Variable | Required | Description |
| :--- | :--- | :--- |
| `XHS_COOKIE` | Yes | Cookie string from logged-in browser session |
| `XHS_OUTPUT_DIR` | No | Base output directory (default: `./xhs_captures`) |
| `XHS_NOTES_DIR` | No | Override notes directory (advanced) |
| `XHS_MEDIA_DIR` | No | Override media directory (advanced) |
| `GEMINI_API_KEY` | No | Enables video analysis via Gemini |

## Workflow

1. **Trigger**: User shares `xiaohongshu.com` link
2. **Extract**: Run `xhs_bridge.py` → outputs `xhs_last_run.json`
3. **Archive**: Run `xhs_archive.py` → downloads media, creates note
4. **Analyze** (optional): If user asks to "analyze the video" and `GEMINI_API_KEY` is set, append Gemini analysis

## Output Structure

```
# Default layout (public-friendly)
{XHS_OUTPUT_DIR}/
├── notes/
│   └── YYYY-MM-DD_Title.md      # Insight note
└── media/
    └── YYYY-MM/
        ├── ..._video.mp4        # Raw video
        ├── ..._img1.jpg         # Images
        └── ..._raw.json         # Full metadata

# Advanced: override with XHS_NOTES_DIR + XHS_MEDIA_DIR
```

## Analysis Modes

| Mode | Trigger Phrase | Requirement |
| :--- | :--- | :--- |
| **Basic** | "save this", "archive this" | XHS_COOKIE only |
| **Full** | "analyze this video", "what does this say" | XHS_COOKIE + GEMINI_API_KEY |

If `GEMINI_API_KEY` is not set, provide text-based analysis from the description/comments.

## Cookie Setup

1. Log in to xiaohongshu.com in browser
2. Open DevTools (F12) → Network tab
3. Refresh page, click any request
4. Copy the `Cookie` header value
5. Set: `export XHS_COOKIE="..."`
