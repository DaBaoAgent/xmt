"""对标账号发现：从 search_hits（关键词搜索到的作品）里反推「值得盯的对标号」。

背景：`config/rivals.json` 里的对标账号需要人工填 url / xhs_id，否则对标对比一直是空的。
但 `collectors/rival.py --search` 已经按监控关键词抓回了大量外部作品（含作者名与作者 ID），
这些正是天然的候选对标池 —— 本模块按「上榜次数 × 点赞表现」给作者打分排序，
产出可直接写进 rivals.json 的条目。

用法：
    python -m analytics.discover                          # 列出候选（全部平台）
    python -m analytics.discover --platform xiaohongshu --top 10
    python -m analytics.discover --write                  # 追加写入 config/rivals.json（不覆盖已有条目）
"""
import os
import json
import argparse
from collections import defaultdict
from datetime import datetime

import db
from analytics import clean_title

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIVALS_JSON = os.path.join(HERE, "config", "rivals.json")


def _fmt(n):
    if n is None:
        return "—"
    if isinstance(n, float) and n == int(n):
        n = int(n)
    return f"{n:,}"


def discover(platform=None, top=10, days=30, min_hits=1):
    """按作者聚合搜索命中，返回候选对标账号（按表现分降序）。

    表现分 = 最高赞 × 0.6 + 平均赞 × 0.4，再按上榜次数加权（多次上榜说明该号稳定出爆款）。
    """
    con = db.connect()
    sql = """SELECT * FROM search_hits
             WHERE snap_date >= date('now', ?)"""
    args = [f"-{days} day"]
    if platform:
        sql += " AND platform = ?"
        args.append(platform)
    rows = [dict(r) for r in con.execute(sql, args).fetchall()]
    con.close()

    agg = defaultdict(lambda: {"hits": 0, "diggs": [], "keywords": set(),
                               "titles": [], "urls": [], "platform": None})
    for r in rows:
        name = (r.get("author_name") or "").strip()
        if not name:
            continue
        key = (r["platform"], name)
        a = agg[key]
        a["platform"] = r["platform"]
        a["hits"] += 1
        a["diggs"].append(r.get("digg") or 0)
        a["keywords"].add(r.get("keyword") or "")
        if r.get("title"):
            a["titles"].append(clean_title(r["title"]) or r["title"])
        if r.get("url"):
            a["urls"].append(r["url"])

    out = []
    for (plat, name), a in agg.items():
        if a["hits"] < min_hits:
            continue
        max_d = max(a["diggs"]) if a["diggs"] else 0
        avg_d = sum(a["diggs"]) / len(a["diggs"]) if a["diggs"] else 0
        score = round(max_d * 0.6 + avg_d * 0.4, 1) * (1 + 0.1 * (a["hits"] - 1))
        out.append({
            "platform": plat,
            "name": name,
            "hits": a["hits"],
            "max_digg": max_d,
            "avg_digg": round(avg_d, 1),
            "score": round(score, 1),
            "keywords": sorted(a["keywords"])[:5],
            "sample_titles": a["titles"][:3],
            "sample_urls": a["urls"][:2],
        })
    return sorted(out, key=lambda x: -x["score"])[:top]


def to_rival_entry(cand, idx=None):
    """候选 → rivals.json 条目骨架。缺 url / xhs_id 时留空并写明待补。"""
    plat = cand["platform"]
    pid = f"rival_{plat[:3]}_{abs(hash(cand['name'])) % 10000:04d}"
    entry = {
        "id": pid,
        "owner": "待补",
        "name": cand["name"],
        "platform": plat,
        "role": f"关键词上榜 {cand['hits']} 次 · 最高 {cand['max_digg']} 赞",
        "note": "由 analytics/discover 从关键词搜索命中反推；补上 "
                + ("url" if plat == "douyin" else "xhs_id") + " 后即参与对标采集",
    }
    if plat == "douyin":
        entry["url"] = ""
    else:
        entry["xhs_id"] = ""
    return entry


def write_rivals(cands, dry=False):
    """追加写入 config/rivals.json，保留已有条目（按 name+platform 去重）。"""
    if not os.path.exists(RIVALS_JSON):
        data = {"_comment": "对标账号 + 监控关键词", "rivals": [], "keywords": {}}
    else:
        with open(RIVALS_JSON, encoding="utf-8") as f:
            data = json.load(f)
    existing = {(r.get("name"), r.get("platform")) for r in (data.get("rivals") or [])}
    added = []
    for c in cands:
        if (c["name"], c["platform"]) in existing:
            continue
        # 示例占位条目（名字里带"示例"）在首次真实写入时清掉
        data["rivals"] = [r for r in (data.get("rivals") or [])
                          if "示例" not in (r.get("name") or "")]
        entry = to_rival_entry(c)
        data.setdefault("rivals", []).append(entry)
        existing.add((c["name"], c["platform"]))
        added.append(entry)
    if dry:
        return added
    with open(RIVALS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return added


def report(cands):
    if not cands:
        print("没有候选：先跑 collectors.rival --search 抓关键词作品，本模块再从命中里挑号。")
        return
    print("=" * 96)
    print("对标账号候选（从关键词搜索命中反推，按表现分排序）")
    print("=" * 96)
    print(f"{'排名':<5}{'平台':<12}{'账号':<22}{'上榜':<6}{'最高赞':<9}{'平均赞':<9}{'表现分':<9}命中关键词")
    print("-" * 96)
    for i, c in enumerate(cands, 1):
        print(f"{i:<5}{c['platform']:<12}{c['name'][:20]:<22}{c['hits']:<6}"
              f"{_fmt(c['max_digg']):<9}{_fmt(c['avg_digg']):<9}{c['score']:<9}"
              f"{'/'.join(c['keywords'][:3])}")
        for t in c["sample_titles"][:1]:
            print(f"     └ 代表作：{t[:60]}")
    print("-" * 96)
    print("提示：确认要盯的号后，用 --write 追加进 config/rivals.json，再补上 "
          "url（抖音）或 xhs_id（小红书）即可参与对标采集。")


def _classify_safe(title):
    """复用 insight.direction 的题材分类器；不可用时退化为返回前 8 字。
    分类前先清洗（抖音标题常是整段文案，话题标签会污染题材判断）。"""
    t = clean_title(title) or (title or "")
    try:
        from insight.direction import _classify
        return _classify(t)
    except Exception:
        return (t or "未分类")[:8]


def content_gap(days=30, top=6):
    """对标爆款题材 vs 自有内容题材的差异分析。

    这是「下一步拍什么」的直接依据：如果外部爆款集中在 A 题材，
    而自家内容全在 B 题材，说明不是产品不行，是选题视角跑偏了。
    """
    con = db.connect()
    hits = [dict(r) for r in con.execute(
        """SELECT title, digg FROM search_hits
           WHERE snap_date >= date('now', ?) AND title IS NOT NULL AND title != ''""",
        (f"-{days} day",)).fetchall()]
    own = [dict(r) for r in con.execute(
        """SELECT w.title, w.digg FROM works w
           JOIN accounts a ON a.id = w.account_id
           WHERE a.kind = 'own' AND w.title IS NOT NULL AND w.title != ''
             AND w.publish_ts >= strftime('%s','now') - ?""",
        (days * 86400,)).fetchall()]
    con.close()

    def stat(rows):
        agg = defaultdict(lambda: {"count": 0, "max_digg": 0, "examples": []})
        for r in rows:
            c = _classify_safe(r["title"])
            agg[c]["count"] += 1
            d = r.get("digg") or 0
            if d > agg[c]["max_digg"]:
                agg[c]["max_digg"] = d
            if len(agg[c]["examples"]) < 2:
                agg[c]["examples"].append(clean_title(r["title"]) or r["title"])
        rows_out = [{"topic": k, "count": v["count"], "max_digg": v["max_digg"],
                     "examples": v["examples"]} for k, v in agg.items()]
        return sorted(rows_out, key=lambda x: (-x["max_digg"], -x["count"]))

    return {
        "rival_topics": stat(hits)[:top],
        "own_topics": stat(own)[:top],
        "rival_count": len(hits),
        "own_count": len(own),
        "rival_titles": [t for t in (clean_title(r["title"]) for r in hits) if t],
        "own_titles": [t for t in (clean_title(r["title"]) for r in own) if t],
    }


PERSON_WORDS = ["大爷", "阿姨", "奶奶", "爷爷", "女友", "老婆", "老公", "年轻人", "男生", "女生",
                "我妈", "我爸", "老人", "长辈", "孕妇", "同事", "闺蜜", "一家人", "小孩", "宝宝"]
SCENE_WORDS = ["山姆", "超市", "公园", "地铁", "通勤", "旅行", "citywalk", "逛街", "菜市场",
               "医院", "机场", "火车站", "景区", "商场", "马路", "小区", "电梯", "马路牙"]
SELL_WORDS = ["推荐", "选购", "必备", "指南", "型号", "参数", "新款", "优惠", "包邮", "现货",
              "厂家", "批发", "直供", "正品", "特价", "下单"]


def _hit_rate(rows, words):
    """rows 可以是 dict 列表或纯标题字符串列表。"""
    n = len(rows)
    if not n:
        return 0.0
    hit = 0
    for r in rows:
        t = r if isinstance(r, str) else (r.get("title") or "")
        if any(w in t for w in words):
            hit += 1
    return round(hit * 100.0 / n, 1)


def report_gap(gap, rival_titles=None, own_titles=None):
    if rival_titles is None:
        rival_titles = gap.get("rival_titles")
    if own_titles is None:
        own_titles = gap.get("own_titles")
    print("=" * 96)
    print("题材差距：外部爆款 vs 自有内容（近 30 天）")
    print("=" * 96)
    print(f"\n【外部对标爆款】样本 {gap['rival_count']} 条")
    if not gap["rival_topics"]:
        print("  无数据：先跑 collectors.rival --search")
    for t in gap["rival_topics"]:
        print(f"  · {t['topic']}：{t['count']} 条，最高 {_fmt(t['max_digg'])} 赞")
        for e in t["examples"][:1]:
            print(f"      例：{e[:52]}")
    print(f"\n【自有内容】样本 {gap['own_count']} 条")
    for t in gap["own_topics"]:
        print(f"  · {t['topic']}：{t['count']} 条，最高 {_fmt(t['max_digg'])} 赞")

    if rival_titles is not None and own_titles is not None:
        print("\n" + "=" * 96)
        print("标题写法对比（这才是可执行的部分）")
        print("=" * 96)
        print(f"{'特征':<18}{'外部爆款':<14}{'自有内容':<14}差距")
        print("-" * 96)
        for label, words in (("人称/角色词", PERSON_WORDS), ("生活场景词", SCENE_WORDS),
                             ("卖点/促销词", SELL_WORDS)):
            r = _hit_rate(rival_titles, words)
            o = _hit_rate(own_titles, words)
            d = f"{'+' if r - o >= 0 else ''}{round(r - o, 1)} 个百分点"
            print(f"{label:<18}{str(r) + '%':<14}{str(o) + '%':<14}{d}")
        print("-" * 96)

    print("-" * 96)
    rt = {t["topic"] for t in gap["rival_topics"]}
    ot = {t["topic"] for t in gap["own_topics"]}
    only_rival = rt - ot
    if only_rival:
        print(f"结论：外部跑得动但自家没做的题材 → {'、'.join(sorted(only_rival))}")
        print("      这些是可以直接排产的选题方向（对标已验证过有流量）。")
        return
    print("结论：题材覆盖基本重合。")

    if rival_titles and own_titles:
        rp, op = _hit_rate(rival_titles, PERSON_WORDS), _hit_rate(own_titles, PERSON_WORDS)
        rsc, osc = _hit_rate(rival_titles, SCENE_WORDS), _hit_rate(own_titles, SCENE_WORDS)
        rsel, osel = _hit_rate(rival_titles, SELL_WORDS), _hit_rate(own_titles, SELL_WORDS)
        if rp - op >= 8:
            print(f"      关键差异在「人称/角色词」：外部 {rp}% vs 自有 {op}%"
                  f"（差 {round(rp - op, 1)} 个百分点）。")
            print("      外部爆款习惯把「人」放在标题与画面最前（大爷 / 女友 / 年轻人 / 一家人），")
            print("      自家内容更偏产品与功能描述 —— 这正是 A 线全实拍要解决的问题：")
            print("      → 让真人、真实使用者出镜当主角，产品只做配角（一物一故事）。")
        elif abs(rp - op) <= 8 and abs(rsc - osc) <= 8:
            print("      标题写法也接近（人称/场景词命中率相差不到 8 个百分点），")
            print("      所以卡点不在「标题怎么写」，在「内容形态」：")
            print("      外部爆款是真人出镜 + 生活叙事/人物反差（citywalk、逛超市、当事人吐槽），")
            print("      自家内容以产品展示与参数说明为主 —— 缺人物、缺情节、缺情绪。")
            print("      → 建议整改方向：一物一故事，让真人/使用者成为画面主角，产品只做配角。")
        elif osel > rsel + 8:
            print(f"      且自家标题里卖点/促销词占比明显更高（{osel}% vs 外部 {rsel}%），")
            print("      → 建议去掉「推荐/必备/厂家直供」这类叫卖词，换成人物与场景开头。")
        else:
            print("      差距集中在表达方式与钩子上，需逐条对比高赞与低赞作品的开头三秒。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", help="douyin / xiaohongshu")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--min-hits", type=int, default=1, help="至少上榜几次才算候选")
    ap.add_argument("--write", action="store_true", help="追加写入 config/rivals.json")
    ap.add_argument("--dry-run", action="store_true", help="配合 --write：只打印将写入的内容")
    ap.add_argument("--gap", action="store_true", help="只做题材差距分析")
    args = ap.parse_args()

    if args.gap:
        report_gap(content_gap(days=args.days))
        return

    cands = discover(platform=args.platform, top=args.top, days=args.days,
                     min_hits=args.min_hits)
    report(cands)
    report_gap(content_gap(days=args.days))
    if args.write:
        added = write_rivals(cands, dry=args.dry_run)
        verb = "将追加" if args.dry_run else "已追加"
        print(f"\n{verb} {len(added)} 个对标账号到 {RIVALS_JSON}")
        for a in added:
            print(f"  · {a['name']}（{a['platform']}）")


if __name__ == "__main__":
    main()
