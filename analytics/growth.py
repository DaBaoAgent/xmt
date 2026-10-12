"""增长分析：账号粉丝 / 获赞 / 作品数的「变化、日增、环比」。

只读 SQLite（db.connect()），不写任何数据。

对外接口：
  account_growth(account_id=None, days=30) -> dict
      单账号（传 account_id）或全部自有账号（不传）的增长概览。
  growth_ranking(days=7) -> list[dict]
      自有账号按「窗口内涨粉」降序排名。

窗口口径：以库中「最新快照日」为期末，往前 days 天为窗口。
  期初值  = 窗口开始日「之前」最近的一条快照（无则退化为窗口内最早一条）
  期末值  = 期末日「及之前」最近的一条快照
  日增    = 变化 / 实际跨度天数
  环比    = (本期变化 - 上期变化) / |上期变化| * 100%

命令行：
  python -m analytics.growth [days]
"""
import sys
from datetime import date, timedelta

import db
from analytics import (PLATFORM_LABEL, fmt_num, fmt_delta, fmt_pct,
                       render_table, parse_date, date_str)

METRICS = ("followers", "total_likes", "works_count")
METRIC_LABEL = {"followers": "粉丝", "total_likes": "获赞", "works_count": "作品"}


# ---------- 内部工具 ----------

def _accounts(con, account_id=None):
    """自有账号列表；指定 account_id 时只取该号（不在表内也容许分析）。"""
    if account_id:
        rows = con.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchall()
        if rows:
            return [dict(r) for r in rows]
        return [{"id": account_id, "name": account_id, "platform": "", "kind": "own"}]
    rows = con.execute(
        "SELECT * FROM accounts WHERE kind='own' AND enabled=1 ORDER BY platform, id"
    ).fetchall()
    return [dict(r) for r in rows]


def _snap_at_or_before(con, aid, d):
    r = con.execute(
        "SELECT snap_date, followers, total_likes, works_count FROM account_snapshots "
        "WHERE account_id=? AND snap_date<=? ORDER BY snap_date DESC LIMIT 1",
        (aid, date_str(d))).fetchone()
    return dict(r) if r else None


def _snap_before(con, aid, d):
    r = con.execute(
        "SELECT snap_date, followers, total_likes, works_count FROM account_snapshots "
        "WHERE account_id=? AND snap_date<? ORDER BY snap_date DESC LIMIT 1",
        (aid, date_str(d))).fetchone()
    return dict(r) if r else None


def _snap_first_in(con, aid, d0, d1):
    r = con.execute(
        "SELECT snap_date, followers, total_likes, works_count FROM account_snapshots "
        "WHERE account_id=? AND snap_date>=? AND snap_date<=? ORDER BY snap_date LIMIT 1",
        (aid, date_str(d0), date_str(d1))).fetchone()
    return dict(r) if r else None


def _pct(cur, prev):
    """环比百分比；prev 为空或 0 时返回 None。"""
    if cur is None or prev in (None, 0):
        return None
    return (cur - prev) / abs(prev) * 100.0


def _analyze_account(con, acct, end_d, days):
    """单个账号在 [end_d-days+1, end_d] 窗口内的增长。无快照返回 None。"""
    aid = acct["id"]
    start_d = end_d - timedelta(days=days - 1)

    end_row = _snap_at_or_before(con, aid, end_d)
    if end_row is None:
        return None
    start_row = _snap_before(con, aid, start_d) or _snap_first_in(con, aid, start_d, end_d) or end_row

    sd = parse_date(start_row["snap_date"]) or start_d
    ed = parse_date(end_row["snap_date"]) or end_d
    span = max(1, (ed - sd).days)

    # 上一周期（等长窗口）用于算环比
    prev_end_d = start_d - timedelta(days=1)
    prev_start_d = prev_end_d - timedelta(days=days - 1)
    prev_end_row = _snap_at_or_before(con, aid, prev_end_d)
    prev_start_row = _snap_before(con, aid, prev_start_d)

    metrics = {}
    for m in METRICS:
        sv = start_row.get(m)
        ev = end_row.get(m)
        delta = None if (sv is None or ev is None) else ev - sv
        daily = None if delta is None else delta / span
        pe = prev_end_row.get(m) if prev_end_row else None
        ps = prev_start_row.get(m) if prev_start_row else None
        prev_delta = None if (pe is None or ps is None) else pe - ps
        metrics[m] = {
            "start": sv, "end": ev, "delta": delta,
            "daily_avg": daily, "prev_delta": prev_delta,
            "mom_pct": _pct(delta, prev_delta),
        }

    return {
        "account_id": aid,
        "name": acct.get("name") or aid,
        "platform": acct.get("platform") or "",
        "kind": acct.get("kind") or "own",
        "period": {"start": start_row["snap_date"], "end": end_row["snap_date"], "days": span},
        "metrics": metrics,
    }


def _aggregate(per, days):
    """把多账号的 start/end/delta 汇总成合计。"""
    out = {}
    for m in METRICS:
        total_start = total_end = total_delta = total_prev = 0
        has_start = has_end = has_delta = has_prev = False
        for a in per:
            b = a["metrics"][m]
            if b["start"] is not None:
                total_start += b["start"]; has_start = True
            if b["end"] is not None:
                total_end += b["end"]; has_end = True
            if b["delta"] is not None:
                total_delta += b["delta"]; has_delta = True
            if b["prev_delta"] is not None:
                total_prev += b["prev_delta"]; has_prev = True
        out[m] = {
            "start": total_start if has_start else None,
            "end": total_end if has_end else None,
            "delta": total_delta if has_delta else None,
            "daily_avg": (total_delta / days) if has_delta else None,
            "prev_delta": total_prev if has_prev else None,
            "mom_pct": _pct(total_delta if has_delta else None,
                            total_prev if has_prev else None),
        }
    return out


# ---------- 对外接口 ----------

def account_growth(account_id=None, days=30):
    """单账号或全部自有账号的粉丝 / 获赞 / 作品数变化、日增、环比。

    返回：
      {
        "scope": account_id 或 "all",
        "days": int, "start_date": "YYYY-MM-DD"|None, "end_date": "YYYY-MM-DD"|None,
        "accounts": [ {account_id,name,platform,kind,
                        period:{start,end,days},
                        metrics:{<指标>:{start,end,delta,daily_avg,prev_delta,mom_pct}}} ],
        "total": {<指标>:{start,end,delta,daily_avg,prev_delta,mom_pct}},
      }
    空数据时 accounts=[]，total 各字段为 None。
    """
    days = max(1, int(days))
    con = db.connect()
    try:
        maxd = con.execute("SELECT MAX(snap_date) m FROM account_snapshots").fetchone()["m"]
        end_d = parse_date(maxd) or date.today()
        per = []
        for a in _accounts(con, account_id):
            r = _analyze_account(con, a, end_d, days)
            if r:
                per.append(r)
        return {
            "scope": account_id or "all",
            "days": days,
            "start_date": date_str(end_d - timedelta(days=days - 1)),
            "end_date": date_str(end_d),
            "accounts": per,
            "total": _aggregate(per, days),
        }
    finally:
        con.close()


def growth_ranking(days=7):
    """自有账号按窗口内涨粉降序排名。

    返回：[ {rank, account_id, name, platform,
             followers_start, followers_end, followers_delta, daily_avg,
             likes_delta, works_delta, mom_pct, period} ]
    空数据返回 []。
    """
    days = max(1, int(days))
    con = db.connect()
    try:
        maxd = con.execute("SELECT MAX(snap_date) m FROM account_snapshots").fetchone()["m"]
        if not maxd:
            return []
        end_d = parse_date(maxd) or date.today()
        rows = []
        for a in _accounts(con):
            r = _analyze_account(con, a, end_d, days)
            if not r:
                continue
            f = r["metrics"]["followers"]
            l = r["metrics"]["total_likes"]
            w = r["metrics"]["works_count"]
            rows.append({
                "account_id": r["account_id"],
                "name": r["name"],
                "platform": r["platform"],
                "followers_start": f["start"],
                "followers_end": f["end"],
                "followers_delta": f["delta"],
                "daily_avg": f["daily_avg"],
                "likes_delta": l["delta"],
                "works_delta": w["delta"],
                "mom_pct": f["mom_pct"],
                "period": r["period"],
            })
        rows.sort(key=lambda x: (x["followers_delta"] is None, -(x["followers_delta"] or 0)))
        for i, x in enumerate(rows, 1):
            x["rank"] = i
        return rows
    finally:
        con.close()


# ---------- 命令行 ----------

def _print_growth(res, days):
    line = "=" * 74
    print(line)
    print(f"账号增长分析（最近 {days} 天：{res['start_date']} ~ {res['end_date']} ｜ 口径=窗口末值-窗口前值）")
    print(line)
    if not res["accounts"]:
        print("暂无快照数据（account_snapshots 为空），今日无可分析增长。")
        return
    headers = ["账号", "平台", "期末粉丝", "粉丝变化", "日均涨粉", "获赞变化", "作品变化", "粉丝环比"]
    rows = []
    for a in res["accounts"]:
        f = a["metrics"]["followers"]
        l = a["metrics"]["total_likes"]
        w = a["metrics"]["works_count"]
        rows.append([
            a["name"], PLATFORM_LABEL.get(a["platform"], a["platform"] or "—"),
            fmt_num(f["end"]), fmt_delta(f["delta"]),
            fmt_num(round(f["daily_avg"], 1)) if f["daily_avg"] is not None else "—",
            fmt_delta(l["delta"]), fmt_delta(w["delta"]), fmt_pct(f["mom_pct"]),
        ])
    print(render_table(headers, rows,
                       aligns=["left", "left", "right", "right", "right", "right", "right", "right"]))
    t = res["total"]
    print()
    print(f"合计：粉丝 {fmt_num(t['followers']['end'])}（{fmt_delta(t['followers']['delta'])}）"
          f"｜获赞 {fmt_num(t['total_likes']['end'])}（{fmt_delta(t['total_likes']['delta'])}）"
          f"｜作品 {fmt_num(t['works_count']['end'])}（{fmt_delta(t['works_count']['delta'])}）")


def _print_ranking(days):
    rows = growth_ranking(days)
    print()
    print("=" * 74)
    print(f"账号涨粉榜（最近 {days} 天）")
    print("=" * 74)
    if not rows:
        print("暂无快照数据。")
        return
    headers = ["排名", "账号", "平台", "涨粉", "期末粉丝", "日均涨粉", "涨赞", "增收作品"]
    table = []
    for r in rows:
        table.append([
            r["rank"], r["name"], PLATFORM_LABEL.get(r["platform"], r["platform"] or "—"),
            fmt_delta(r["followers_delta"]), fmt_num(r["followers_end"]),
            fmt_num(round(r["daily_avg"], 1)) if r["daily_avg"] is not None else "—",
            fmt_delta(r["likes_delta"]), fmt_delta(r["works_delta"]),
        ])
    print(render_table(headers, table,
                       aligns=["right", "left", "left", "right", "right", "right", "right", "right"]))


if __name__ == "__main__":
    _days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    _print_growth(account_growth(days=_days), _days)
    _print_ranking(_days)
