# -*- coding: utf-8 -*-
"""多路尝试定位抖音号对应的账号主页（绕搜索页验证码）。"""
import io
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

CANDIDATES = [
    ("PC user/抖音号", "https://www.douyin.com/user/" + ACCOUNT, None),
    ("移动 m/抖音号", "https://m.douyin.com/user/" + ACCOUNT, MOBILE_UA),
    ("分享页 iesdouyin", "https://www.iesdouyin.com/share/user/" + ACCOUNT, MOBILE_UA),
    ("搜索(移动UA)", "https://www.douyin.com/search/" + ACCOUNT + "?type=user", MOBILE_UA),
    ("搜索(PC+带referer)", "https://www.douyin.com/search/" + ACCOUNT + "?type=user&aid=6383", None),
]

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PROFILE, headless=True, channel="chrome",
        viewport={"width": 414, "height": 900},
        user_agent=MOBILE_UA,
        args=["--disable-blink-features=AutomationControlled",
              "--no-sandbox", "--disable-gpu", "--mute-audio"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(40000)

    for label, url, ua in CANDIDATES:
        print("=" * 62)
        print("[%s] %s" % (label, url))
        try:
            if ua:
                page.goto(url, wait_until="domcontentloaded", timeout=35000)
            else:
                page.goto(url, wait_until="domcontentloaded", timeout=35000)
            page.wait_for_timeout(5000)
            for _ in range(3):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(1000)
            html = page.content()
            title = page.title()[:60]
            print("  最终URL:", page.url[:110])
            print("  标题:", title, "| 长度:", len(html))
            if "验证码" in title:
                print("  → 验证码拦截")
                continue
            sec = re.findall(r'"sec[Uu]id"\s*:\s*"([A-Za-z0-9_\-]{20,})"', html)
            nick = re.findall(r'"nickname"\s*:\s*"([^"]{1,40})"', html)
            uid = re.findall(r'"uid"\s*:\s*"(\d{10,})"', html)
            vids = re.findall(r'"aweme_id"\s*:\s*"(\d{15,})"', html)
            print("  sec_uid:", list(dict.fromkeys(sec))[:2])
            print("  uid:", list(dict.fromkeys(uid))[:2])
            print("  nickname:", list(dict.fromkeys(nick))[:3])
            print("  视频数:", len(set(vids)))
            if vids:
                for m in re.finditer(
                        r'"aweme_id"\s*:\s*"(\d{15,})".{0,1500}?"desc"\s*:\s*"([^"]{0,100})"',
                        html):
                    print("   ·", m.group(1), m.group(2)[:60])
                break
        except Exception as e:
            print("  失败:", type(e).__name__, str(e)[:120])
    ctx.close()
