# -*- coding: utf-8 -*-
"""分析抖音账号（按抖音号搜索 → 找主页 → 抓视频列表 → 抓文案）。

用法：
  .venv/Scripts/python.exe tools/probe_douyin_account.py C1585273.6019

输出：
  1) 账号昵称/抖音号/简介/粉丝数
  2) 最近 N 条视频（标题、点赞、时长、videoId）
  3) 指定条数的视频文案（本地 Whisper 转写，走免积分链路）
"""
import io
import json
import os
import re
import subprocess
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROFILE = os.path.join(ROOT, "out", "chrome-dy")
DL_DIR = os.path.join(ROOT, "out", "sph_dl")
CDN = ("aweme.snssdk.com", "douyinvod.com", "v3-dy-", "v26-dy-",
       "video.toutiao.com", "bytecdn")


def grab(page, seconds=12):
    """在页面上挂 hook 收集 CDN 直链。"""
    hits = []

    def on_resp(resp):
        u = resp.url
        if any(c in u for c in CDN) and re.search(r"\.mp4|/video/", u):
            if u not in hits:
                hits.append(u)
    page.on("response", on_resp)
    page.wait_for_timeout(seconds * 1000)
    return hits


def main():
    account = sys.argv[1] if len(sys.argv) > 1 else "C1585273.6019"
    n_video = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    from playwright.sync_api import sync_playwright
    os.makedirs(PROFILE, exist_ok=True)
    os.makedirs(DL_DIR, exist_ok=True)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE, headless=True, channel="chrome",
            viewport={"width": 1440, "height": 1000},
            args=["--disable-blink-features=AutomationControlled",
                  "--no-sandbox", "--disable-gpu", "--mute-audio"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(45000)

        # 1) 搜索抖音号
        search_url = ("https://www.douyin.com/search/"
                      + account + "?type=user")
        print("搜索页:", search_url)
        page.goto(search_url, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        # 滚一屏加载
        for _ in range(3):
            page.mouse.wheel(0, 1200)
            page.wait_for_timeout(1200)

        html = page.content()
        # 用户主页链接
        users = re.findall(r'https://www\.douyin\.com/user/([A-Za-z0-9_\-]+)', html)
        seen = []
        for u in users:
            if u not in seen:
                seen.append(u)
        print("找到用户主页:", seen[:3] if seen else "（无）")
        if not seen:
            # 换个搜索入口
            page.goto("https://www.douyin.com/search/" + account,
                      wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            html = page.content()
            users = re.findall(r'"sec_uid"\s*:\s*"([A-Za-z0-9_\-]+)"', html)
            for u in users:
                if u not in seen:
                    seen.append(u)
            print("二次搜索结果:", seen[:3] if seen else "（无）")
        if not seen:
            print("找不到该账号")
            ctx.close()
            return

        sec = seen[0]
        home = "https://www.douyin.com/user/" + sec
        print("主页:", home)

        # 2) 打开主页
        page.goto(home, wait_until="domcontentloaded")
        page.wait_for_timeout(7000)
        for _ in range(4):
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(1500)
        html = page.content()

        # 账号信息
        for pat, label in [(r'"nickname"\s*:\s*"([^"]+)"', "昵称"),
                           (r'"uniqueId"\s*:\s*"([^"]+)"', "抖音号"),
                           (r'"signature"\s*:\s*"([^"]{0,120})"', "简介"),
                           (r'"followerCount"\s*:\s*"?(\d+)"?', "粉丝数"),
                           (r'"awemeCount"\s*:\s*"?(\d+)"?', "作品数")]:
            m = re.search(pat, html)
            if m:
                print("%s: %s" % (label, m.group(1)))

        # 3) 视频列表
        vids = []
        for m in re.finditer(r'"aweme_id"\s*:\s*"(\d{15,})"', html):
            v = m.group(1)
            if v not in vids:
                vids.append(v)
        print("\n视频数(本页抓到):", len(vids))

        # 标题
        titles = {}
        for m in re.finditer(
                r'"aweme_id"\s*:\s*"(\d{15,})".{0,2000}?"desc"\s*:\s*"([^"]{0,120})"',
                html):
            titles.setdefault(m.group(1), m.group(2))
        for i, v in enumerate(vids[:n_video], 1):
            print("  %2d. %s  %s" % (i, v, titles.get(v, "")[:60]))
        ctx.close()

    out = os.path.join(DL_DIR, "douyin_account_%s.json" % account)
    with io.open(out, "w", encoding="utf-8") as f:
        f.write(json.dumps({"account": account, "sec_uid": sec,
                            "videos": vids[:n_video],
                            "titles": titles}, ensure_ascii=False, indent=1))
    print("\n已存:", out)


if __name__ == "__main__":
    main()
