#!/usr/bin/env python3
"""
XHS Archiver - Downloads assets and creates insight notes.
Part of the XHS Clawdbot Skill.

Environment:
    XHS_OUTPUT_DIR: Base output directory (default: ./xhs_captures)
    XHS_NOTES_DIR: Optional. Notes directory override (default: {XHS_OUTPUT_DIR}/notes)
    XHS_MEDIA_DIR: Optional. Media directory override (default: {XHS_OUTPUT_DIR}/media)
    GEMINI_API_KEY: Optional. Enables video analysis.

Usage:
    python3 xhs_archive.py <json_file>              # Basic archive
    python3 xhs_archive.py <json_file> --analyze    # With Gemini video analysis
    python3 xhs_archive.py <json_file> --analyze pro  # Gemini Pro quality
"""

import json
import sys
import os
import requests
import datetime
import re
import subprocess

def get_output_dir():
    """Get base output directory from environment or use default."""
    return os.environ.get("XHS_OUTPUT_DIR", "./xhs_captures")

def get_notes_dir():
    """Get notes directory (supports override)."""
    return os.environ.get("XHS_NOTES_DIR") or os.path.join(get_output_dir(), "notes")

def get_media_root_dir():
    """Get media root directory (supports override)."""
    return os.environ.get("XHS_MEDIA_DIR") or os.path.join(get_output_dir(), "media")

def sanitize_filename(name):
    """Make string safe for filenames."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = clean.replace(" ", "_")
    return clean[:50]

def download_file(url, folder, filename):
    """Download file to folder."""
    if not url:
        return None
    
    local_path = os.path.join(folder, filename)
    if os.path.exists(local_path):
        return local_path
        
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/"
        }
        r = requests.get(url, headers=headers, stream=True)
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return local_path
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

def run_video_analysis(video_path, quality="flash"):
    """Run Gemini video analysis if API key is available."""
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️ GEMINI_API_KEY not set. Skipping video analysis.")
        return None
    
    # Find the analyze script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    analyze_script = os.path.join(script_dir, "xhs_analyze.py")
    
    if not os.path.exists(analyze_script):
        print(f"⚠️ Analyze script not found: {analyze_script}")
        return None
    
    try:
        print(f"🎬 Running video analysis ({quality})...")
        result = subprocess.run(
            ["python3", analyze_script, video_path, quality],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            output_file = "xhs_video_analysis.json"
            if os.path.exists(output_file):
                with open(output_file, "r") as f:
                    return json.load(f)
        else:
            print(f"⚠️ Video analysis failed: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        print("⚠️ Video analysis timed out")
        return None
    except Exception as e:
        print(f"⚠️ Video analysis error: {e}")
        return None

def process_archive(json_path, analyze=False, quality="flash"):
    """Read JSON, download assets, create Markdown note."""
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    note = data.get("note", {})
    if not note:
        print("❌ No note data found in JSON.")
        return None

    # Metadata (handle both direct and note_card wrapped structures)
    note_card = note.get("note_card", {})
    title = note.get("title") or note_card.get("title") or "Untitled"
    desc = note.get("desc") or note_card.get("desc") or ""
    note_id = note.get("noteId") or note_card.get("note_id") or note.get("id", "")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    month_str = datetime.datetime.now().strftime("%Y-%m")
    
    clean_title = sanitize_filename(title)
    if not clean_title:
        clean_title = note_id

    # Setup directories
    notes_dir = get_notes_dir()
    media_root = get_media_root_dir()
    media_dir = os.path.join(media_root, month_str)
    os.makedirs(notes_dir, exist_ok=True)
    os.makedirs(media_dir, exist_ok=True)
    
    media_links = []
    video_path = None
    
    # Save raw JSON
    raw_filename = f"{date_str}_{clean_title}_raw.json"
    raw_path = os.path.join(media_dir, raw_filename)
    with open(raw_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    rel_raw = os.path.relpath(raw_path, notes_dir)
    media_links.append(f"**Raw Data**: [{raw_filename}]({rel_raw})")
    
    # Download video
    if note.get("type") == "video":
        video_info = note.get("video", {}).get("media", {}).get("stream", {}).get("h264", [])
        if video_info:
            vid_url = video_info[0].get("masterUrl")
            fname = f"{date_str}_{clean_title}.mp4"
            video_path = download_file(vid_url, media_dir, fname)
            if video_path:
                rel_path = os.path.relpath(video_path, notes_dir)
                media_links.append(f"**Video**: [{fname}]({rel_path})")

    # Download images
    img_list = note.get("imageList", [])
    for idx, img in enumerate(img_list):
        url = img.get("urlDefault") or img.get("url")
        if url:
            fname = f"{date_str}_{clean_title}_img{idx+1}.jpg"
            local_img = download_file(url, media_dir, fname)
            if local_img:
                rel_path = os.path.relpath(local_img, notes_dir)
                media_links.append(f"![Image {idx+1}]({rel_path})")

    # Video analysis (optional)
    video_analysis = None
    if analyze and video_path:
        video_analysis = run_video_analysis(video_path, quality)

    # Get user and stats from either structure
    user_info = note.get("user") or note_card.get("user") or {}
    interact_info = note.get("interactInfo") or note_card.get("interact_info") or {}
    note_type = note.get("type") or note_card.get("type") or "Unknown"

    # Generate Markdown
    md_filename = f"{date_str}_XHS_{clean_title}.md"
    md_path = os.path.join(notes_dir, md_filename)
    
    content = f"""# {title}

**Source**: [Xiaohongshu](https://www.xiaohongshu.com/explore/{note_id})
**Captured**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
**Type**: {note_type}

## Media Archive
"""
    for link in media_links:
        content += f"{link}\n\n"

    if video_analysis:
        content += f"""
## 🎬 Video Analysis (Gemini {quality.upper()})

{video_analysis.get("analysis", "No analysis available.")}

"""
    
    content += f"""
## Description
{desc}

## Metadata
- **Author**: {user_info.get("nickname")}
- **Likes**: {interact_info.get("likedCount") or interact_info.get("liked_count")}
- **Comments**: {interact_info.get("commentCount") or interact_info.get("comment_count")}

## Top Comments
"""
    comments = data.get("comments", [])
    if comments:
        for c in comments[:10]:
            user = c.get("user_info", {}).get("nickname", "Anon")
            text = c.get("content", "")
            likes = c.get("like_count", 0)
            content += f"- **{user}** (❤️ {likes}): {text}\n"
    else:
        content += "*No comments captured.*\n"

    with open(md_path, 'w') as f:
        f.write(content)
        
    print(f"✅ Note: {md_path}")
    print(f"📦 Media: {media_dir}")
    if video_analysis:
        print(f"🎬 Analysis: Gemini {quality}")
    
    return md_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 xhs_archive.py <json_file> [--analyze [flash|pro]]")
        print("\nEnvironment:")
        print("  XHS_OUTPUT_DIR   Base output directory (default: ./xhs_captures)")
        print("  XHS_NOTES_DIR    Override notes directory (optional)")
        print("  XHS_MEDIA_DIR    Override media directory (optional)")
        print("  GEMINI_API_KEY   Optional. Enables video analysis.")
        sys.exit(1)
    
    json_path = sys.argv[1]
    analyze = "--analyze" in sys.argv
    quality = "flash"
    
    if analyze and len(sys.argv) > 3:
        idx = sys.argv.index("--analyze")
        if idx + 1 < len(sys.argv) and sys.argv[idx + 1] in ["flash", "pro"]:
            quality = sys.argv[idx + 1]
    
    process_archive(json_path, analyze=analyze, quality=quality)
