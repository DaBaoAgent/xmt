"""周报生成器：汇总增长 / 爆款 / 对标分析，产出中文 markdown 周报并入库。

流程：
  1) 调 analytics.growth / .hits / .bench 取数
  2) 拼装中文 markdown
  3) 写文件 out/weekly_report.md
  4) db.save_insight(kind='growth_report') 落到 insights 表

对外接口：
  build_weekly_report(days=7) -> str  # 返回 markdown 正文（同时写文件 + 入库）

命令行：
  python report.py [days]
"""
import os
import sys
from datetime import datetime

import db
from analytics import (PLATFORM_LABEL, fmt_num, fmt_delta, fmt_pct, fmt_ratio,
                       today_str)
from analytics import growth, hits, bench

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "weekly_report.md")


# ---------- markdown 小工具 ----------

def _cell(v):
    """表格单元格安全化：去掉竖线/换行。"""
    if v is None:
        return "—"
    return str(v).replace("|", "｜").replace("\n", " ").replace("\r", " ")


def _md_table(headers, rows):
    lines = ["| " + " | ".join(str(h) for h in headers) + " |",
             "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(_cell(c) for c in r) + " |")
    return "\n".join(lines)


# ---------- 正文构建 ----------

def _build_md(days):
    """拼装完整周报 markdown。"""
    gr = growth.account_growth(days=days)          # 总览（全部自有）
    ranking = growth.growth_ranking(days=days)     # 涨粉榜
    hw = hits.hit_works(days=days, limit=20)       # 爆款榜
    tp = hits.title_patterns(hw)                   # 标题特征
    tt = hits.hit_timing(hw)                       # 发布时机
    rs = hits.rising_works(days=min(days, 7), min_delta=100)  # 仍在涨
    bt = bench.bench_table()                       # 对标表
    gs = bench.gap_summary()                       # 差距摘要

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    L = []
    L.append(f"# 佳康顺新媒体矩阵周报（最近 {days} 天）")
    L.append("")
    L.append(f"- 生成时间：{now}")
    L.append(f"- 数据窗口：{gr['start_date'] or '—'} ~ {gr['end_date'] or '—'}")
    L.append(f"- 覆盖账号：自有 {gs['own']['accounts']} 个 / 对标 {gs['rival']['accounts']} 个")
    L.append("")

    # 一、总览
    L.append("## 一、总览（自有账号合计）")
    L.append("")
    L.append("| 指标 | 期初 | 期末 | 本期变化 | 日均 | 环比 |")
    L.append("|---|---|---|---|---|---|")
    for m, label in (("followers", "粉丝"), ("total_likes", "获赞"), ("works_count", "作品数")):
        b = gr["total"][m]
        L.append(f"| {label} | {fmt_num(b['start'])} | {fmt_num(b['end'])} | "
                 f"{fmt_delta(b['delta'])} | {fmt_num(round(b['daily_avg'], 1)) if b['daily_avg'] is not None else '—'} | "
                 f"{fmt_pct(b['mom_pct'])} |")
    L.append("")
    if not gr["accounts"]:
        L.append("> 暂无快照数据（account_snapshots 为空），请先运行采集。")
        L.append("")

    # 二、账号涨粉榜
    L.append("## 二、账号涨粉榜")
    L.append("")
    if not ranking:
        L.append("_暂无快照数据。_")
    else:
        rows = []
        for r in ranking:
            rows.append([
                r["rank"], r["name"], PLATFORM_LABEL.get(r["platform"], r["platform"] or "—"),
                fmt_delta(r["followers_delta"]), fmt_num(r["followers_end"]),
                fmt_num(round(r["daily_avg"], 1)) if r["daily_avg"] is not None else "—",
                fmt_delta(r["likes_delta"]), fmt_delta(r["works_delta"]),
            ])
        L.append(_md_table(["排名", "账号", "平台", "涨粉", "期末粉丝", "日均涨粉", "涨赞", "新增作品"], rows))
    L.append("")

    # 三、增长明细
    L.append("## 三、增长明细（逐账号）")
    L.append("")
    if not gr["accounts"]:
        L.append("_暂无快照数据。_")
    else:
        rows = []
        for a in gr["accounts"]:
            f = a["metrics"]["followers"]
            l = a["metrics"]["total_likes"]
            w = a["metrics"]["works_count"]
            rows.append([
                a["name"], PLATFORM_LABEL.get(a["platform"], a["platform"] or "—"),
                fmt_num(f["start"]), fmt_num(f["end"]), fmt_delta(f["delta"]),
                fmt_delta(l["delta"]), fmt_delta(w["delta"]),
                f"{a['period']['start']}~{a['period']['end']}",
            ])
        L.append(_md_table(["账号", "平台", "期初粉丝", "期末粉丝", "粉丝变化", "获赞变化", "作品变化", "窗口"], rows))
    L.append("")

    # 四、爆款作品榜
    L.append(f"## 四、爆款作品 TOP{len(hw)}")
    L.append("")
    if not hw:
        L.append(f"_最近 {days} 天内无已发布作品（或发布时间无法解析）。_")
    else:
        rows = []
        for w in hw:
            title = w["title"]
            title = (title[:40] + "…") if len(title) > 40 else title
            rows.append([
                w["rank"], w["account_name"], w["platform_label"],
                w["work_type_label"], _cell(title),
                fmt_num(w["digg"]), fmt_num(w["comment"]), fmt_num(w["share"]),
                w["publish_dt"],
            ])
        L.append(_md_table(["排名", "账号", "平台", "类型", "标题", "点赞", "评论", "分享", "发布时间"], rows))
    L.append("")

    # 五、标题特征
    L.append("## 五、标题特征（爆款样本）")
    L.append("")
    if tp["count"] == 0:
        L.append("_无样本。_")
    else:
        Lb = tp["length"]
        L.append(f"- 样本量：{tp['count']} 条")
        L.append(f"- 标题长度：平均 {Lb['avg']} 字，最短 {Lb['min']}，最长 {Lb['max']}；"
                 f"分布 " + "、".join(f"{k} {v} 条" for k, v in Lb["buckets"].items()))
        words = "、".join(f"{w['word']}({w['count']})" for w in tp["top_words"]) or "—"
        L.append(f"- 高频词：{words}")
        L.append(f"- 疑问句占比 {tp['question_ratio']}%，含数字 {tp['number_ratio']}%，"
                 f"含感叹号 {tp['exclamation_ratio']}%，含表情 {tp['emoji_ratio']}%，"
                 f"平均话题标签 {tp['hashtag_avg']} 个")
    L.append("")

    # 六、发布时机
    L.append("## 六、发布时机")
    L.append("")
    if tt["count"] == 0:
        L.append("_无样本。_")
    else:
        rows = [[k, v["count"], fmt_num(v["total_digg"]), v["avg_digg"]] for k, v in tt["slots"].items()]
        L.append("**按时段：**")
        L.append("")
        L.append(_md_table(["时段", "条数", "总点赞", "平均点赞"], rows))
        L.append("")
        rows = [[k, v["count"], fmt_num(v["total_digg"]), v["avg_digg"]] for k, v in tt["by_weekday"].items()]
        L.append("**按星期：**")
        L.append("")
        L.append(_md_table(["星期", "条数", "总点赞", "平均点赞"], rows))
        L.append("")
        b = tt["best_slot"]
        bd = tt["best_weekday"]
        bh = tt["best_hour"]
        L.append("**结论：**")
        L.append(f"- 最容易爆的时段：{b['key']}（平均 {b['avg_digg']} 赞 / {b['count']} 条）" if b else "- 最容易爆的时段：—")
        L.append(f"- 最容易爆的星期：{bd['key']}（平均 {bd['avg_digg']} 赞 / {bd['count']} 条）" if bd else "- 最容易爆的星期：—")
        L.append(f"- 单点最佳小时：{bh['key']}（平均 {bh['avg_digg']} 赞 / {bh['count']} 条）" if bh else "- 单点最佳小时：—")
    L.append("")

    # 七、仍在涨
    L.append("## 七、仍在涨的作品（上升中）")
    L.append("")
    if not rs:
        L.append("_work_snapshots 为空或无达标作品（需至少两次快照才可算增量）。_")
    else:
        rows = []
        for r in rs:
            title = r["title"]
            title = (title[:40] + "…") if len(title) > 40 else title
            rows.append([
                r["rank"], r["account_name"], _cell(title),
                fmt_num(r["digg_start"]), fmt_num(r["digg_end"]), fmt_delta(r["delta_digg"]),
                (f"+{r['growth_rate_pct']}%" if r["growth_rate_pct"] is not None else "—"),
                f"{r['snap_from']}~{r['snap_to']}",
            ])
        L.append(_md_table(["排名", "账号", "标题", "起量点赞", "当前点赞", "增量", "增量率", "窗口"], rows))
    L.append("")

    # 八、对标差距
    L.append("## 八、对标差距")
    L.append("")
    if not bt:
        L.append("_accounts 表为空。_")
    else:
        rows = []
        for r in bt:
            rows.append([
                r["name"], r["kind_label"], r["platform_label"],
                fmt_num(r["followers"]), fmt_num(r["works_count"]),
                fmt_ratio(r["avg_digg"], 1), fmt_ratio(r["avg_interact"], 1),
                fmt_ratio(r["freq_weekly"], 2), fmt_ratio(r["engagement_rate"], 3),
            ])
        L.append(_md_table(["账号", "类型", "平台", "粉丝", "作品数", "平均点赞",
                            "平均互动", "周更条数", "互动效率%"], rows))
    L.append("")
    if gs["gaps"]:
        rows = [[g["metric"],
                 fmt_num(g["own"]) if isinstance(g["own"], (int, float)) else "—",
                 fmt_num(g["rival"]) if isinstance(g["rival"], (int, float)) else "—",
                 (f"{g['ratio']}x" if g["ratio"] is not None else "—"),
                 g["verdict"]] for g in gs["gaps"]]
        L.append(_md_table(["指标", "自有", "对标", "自有/对标", "判定"], rows))
        L.append("")

    # 九、行动建议
    L.append("## 九、行动建议")
    L.append("")
    if gs["conclusions"]:
        for i, c in enumerate(gs["conclusions"], 1):
            L.append(f"{i}. {c}")
    if tt["count"] and tt["best_slot"]:
        L.append(f"{len(gs['conclusions']) + 1}. 排期优先命中高表现时段（{tt['best_slot']['key']}），"
                 f"并按「{_hot_theme(tp)}」方向出脚本。")
    L.append("")
    L.append("---")
    L.append(f"_本报告由 xmt 分析层自动生成于 {now}，数据源 data/xmt.db。_")
    return "\n".join(L)


def _hot_theme(tp):
    """从高频词里挑 3 个作为选题方向提示。"""
    words = [w["word"] for w in tp.get("top_words", [])][:3]
    return " / ".join(words) if words else "高互动题材"


# ---------- 对外接口 ----------

def build_weekly_report(days=7):
    """生成周报：返回 markdown 正文（写文件 + 落 insights 表）。

    - 文件：out/weekly_report.md
    - 入库：insights(kind='growth_report', scope='all')
    """
    days = max(1, int(days))
    md = _build_md(days)

    # 1) 写文件
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(md)

    # 2) 写入洞察表
    title = f"周报 {today_str()}（最近 {days} 天）"
    con = db.connect()
    try:
        db.save_insight(con, "growth_report", "all", title, md,
                        {"days": days, "out_path": OUT})
        con.commit()
    finally:
        con.close()

    return md


if __name__ == "__main__":
    _days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    _md = build_weekly_report(_days)
    print(_md)
    print()
    print("=" * 60)
    print("已写入：", OUT)
    print("已入库：insights(kind='growth_report')")
