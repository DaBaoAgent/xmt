# -*- coding: utf-8 -*-
"""抓抖音分享页渲染后的数据（hook API 响应 + DOM 文本）。"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROFILE = os.path.join(ROOT, "out", "chrome-dy")
ACCOUNT = sys.argv[1] if len(sys.argv) > 1 else "C1585273.6019"

MOBILE_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
             "AppleWebKit/605.1.15 (KHTML, like Gecko) "
             "Version/16.6 Mobile/15E148 Safari/604.1")

from playwright.sync_api import sync_playwright  # noqa: E402

apihits = []


def main():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE, headless=True, channel="chrome",
            viewport={"width": 414, "height": 900},
            user_agent=MOBILE_UA,
            args=["--disable-blink-features=AutomationControlled",
                  "--no-sandbox", "--disable-gpu", "--mute-audio"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(40000)

        def on_resp(resp):
            u = resp.url
            if any(k in u for k in ("/web/api/", "/aweme/post", "/aweme/detail",
                                    "user/profile", "sec_uid", "aweme/v1")):
                try:
                    body = resp.text()
                except Exception:
                    return
                apihits.append((u, body[:400000]))

        page.on("response", on_resp)
        url = "https://m.douyin.com/share/user/" + ACCOUNT
        print("打开:", url)
        page.goto(url, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(9000)
        for _ in range(4):
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(1500)

        print("\n--- API 响应 ---")
        for u, b in apihits[:10]:
            print("URL:", u[:150])
            print("  长度:", len(b))
            for k in ['"nickname"', '"unique_id"', '"short_id"', '"sec_uid"',
                      '"follower_count"', '"aweme_count"', '"signature"',
                      '"aweme_id"', '"desc"']:
                mm = re.search(re.escape(k) + r'\s*:\s*("(?:[^"\\]|\\.)*"|\d+)', b)
                if mm:
                    print("   %-16s %s" % (k, mm.group(1)[:80]))
            print()

        print("--- DOM 文本（前 800 字）---")
        txt = page.inner_text("body")[:800]
        print(txt)
        ctx.close()


if __name__ == "__main__":
    main()
