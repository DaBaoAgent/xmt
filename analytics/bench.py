"""对标分析：自有账号 vs 对标账号的体量、互动、更新频率、互动效率与差距摘要。

只读 SQLite（db.connect()），不写任何数据。

对外接口：
  bench_table(platform=None) -> list[dict]
      逐账号对标表：粉丝、作品数、平均点赞、更新频率、互动效率。
  gap_summary() -> dict
      自有 / 对标两组汇总 + 差距比例 + 可执行结论（中文）。

口径说明：
  粉丝/作品数 取该账号最新一条 account_snapshots；无快照则粉丝回退 accounts.followers、
  作品数回退 works 表计数。
  平均点赞等取 works 表全量均值；更新频率 = 近 30 天发布数 / (30/7) → 周均条数；
  互动效率 = 平均(点赞+评论+分享) / 粉丝数 × 100%（每百粉互动量级）。

命令行：
  python -m analytics.bench [douyin|xiaohongshu|channels]
"""
import sys
from datetime import timedelta

import db
from analytics import (PLATFORM_LABEL, fmt_num, fmt_delta, fmt_ratio,
                       render_table, parse_date, date_str, work_dt)

_KIND_LABEL = {"own": "自有", "rival": "对标"}
_FREQ_DAYS = 30


# ---------- 内部工具 ----------

def _latest_snapshot(con, aid):
    r = con.execute(
        "SELECT followers, works_count, total_likes, snap_date FROM account_snapshots "
        "WHERE account_id=? ORDER BY snap_date DESC LIMIT 1", (aid,)).fetchone()
    return dict(r) if r else {}


def _works_stats(con, aid):
    """works 表统计：条数、平均点赞/评论/分享。"""
    r = con.execute(
        "SELECT COUNT(*) n, AVG(COALESCE(digg,0)) ad, AVG(COALESCE(comment,0)) ac, "
        "AVG(COALESCE(share,0)) ash FROM works WHERE account_id=?", (aid,)).fetchone()
    n = r["n"] or 0
    return {
        "n": n,
        "avg_digg": round(r["ad"], 1) if r["ad"] is not None else None,
        "avg_comment": round(r["ac"], 1) if r["ac"] is not None else None,
        "avg_share": round(r["ash"], 1) if r["ash"] is not None else None,
    }


def _freq_weekly(con, aid, ref_date):
    """近 _FREQ_DAYS 天周均更新条数。"""
    cutoff = ref_date - timedelta(days=_FREQ_DAYS)
    n = 0
    for r in con.execute("SELECT publish_time, publish_ts FROM works WHERE account_id=?", (aid,)):
        dt = work_dt(dict(r))
        if dt and dt.date() > cutoff:
            n += 1
    return round(n / (_FREQ_DAYS / 7), 2)


def _mean(vals):
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else None


# ---------- 对外接口 ----------

def bench_table(platform=None):
    """自有 vs 对标逐账号对比表。

    返回：[ {account_id, name, platform, platform_label, kind, kind_label,
             followers, works_count, avg_digg, avg_comment, avg_share, avg_interact,
             freq_weekly, engagement_rate, data_days} ]
    空数据返回 []。
    """
    con = db.connect()
    try:
        # 参考日：优先用库内最新快照日，其次今天
        maxd = con.execute("SELECT MAX(snap_date) m FROM account_snapshots").fetchone()["m"]
        from datetime import date as _date
        ref_date = parse_date(maxd) or _date.today()

        sql = "SELECT * FROM accounts WHERE enabled=1"
        args = []
        if platform:
            sql += " AND platform=?"
            args.append(platform)
        sql += " ORDER BY kind, platform, id"
        accts = [dict(r) for r in con.execute(sql, args).fetchall()]

        rows = []
        for a in accts:
            aid = a["id"]
            snap = _latest_snapshot(con, aid)
            ws = _works_stats(con, aid)

            followers = snap.get("followers")
            if followers is None:
                followers = a.get("followers")
            works_count = snap.get("works_count")
            if works_count is None:
                works_count = ws["n"]

            avg_interact = None
            if ws["avg_digg"] is not None:
                avg_interact = round(
                    (ws["avg_digg"] or 0) + (ws["avg_comment"] or 0) + (ws["avg_share"] or 0), 1)

            engagement = None
            if followers and avg_interact is not None:
                engagement = round(avg_interact / followers * 100, 3)

            rows.append({
                "account_id": aid,
                "name": a.get("name") or aid,
                "platform": a.get("platform") or "",
                "platform_label": PLATFORM_LABEL.get(a.get("platform"), a.get("platform") or "—"),
                "kind": a.get("kind") or "own",
                "kind_label": _KIND_LABEL.get(a.get("kind"), a.get("kind") or "—"),
                "followers": followers,
                "works_count": works_count,
                "avg_digg": ws["avg_digg"],
                "avg_comment": ws["avg_comment"],
                "avg_share": ws["avg_share"],
                "avg_interact": avg_interact,
                "freq_weekly": _freq_weekly(con, aid, ref_date),
                "engagement_rate": engagement,
                "data_days": len(con.execute(
                    "SELECT 1 FROM account_snapshots WHERE account_id=?", (aid,)).fetchall()),
            })
        return rows
    finally:
        con.close()


def _group(rows, kind):
    rs = [r for r in rows if r["kind"] == kind]
    return {
        "accounts": len(rs),
        "followers": sum(r["followers"] for r in rs if r["followers"] is not None) or 0,
        "works": sum(r["works_count"] for r in rs if r["works_count"] is not None) or 0,
        "avg_works": _mean([r["works_count"] for r in rs]),
        "avg_digg": _mean([r["avg_digg"] for r in rs]),
        "avg_freq": _mean([r["freq_weekly"] for r in rs]),
        "avg_engagement": _mean([r["engagement_rate"] for r in rs]),
        "avg_followers": _mean([r["followers"] for r in rs]),
    }


def gap_summary():
    """自有 vs 对标差距摘要 + 可执行结论。

    返回：
      {
        "own": {...汇总...}, "rival": {...汇总...},
        "gaps": [ {"metric","own","rival","ratio","verdict"} ],
        "conclusions": ["中文结论", ...],
      }
    空数据时各组为 0/None，conclusions 给出提示。
    """
    table = bench_table()
    own = _group(table, "own")
    rival = _group(table, "rival")

    def ratio(o, r):
        if o is None or r in (None, 0):
            return None
        return round(o / r, 2)

    def verdict(o, r):
        if r in (None, 0) or o is None:
            return "对标样本不足"
        if o >= r * 1.1:
            return "自有领先"
        if o <= r * 0.9:
            return "自有落后"
        return "基本持平"

    defs = [
        ("账号数", own["accounts"], rival["accounts"]),
        ("粉丝总量", own["followers"], rival["followers"]),
        ("平均粉丝", own["avg_followers"], rival["avg_followers"]),
        ("作品总量", own["works"], rival["works"]),
        ("平均点赞", own["avg_digg"], rival["avg_digg"]),
        ("周均更新", own["avg_freq"], rival["avg_freq"]),
        ("互动效率", own["avg_engagement"], rival["avg_engagement"]),
    ]
    gaps = [{"metric": m, "own": o, "rival": r, "ratio": ratio(o, r), "verdict": verdict(o, r)}
            for m, o, r in defs]

    # ---- 结论 ----
    C = []
    if own["accounts"] == 0:
        C.append("未采集到自有账号数据，请先运行采集（snapshot.py）后重试。")
    else:
        C.append(f"自有 {own['accounts']} 个号合计粉丝 {fmt_num(own['followers'])}、"
                 f"作品 {fmt_num(own['works'])} 条，平均每号粉丝 {fmt_num(own['avg_followers'])}。")
    if rival["accounts"] == 0 or not ((rival["works"] or 0) > 0 or (rival["followers"] or 0) > 0):
        C.append("对标账号尚无有效数据（config/rivals.json 未填主页链接或未采集），"
                 "补齐后重跑即可生成对比与差距结论。")
    else:
        C.append(f"对标 {rival['accounts']} 个号合计粉丝 {fmt_num(rival['followers'])}，"
                 f"平均点赞 {fmt_ratio(rival['avg_digg'], 1)}。")
        # 更新频率
        if own["avg_freq"] is not None and rival["avg_freq"] is not None:
            if own["avg_freq"] < rival["avg_freq"] * 0.8:
                C.append(f"更新频率落后：自有周均 {own['avg_freq']} 条 < 对标 {rival['avg_freq']} 条，"
                         f"建议提高发布密度（每日至少 1 条实拍）。")
            elif own["avg_freq"] > rival["avg_freq"] * 1.2:
                C.append(f"更新频率领先：自有周均 {own['avg_freq']} 条 > 对标 {rival['avg_freq']} 条，"
                         f"保持节奏，重点转向内容质量。")
        # 互动效率
        if own["avg_engagement"] is not None and rival["avg_engagement"] is not None:
            if own["avg_engagement"] < rival["avg_engagement"] * 0.8:
                C.append(f"互动效率落后：自有每百粉互动 {own['avg_engagement']} < "
                         f"对标 {rival['avg_engagement']}，建议优化选题与开头钩子。")
            elif own["avg_engagement"] > rival["avg_engagement"] * 1.2:
                C.append(f"互动效率领先：自有每百粉互动 {own['avg_engagement']} > "
                         f"对标 {rival['avg_engagement']}，可放大高互动选题类型。")
        # 平均点赞
        if own["avg_digg"] is not None and rival["avg_digg"] is not None:
            if own["avg_digg"] < rival["avg_digg"] * 0.8:
                C.append(f"单条点赞落后：自有均值 {fmt_ratio(own['avg_digg'], 1)} < "
                         f"对标 {fmt_ratio(rival['avg_digg'], 1)}，拆解对标爆款结构复用。")
            elif own["avg_digg"] > rival["avg_digg"] * 1.2:
                C.append(f"单条点赞领先：自有均值 {fmt_ratio(own['avg_digg'], 1)} > "
                         f"对标 {fmt_ratio(rival['avg_digg'], 1)}。")
    return {"own": own, "rival": rival, "gaps": gaps, "conclusions": C}


# ---------- 命令行 ----------

def _print_bench(platform=None):
    rows = bench_table(platform)
    title = f"对标分析（{PLATFORM_LABEL.get(platform, platform) if platform else '全部平台'}）"
    print("=" * 100)
    print(title)
    print("=" * 100)
    if not rows:
        print("accounts 表为空或无启用账号。")
    else:
        headers = ["账号", "类型", "平台", "粉丝", "作品数", "平均点赞", "平均互动", "周更条数", "互动效率%", "快照天"]
        table = [[r["name"], r["kind_label"], r["platform_label"],
                  fmt_num(r["followers"]), fmt_num(r["works_count"]),
                  fmt_ratio(r["avg_digg"], 1), fmt_ratio(r["avg_interact"], 1),
                  fmt_ratio(r["freq_weekly"], 2), fmt_ratio(r["engagement_rate"], 3),
                  r["data_days"]] for r in rows]
        print(render_table(headers, table, aligns=[
            "left", "left", "left", "right", "right", "right", "right", "right", "right", "right"]))

    gs = gap_summary()
    print()
    print("-" * 100)
    print("差距摘要（自有 vs 对标）")
    print("-" * 100)
    headers = ["指标", "自有", "对标", "自有/对标", "判定"]
    table = [[g["metric"],
              fmt_num(g["own"]) if isinstance(g["own"], (int, float)) else "—",
              fmt_num(g["rival"]) if isinstance(g["rival"], (int, float)) else "—",
              (f"{g['ratio']}x" if g["ratio"] is not None else "—"),
              g["verdict"]] for g in gs["gaps"]]
    print(render_table(headers, table, aligns=["left", "right", "right", "right", "left"]))
    print()
    print("结论与建议：")
    for i, c in enumerate(gs["conclusions"], 1):
        print(f"  {i}. {c}")


if __name__ == "__main__":
    _plat = sys.argv[1] if len(sys.argv) > 1 else None
    _print_bench(_plat)
