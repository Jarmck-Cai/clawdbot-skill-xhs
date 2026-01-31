#!/usr/bin/env python3
"""
XHS Bridge - Extracts data from Xiaohongshu posts via browser automation.
Part of the XHS Clawdbot Skill.

Environment:
    XHS_COOKIE: Required. Cookie string from logged-in browser session.
    
Output:
    Writes extracted data to xhs_last_run.json
"""

import json
import sys
import os
import time

def get_cookie():
    """Get cookie from environment or config file."""
    # Priority 1: Environment variable
    cookie = os.environ.get("XHS_COOKIE")
    if cookie:
        return cookie
    
    # Priority 2: Config file (for backwards compatibility)
    config_paths = [
        "secrets/xhs_config.json",
        os.path.expanduser("~/.config/xhs/config.json")
    ]
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f).get("cookie")
            except:
                pass
    
    return None

def load_cookies():
    """Parse cookie string into list of dicts for Playwright."""
    cookie_str = get_cookie()
    if not cookie_str:
        print("❌ No cookie found. Set XHS_COOKIE environment variable.")
        print("   See SKILL.md for setup instructions.")
        return []
    
    cookies = []
    for item in cookie_str.split("; "):
        if "=" in item:
            name, value = item.split("=", 1)
            cookies.append({
                "name": name,
                "value": value,
                "domain": ".xiaohongshu.com",
                "path": "/"
            })
    return cookies

def extract_note_data(note_url):
    """Extract note data using browser automation."""
    # Import here to allow graceful failure if not installed
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
        return None
    
    data_captured = {"note": None, "comments": []}
    
    # Extract ID from URL
    note_id = None
    if "explore/" in note_url:
        note_id = note_url.split("explore/")[1].split("?")[0]
    elif "/discovery/item/" in note_url:
        note_id = note_url.split("/discovery/item/")[1].split("?")[0]
    else:
        note_id = note_url

    def handle_response(response):
        if "/api/sns/web/v1/feed" in response.url or "/api/sns/web/v1/note" in response.url:
            try:
                json_data = response.json()
                if "data" in json_data and "items" in json_data["data"]:
                    item = json_data["data"]["items"][0]
                    if item.get("note_id") == note_id or item.get("id") == note_id:
                        data_captured["note"] = item
                    elif not data_captured["note"]:
                        data_captured["note"] = item
            except:
                pass
        
        if "/api/sns/web/v2/comment/page" in response.url:
            print("💬 Intercepted Comments!")
            try:
                json_data = response.json()
                if "data" in json_data and "comments" in json_data["data"]:
                    new_comments = json_data["data"]["comments"]
                    data_captured["comments"].extend(new_comments)
                    print(f"   + {len(new_comments)} comments captured.")
            except:
                pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        
        cookies = load_cookies()
        if cookies:
            context.add_cookies(cookies)
        else:
            print("⚠️ No cookies loaded. Content may be limited.")

        page = context.new_page()
        page.on("response", handle_response)
        
        print(f"Navigating to: {note_url}")
        page.goto(note_url, wait_until="domcontentloaded", timeout=45000)
        
        if "无法浏览" in page.title() or "页面不见了" in page.title():
            print("⚠️ Hit Access Wall. Checking for embedded data...")

        print(f"Page Title: {page.title()}")
        
        # Extract from SSR state
        note_state = page.evaluate("""() => {
            try {
                const state = window.__INITIAL_STATE__;
                if (state && state.note && state.note.noteDetailMap) {
                    return Object.values(state.note.noteDetailMap);
                }
                return null;
            } catch (e) {
                return null;
            }
        }""")
        
        if note_state:
            for raw_item in note_state:
                if not raw_item:
                    continue
                # Some pages wrap as {note: {...}, comments: {...}}
                item = raw_item.get("note") if isinstance(raw_item, dict) and raw_item.get("note") else raw_item

                if item and (item.get("noteId") == note_id or item.get("id") == note_id):
                    data_captured["note"] = item
                    print("✨ Found exact match in SSR state")
                    break
                elif item and (item.get("title") or item.get("desc")):
                    if not data_captured["note"]:
                        data_captured["note"] = item

        # Scroll for comments
        if data_captured["note"]:
            print("Scrolling to load comments...")
            page.mouse.wheel(0, 2000)
            time.sleep(2)
            page.mouse.wheel(0, 2000)
            time.sleep(2)
        
        browser.close()
        
    return data_captured

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 xhs_bridge.py <note_url>")
        print("\nEnvironment: XHS_COOKIE must be set")
        sys.exit(1)
        
    url = sys.argv[1]
    print(f"🕵️ Bridging to XHS: {url}")
    
    result = extract_note_data(url)
    
    if result and result.get("note"):
        note_data = result["note"]
        title = note_data.get('note_card', {}).get('title') or note_data.get('title')
        note_type = note_data.get('note_card', {}).get('type') or note_data.get('type')
        
        print(f"\n✅ Success!")
        print(f"Title: {title}")
        print(f"Type: {note_type}")
        print(f"Comments: {len(result.get('comments', []))}")
        
        with open("xhs_last_run.json", "w") as f:
            json.dump({"note": note_data, "comments": result.get("comments", [])}, f, indent=2, ensure_ascii=False)
        print("📄 Saved to xhs_last_run.json")
    else:
        print("❌ Failed to capture note data.")
        sys.exit(1)
