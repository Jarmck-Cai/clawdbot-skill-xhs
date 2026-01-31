#!/usr/bin/env python3
"""
XHS Video Analyzer - Sends video to Gemini for multimodal analysis.
Part of the XHS Clawdbot Skill.

Environment:
    GEMINI_API_KEY: Required. Google AI API key.

Usage:
    python3 xhs_analyze.py <video_path> [flash|pro]
"""

import os
import sys
import json

def analyze_video(video_path, quality="flash", max_retries=3):
    """Analyze a video file using Gemini, with retry/backoff for transient 429s.

    Args:
        video_path: Path to the .mp4 file
        quality: "flash" (fast/cheap) or "pro" (quality)
        max_retries: Retry count for 429/ResourceExhausted

    Returns:
        dict with 'model' and 'analysis' on success, else None
    """
    # Import here to allow graceful failure
    try:
        import google.generativeai as genai
    except ImportError:
        print("❌ google-generativeai not installed.")
        print("   Run: pip install google-generativeai")
        return None
    
    # Configure API
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set.")
        return None
    
    genai.configure(api_key=api_key)
    
    # Model selection
    model_map = {
        "flash": "gemini-2.0-flash",
        "pro": "gemini-2.5-pro"
    }
    model_name = model_map.get(quality, "gemini-2.0-flash")
    
    print(f"🎬 Analyzing with {model_name}...")
    
    import time

    # Upload video
    print(f"📤 Uploading: {video_path}")
    video_file = genai.upload_file(video_path)

    # Wait for processing
    while video_file.state.name == "PROCESSING":
        print("⏳ Processing...")
        time.sleep(2)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError(f"Video processing failed: {video_file.state.name}")

    print("✅ Video ready")

    # Analysis prompt
    prompt = """Analyze this video and provide:

1. **Summary** (2-3 sentences): What is this video about?

2. **Key Points** (bullet list): Main ideas, quotes, or insights.

3. **Transcript** (if spoken content): Transcribe the main spoken content.

4. **Visual Notes**: Any important visual elements (text on screen, demonstrations, etc.)

Be concise but comprehensive. If content is in Chinese, respond in Chinese."""

    model = genai.GenerativeModel(model_name)

    # Retry/backoff for transient 429s
    # User-facing backoff (fail fast): total wait ~50s max
    backoffs = [5, 15, 30]
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content([video_file, prompt])
            # Cleanup uploaded file
            try:
                genai.delete_file(video_file.name)
            except Exception:
                pass
            return {"model": model_name, "analysis": response.text}
        except Exception as e:
            last_err = e
            msg = repr(e)
            is_429 = ("429" in msg) or ("ResourceExhausted" in msg)
            if is_429 and attempt < max_retries:
                wait_s = backoffs[min(attempt - 1, len(backoffs) - 1)]
                print(f"⚠️ Gemini throttled (429). Backing off {wait_s}s then retrying ({attempt}/{max_retries})...")
                time.sleep(wait_s)
                continue
            break

    # Cleanup uploaded file best-effort
    try:
        genai.delete_file(video_file.name)
    except Exception:
        pass

    print(f"❌ Gemini video analysis failed after retries: {last_err}")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 xhs_analyze.py <video_path> [flash|pro]")
        print("\nEnvironment: GEMINI_API_KEY must be set")
        sys.exit(1)
    
    video_path = sys.argv[1]
    quality = sys.argv[2] if len(sys.argv) > 2 else "flash"
    
    if not os.path.exists(video_path):
        print(f"❌ File not found: {video_path}")
        sys.exit(1)
    
    result = analyze_video(video_path, quality)
    
    if result:
        print("\n" + "="*50)
        print(f"Model: {result['model']}")
        print("="*50)
        print(result["analysis"])
        
        with open("xhs_video_analysis.json", "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\n📄 Saved to xhs_video_analysis.json")
    else:
        sys.exit(1)
