"""RedFox 通道采集：小红书 / 视频号（替代已停用的 cookie + Playwright 方案）。

背景（2026-10-19 调研 + 2026-10-20 复测）：
  - 小红书 cookie 采集因平台风控提示已停用，改用 RedFox API；
    账号级指标走 `xiaohongshu.get_account(account_id=小红书号)`，
    作品明细走 `get_user_works`（优质库对中小号多为 3203 未收录，有数据才写 works）。
  - 视频号走 `wechat_channels.search_users` + `get_user_works`，
    当前库未收录矩阵内 3 个号（实测 total=0），采集结果为空时跳过并记录原因。

字段口径：
  followers   = accountFans
  total_likes = accountLikes + accountCollectes（对应平台「获赞与收藏」，与历史快照口径一致）
  works_count = accountTotalWorks

密钥：环境变量 REDFOX_API_KEY（用户级，已持久化）。

用法：
    python collect_redfox.py                     # 小红书 + 视频号
    python collect_redfox.py --platform xiaohongshu
    python collect_redfox.py --account tyy_oral_xhs
    python collect_redfox.py --no-works          # 只采账号级指标，不试作品列表
"""
import os
import sys
import json
import time
import argparse
import traceback
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import db  # noqa: E402

CONFIG = os.path.join(HERE, "config", "accounts.json")
PLATFORMS = ("xiaohongshu", "channels")


def available():
    return bool(os.environ.get("REDFOX_API_KEY"))


def _client():
    from redfox import RedFoxClient
    return RedFoxClient()


def load_accounts(platform=None):
    """读 config/accounts.json 里配置了 RedFox 可识别 id 的自有号。"""
    with open(CONFIG, encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for a in data.get("accounts") or []:
        p = a.get("platform")
        if p not in PLATFORMS:
            continue
        if platform and p != platform:
            continue
        if p == "xiaohongshu" and not a.get("xhs_id"):
            continue
        out.append(a)
    return out


def _int(v):
    if v is None:
        return None
    try:
        return int(v)
    except Exception:
        try:
            return int(float(v))
        except Exception:
            return None


def collect_xhs_account(client, acct):
    """小红书账号级指标。返回 (profile, err)。"""
    xid = str(acct["xhs_id"])
    try:
        d = client.xiaohongshu.get_account(account_id=xid)
    except Exception as e:
        msg = str(e)
        if "3203" in msg:
            return None, "3203 优质库未收录"
        return None, f"{type(e).__name__}: {msg[:160]}"
    if not isinstance(d, dict):
        return None, "返回结构异常"
    likes = _int(d.get("accountLikes")) or 0
    collects = _int(d.get("accountCollectes")) or 0
    return {
        "nickname": d.get("accountName"),
        "followers": _int(d.get("accountFans")),
        "total_likes": (likes + collects) or None,
        "works_count": _int(d.get("accountTotalWorks")),
        "update_time": d.get("accountUpdateTime"),
    }, None


def collect_xhs_works(client, acct, target=30):
    """小红书作品列表。优质库多返回 3203，返回 [] 表示不可得。"""
    xid = str(acct["xhs_id"])
    items = []
    try:
        r = client.xiaohongshu.get_user_works(red_id=xid, offset=0)
    except Exception:
        return items
    rows = []
    if isinstance(r, dict):
        rows = r.get("list") or r.get("notes") or r.get("data") or []
        if isinstance(rows, dict):
            rows = rows.get("list") or []
    for n in rows[:target]:
        nc = n.get("noteCard") or n.get("note_card") or n
        wid = n.get("noteId") or n.get("note_id") or n.get("id")
        if not wid:
            continue
        inter = nc.get("interactInfo") or nc.get("interact_info") or {}
        t = n.get("publishTime") or n.get("time")
        items.append({
            "work_id": str(wid),
            "title": (nc.get("displayTitle") or nc.get("display_title") or "").strip(),
            "work_type": 1 if (nc.get("type") or "").lower() in ("normal", "image") else 0,
            "publish_ts": int(t // 1000) if isinstance(t, (int, float)) and t > 1e11 else (t if isinstance(t, int) else None),
            "publish_time": datetime.fromtimestamp(t / 1000).strftime("%Y-%m-%d %H:%M")
            if isinstance(t, (int, float)) and t > 1e11 else None,
            "digg": _int(str(inter.get("likedCount") or "").replace("+", "")),
            "comment": _int(str(inter.get("commentCount") or "").replace("+", "")),
            "share": _int(str(inter.get("shareCount") or "").replace("+", "")),
            "play": None,
            "url": f"https://www.xiaohongshu.com/explore/{wid}",
        })
    return items


def collect_channels(client, acct, target=30):
    """视频号：先按昵称确认库中是否存在，再取作品。库未收录则返回 (None, [], 原因)。"""
    name = acct.get("name")
    if not name:
        return None, [], "缺少昵称"
    try:
        r = client.wechat_channels.get_user_works(nickname=name, page=1, size=target)
    except Exception as e:
        return None, [], f"{type(e).__name__}: {str(e)[:140]}"
    rows = (r or {}).get("list") or []
    total = (r or {}).get("total")
    if not rows:
        return None, [], f"库未收录（get_user_works total={total}）"
    items = []
    for n in rows[:target]:
        wid = n.get("id") or n.get("objectId") or n.get("object_id")
        if not wid:
            continue
        items.append({
            "work_id": str(wid),
            "title": (n.get("title") or n.get("desc") or "").strip(),
            "work_type": 0,
            "publish_ts": _int(n.get("createTime") or n.get("create_time")),
            "publish_time": n.get("createTimeStr") or n.get("publishTime"),
            "digg": _int(n.get("likeCount") or n.get("like_count")),
            "comment": _int(n.get("commentCount") or n.get("comment_count")),
            "share": _int(n.get("shareCount") or n.get("share_count")),
            "play": _int(n.get("playCount") or n.get("play_count")),
            "url": n.get("url"),
        })
    return {"nickname": name}, items, None


def run(platform=None, account=None, with_works=True, target=30):
    if not available():
        print("[redfox] 未配置 REDFOX_API_KEY，跳过")
        return 0, 0
    db.init()
    accounts = load_accounts(platform)
    if account:
        accounts = [a for a in accounts if a["id"] == account]
    if not accounts:
        print("[redfox] 没有可采集的账号")
        return 0, 0

    client = _client()
    con = db.connect()
    ok = 0
    skipped = []
    for acct in accounts:
        p = acct["platform"]
        label = f"{acct['owner']} / {acct['name']}"
        print(f"[redfox] {p} 采集 {label} ...", flush=True)
        try:
            if p == "xiaohongshu":
                prof, err = collect_xhs_account(client, acct)
                items = []
                if prof and with_works:
                    items = collect_xhs_works(client, acct, target=target)
            else:
                prof, items, err = collect_channels(client, acct, target=target)

            if err:
                print(f"   [skip] {err}")
                skipped.append(f"{acct['name']}: {err}")
                continue

            db.upsert_snapshot(con, acct["id"], prof.get("followers"),
                               prof.get("total_likes"), prof.get("works_count"),
                               note=(prof.get("nickname") or acct["name"]))
            if items:
                db.upsert_works(con, acct["id"], p, items)
            con.commit()
            ok += 1
            extra = f" | 作品 {len(items)} 条" if with_works else ""
            print(f"   平台名={prof.get('nickname')} 粉丝={prof.get('followers')} "
                  f"获赞与收藏={prof.get('total_likes')} 作品数={prof.get('works_count')}{extra}")
        except Exception as e:
            print(f"   [error] {type(e).__name__}: {e}")
            traceback.print_exc()
        time.sleep(0.4)
    con.close()
    print(f"[redfox] 完成，成功 {ok}/{len(accounts)}")
    if skipped:
        print("[redfox] 跳过明细：")
        for s in skipped:
            print("   -", s)
    return ok, len(accounts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", choices=PLATFORMS, help="只采某个平台")
    ap.add_argument("--account", help="只采某个 account_id")
    ap.add_argument("--no-works", action="store_true", help="只采账号级指标")
    ap.add_argument("--target", type=int, default=30)
    args = ap.parse_args()
    run(args.platform, args.account, with_works=not args.no_works, target=args.target)


if __name__ == "__main__":
    main()
