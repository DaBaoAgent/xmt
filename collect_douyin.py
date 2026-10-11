"""抖音前台采集（免登录）：Playwright 驱动本机 Chrome，游客态拦截官方 XHR。
抓取：粉丝数 / 总获赞 / 作品总数 / 最近 N 条作品(发布时间、标题、类型、单条点赞等)。
"""
import os
import re
import sys
import json
import time
import argparse
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")
from playwright.sync_api import sync_playwright

import db

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "config", "accounts.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")

PROFILE_API = "user/profile/other"
POST_API = "/aweme/v1/web/aweme/post/"


def load_douyin_accounts():
    with open(CONFIG, encoding="utf-8") as f:
        data = json.load(f)
    return [a for a in data["accounts"]
            if a.get("platform") == "douyin" and a.get("url")]


def collect_one(ctx, acct, target=30, scroll_max=12):
    page = ctx.new_page()
    posts = {}          # work_id -> work dict
    profile = {}

    def on_resp(resp):
        u = resp.url
        try:
            if PROFILE_API in u:
                j = resp.json()
                user = (j or {}).get("user") or {}
                if user:
                    profile.update({
                        "nickname": user.get("nickname"),
                        "sec_uid": user.get("sec_uid"),
                        "unique_id": user.get("unique_id"),
                        "followers": user.get("follower_count"),
                        "total_likes": user.get("total_favorited"),
                        "works_count": user.get("aweme_count"),
                        "signature": user.get("signature"),
                    })
            elif POST_API in u:
                j = resp.json()
                for aw in (j or {}).get("aweme_list", []) or []:
                    wid = aw.get("aweme_id")
                    if not wid:
                        continue
                    st = aw.get("statistics", {}) or {}
                    ct = aw.get("create_time")
                    posts[wid] = {
                        "work_id": wid,
                        "title": (aw.get("desc") or "").strip(),
                        "work_type": aw.get("aweme_type"),
                        "publish_ts": ct,
                        "publish_time": datetime.fromtimestamp(ct).strftime("%Y-%m-%d %H:%M") if ct else None,
                        "digg": st.get("digg_count"),
                        "comment": st.get("comment_count"),
                        "share": st.get("share_count"),
                        "play": st.get("play_count"),
                        "url": f"https://www.douyin.com/video/{wid}",
                    }
        except Exception:
            pass

    page.on("response", on_resp)
    page.goto(acct["url"], wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4500)

    # 把鼠标移到内容区中央，滚轮才作用在作品网格上（触发分页请求）
    try:
        page.mouse.move(700, 500)
        page.wait_for_timeout(300)
    except Exception:
        pass

    for _ in range(scroll_max):
        if len(posts) >= target:
            break
        page.mouse.wheel(0, 3200)
        page.wait_for_timeout(1600)
        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        except Exception:
            pass
        page.wait_for_timeout(900)

    page.close()
    items = sorted(posts.values(), key=lambda x: x.get("publish_ts") or 0, reverse=True)[:target]
    return profile, items


def run(account=None, target=30, headed=False):
    db.init()
    accounts = load_douyin_accounts()
    if account:
        accounts = [a for a in accounts if a["id"] == account]
    if not accounts:
        print("[warn] 没有可采集的抖音账号（url 为空？）")
        return 0, 0

    con = db.connect()
    ok = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=not headed)
        ctx = browser.new_context(locale="zh-CN", user_agent=UA,
                                  viewport={"width": 1400, "height": 900})
        for acct in accounts:
            print(f"[douyin] 采集 {acct['owner']} / {acct['name']} ...", flush=True)
            try:
                profile, items = collect_one(ctx, acct, target=target)
                if not profile and not items:
                    print("   [fail] 未取到任何数据（链接是否正确/是否被风控）")
                    continue
                db.upsert_snapshot(con, acct["id"], profile.get("followers"),
                                   profile.get("total_likes"), profile.get("works_count"),
                                   note=profile.get("nickname"))
                if items:
                    db.upsert_works(con, acct["id"], "douyin", items)
                con.commit()
                ok += 1
                print(f"   粉丝={profile.get('followers')} 总赞={profile.get('total_likes')} "
                      f"作品数={profile.get('works_count')} | 抓到作品 {len(items)} 条")
            except Exception as e:
                print(f"   [error] {type(e).__name__}: {e}")
        browser.close()
    con.close()
    print(f"[douyin] 完成，成功 {ok}/{len(accounts)}")
    return ok, len(accounts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", help="只采某个 account_id")
    ap.add_argument("--target", type=int, default=30, help="每个号采集最近 N 条作品")
    ap.add_argument("--headed", action="store_true", help="显示浏览器窗口(排错用)")
    args = ap.parse_args()
    run(args.account, args.target, args.headed)


if __name__ == "__main__":
    main()
