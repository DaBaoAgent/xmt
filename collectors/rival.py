"""对标采集 v2：
  A. 关键词搜索（抖音 / 小红书）→ search_hits 表。用于「找对标 + 找选题 + 爆款素材库」。
  B. 对标账号主页（config/rivals.json 中 kind=rival 且填了 url/xhs_id 的号）→ works 表。

关键词列表来自 config/rivals.json 的 keywords（同步进 DB 的 keywords 表）。

用法：
    python -m collectors.rival --search             # 跑全部关键词搜索
    python -m collectors.rival --search --platform douyin
    python -m collectors.rival --rivals             # 采集对标账号主页
    python -m collectors.rival --keyword 电动轮椅 --platform douyin --headed
"""
import os
import re
import json
import time
import random
import argparse
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")
from playwright.sync_api import sync_playwright

import db

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
XHS_BASE = "https://www.xiaohongshu.com"

DY_SEARCH_API = "general/search/single"
XHS_SEARCH_API = "search/notes"


# ============ 抖音关键词搜索 ============
def douyin_search(ctx, keyword, limit=30, scroll_max=6):
    """搜索页拦截 XHR，返回 [{work_id, author_name, author_id, title, digg, ...}]。"""
    page = ctx.new_page()
    hits = {}

    def on_resp(resp):
        if DY_SEARCH_API not in resp.url:
            return
        try:
            j = resp.json() or {}
            for item in j.get("data") or []:
                aw = item.get("aweme_info") or item.get("aweme_list") or []
                if isinstance(aw, list):
                    aw_list = aw
                else:
                    aw_list = [aw]
                for a in aw_list:
                    wid = a.get("aweme_id")
                    if not wid:
                        continue
                    st = a.get("statistics") or {}
                    au = a.get("author") or {}
                    ct = a.get("create_time")
                    hits[wid] = {
                        "work_id": wid,
                        "author_name": au.get("nickname"),
                        "author_id": au.get("sec_uid") or au.get("unique_id"),
                        "title": (a.get("desc") or "").strip(),
                        "work_type": a.get("aweme_type"),
                        "digg": st.get("digg_count"),
                        "comment": st.get("comment_count"),
                        "share": st.get("share_count"),
                        "play": st.get("play_count"),
                        "publish_ts": ct,
                        "publish_time": datetime.fromtimestamp(ct).strftime("%Y-%m-%d %H:%M") if ct else None,
                        "url": f"https://www.douyin.com/video/{wid}",
                    }
        except Exception:
            pass

    page.on("response", on_resp)
    url = "https://www.douyin.com/search/" + re.sub(r"\s+", "%20", keyword) + "?type=video"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(4500)
        page.mouse.move(700, 500)
        for _ in range(scroll_max):
            if len(hits) >= limit:
                break
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(1800)
    except Exception as e:
        print(f"   [warn] 抖音搜索失败 {keyword}: {type(e).__name__}: {e}")
    page.close()
    return sorted(hits.values(), key=lambda x: x.get("digg") or 0, reverse=True)[:limit]


# ============ 小红书关键词搜索 ============
def _xhs_int(v):
    if v is None:
        return None
    s = str(v).replace(",", "").strip()
    if not s:
        return None
    try:
        return int(float(s))
    except Exception:
        pass
    mult = 1
    if s.endswith("万") or s.lower().endswith("w"):
        mult, s = 10000, s[:-1]
    elif s.endswith("亿"):
        mult, s = 100000000, s[:-1]
    try:
        return int(float(s) * mult)
    except Exception:
        return None


def xhs_search(ctx, keyword, limit=30, scroll_max=6):
    page = ctx.new_page()
    hits = {}

    def on_resp(resp):
        if XHS_SEARCH_API not in resp.url:
            return
        try:
            j = resp.json() or {}
            items = (j.get("data") or {}).get("items") or []
            for it in items:
                nc = it.get("note_card") or {}
                nid = it.get("id") or nc.get("note_id")
                if not nid or not nc:
                    continue
                ii = nc.get("interact_info") or {}
                us = nc.get("user") or {}
                t = nc.get("time")
                hits[nid] = {
                    "work_id": nid,
                    "author_name": us.get("nickname") or us.get("nick_name"),
                    "author_id": us.get("user_id"),
                    "title": (nc.get("display_title") or nc.get("title") or "").strip(),
                    "work_type": 1 if nc.get("type") == "normal" else 0,
                    "digg": _xhs_int(ii.get("liked_count")),
                    "comment": _xhs_int(ii.get("comment_count")),
                    "share": _xhs_int(ii.get("shared_count")),
                    "play": None,
                    "publish_ts": int(t // 1000) if t else None,
                    "publish_time": datetime.fromtimestamp(t / 1000).strftime("%Y-%m-%d %H:%M") if t else None,
                    "url": f"{XHS_BASE}/explore/{nid}",
                }
        except Exception:
            pass

    page.on("response", on_resp)
    import urllib.parse
    url = XHS_BASE + "/search_result?keyword=" + urllib.parse.quote(keyword) + "&type=51"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5500)
        page.mouse.move(700, 500)
        for _ in range(scroll_max):
            if len(hits) >= limit:
                break
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(1800)
    except Exception as e:
        print(f"   [warn] 小红书搜索失败 {keyword}: {type(e).__name__}: {e}")
    page.close()
    return sorted(hits.values(), key=lambda x: x.get("digg") or 0, reverse=True)[:limit]


SEARCHERS = {"douyin": douyin_search, "xiaohongshu": xhs_search}


# ============ 落库 ============
def save_hits(con, platform, keyword, rows):
    now = datetime.now()
    snap_date = now.strftime("%Y-%m-%d")
    ts = now.isoformat(timespec="seconds")
    n = 0
    for r in rows:
        con.execute(
            """INSERT INTO search_hits(platform, keyword, work_id, author_name, author_id, title,
                    work_type, digg, comment, share, play, publish_ts, publish_time, url, snap_date, ts)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(platform, keyword, work_id, snap_date) DO UPDATE SET
                 digg=excluded.digg, comment=excluded.comment, share=excluded.share,
                 play=excluded.play, author_name=excluded.author_name, ts=excluded.ts""",
            (platform, keyword, r["work_id"], r.get("author_name"), r.get("author_id"),
             r.get("title"), r.get("work_type"), r.get("digg"), r.get("comment"),
             r.get("share"), r.get("play"), r.get("publish_ts"), r.get("publish_time"),
             r.get("url"), snap_date, ts))
        n += 1
    return n


def _new_ctx(p, with_cookie=False, headed=False, platform=None):
    browser = p.chromium.launch(channel="chrome", headless=not headed)
    ctx = browser.new_context(locale="zh-CN", user_agent=UA,
                              viewport={"width": 1400, "height": 900})
    if with_cookie:
        loaded = False
        if platform == "douyin" or platform is None:
            loaded = _load_douyin_cookie(ctx)
        if not loaded:
            # 小红书 / 兜底：复用 collect_xhs 的 cookie 加载逻辑
            try:
                import collect_xhs
                if collect_xhs.available():
                    ctx.add_cookies(collect_xhs.load_cookies())
                    loaded = True
            except Exception as e:
                print(f"   [warn] 加载小红书 cookie 失败: {type(e).__name__}")
        if not loaded:
            print("   [warn] 未配置 cookie —— 抖音搜索页会跳验证码，小红书搜索可能被拦")
    return browser, ctx


def _load_douyin_cookie(ctx):
    """抖音登录态：config/douyin_cookie.txt（浏览器复制的原始 cookie header 串）。
    实测（2026-10-12）：抖音搜索页在无登录态时直接跳「验证码中间页」，必须带登录 cookie；
    热搜榜页不需要 cookie。"""
    path = os.path.join(HERE, "config", "douyin_cookie.txt")
    if not (os.path.exists(path) and os.path.getsize(path) > 20):
        return False
    raw = open(path, encoding="utf-8").read().strip()
    cookies = []
    for part in raw.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        cookies.append({"name": k.strip(), "value": v.strip(),
                        "domain": ".douyin.com", "path": "/"})
    if not cookies:
        return False
    ctx.add_cookies(cookies)
    print(f"   [info] 已加载抖音 cookie {len(cookies)} 条")
    return True


def run_search(platforms=None, keyword=None, limit=30, headed=False):
    db.init()
    platforms = platforms or ["douyin", "xiaohongshu"]
    con = db.connect()
    summary = {}
    with sync_playwright() as p:
        for plat in platforms:
            fn = SEARCHERS.get(plat)
            if not fn:
                continue
            kws = [keyword] if keyword else [k["keyword"] for k in db.get_keywords(plat)]
            if not kws:
                print(f"[rival] {plat} 无关键词，跳过")
                continue
            browser, ctx = _new_ctx(p, with_cookie=True, headed=headed, platform=plat)
            for kw in kws:
                print(f"[rival] 搜索 {plat} / {kw} ...", flush=True)
                try:
                    rows = fn(ctx, kw, limit=limit)
                    n = save_hits(con, plat, kw, rows)
                    con.commit()
                    top = rows[0] if rows else None
                    print(f"   {n} 条" + (f" | 最高赞 {top.get('digg')} · {str(top.get('title'))[:24]}" if top else ""))
                    summary[f"{plat}/{kw}"] = n
                except Exception as e:
                    print(f"   [error] {type(e).__name__}: {e}")
                    summary[f"{plat}/{kw}"] = f"error: {type(e).__name__}"
                time.sleep(random.uniform(4, 9))
            browser.close()
    con.close()
    return summary


def run_rivals(platforms=None, target=30, headed=False):
    """采集对标账号主页（kind=rival 且有 url / xhs_id）。"""
    db.init()
    con = db.connect()
    ok = 0
    total = 0
    with sync_playwright() as p:
        for plat in (platforms or ["douyin", "xiaohongshu"]):
            accts = db.get_accounts(platform=plat, kind="rival")
            if plat == "douyin":
                accts = [a for a in accts if a.get("url")]
                import collect_douyin as coll
            else:
                accts = [a for a in accts if a.get("xhs_id")]
                import collect_xhs as coll
            if not accts:
                print(f"[rival] {plat} 无可用对标账号（url/xhs_id 为空？）")
                continue
            browser, ctx = _new_ctx(p, with_cookie=True, headed=headed, platform=plat)
            for acct in accts:
                total += 1
                print(f"[rival] 采集对标 {plat} / {acct['name']} ...", flush=True)
                try:
                    profile, items = coll.collect_one(ctx, acct, target=target)
                    if not profile and not items:
                        print("   [fail] 无数据")
                        continue
                    db.upsert_snapshot(con, acct["id"], profile.get("followers"),
                                       profile.get("total_likes"), profile.get("works_count"),
                                       note=profile.get("nickname"))
                    if items:
                        db.upsert_works(con, acct["id"], plat, items)
                    con.execute("UPDATE accounts SET followers=? WHERE id=?",
                                (profile.get("followers"), acct["id"]))
                    con.commit()
                    ok += 1
                    print(f"   粉丝={profile.get('followers')} 作品={len(items)} 条")
                except Exception as e:
                    print(f"   [error] {type(e).__name__}: {e}")
                time.sleep(random.uniform(8, 18))
            browser.close()
    con.close()
    print(f"[rival] 对标主页完成 {ok}/{total}")
    return ok, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--search", action="store_true", help="跑关键词搜索")
    ap.add_argument("--rivals", action="store_true", help="采集对标账号主页")
    ap.add_argument("--platform", action="append", help="douyin / xiaohongshu，可重复")
    ap.add_argument("--keyword", help="只搜单个关键词")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--target", type=int, default=30, help="对标主页作品条数")
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    if not args.search and not args.rivals:
        args.search = args.rivals = True
    if args.search:
        run_search(args.platform, args.keyword, args.limit, args.headed)
    if args.rivals:
        run_rivals(args.platform, args.target, args.headed)


if __name__ == "__main__":
    main()
