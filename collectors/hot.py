"""平台热点采集：抖音热搜榜（Playwright 拦截前端 XHR）+ 微博/百度热搜（公开 JSON）。

用途：给「找选题」提供当日外部热点证据，落 hot_items 表。
用法：
    python -m collectors.hot            # 全部平台
    python -m collectors.hot --platform douyin
"""
import os
import json
import time
import argparse
import warnings

warnings.filterwarnings("ignore")

import requests

import db

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
TIMEOUT = 15


# ---------- 微博热搜（公开 JSON 接口，无需登录） ----------
def weibo_hot():
    url = "https://weibo.com/ajax/side/hotSearch"
    r = requests.get(url, headers={"User-Agent": UA, "Referer": "https://weibo.com/"}, timeout=TIMEOUT)
    r.raise_for_status()
    data = (r.json() or {}).get("data") or {}
    rows = []
    for i, it in enumerate(data.get("realtime") or [], 1):
        title = it.get("word") or it.get("note")
        if not title:
            continue
        rows.append({
            "rank": i,
            "title": title,
            "score": it.get("num") or it.get("raw_hot"),
            "url": "https://s.weibo.com/weibo?q=" + requests.utils.quote(title),
        })
    return rows


# ---------- 百度热搜（公开接口） ----------
def baidu_hot():
    url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    r.raise_for_status()
    cards = ((r.json() or {}).get("data") or {}).get("cards") or []
    rows = []
    if not cards:
        return rows
    # 结构：cards[0].content[0].content = [{word, url, hotScore, index, ...}, ...]
    items = cards[0].get("content") or []
    if items and isinstance(items[0], dict) and "content" in items[0]:
        items = items[0].get("content") or []
    for i, it in enumerate(items, 1):
        title = (it.get("word") or it.get("query") or "").strip()
        if not title:
            continue
        rows.append({
            "rank": it.get("index") or i,
            "title": title,
            "score": it.get("hotScore"),
            "url": it.get("url") or it.get("rawUrl"),
        })
    return rows


# ---------- 抖音热搜榜（Playwright 拦截前端 XHR；前台免登录） ----------
DOUYIN_HOT_API = "hot/search/list"


def douyin_hot(headed=False, wait_ms=11000):
    """抖音热搜榜：拦截 /aweme/v1/web/hot/search/list/ 的响应。
    实测（2026-10-12）：该 XHR 在页面加载 9-11 秒后才返回，等待需 ≥11s；
    word_list 项不含 position 字段（rank 用顺序），hot_value 常为 0（用 view_count/discuss_video_count 兜底）。"""
    from playwright.sync_api import sync_playwright
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=not headed)
        ctx = browser.new_context(locale="zh-CN", user_agent=UA,
                                  viewport={"width": 1400, "height": 900})
        page = ctx.new_page()

        def on_resp(resp):
            if DOUYIN_HOT_API in resp.url:
                try:
                    j = resp.json() or {}
                    for i, it in enumerate((j.get("data") or {}).get("word_list") or [], 1):
                        title = (it.get("word") or "").strip()
                        if not title:
                            continue
                        rows.append({
                            "rank": it.get("position") or i,
                            "title": title,
                            "score": it.get("hot_value") or it.get("view_count")
                                     or it.get("discuss_video_count"),
                            "url": "https://www.douyin.com/search/" + requests.utils.quote(title),
                        })
                except Exception:
                    pass

        page.on("response", on_resp)
        try:
            page.goto("https://www.douyin.com/hot", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(wait_ms)
        except Exception as e:
            print(f"   [warn] 抖音热搜页打开失败: {type(e).__name__}: {e}")
        browser.close()

    # 去重（同一词可能在两次 XHR 里重复出现）
    seen, out = set(), []
    for r in rows:
        if r["title"] in seen:
            continue
        seen.add(r["title"])
        out.append(r)
    return out


SOURCES = {
    "douyin": [("hot_search", douyin_hot)],
    "weibo": [("hot_search", weibo_hot)],
    "baidu": [("hot_search", baidu_hot)],
}


def run(platforms=None, headed=False):
    db.init()
    platforms = platforms or list(SOURCES.keys())
    con = db.connect()
    summary = {}
    for plat in platforms:
        for kind, fn in SOURCES.get(plat, []):
            try:
                rows = fn(headed=headed) if fn is douyin_hot else fn()
                n = db.upsert_hot(con, plat, kind, rows)
                con.commit()
                summary[f"{plat}/{kind}"] = f"{n} 条"
                print(f"[hot] {plat}/{kind}: {n} 条")
            except Exception as e:
                summary[f"{plat}/{kind}"] = f"error: {type(e).__name__}: {e}"
                print(f"[hot] {plat}/{kind} 失败: {type(e).__name__}: {e}")
    con.close()
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", action="append", help="douyin / weibo / baidu，可重复")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    run(args.platform, args.headed)


if __name__ == "__main__":
    main()
