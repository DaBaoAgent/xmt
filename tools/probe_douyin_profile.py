# -*- coding: utf-8 -*-
"""抓抖音账号主页（分享页 sec_uid）→ 账号信息 + 作品列表 + 视频直链。"""
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
CDN = ("aweme.snssdk.com", "douyinvod.com", "v3-dy-", "v26-dy-",
       "video.toutiao.com", "bytecdn")


def main():
    sec = sys.argv[1]
    n_video = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    from playwright.sync_api import sync_playwright
    os.makedirs(PROFILE, exist_ok=True)
    os.makedirs(DL_DIR, exist_ok=True)
    api = []
    cdn = []

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE, headless=True, channel="chrome",
            viewport={"width": 414, "height": 900},
            user_agent=MOBILE_UA,
            args=["--disable-blink-features=AutomationControlled",
                  "--no-sandbox", "--disable-gpu", "--mute-audio"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(45000)

        def on_resp(resp):
            u = resp.url
            if any(c in u for c in CDN) and re.search(r"\.mp4|/video/", u):
                if u not in cdn:
                    cdn.append(u)
            if "/web/api/" in u and ("aweme/post" in u or "user/info" in u
                                    or "aweme/v1" in u):
                try:
                    api.append((u, resp.text()))
                except Exception:
                    pass
        page.on("response", on_resp)

        url = "https://www.iesdouyin.com/share/user/" + sec
        print("打开主页:", url)
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(9000)
        for _ in range(6):
            page.mouse.wheel(0, 1200)
            page.wait_for_timeout(1500)

        html = page.content()
        print("标题:", page.title()[:60], "| 长度:", len(html))

        # 账号信息
        info = {}
        for key, pat in [
            ("nickname", r'"nickname"\s*:\s*"([^"]{1,60})"'),
            ("unique_id", r'"unique_id"\s*:\s*"([^"]{1,60})"'),
            ("short_id", r'"short_id"\s*:\s*"([^"]{1,60})"'),
            ("signature", r'"signature"\s*:\s*"([^"]{0,200})"'),
            ("follower", r'"follower_count"\s*:\s*(\d+)'),
            ("following", r'"following_count"\s*:\s*(\d+)'),
            ("aweme_count", r'"aweme_count"\s*:\s*(\d+)'),
            ("total_favorited", r'"total_favorited"\s*:\s*(\d+)'),
        ]:
            m = re.search(pat, html)
            if m:
                info[key] = m.group(1)
        print("\n=== 账号信息 ===")
        for k, v in info.items():
            print("  %-16s %s" % (k, v))

        # 作品列表
        items = []
        for m in re.finditer(
                r'"aweme_id"\s*:\s*"(\d{15,})".{0,3000}?"desc"\s*:\s*"([^"]{0,200})"',
                html):
            aid, desc = m.group(1), m.group(2)
            if aid not in [i[0] for i in items]:
                items.append((aid, desc))
        # 点赞数
        likes = {}
        for m in re.finditer(
                r'"aweme_id"\s*:\s*"(\d{15,})".{0,3000}?"digg_count"\s*:\s*(\d+)',
                html):
            likes.setdefault(m.group(1), m.group(2))
        print("\n=== 作品（抓到 %d 条）===" % len(items))
        for i, (aid, desc) in enumerate(items[:n_video], 1):
            print("  %2d. %s  赞%s  %s" % (i, aid, likes.get(aid, "?"),
                                          desc[:56]))
        out = {"sec_uid": sec, "info": info,
               "items": [{"aweme_id": a, "desc": d, "likes": likes.get(a)}
                         for a, d in items[:n_video]]}
        with io.open(os.path.join(DL_DIR, "account_%s.json" % sec[:12]),
                     "w", encoding="utf-8") as f:
            f.write(json.dumps(out, ensure_ascii=False, indent=1))
        print("\nAPI 响应数:", len(api))
        for u, b in api[:3]:
            print("  ", u[:110], "len", len(b))
        ctx.close()


if __name__ == "__main__":
    main()
