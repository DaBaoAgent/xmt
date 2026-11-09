"""小红书前台采集（免后台登录）：Playwright 驱动本机 Chrome，带普通账号 cookie。
流程：按「小红书号」搜索 -> 命中精确用户(id+token) -> 打开主页 -> 拦截官方 XHR/读页面内嵌数据。
抓取：粉丝数 / 获赞与收藏 / 笔记数 / 最近 N 条笔记(发布时间、标题、类型、单条点赞)。
cookie 文件优先 config/xhs_cookie.txt，其次项目根 小红书cookie.txt（原始 header 串）。
"""
import os
import sys
import json
import time
import random
import argparse
import urllib.parse
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")
from playwright.sync_api import sync_playwright

import db

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "config", "accounts.json")
COOKIE_CANDIDATES = [
    os.path.join(HERE, "config", "xhs_cookie.txt"),
    os.path.join(HERE, "小红书cookie.txt"),
]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
BASE = "https://www.xiaohongshu.com"

# 网格懒加载+虚拟化：必须在滚动过程中累积，否则顶部卡片会被卸载、丢失点赞数
SNAP_COUNTS_JS = """() => {
    const res = {};
    document.querySelectorAll("section.note-item[data-note-id]").forEach(el => {
        const c = el.querySelector('.count');
        const tl = el.querySelector('.footer .title');
        res[el.getAttribute('data-note-id')] = {
            count: c ? c.innerText.trim() : '',
            title: tl ? tl.innerText.trim() : ''};
    });
    return res;
}"""


def cookie_file():
    for p in COOKIE_CANDIDATES:
        if os.path.exists(p) and os.path.getsize(p) > 20:
            return p
    return None


def available():
    return cookie_file() is not None


def load_cookies():
    raw = open(cookie_file(), encoding="utf-8").read().strip()
    out = []
    for part in raw.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        out.append({"name": k.strip(), "value": v.strip(),
                    "domain": ".xiaohongshu.com", "path": "/"})
    return out


def load_xhs_accounts():
    with open(CONFIG, encoding="utf-8") as f:
        data = json.load(f)
    return [a for a in data["accounts"]
            if a.get("platform") == "xiaohongshu" and a.get("xhs_id")]


def _captcha(page):
    try:
        if "/captcha" in page.url:
            return True
        return bool(page.query_selector('[data-captcha-role="modal"]'))
    except Exception:
        return False


def resolve_user(ctx, red_id, timeout=45000, retries=2):
    """按小红书号精确搜索，返回 {id,name,fans,note_count,xsec_token}；遇验证码重试。"""
    for attempt in range(retries + 1):
        page = ctx.new_page()
        found = []

        def on_resp(resp):
            if "search/usersearch" in resp.url:
                try:
                    found.append(resp.json())
                except Exception:
                    pass

        page.on("response", on_resp)
        try:
            page.goto(BASE + "/search_result?keyword=" + urllib.parse.quote(str(red_id)),
                      wait_until="domcontentloaded", timeout=timeout)
            page.wait_for_timeout(3500)
            if _captcha(page):
                page.close()
                wait = random.uniform(20, 35)
                print(f"   [warn] 触发验证码，等待 {wait:.0f}s 后重试 ({attempt+1}/{retries+1})")
                time.sleep(wait)
                continue
            try:
                page.get_by_text("用户", exact=True).first.click(timeout=5000)
            except Exception:
                pass
            page.wait_for_timeout(4500)
            if _captcha(page):
                page.close()
                wait = random.uniform(20, 35)
                print(f"   [warn] 触发验证码，等待 {wait:.0f}s 后重试 ({attempt+1}/{retries+1})")
                time.sleep(wait)
                continue
        finally:
            try:
                page.close()
            except Exception:
                pass

        for j in found:
            for u in (j.get("data") or {}).get("users", []) or []:
                if str(u.get("red_id")) == str(red_id):
                    return {
                        "id": u.get("id"),
                        "name": u.get("name"),
                        "fans": _int(u.get("fans")),
                        "note_count": u.get("note_count"),
                        "xsec_token": u.get("xsec_token"),
                    }
    return None


def _int(v):
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


def collect_one(ctx, acct, target=30, scrolls=8):
    red_id = acct["xhs_id"]
    u = resolve_user(ctx, red_id)
    if not u or not u.get("id"):
        print(f"   [fail] 未解析到用户（小红书号 {red_id}）")
        return None, []

    token = urllib.parse.quote(u["xsec_token"] or "")
    href = f"/user/profile/{u['id']}?xsec_token={token}&xsec_source=pc_search"

    page = ctx.new_page()
    posts = {}

    def on_resp(resp):
        if "user_posted" in resp.url:
            try:
                for n in ((resp.json().get("data") or {}).get("notes") or []):
                    nid = n.get("note_id")
                    if not nid:
                        continue
                    nc = n.get("note_card") or n
                    t = nc.get("time")
                    posts[nid] = {
                        "note_id": nid,
                        "title": (nc.get("display_title") or nc.get("title") or "").strip(),
                        "type": nc.get("type") or n.get("type"),
                        "publish_ts": int(t // 1000) if t else None,
                        "publish_time": datetime.fromtimestamp(t / 1000).strftime("%Y-%m-%d %H:%M") if t else None,
                        "url": f"{BASE}/explore/{nid}",
                    }
            except Exception:
                pass

    page.on("response", on_resp)
    page.goto(BASE + href, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)
    if _captcha(page):
        print("   [warn] 打开主页触发验证码")
        page.close()
        return None, []

    counts = {}

    def merge_counts():
        # 网格虚拟化：同一 note 会在多轮滚动中重复出现，可能是空的（count/title 未加载）
        # 逐字段合并，绝不用空值覆盖已捕获的非空值
        for k, v in page.evaluate(SNAP_COUNTS_JS).items():
            cur = counts.get(k)
            if cur is None:
                counts[k] = v
                continue
            if not cur.get("count") and v.get("count"):
                cur["count"] = v["count"]
            if not cur.get("title") and v.get("title"):
                cur["title"] = v["title"]

    try:
        page.mouse.move(700, 500)
    except Exception:
        pass
    merge_counts()
    # 赞数是异步懒加载的，且网格有虚拟化，需多轮滚动边滚边累积
    for _ in range(scrolls):
        page.mouse.wheel(0, 2400)
        page.wait_for_timeout(1400)
        merge_counts()
        page.wait_for_timeout(600)

    info = page.evaluate("""() => {
        const r = window.__INITIAL_STATE__?.user?.userPageData;
        const d = r && (r._value || r._rawValue || r.value || r);
        if (!d) return null;
        const bi = d.basicInfo || {};
        const inter = {};
        (d.interactions || []).forEach(x => { inter[x.type] = x.count; });
        return {nickname: bi.nickname, followers: inter.fans,
                interaction: inter.interaction, posted: d.posted};
    }""")
    page.close()

    items = []
    for nid, p in sorted(posts.items(), key=lambda kv: kv[1].get("publish_ts") or 0, reverse=True)[:target]:
        dom = counts.get(nid) or {}
        wtype = 1 if (p.get("type") == "normal") else 0   # 1=图文 0=视频
        items.append({
            "work_id": nid,
            "title": p.get("title") or dom.get("title") or "",
            "work_type": wtype,
            "publish_ts": p.get("publish_ts"),
            "publish_time": p.get("publish_time"),
            "digg": _int(dom.get("count")) if dom.get("count") else 0,
            "comment": None,
            "share": None,
            "play": None,
            "url": p.get("url"),
        })

    profile = {
        "nickname": (info or {}).get("nickname") or u.get("name"),
        "followers": _int((info or {}).get("followers")) if (info or {}).get("followers") is not None else u.get("fans"),
        "total_likes": _int((info or {}).get("interaction")),
        "works_count": _int((info or {}).get("posted")) or u.get("note_count"),
    }
    return profile, items


def run(account=None, target=30, headed=False):
    if not available():
        print("[xhs] 未配置 cookie，跳过")
        return 0, 0
    db.init()
    accounts = load_xhs_accounts()
    if account:
        accounts = [a for a in accounts if a["id"] == account]
    if not accounts:
        print("[xhs] 没有可采集的小红书账号")
        return 0, 0

    con = db.connect()
    ok = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=not headed)
        ctx = browser.new_context(locale="zh-CN", user_agent=UA,
                                  viewport={"width": 1400, "height": 900})
        ctx.add_cookies(load_cookies())
        for acct in accounts:
            print(f"[xhs] 采集 {acct['owner']} / {acct['name']} ...", flush=True)
            try:
                profile, items = collect_one(ctx, acct, target=target)
                if not profile and not items:
                    continue
                db.upsert_snapshot(con, acct["id"], profile.get("followers"),
                                   profile.get("total_likes"), profile.get("works_count"),
                                   note=profile.get("nickname"))
                if items:
                    db.upsert_works(con, acct["id"], "xiaohongshu", items)
                con.commit()
                ok += 1
                print(f"   粉丝={profile.get('followers')} 获赞与收藏={profile.get('total_likes')} "
                      f"笔记数={profile.get('works_count')} | 抓到笔记 {len(items)} 条")
            except Exception as e:
                print(f"   [error] {type(e).__name__}: {e}")
            if acct is not accounts[-1]:
                time.sleep(random.uniform(12, 25))   # 账号间随机间隔，降低风控概率
        browser.close()
    con.close()
    print(f"[xhs] 完成，成功 {ok}/{len(accounts)}")
    return ok, len(accounts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", help="只采某个 account_id")
    ap.add_argument("--target", type=int, default=30)
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()
    run(args.account, args.target, args.headed)


if __name__ == "__main__":
    main()
