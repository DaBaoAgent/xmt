# -*- coding: utf-8 -*-
"""诊断：抖音号搜索页到底返回了什么。"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROFILE = os.path.join(ROOT, "out", "chrome-dy")

from playwright.sync_api import sync_playwright  # noqa: E402

ACCOUNT = sys.argv[1] if len(sys.argv) > 1 else "C1585273.6019"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PROFILE, headless=True, channel="chrome",
        viewport={"width": 1440, "height": 1000},
        args=["--disable-blink-features=AutomationControlled",
              "--no-sandbox", "--disable-gpu", "--mute-audio"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(45000)

    for url in [
        "https://www.douyin.com/search/%s?type=user" % ACCOUNT,
        "https://www.douyin.com/search/%s" % ACCOUNT,
    ]:
        print("=" * 60)
        print("打开:", url)
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(8000)
        for _ in range(3):
            page.mouse.wheel(0, 1400)
            page.wait_for_timeout(1500)
        html = page.content()
        print("最终URL:", page.url[:120])
        print("标题:", page.title()[:80])
        print("HTML长度:", len(html))
        print("含 '登录' :", "登录" in html)
        # 找账号号出现的位置
        for m in re.finditer(re.escape(ACCOUNT), html):
            i = m.start()
            print("命中片段:", html[max(0, i - 260):i + 120].replace("\n", " ")[:380])
            break
        # 各种 uid 形态
        for pat in [r'https://www\.douyin\.com/user/([A-Za-z0-9_\-]+)',
                    r'"secUid"\s*:\s*"([A-Za-z0-9_\-]+)"',
                    r'"sec_uid"\s*:\s*"([A-Za-z0-9_\-]+)"',
                    r'"uid"\s*:\s*"(\d{10,})"',
                    r'data-e2e="user-name"[^>]*>([^<]{1,40})<']:
            hits = re.findall(pat, html)
            if hits:
                print("  %-46s -> %s" % (pat[:44], list(dict.fromkeys(hits))[:4]))
        # 页面上可点的用户卡片
        try:
            cards = page.query_selector_all('[data-e2e="search-user-desc"], li a[href*="/user/"]')
            print("  用户卡片数:", len(cards))
            for c in cards[:5]:
                try:
                    print("   卡片:", (c.inner_text() or "").replace("\n", " | ")[:110])
                except Exception:
                    pass
        except Exception as e:
            print("  取卡片失败:", e)
    ctx.close()
