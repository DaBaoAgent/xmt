"""下一步拍摄方向：复盘近 N 天的账号与作品数据，给出可执行的拍摄方向。

产物：
  1) 落库 insights 表（kind='direction'）；
  2) 写 D:\\@kaifa\\xmt\\out\\next_direction.md（utf-8）。
用法：
    python -m insight.direction --days 7                # 有 key 走 LLM 辅助出方向，无 key 走规则版
    python -m insight.direction --days 14 --no-llm
    python -m insight.direction --days 7 --out out/next_direction.md
"""

import os
import re
import sys
import json
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import db                      # noqa: E402
from insight import llm        # noqa: E402

PLATFORM_LABEL = {"douyin": "抖音", "xiaohongshu": "小红书", "channels": "视频号"}
DEFAULT_OUT = os.path.join(ROOT, "out", "next_direction.md")

# 题材分类规则（标题命中即归入该类，顺序即优先级）
CATEGORIES = [
    ("骨折康复代步", ["骨折", "康复", "脚伤", "扭伤", "术后", "恢复期", "拄拐"]),
    ("陪长辈出行", ["陪", "爸妈", "老人", "奶奶", "长辈", "遛弯", "散步", "公园"]),
    ("轻便折叠收纳", ["折叠", "轻便", "便携", "后备箱", "收纳", "重量", "提着"]),
    ("参数选购指南", ["参数", "怎么选", "避坑", "尺寸", "承重", "对比", "指南"]),
    ("租赁短期用车", ["租赁", "出租", "短租", "押金", "短期"]),
    ("居家照护护理床", ["护理床", "照护", "卧床", "翻身", "护理"]),
    ("安全刹车路面", ["刹车", "坡", "防滑", "雨", "越障", "减速带", "颠", "稳"]),
    ("资质与实体店", ["备案", "资质", "工厂", "实体店", "体验", "老博会", "展"]),
    ("情绪与心愿内容", ["心愿", "看风景", "相守", "浪漫", "慢慢", "一起"]),
]

_DY_SYS = ("你是短视频内容运营顾问，服务佳康顺（昆山，电动轮椅/助行器/护理床等康复辅具厂商）"
           "抖音 + 小红书账号矩阵。你只根据给出的真实数据下判断，不编造数据。"
           "合规：不承诺疗效、不做医疗诊断表述，禁用治疗/治愈/疗效/最/第一/绝对。")


# ==================== 一、数据复盘 ====================

def _rows(con, sql, args=()):
    return [dict(r) for r in con.execute(sql, args).fetchall()]


def _classify(title):
    t = title or ""
    for name, keys in CATEGORIES:
        if any(k in t for k in keys):
            return name
    return "其它日常内容"


def _clean_title(title, limit=34):
    """作品标题清理：去掉尾部 #话题、折叠空白，便于表格阅读。"""
    s = re.sub(r"\s+", " ", (title or "").replace("\n", " ")).strip()
    i = s.find(" #")
    if i >= 6:
        s = s[:i]
    s = s.strip(" ，。、-—")
    return s if len(s) <= limit else s[:limit] + "…"


def collect_metrics(days=7):
    """汇总近 N 天数据：账号涨粉、发布节奏、题材效果、选题池、热点。"""
    days = max(1, int(days))
    today = datetime.now().date()
    start = today - timedelta(days=days - 1)
    start_s, today_s = start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
    start_ts = int(datetime.combine(start, datetime.min.time()).timestamp())

    con = db.connect()
    own = db.get_accounts(kind="own")
    own_ids = [a["id"] for a in own]

    # 1) 账号涨粉（窗口内首末快照）
    snaps = _rows(con, """
        SELECT account_id, snap_date, followers, total_likes, works_count
        FROM account_snapshots WHERE snap_date>=? AND snap_date<=?
        ORDER BY account_id, snap_date""", (start_s, today_s))
    by_acct = {}
    for s in snaps:
        by_acct.setdefault(s["account_id"], []).append(s)
    account_stats = []
    for a in own:
        lst = by_acct.get(a["id"]) or []
        row = {"账号id": a["id"], "账号": a["name"], "平台": PLATFORM_LABEL.get(a["platform"], a["platform"]),
               "定位": a["role"], "快照数": len(lst), "粉丝": None, "粉丝净增": None,
               "总获赞": None, "作品数": None, "新增作品": None}
        if lst:
            first, last = lst[0], lst[-1]
            if last["followers"] is not None and first["followers"] is not None:
                row["粉丝"] = last["followers"]
                row["粉丝净增"] = last["followers"] - first["followers"]
            row["总获赞"] = last["total_likes"]
            if last["works_count"] is not None and first["works_count"] is not None:
                row["作品数"] = last["works_count"]
                row["新增作品"] = last["works_count"] - first["works_count"]
        account_stats.append(row)

    # 2) 窗口内作品（窗口内没有作品时，回退到更大的素材窗口，保证复盘仍有料）
    qs = ",".join("?" * len(own_ids)) if own_ids else "''"
    win_start_ts = start_ts
    works = _rows(con, f"""
        SELECT w.account_id, a.name AS 账号, a.platform, a.role, w.title, w.work_type,
               w.publish_ts, w.publish_time, w.digg, w.comment, w.share
        FROM works w LEFT JOIN accounts a ON a.id = w.account_id
        WHERE w.publish_ts>=? AND w.account_id IN ({qs})
        ORDER BY w.publish_ts DESC""", (win_start_ts, *own_ids))
    fallback_note = ""
    if not works and own_ids:
        wide = min(max(days * 4, 30), 90)
        wide_start = today - timedelta(days=wide - 1)
        win_start_ts = int(datetime.combine(wide_start, datetime.min.time()).timestamp())
        works = _rows(con, f"""
            SELECT w.account_id, a.name AS 账号, a.platform, a.role, w.title, w.work_type,
                   w.publish_ts, w.publish_time, w.digg, w.comment, w.share
            FROM works w LEFT JOIN accounts a ON a.id = w.account_id
            WHERE w.publish_ts>=? AND w.account_id IN ({qs})
            ORDER BY w.publish_ts DESC""", (win_start_ts, *own_ids))
        if works:
            fallback_note = (f"近 {days} 天没有新发布作品，题材统计已回退到 "
                             f"{wide_start.strftime('%Y-%m-%d')} ~ {today_s}（{wide} 天）")
        else:
            fallback_note = "作品库在近 90 天内没有可用作品，题材规律无法判断（先跑一次采集）"
    for w in works:
        w["题材"] = _classify(w.get("title"))
        w["标题精简"] = _clean_title(w.get("title"))

    # 3) 发布节奏（按天）
    per_day = {}
    for w in works:
        d = (w.get("publish_time") or "")[:10]
        per_day[d] = per_day.get(d, 0) + 1
    work_window = (f"{datetime.fromtimestamp(win_start_ts).strftime('%Y-%m-%d')} ~ {today_s}"
                   f"（{(today - datetime.fromtimestamp(win_start_ts).date()).days + 1} 天）")

    # 4) 题材效果
    cat = {}
    for w in works:
        c = cat.setdefault(w["题材"], {"题材": w["题材"], "条数": 0, "总赞": 0, "最高赞": 0, "最高赞作品": ""})
        d = w.get("digg") or 0
        c["条数"] += 1
        c["总赞"] += d
        if d > c["最高赞"]:
            c["最高赞"] = d
            c["最高赞作品"] = _clean_title(w.get("title"), 30)
    cat_list = sorted(cat.values(), key=lambda x: (x["总赞"] / max(x["条数"], 1), x["总赞"]), reverse=True)
    for c in cat_list:
        c["平均赞"] = round(c["总赞"] / max(c["条数"], 1), 1)

    # 5) 全站素材：历史高赞作品 + 热搜 + 选题池 + 对标数据
    hot = _rows(con, """SELECT platform, rank, title, score FROM hot_items
                        WHERE snap_date=(SELECT MAX(snap_date) FROM hot_items) ORDER BY rank LIMIT 15""")
    topics = _rows(con, "SELECT id,title,platform,account_id,score,status,created_at FROM topics ORDER BY score DESC LIMIT 20")
    topics_by_status = {}
    for t in topics:
        topics_by_status[t["status"]] = topics_by_status.get(t["status"], 0) + 1
    hist_top = _rows(con, f"""
        SELECT a.name AS 账号, w.title, w.digg, w.publish_time FROM works w
        LEFT JOIN accounts a ON a.id=w.account_id
        WHERE w.account_id IN ({qs}) AND w.digg IS NOT NULL
        ORDER BY w.digg DESC LIMIT 8""", tuple(own_ids)) if own_ids else []
    con.close()

    top_digg = max([(w.get("digg") or 0) for w in works] or [0])
    m = {
        "窗口": f"{start_s} ~ {today_s}（{days} 天）",
        "天数": days,
        "窗口回退说明": fallback_note,
        "作品统计窗口": work_window,
        "账号概览": account_stats,
        "窗口内作品数": len(works),
        "窗口内总点赞": sum((w.get("digg") or 0) for w in works),
        "窗口内最高赞": top_digg,
        "互动量级偏低": top_digg < 10,
        "发布节奏": dict(sorted(per_day.items())),
        "题材效果": cat_list,
        "窗口内作品": works,
        "历史高赞": hist_top,
        "当日热搜": hot,
        "选题池": topics,
        "选题池状态": topics_by_status,
    }
    m["缺口"] = _gaps(m)
    m["摘要"] = _digest(m)
    return m


def _gaps(m):
    gaps = []
    if not m["窗口内作品数"]:
        gaps.append(f"近 {m['天数']} 天没有新发布作品（或作品库 publish_ts 覆盖不到该窗口）")
    if not m["当日热搜"]:
        gaps.append("hot_items 没有数据：跑一次 python -m collectors.hot")
    if not m["选题池"]:
        gaps.append("topics 表为空：先跑 python -m insight.topics --n 10")
    if any(a["快照数"] < 2 for a in m["账号概览"]):
        gaps.append("部分账号快照不足 2 天，涨粉数算不出来")
    return gaps


def _digest(m):
    lines = [f"作品统计窗口：{m['作品统计窗口']}；窗口内发布 {m['窗口内作品数']} 条，"
             f"累计点赞 {m['窗口内总点赞']}，最高单条 {m['窗口内最高赞']} 赞。"]
    if m.get("窗口回退说明"):
        lines.append(f"注意：{m['窗口回退说明']}")
    if m.get("互动量级偏低"):
        lines.append("注意：窗口内互动量级整体偏低，题材排序只在矩阵内部可比，不能当作绝对效果结论。")
    lines.append("【账号涨粉】")
    for a in sorted(m["账号概览"], key=lambda x: (x["粉丝净增"] if x["粉丝净增"] is not None else -10 ** 9), reverse=True):
        delta = "—" if a["粉丝净增"] is None else f"{a['粉丝净增']:+d}"
        lines.append(f"- {a['平台']}·{a['账号']}（{a['定位']}）粉丝 {a['粉丝'] if a['粉丝'] is not None else '—'}，"
                     f"窗口净增 {delta}，新增作品 {a['新增作品'] if a['新增作品'] is not None else '—'}")
    lines.append("【题材效果（窗口内）】")
    for c in m["题材效果"][:8]:
        lines.append(f"- {c['题材']}：{c['条数']} 条，总赞 {c['总赞']}，平均 {c['平均赞']}，"
                     f"最高《{(c['最高赞作品'] or '')[:30]}》{c['最高赞']}赞")
    if m["历史高赞"]:
        lines.append("【矩阵历史高赞】")
        for w in m["历史高赞"][:5]:
            lines.append(f"- {w['账号']}《{_clean_title(w['title'], 30)}》{w['digg']}赞 {w['publish_time']}")
    if m["当日热搜"]:
        lines.append("【当日热搜（可借势）】" + "；".join((h["title"] or "") for h in m["当日热搜"][:8]))
    if m["选题池"]:
        lines.append("【待拍选题池】")
        for t in m["选题池"][:8]:
            lines.append(f"- [{t['score']}] {t['title']}（{t['platform']} / {t['account_id']} / {t['status']}）")
    if m["缺口"]:
        lines.append("【数据缺口】" + "；".join(m["缺口"]))
    return "\n".join(lines)


# ==================== 二、规则版拍摄方向 ====================

def _fmt_int(v):
    if v is None:
        return "—"
    return f"{v:,}"


# LLM 段落轻净化（只作用于模型生成的章节，不动文件里固定的合规提示文字）
_LLM_SCRUB = [("神器", "实用好物"), ("最好的", "比较合适的"), ("最好", "比较合适"),
              ("第一名", "比较靠前"), ("第一", "比较靠前"), ("绝对", "基本"),
              ("治疗", "辅助改善"), ("治愈", "康复期出行"), ("疗效", "使用效果"),
              ("包治", ""), ("国家级", ""), ("嗨，大家好！", ""), ("总而言之，", "说到底，")]


def _scrub_llm(text):
    t = text or ""
    for bad, good in _LLM_SCRUB:
        if bad in t:
            t = t.replace(bad, good)
    return t.strip()


def _rule_direction(m):
    """规则版：从数据直接推导下周拍什么，返回 (方向条目列表, 排期列表)。"""
    cats = m["题材效果"]
    good = [c for c in cats if c["条数"] >= 1][:3]
    weak = [c for c in cats if c["条数"] >= 1][-2:]
    accounts = m["账号概览"]
    acc_by_platform = {}
    for a in accounts:
        acc_by_platform.setdefault(a["平台"], []).append(a)

    items = []
    id2name = {a["id"]: a.get("name") or a["id"] for a in db.get_accounts(kind=None)}
    hist_note = (f"；矩阵历史高赞第一是《{_clean_title(m['历史高赞'][0]['title'], 20)}》"
                 f"{m['历史高赞'][0]['digg']} 赞，复刻时优先参考它的开头和呈现方式") if m["历史高赞"] else ""
    if m.get("互动量级偏低"):
        trend = "，在当前窗口内排序最靠前（绝对值都偏低，只作内部相对比较）"
    else:
        trend = "，是当前最能跑出互动的题材"
    # 方向 1：放大已验证题材
    for c in good[:2]:
        acc = None
        for w in m["窗口内作品"]:
            if w["题材"] == c["题材"]:
                acc = w
                break
        plat = PLATFORM_LABEL.get((acc or {}).get("platform"), "")
        who = (acc or {}).get("账号") or "矩阵内同定位账号"
        items.append({
            "方向": f"放大已验证题材：{c['题材']}",
            "账号": f"{plat}·{who}",
            "拍法": f"把《{(c['最高赞作品'] or '')[:28]}》这条的结构拆开重拍一遍：同题材换场景再拍 2-3 条，"
                    f"开头 3 秒沿用同类钩子，结尾保留互动提问。",
            "依据": f"窗口内 {c['条数']} 条、平均 {c['平均赞']} 赞（最高 {c['最高赞']}）{trend}{hist_note}。",
            "量": "2-3 条/周",
        })
    # 方向 2：补高潜力低产题材
    idle = [c for c in cats if c["条数"] <= 2 and c["平均赞"] >= 20]
    for c in idle[:1]:
        items.append({
            "方向": f"补产能：{c['题材']}拍得太少",
            "账号": "抖音工厂店 + 小红书品牌号各 1 条",
            "拍法": "同一素材剪两个版本：抖音走口播解释型（30-60 秒），小红书走图文清单（5 图 + 真实体验文案）。",
            "依据": f"该题材窗口内只有 {c['条数']} 条但平均 {c['平均赞']} 赞，说明选题被低估，产能没跟上。",
            "量": "2 条/周",
        })
    # 方向 3：选购/参数类信任内容
    if not any(i["方向"].startswith("补产能") and "参数" in i["方向"] for i in items):
        items.append({
            "方向": "信任型内容：把参数讲成人话",
            "账号": "小红书品牌号（佳康顺医疗器械）主发，抖音品牌号同步剪辑",
            "拍法": "一条只讲一个判断标准：先量门宽、再量身高、最后试刹车。用卷尺和实物同框，画面里出数字字幕。",
            "依据": "矩阵历史高赞集中在「真实体验 + 具体数据」两类；医疗器械类目里可核查的参数最容易建立信任。",
            "量": "1-2 条/周",
        })
    # 方向 4：情绪叙事 + 借势热点
    hot_words = "、".join((h["title"] or "")[:12] for h in m["当日热搜"][:3]) or "（今日无可用热点）"
    items.append({
        "方向": "情绪内容收口：一条讲「陪长辈出门」的心愿",
        "账号": "抖音租赁号实拍（昆山佳康顺工厂店）",
        "拍法": "不推产品，先拍一段真实陪同出行的日常（公园/菜场/复查路上），产品只在画面里自然出现，结尾一句互动提问。",
        "依据": f"矩阵历史高赞里情绪题材互动最好；当日可借势的外部热点：{hot_words}。",
        "量": "1 条/周",
    })
    # 方向 5：低效题材做减法
    if weak:
        names = "、".join(c["题材"] for c in weak)
        items.append({
            "方向": f"做减法：{names} 停一停",
            "账号": "全部自有账号",
            "拍法": "这两类题材窗口内平均点赞明显偏低，本周先不排；确有工作素材要发，改成合集或尾图形式，不单独占一条。",
            "依据": "；".join(f"{c['题材']} {c['条数']}条/平均{c['平均赞']}赞" for c in weak),
            "量": "0 条/周",
        })

    # 数据太薄（窗口内无作品）时的兜底方向：直接开拍选题池里排第一的
    if len(items) < 3 and m["选题池"]:
        t = m["选题池"][0]
        items.insert(0, {
            "方向": f"直接开拍：选题池里分最高的一条《{t['title']}》",
            "账号": f"{PLATFORM_LABEL.get(t['platform'], t['platform'])}·{t['account_id'] or '待定账号'}",
            "拍法": "开头 3 秒用它的钩子，中段按结构要点分 3 点各配一个实拍镜头，结尾做互动提问；"
                    "素材够了就同题材再补 1 条换场景的。",
            "依据": f"选题池里推荐度最高的一条（{t['score']} 分），题材为「{t['title']}」。",
            "量": "2 条/周",
        })
    if len(items) < 3:
        items.append({
            "方向": "先把素材补齐再定方向",
            "账号": "全部自有账号",
            "拍法": "跑一次 python -m collectors.hot 与 snapshot.py 采集，再重新生成本文件；当前作品库不足，方向判断置信度低。",
            "依据": "作品库在窗口内没有可用数据，无法从题材效果反推方向。",
            "量": "—",
        })

    # 排期表：优先把选题池里已备好的选题排进去，其次用上面的方向轮排
    sched = []
    topic_pool = [t for t in m["选题池"] if t.get("title")][:7]
    if topic_pool:
        for i, t in enumerate(topic_pool, 1):
            aid = t["account_id"] or ""
            sched.append({
                "天": f"D{i}",
                "账号": f"{PLATFORM_LABEL.get(t['platform'], t['platform'])}·{id2name.get(aid, aid or '待定')}",
                "题材": t["title"],
                "要点": f"推荐度 {t['score']}；按选题结构拍，结尾做互动引导。",
                "量": "1 条",
            })
    if not sched:
        for i in range(1, 8):
            it = items[(i - 1) % len(items)]
            sched.append({"天": f"D{i}", "账号": it["账号"], "题材": it["方向"], "要点": it["拍法"][:60], "量": "1 条"})
    return items, sched


# ==================== 三、LLM 增强 ====================

def _llm_direction(m, days):
    prompt = f"""以下是佳康顺新媒体账号矩阵近 {days} 天的真实数据复盘：
{m['摘要']}

请给出**下周（7 天）拍摄方向**，输出 markdown，结构严格如下（不要输出其它章节、不要重复上面的数据）：

## 三、下周拍摄方向

### 方向1：<一句话标题>
- 账号：<具体到平台 + 账号名>
- 拍什么：<具体到场景、镜头、开头 3 秒怎么说>
- 依据：<必须引用上面数据里的账号名/点赞数/条数>
- 产量：<几条/周>

（同样格式给到 4-6 个方向，按优先级排序；最后一条必须是「做减法」，指出应减少哪类内容）

## 四、内容排期建议

| 天 | 账号 | 题材 | 要点 |
|---|---|---|---|
| D1 | ... | ... | ... |
（7 行）

要求：判断必须有数据支撑，不要写「要重视内容质量」这类空话；每条方向都要能直接安排拍摄。"""
    raw = llm.chat([{"role": "system", "content": _DY_SYS}, {"role": "user", "content": prompt}],
                   temperature=0.7, max_tokens=2600)
    if not raw:
        return None
    txt = llm.strip_fence(raw)
    if "下周拍摄方向" not in txt:
        return None
    return txt


# ==================== 四、组装 markdown ====================

def _render(m, days, direction_md, items, sched, source):
    acc_rows = []
    for a in sorted(m["账号概览"], key=lambda x: (x["粉丝"] if x["粉丝"] is not None else -1), reverse=True):
        delta = "—" if a["粉丝净增"] is None else f"{a['粉丝净增']:+d}"
        acc_rows.append(f"| {a['平台']}·{a['账号']} | {a['定位']} | {_fmt_int(a['粉丝'])} | {delta} | "
                        f"{a['新增作品'] if a['新增作品'] is not None else '—'} | {a['快照数']} |")

    cat_rows = [f"| {c['题材']} | {c['条数']} | {c['总赞']} | {c['平均赞']} | "
                f"{(c['最高赞作品'] or '')[:24]} | {c['最高赞']} |" for c in m["题材效果"]] or ["| （窗口内无作品） | 0 | 0 | 0 | — | 0 |"]

    pace_items = list(m["发布节奏"].items())
    if len(pace_items) > 8:
        pace = "……（更早省略）、" + "、".join(f"{d}：{n} 条" for d, n in pace_items[-8:])
    else:
        pace = "、".join(f"{d}：{n} 条" for d, n in pace_items) or "窗口内无发布记录"
    hist = "\n".join(f"- {w['账号']}《{_clean_title(w['title'], 34)}》{w['digg']} 赞（{w['publish_time']}）"
                     for w in m["历史高赞"][:5]) or "- 暂无"
    hot = "\n".join(f"- {h['platform']} 第{h['rank']} 名：{h['title']}（热度 {h['score']}）"
                    for h in m["当日热搜"][:8]) or "- 当日无热搜数据"
    tp = "\n".join(f"- [{t['score']}] {t['title']}（{t['platform']} / {t['account_id']} / {t['status']}）"
                   for t in m["选题池"][:8]) or "- 选题池为空，先跑 `python -m insight.topics --n 10`"
    gaps = "\n".join(f"- {g}" for g in m["缺口"]) or "- 无"
    note = f"\n> 口径说明：{m['窗口回退说明']}\n" if m.get("窗口回退说明") else ""

    if direction_md:
        sec3 = direction_md.strip()
    else:
        lines = ["## 三、下周拍摄方向", ""]
        if m.get("互动量级偏低"):
            lines += [f"> 先说口径：{m['作品统计窗口']} 窗口内单条最高只有 {m['窗口内最高赞']} 赞，"
                      f"绝对量级偏小，下面的方向按「题材相对排序 + 矩阵历史高赞」推导，"
                      f"执行时以实拍后的真实数据回看。", ""]
        for i, it in enumerate(items, 1):
            lines += [f"### 方向{i}：{it['方向']}", f"- 账号：{it['账号']}",
                      f"- 拍什么：{it['拍法']}", f"- 依据：{it['依据']}", f"- 产量：{it['量']}", ""]
        lines += ["## 四、内容排期建议", "", "| 天 | 账号 | 题材 | 要点 |", "|---|---|---|---|"]
        for s in sched:
            lines.append(f"| {s['天']} | {s['账号']} | {s['题材']} | {s['要点']} |")
        sec3 = "\n".join(lines)

    md = f"""# 下一步拍摄方向（佳康顺新媒体矩阵）

- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 统计窗口：{m['窗口']}
- 生成方式：{source}
- 数据来源：account_snapshots / works / hot_items / topics（本地 SQLite，未做任何外部采集）

## 一、数据现状

作品统计窗口 {m['作品统计窗口']}：共发布 {m['窗口内作品数']} 条作品，累计点赞 {m['窗口内总点赞']}，最高单条 {m['窗口内最高赞']} 赞；发布节奏：{pace}。
{note}

| 账号 | 定位 | 最新粉丝 | 窗口净增 | 新增作品 | 有效快照 |
|---|---|---|---|---|---|
{chr(10).join(acc_rows)}

## 二、内容规律

窗口内题材效果（按平均点赞排序）：

| 题材 | 条数 | 总赞 | 平均赞 | 最高赞作品 | 最高赞 |
|---|---|---|---|---|---|
{chr(10).join(cat_rows)}

矩阵历史高赞参考：

{hist}

当日外部热点：

{hot}

待拍选题池：

{tp}

{sec3}

## 五、风险与合规提示

- 医疗器械类内容不承诺疗效、不做诊断表述；文案禁用「治疗 / 治愈 / 疗效 / 最 / 第一 / 绝对」。
- 视频与图文都不出现价格、微信号、电话、二维码等站外引流信息。
- 涉及产品参数（重量、尺寸、承重、续航）一律以官方资料为准，画面里给数字字幕，口播不做口头许诺。
- 涉及老人出镜需本人或家属同意；拍摄康复期人群时不拍伤口、不做康复进度承诺。

## 六、数据缺口（影响判断置信度）

{gaps}

---
> 本文件由 `python -m insight.direction --days {days}` 生成，同时已写入 insights 表（kind='direction'）。
"""
    return md


# ==================== 五、对外主函数 ====================

def next_direction(days=7, use_llm=True):
    """给出下一步拍摄方向，落 insights 表并写 out/next_direction.md，返回 markdown 字符串。"""
    days = max(1, int(days))
    m = collect_metrics(days)

    direction_md, source = None, "规则模板"
    if use_llm and llm.available():
        direction_md = _llm_direction(m, days)
        if direction_md:
            direction_md = _scrub_llm(direction_md)
            source = "LLM + 数据规则"

    items, sched = _rule_direction(m)
    md = _render(m, days, direction_md, items, sched, source)

    # 落库
    con = db.connect()
    db.save_insight(con, "direction", "all",
                    f"下一步拍摄方向（近 {days} 天）", md,
                    {"窗口": m["窗口"], "窗口内作品数": m["窗口内作品数"], "窗口内总点赞": m["窗口内总点赞"],
                     "题材效果": m["题材效果"], "账号概览": m["账号概览"],
                     "发布节奏": m["发布节奏"], "生成方式": source, "数据缺口": m["缺口"]})
    con.commit()
    con.close()

    # 写文件
    try:
        os.makedirs(os.path.dirname(DEFAULT_OUT), exist_ok=True)
        with open(DEFAULT_OUT, "w", encoding="utf-8") as f:
            f.write(md)
    except Exception as e:
        print(f"[direction] 写 {DEFAULT_OUT} 失败：{type(e).__name__}: {e}", file=sys.stderr)

    return md


def main():
    import argparse
    ap = argparse.ArgumentParser(description="下一步拍摄方向（佳康顺新媒体矩阵）")
    ap.add_argument("--days", type=int, default=7, help="复盘窗口天数，默认 7")
    ap.add_argument("--no-llm", action="store_true", help="强制规则模板版")
    ap.add_argument("--out", help="额外写出到指定文件（默认已写 out/next_direction.md）")
    ap.add_argument("--json", action="store_true", help="只打印指标 JSON，不生成方向")
    args = ap.parse_args()

    if args.json:
        print(json.dumps(collect_metrics(args.days), ensure_ascii=False, indent=2))
        return

    if not args.no_llm:
        llm.available(verbose=True)
    md = next_direction(days=args.days, use_llm=not args.no_llm)
    print(md)
    print(f"\n[已写入] {DEFAULT_OUT}")
    if args.out:
        p = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[已写入] {p}")


if __name__ == "__main__":
    main()
