"""爆款作品分析：爆款榜、标题特征、发布时机、仍在涨的作品。

只读 SQLite（db.connect()），不写任何数据。

对外接口：
  hit_works(platform=None, account_id=None, min_digg=None, days=30, limit=20) -> list[dict]
      爆款作品榜：最近 days 天发布的作品，按点赞降序。
  title_patterns(works) -> dict
      标题特征：长度分布、高频词（话题标签 + 中文双字词）、疑问句/数字/感叹号占比。
  hit_timing(works) -> dict
      发布时段 / 星期分布 vs 点赞表现（哪个时间发最容易爆）。
  rising_works(days=7, min_delta=100) -> list[dict]
      基于 work_snapshots 计算「仍在涨」的作品（窗口内点赞增量 ≥ min_delta）。

命令行：
  python -m analytics.hits [days]
"""
import re
import sys
from datetime import date, timedelta

import db
from analytics import (PLATFORM_LABEL, fmt_num, fmt_delta, render_table,
                       parse_date, date_str, work_dt)

# 话题标签：抖音/小红书常见形如 #关键词 或 #关键词#，关键词一般不含空格
_HASHTAG_RE = re.compile(r"#([^#\s]{1,30})#?")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
_DIGIT_RE = re.compile(r"\d")
_QWORDS = ("怎么", "如何", "为什么", "什么", "哪些", "哪个", "多少", "几", "吗", "呢", "么", "哪")
# 高频双字词过滤（虚词/口头禅，无信息量）
_STOP_BIGRAMS = {
    "可以", "我们", "你们", "他们", "这个", "那个", "什么", "自己", "就是", "然后",
    "而且", "因为", "所以", "这样", "那样", "没有", "一个", "真的", "非常", "已经",
    "还是", "但是", "如果", "只是", "还有", "不是", "就是", "一下", "一直", "能就",
}
_WEEKDAY = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
_SLOTS = [
    ("凌晨 0-6", 0, 6), ("早间 6-9", 6, 9), ("上午 9-12", 9, 12),
    ("午间 12-14", 12, 14), ("下午 14-18", 14, 18), ("晚间 18-24", 18, 24),
]


# ---------- 内部工具 ----------

def _fetch_works(platform=None, account_id=None, min_digg=None):
    """按平台/账号/点赞门槛取作品行（含账号名），时间过滤在 Python 侧做。"""
    con = db.connect()
    try:
        sql = ("SELECT w.*, a.name AS account_name, a.kind AS account_kind "
               "FROM works w LEFT JOIN accounts a ON a.id=w.account_id WHERE 1=1")
        args = []
        if platform:
            sql += " AND w.platform=?"; args.append(platform)
        if account_id:
            sql += " AND w.account_id=?"; args.append(account_id)
        if min_digg is not None:
            sql += " AND COALESCE(w.digg,0)>=?"; args.append(min_digg)
        return [dict(r) for r in con.execute(sql, args).fetchall()]
    finally:
        con.close()


def _has_emoji(s):
    for ch in s:
        o = ord(ch)
        if o >= 0x1F000 or 0x2600 <= o <= 0x27BF or 0x2B00 <= o <= 0x2BFF or o == 0xFE0F:
            return True
    return False


def _is_question(t):
    if "?" in t or "？" in t:
        return True
    return any(w in t for w in _QWORDS)


def _len_buckets(lens):
    b = {"≤10": 0, "11-20": 0, "21-30": 0, "31-50": 0, ">50": 0}
    for n in lens:
        if n <= 10:
            b["≤10"] += 1
        elif n <= 20:
            b["11-20"] += 1
        elif n <= 30:
            b["21-30"] += 1
        elif n <= 50:
            b["31-50"] += 1
        else:
            b[">50"] += 1
    return b


# ---------- 对外接口 ----------

def hit_works(platform=None, account_id=None, min_digg=None, days=30, limit=20):
    """爆款作品榜：最近 days 天发布、按点赞降序，最多 limit 条。

    返回：[ {rank, account_id, account_name, platform, platform_label,
             work_id, title, work_type, work_type_label,
             digg, comment, share, play, interact,
             publish_time, publish_dt, days_ago, url} ]
    空数据或无符合条件作品返回 []。
    """
    days = max(1, int(days))
    limit = max(1, int(limit))
    rows = _fetch_works(platform, account_id, min_digg)
    ref = date.today()
    cutoff = ref - timedelta(days=days)

    out = []
    for d in rows:
        dt = work_dt(d)
        if dt is None or dt.date() < cutoff:
            continue
        digg = d.get("digg") or 0
        com = d.get("comment") or 0
        sh = d.get("share") or 0
        wt = d.get("work_type")
        out.append({
            "account_id": d["account_id"],
            "account_name": d.get("account_name") or d["account_id"],
            "platform": d.get("platform"),
            "platform_label": PLATFORM_LABEL.get(d.get("platform"), d.get("platform") or "—"),
            "work_id": d["work_id"],
            "title": d.get("title") or "",
            "work_type": wt,
            "work_type_label": "图文" if wt == 1 else ("视频" if wt == 0 else "—"),
            "digg": digg, "comment": com, "share": sh, "play": d.get("play"),
            "interact": digg + com + sh,
            "publish_time": d.get("publish_time"),
            "publish_dt": dt.strftime("%Y-%m-%d %H:%M"),
            "days_ago": (ref - dt.date()).days,
            "url": d.get("url"),
        })
    out.sort(key=lambda x: (-x["digg"], -x["interact"]))
    out = out[:limit]
    for i, x in enumerate(out, 1):
        x["rank"] = i
    return out


def title_patterns(works):
    """对一批作品（hit_works 的返回值即可）做标题特征统计。

    返回：
      {
        "count": 有效标题数,
        "length": {"avg","min","max","buckets":{"≤10","11-20","21-30","31-50",">50"}},
        "top_words": [{"word","count"}],       # 话题标签 + 高频中文双字词
        "question_ratio": 百分数(疑问句),
        "number_ratio": 百分数(含阿拉伯数字),
        "exclamation_ratio": 百分数(含感叹号),
        "emoji_ratio": 百分数(含表情),
        "hashtag_avg": 平均话题标签数,
      }
    """
    works = works or []
    titles = [(w.get("title") or "").strip() for w in works]
    titles = [t for t in titles if t]
    n = len(titles)
    res = {
        "count": n,
        "length": {"avg": 0, "min": 0, "max": 0, "buckets": _len_buckets([])},
        "top_words": [], "question_ratio": 0.0, "number_ratio": 0.0,
        "exclamation_ratio": 0.0, "emoji_ratio": 0.0, "hashtag_avg": 0.0,
    }
    if n == 0:
        return res

    lens = [len(t) for t in titles]
    res["length"] = {"avg": round(sum(lens) / n, 1), "min": min(lens),
                     "max": max(lens), "buckets": _len_buckets(lens)}

    # 高频词：话题标签权重高，另统计中文双字词（去话题后）
    counts = {}
    for t in titles:
        for m in _HASHTAG_RE.findall(t):
            w = m.strip()
            if w:
                counts[w] = counts.get(w, 0) + 1
    bigrams = {}
    for t in titles:
        cleaned = _HASHTAG_RE.sub(" ", t)
        for run in _CJK_RE.findall(cleaned):
            for i in range(len(run) - 1):
                bg = run[i:i + 2]
                bigrams[bg] = bigrams.get(bg, 0) + 1
    for w, c in bigrams.items():
        if c >= 2 and w not in _STOP_BIGRAMS:
            counts[w] = counts.get(w, 0) + c
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:15]
    res["top_words"] = [{"word": w, "count": c} for w, c in top]

    res["question_ratio"] = round(sum(1 for t in titles if _is_question(t)) / n * 100, 1)
    res["number_ratio"] = round(sum(1 for t in titles if _DIGIT_RE.search(t)) / n * 100, 1)
    res["exclamation_ratio"] = round(sum(1 for t in titles if ("!" in t or "！" in t)) / n * 100, 1)
    res["emoji_ratio"] = round(sum(1 for t in titles if _has_emoji(t)) / n * 100, 1)
    ht = [len(_HASHTAG_RE.findall(t)) for t in titles]
    res["hashtag_avg"] = round(sum(ht) / n, 1)
    return res


def hit_timing(works):
    """发布时段 / 星期分布 vs 点赞表现。

    返回：
      {
        "count": 可解析发布时间的作品数,
        "by_hour":    {"HH时": {"count","total_digg","avg_digg"}},
        "by_weekday": {"周一": {...}, ...},
        "slots":      {"晚间 18-24": {...}, ...},
        "best_hour": {"key","avg_digg","count"}|None,
        "best_weekday": {...}|None,
        "best_slot": {...}|None,
      }
    """
    works = works or []
    pairs = []
    for w in works:
        dt = work_dt(w)
        if dt:
            pairs.append((dt, w.get("digg") or 0))
    res = {"count": len(pairs), "by_hour": {}, "by_weekday": {}, "slots": {},
           "best_hour": None, "best_weekday": None, "best_slot": None}
    if not pairs:
        return res

    def agg(keyfn, keyfmt=str):
        d = {}
        for dt, dg in pairs:
            k = keyfmt(keyfn(dt))
            e = d.setdefault(k, {"count": 0, "total_digg": 0, "avg_digg": 0.0})
            e["count"] += 1
            e["total_digg"] += dg
        for e in d.values():
            e["avg_digg"] = round(e["total_digg"] / e["count"], 1)
        return d

    def slot_of(dt):
        for name, a, b in _SLOTS:
            if a <= dt.hour < b:
                return name
        return "晚间 18-24"

    res["by_hour"] = dict(sorted(agg(lambda dt: dt.hour, lambda h: f"{h:02d}时").items()))
    res["by_weekday"] = dict(sorted(agg(lambda dt: dt.weekday(), lambda k: _WEEKDAY[k]).items()))
    res["slots"] = agg(slot_of)

    def best(d):
        if not d:
            return None
        items = sorted(d.items(), key=lambda kv: (-kv[1]["avg_digg"], -kv[1]["count"]))
        k, v = items[0]
        return {"key": k, "avg_digg": v["avg_digg"], "count": v["count"]}

    res["best_hour"] = best(res["by_hour"])
    res["best_weekday"] = best(res["by_weekday"])
    res["best_slot"] = best(res["slots"])
    return res


def rising_works(days=7, min_delta=100):
    """用 work_snapshots 找「仍在涨」的作品：窗口内点赞增量 ≥ min_delta。

    返回（按点赞增量降序）：
      [ {rank, account_id, account_name, platform, work_id, title,
         digg_start, digg_end, delta_digg, delta_comment, delta_share,
         growth_rate_pct, snap_from, snap_to, days, url} ]
    work_snapshots 为空返回 []。
    """
    days = max(1, int(days))
    min_delta = int(min_delta)
    con = db.connect()
    try:
        maxd = con.execute("SELECT MAX(snap_date) m FROM work_snapshots").fetchone()["m"]
        if not maxd:
            return []
        end_d = parse_date(maxd) or date.today()
        start_d = end_d - timedelta(days=days - 1)
        rows = [dict(r) for r in con.execute(
            "SELECT account_id, work_id, snap_date, digg, comment, share, play "
            "FROM work_snapshots WHERE snap_date>=? AND snap_date<=? "
            "ORDER BY account_id, work_id, snap_date",
            (date_str(start_d), date_str(end_d))).fetchall()]
        if not rows:
            return []

        groups = {}
        for r in rows:
            groups.setdefault((r["account_id"], r["work_id"]), []).append(r)

        out = []
        for (aid, wid), lst in groups.items():
            first, last = lst[0], lst[-1]
            d0 = first.get("digg") or 0
            d1 = last.get("digg") or 0
            delta = d1 - d0
            if delta < min_delta:
                continue
            meta = con.execute(
                "SELECT w.title, w.platform, w.url, w.publish_time, a.name AS account_name "
                "FROM works w LEFT JOIN accounts a ON a.id=w.account_id "
                "WHERE w.account_id=? AND w.work_id=?", (aid, wid)).fetchone()
            meta = dict(meta) if meta else {}
            out.append({
                "account_id": aid,
                "account_name": meta.get("account_name") or aid,
                "platform": meta.get("platform"),
                "work_id": wid,
                "title": meta.get("title") or "",
                "digg_start": d0,
                "digg_end": d1,
                "delta_digg": delta,
                "delta_comment": (last.get("comment") or 0) - (first.get("comment") or 0),
                "delta_share": (last.get("share") or 0) - (first.get("share") or 0),
                "growth_rate_pct": round(delta / d0 * 100, 1) if d0 > 0 else None,
                "snap_from": first["snap_date"],
                "snap_to": last["snap_date"],
                "days": days,
                "url": meta.get("url"),
            })
        out.sort(key=lambda x: -x["delta_digg"])
        for i, x in enumerate(out, 1):
            x["rank"] = i
        return out
    finally:
        con.close()


# ---------- 命令行 ----------

def _print_hits(days):
    ws = hit_works(days=days, limit=15)
    print("=" * 90)
    print(f"爆款作品 TOP15（最近 {days} 天发布，按点赞降序）")
    print("=" * 90)
    if not ws:
        print(f"最近 {days} 天内无已发布作品（或作品发布时间无法解析）。")
    else:
        headers = ["排名", "账号", "平台", "标题", "点赞", "评论", "分享", "发布时间"]
        table = [[w["rank"], w["account_name"], w["platform_label"],
                  (w["title"][:22] + "…" if len(w["title"]) > 22 else w["title"]),
                  fmt_num(w["digg"]), fmt_num(w["comment"]), fmt_num(w["share"]),
                  w["publish_dt"]] for w in ws]
        print(render_table(headers, table,
                           aligns=["right", "left", "left", "left", "right", "right", "right", "left"]))

    tp = title_patterns(ws)
    print()
    print("-" * 90)
    print(f"标题特征（样本 {tp['count']} 条）")
    print("-" * 90)
    if tp["count"] == 0:
        print("无样本。")
    else:
        L = tp["length"]
        print(f"长度：平均 {L['avg']} 字，最短 {L['min']}，最长 {L['max']}；分布 " +
              "，".join(f"{k}={v}" for k, v in L["buckets"].items()))
        words = "，".join(f"{w['word']}({w['count']})" for w in tp["top_words"]) or "—"
        print(f"高频词：{words}")
        print(f"疑问句 {tp['question_ratio']}% ｜ 含数字 {tp['number_ratio']}% ｜ "
              f"含感叹号 {tp['exclamation_ratio']}% ｜ 含表情 {tp['emoji_ratio']}% ｜ "
              f"平均话题标签 {tp['hashtag_avg']} 个")

    tt = hit_timing(ws)
    print()
    print("-" * 90)
    print(f"发布时机（可解析时间 {tt['count']} 条）")
    print("-" * 90)
    if tt["count"] == 0:
        print("无样本。")
    else:
        rows = [[k, v["count"], fmt_num(v["total_digg"]), v["avg_digg"]] for k, v in tt["slots"].items()]
        print("时段表现：")
        print(render_table(["时段", "条数", "总点赞", "平均点赞"], rows,
                           aligns=["left", "right", "right", "right"]))
        print("星期表现：")
        rows = [[k, v["count"], fmt_num(v["total_digg"]), v["avg_digg"]] for k, v in tt["by_weekday"].items()]
        print(render_table(["星期", "条数", "总点赞", "平均点赞"], rows,
                           aligns=["left", "right", "right", "right"]))
        for label, key in (("最佳时段", "best_slot"), ("最佳星期", "best_weekday"), ("最佳小时", "best_hour")):
            b = tt[key]
            print(f"{label}：" + (f"{b['key']}（平均 {b['avg_digg']} 赞 / {b['count']} 条）" if b else "—"))


def _print_rising(days):
    rs = rising_works(days=days, min_delta=100)
    print()
    print("=" * 90)
    print(f"仍在涨的作品（最近 {days} 天点赞增量 ≥ 100）")
    print("=" * 90)
    if not rs:
        print("work_snapshots 为空或无达标作品（首次采集后需至少两次快照才可计算增量）。")
        return
    headers = ["排名", "账号", "标题", "起量点赞", "当前点赞", "增量", "增量率", "窗口"]
    table = [[r["rank"], r["account_name"],
              (r["title"][:24] + "…" if len(r["title"]) > 24 else r["title"]),
              fmt_num(r["digg_start"]), fmt_num(r["digg_end"]), fmt_delta(r["delta_digg"]),
              (f"+{r['growth_rate_pct']}%" if r["growth_rate_pct"] is not None else "—"),
              f"{r['snap_from']}~{r['snap_to']}"] for r in rs]
    print(render_table(headers, table,
                       aligns=["right", "left", "left", "right", "right", "right", "right", "left"]))


if __name__ == "__main__":
    _days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    _print_hits(_days)
    _print_rising(min(_days, 7) if _days > 0 else 7)
