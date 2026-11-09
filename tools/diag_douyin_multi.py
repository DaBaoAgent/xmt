# -*- coding: utf-8 -*-
"""综合探测：抖音号 → sec_uid/昵称/作品列表。多路并行尝试。"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ACCOUNT = sys.argv[1] if len(sys.argv) > 1 else "C1585273.6019"
FRESH = os.path.join(ROOT, "out", "chrome-dy-fresh")

PC_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

import requests  # noqa: E402

s = requests.Session()
s.trust_env = False
s.headers.update({"User-Agent": PC_UA, "Referer": "https://www.douyin.com/"})

print("=== 路线1：直接调 user/info 接口（抖音号当 sec_uid）===")
for url in [
    "https://www.iesdouyin.com/web/api/v2/user/info/?sec_uid=%s" % ACCOUNT,
    "https://www.iesdouyin.com/web/api/v2/aweme/post/?sec_uid=%s&count=20" % ACCOUNT,
    "https://www.douyin.com/aweme/v1/web/user/profile/other/?device_platform=webapp"
    "&aid=6383&unique_id=%s" % ACCOUNT,
]:
    try:
        r = s.get(url, timeout=25)
        body = r.text[:600]
        print("-", url[:90], "→", r.status_code, body[:200].replace("\n", " "))
    except Exception as e:
        print("-", url[:90], "→ 失败", str(e)[:80])

print()
print("=== 路线2：新 profile 打开搜索页（绕验证码）===")
from playwright.sync_api import sync_playwright  # noqa: E402

os.makedirs(FRESH, exist_ok=True)
apihits = []
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        FRESH, headless=True, channel="chrome",
        viewport={"width": 1440, "height": 1000},
        args=["--disable-blink-features=AutomationControlled",
              "--no-sandbox", "--disable-gpu", "--mute-audio"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.set_default_timeout(45000)

    def on_resp(resp):
        u = resp.url
        if "/web/api/" in u or "search/item" in u or "search/user" in u:
            try:
                apihits.append((u, resp.text()[:200000]))
            except Exception:
                pass
    page.on("response", on_resp)

    for u in ["https://www.douyin.com/search/%s?type=user&aid=6383" % ACCOUNT,
              "https://www.douyin.com/search/%s" % ACCOUNT]:
        print("打开:", u)
        page.goto(u, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(11000)
        t = page.title()
        print("  标题:", t[:50])
        if "验证码" in t:
            print("  → 仍被验证码拦")
            continue
        html = page.content()
        print("  长度:", len(html))
        sec = list(dict.fromkeys(re.findall(r'"sec[Uu]id"\s*:\s*"([A-Za-z0-9_\-]{20,})"', html)))
        nick = list(dict.fromkeys(re.findall(r'"nickname"\s*:\s*"([^"]{1,40})"', html)))
        print("  sec_uid:", sec[:3])
        print("  nickname:", nick[:3])
        if sec:
            break
    print("  捕获 API:", len(apihits))
    for u, b in apihits[:6]:
        print("  API:", u[:120])
        for k in ['"nickname"', '"unique_id"', '"short_id"', '"sec_uid"',
                  '"follower_count"', '"aweme_count"', '"signature"']:
            mm = re.search(re.escape(k) + r'\s*:\s*("(?:[^"\\]|\\.)*"|\d+)', b)
            if mm:
                print("     %-16s %s" % (k, mm.group(1)[:70]))
    ctx.close()
