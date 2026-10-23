# -*- coding: utf-8 -*-
"""解析主页 API 响应 → 作品列表（aweme_id/desc/点赞/时长）。"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROFILE = os.path.join(ROOT, "out", "chrome-dy")
DL_DIR = os.path.join(ROOT, "out", "sph_dl")
MOBILE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) "
             "Version/16.6 Mobile/15E148 Safari/604.1")

SEC = sys.argv[1] if len(sys.argv) > 1 else \
    "MS4wLjABAAAAkXeNrjW00-miU-v69O5FmHJI2zcaeZtxNBbrhNEudTo"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 12

from playwright.sync_api import sync_playwright  # noqa: E402

api = []
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PROFILE, headless=True, channel="chrome",
        viewport={"width": 414, "height": 900}, user_agent=MOBILE_UA,
        args=["--disable-blink-features=AutomationControlled",
              "--no-sandbox", "--disable-gpu", "--mute-audio"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(45000)

    def on_resp(resp):
        if "/web/api/v2/aweme/post" in resp.url:
            try:
                api.append(resp.text())
            except Exception:
                pass
    page.on("response", on_resp)
    page.goto("https://www.iesdouyin.com/share/user/" + SEC,
              wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(9000)
    for _ in range(6):
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(1500)
    ctx.close()

if not api:
    print("没抓到 API 响应")
    sys.exit(1)

raw = api[0]
try:
    data = json.loads(raw)
except Exception:
    print("不是 JSON，前 300:", raw[:300])
    sys.exit(1)

lst = data.get("aweme_list") or []
print("作品数(本次抓到):", len(lst), "| status:", data.get("status_code"))
items = []
for a in lst:
    vid = a.get("aweme_id")
    stat = a.get("statistics") or {}
    video = a.get("video") or {}
    dur = (video.get("duration") or 0) / 1000.0
    items.append({
        "aweme_id": vid,
        "desc": a.get("desc") or "",
        "likes": stat.get("digg_count"),
        "comments": stat.get("comment_count"),
        "dur": round(dur, 1),
        "create": a.get("create_time"),
    })
    print("  %s ｜ %4.1fs ｜ 赞%-7s 评%-5s ｜ %s" % (
        vid, dur, stat.get("digg_count"), stat.get("comment_count"),
        (a.get("desc") or "")[:52]))

with io.open(os.path.join(DL_DIR, "account_items.json"), "w",
             encoding="utf-8") as f:
    f.write(json.dumps(items, ensure_ascii=False, indent=1))
print("\n已存 items:", len(items))
