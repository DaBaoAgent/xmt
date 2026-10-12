"""选题生成：把「热搜 / 对标爆款 / 自有高赞作品 / 监控关键词」汇总成素材，产出可拍选题并落库 topics 表。

用法：
    python -m insight.topics --n 10                      # 生成 10 条选题（有 key 走 LLM，无 key 走规则模板）
    python -m insight.topics --n 8 --platform douyin     # 只针对抖音
    python -m insight.topics --account-id sxy_brand_dy --no-llm
    python -m insight.topics --material                  # 只看素材汇总，不生成
"""

import os
import re
import sys
import json
import random
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import db                      # noqa: E402  （只读使用，不修改 db.py）
from insight import llm        # noqa: E402

PLATFORM_LABEL = {"douyin": "抖音", "xiaohongshu": "小红书", "channels": "视频号"}
MAX_TITLE_FOR_PROMPT = 50      # 素材里作品标题的截断长度


# ==================== 一、品类痛点库（规则降级版的骨架，也是 LLM 的备选池） ====================

PAIN_LIB = [
    {
        "key": "轻便折叠", "平台": ["douyin", "xiaohongshu"], "适配角色": ["个人", "品牌"],
        "人群": "家属", "场景": "装后备箱、玄关收纳", "痛点": "车身太重、放不进后备箱",
        "角度": "整备重量与折叠后尺寸实测", "关键词": ["折叠", "后备箱", "轻便", "便携", "收纳", "手提", "重量"],
        "标题": ["放不进后备箱？先看重量和折叠尺寸", "老人自己拎得动，才是真的轻便"],
    },
    {
        "key": "骨折康复", "平台": ["douyin", "xiaohongshu"], "适配角色": ["租赁", "个人"],
        "人群": "康复期人群", "场景": "骨折或脚踝术后出门复查", "痛点": "拄拐时手不够用、伤脚不能负重",
        "角度": "解放双手 + 伤脚零负重的用法", "关键词": ["骨折", "康复", "脚伤", "扭伤", "术后", "恢复期", "助行", "拄拐"],
        "标题": ["脚伤恢复期还想出门？先解决手不够用", "骨折康复路上，这台车让伤脚不用落地"],
    },
    {
        "key": "陪长辈出行", "平台": ["douyin", "xiaohongshu"], "适配角色": ["个人", "品牌"],
        "人群": "子女", "场景": "陪爸妈散步、遛弯、逛公园", "痛点": "走得慢、走两步就累、路上没地方歇",
        "角度": "慢节奏出行 + 走累了原地能坐", "关键词": ["陪", "老", "爸妈", "奶奶", "出门", "遛弯", "散步", "公园"],
        "标题": ["陪爸妈散步，走累了能坐一会儿的车", "爸妈走得慢，那就把节奏放慢一点"],
    },
    {
        "key": "选购避坑", "平台": ["douyin", "xiaohongshu"], "适配角色": ["品牌", "个人"],
        "人群": "家属", "场景": "第一次给家人买代步车", "痛点": "参数看不懂、怕买错",
        "角度": "三个必须看的硬指标：承重、尺寸、刹车", "关键词": ["选", "挑", "参数", "怎么选", "避坑", "对比", "指南"],
        "标题": ["第一次买代步车，只看这三个硬指标", "别再问哪个好，先量这三个尺寸"],
    },
    {
        "key": "适老化改造", "平台": ["xiaohongshu", "douyin"], "适配角色": ["品牌", "个人"],
        "人群": "家属", "场景": "家里的门槛、过道、卫生间", "痛点": "车进不去卫生间、过道转不过弯",
        "角度": "门宽与转弯半径到底怎么量", "关键词": ["适老", "改造", "居家", "卫生间", "门槛", "无障碍", "过道"],
        "标题": ["买之前先量门宽，不然进不了卫生间", "适老化改造，先解决这三个卡点"],
    },
    {
        "key": "出行合规", "平台": ["douyin", "xiaohongshu"], "适配角色": ["品牌", "租赁"],
        "人群": "家属", "场景": "带轮椅坐飞机、高铁、地铁", "痛点": "怕电池不合规、怕被拦在门口",
        "角度": "电池类型与托运口径怎么提前问清楚", "关键词": ["托运", "飞机", "高铁", "地铁", "电池", "出行", "安检"],
        "标题": ["带轮椅上高铁，电池怎么问才不踩坑", "出远门前，先把电池这件事问清楚"],
    },
    {
        "key": "坡道越障", "平台": ["douyin"], "适配角色": ["个人", "品牌"],
        "人群": "使用者", "场景": "小区减速带、土路、坡道", "痛点": "推不上去、怕侧翻",
        "角度": "电机与轮径在真实路面的差别", "关键词": ["坡", "越障", "坎", "土路", "减速带", "爬坡", "颠"],
        "标题": ["减速带和土路上跑一趟，差别太明显", "上坡行不行，看这两个地方就够了"],
    },
    {
        "key": "独立出行", "平台": ["douyin", "xiaohongshu"], "适配角色": ["个人"],
        "人群": "长辈本人", "场景": "想自己下楼、不愿麻烦子女", "痛点": "怕被说老、也怕给别人添负担",
        "角度": "能自己收放、自己操作的那一款", "关键词": ["独立", "自己出门", "不愿麻烦", "自尊", "体面", "下楼"],
        "标题": ["不想麻烦子女，那就选自己能收的", "一个人下楼买菜，也能走到菜场"],
    },
    {
        "key": "租赁场景", "平台": ["douyin", "xiaohongshu"], "适配角色": ["租赁"],
        "人群": "康复期短期用户", "场景": "康复期只有两三个月", "痛点": "买一台只用几个月不划算",
        "角度": "租赁周期与押金怎么算", "关键词": ["租赁", "租", "短租", "押金", "短期"],
        "标题": ["康复期只有三个月，租还是买？", "短期用就租：把周期和押金说明白"],
    },
    {
        "key": "居家照护", "平台": ["xiaohongshu", "douyin"], "适配角色": ["品牌"],
        "人群": "照护者", "场景": "卧床照护与日常翻身", "痛点": "照护的人腰先受不了",
        "角度": "护理床的省力结构怎么看", "关键词": ["护理床", "照护", "翻身", "卧床", "护理", "腰"],
        "标题": ["照护者先别累垮，护理床看这三点", "翻身这件事，省力的结构长什么样"],
    },
    {
        "key": "雨天防滑", "平台": ["douyin", "xiaohongshu"], "适配角色": ["个人", "品牌"],
        "人群": "使用者", "场景": "雨天出门", "痛点": "地面湿滑、刹车心里没底",
        "角度": "刹车形式与轮胎花纹怎么看", "关键词": ["雨", "防滑", "湿", "刹车", "溜坡", "安全"],
        "标题": ["雨天出门前，先检查这两个地方", "湿地面刹车顶不顶用，现场试给你看"],
    },
    {
        "key": "尺寸适配", "平台": ["douyin", "xiaohongshu"], "适配角色": ["品牌", "个人"],
        "人群": "家属", "场景": "个子高/体型偏大的使用者选车", "痛点": "普通款坐着挤、久坐硌得慌",
        "角度": "座宽座深与承重怎么对号入座", "关键词": ["承重", "身高", "座宽", "尺寸", "体重", "挤"],
        "标题": ["个子高的人选车，先看座宽和承重", "坐得挤不挤，量三个数据就知道"],
    },
    {
        "key": "日常代步", "平台": ["douyin", "xiaohongshu"], "适配角色": ["租赁", "个人"],
        "人群": "使用者", "场景": "每周复查、买菜、赶集", "痛点": "来回几公里实在走不动",
        "角度": "续航与充电怎么安排才不慌", "关键词": ["复查", "医院", "买菜", "赶集", "日常", "续航", "充电", "菜场"],
        "标题": ["每周复查来回几公里，续航得这么算", "买菜赶集的一天，电量够不够用"],
    },
    {
        "key": "心愿叙事", "平台": ["douyin", "xiaohongshu"], "适配角色": ["个人", "品牌"],
        "人群": "子女", "场景": "带行动不便的长辈看一次风景", "痛点": "总说下次，一拖就是好几年",
        "角度": "把心愿安排在还能走动的时候", "关键词": ["陪", "看风景", "慢慢", "心愿", "一起", "浪漫"],
        "标题": ["带妈妈看一次风景，别再拖到下次", "这满园的花，我想慢慢陪你看完"],
    },
    {
        "key": "信任资质", "平台": ["douyin", "xiaohongshu"], "适配角色": ["品牌"],
        "人群": "家属", "场景": "担心线上买辅具没人管", "痛点": "怕货不对板、怕售后找不到人",
        "角度": "备案信息 + 实体店能不能当面试", "关键词": ["备案", "资质", "工厂", "实体店", "体验", "售后", "展"],
        "标题": ["买辅具最怕没人管，来店里亲自试", "备案号怎么查，一次给你看明白"],
    },
    {
        "key": "配件收纳", "平台": ["douyin", "xiaohongshu"], "适配角色": ["个人"],
        "人群": "使用者", "场景": "出门随身的东西没处放", "痛点": "手上拿着东西、包没地方挂",
        "角度": "挂袋与前袋的分层放法", "关键词": ["袋", "挂", "收纳", "水杯", "配件", "分层"],
        "标题": ["出门东西没处放？分层挂袋怎么用", "手机钥匙水杯，一次放好不用背包"],
    },
]

# 合规红线（医疗器械类文案不可触碰）
BANNED_WORDS = ["治疗", "治愈", "疗效", "根治", "药到病除", "最", "第一", "绝对", "100%", "国家级", "包治"]

# 选题层面的合规/去水净化（最终文案还会再过一遍 copy.scrub_compliance）
TOPIC_SCRUB = [
    ("神医", "好帮手"), ("神器", "实用款"), ("一秒", "轻松"), ("一下就好", "用起来顺手"),
    ("活力满格", "出门更自在"), ("彻底解决", "解决不少"), ("包治", ""), ("根治", "长期使用"),
    ("治疗", "辅助改善"), ("治愈", "康复期出行"), ("疗效", "使用效果"), ("特效", "实用"),
    ("最好的", "比较合适的"), ("最好", "比较合适"), ("最佳", "较合适"), ("最强", "较稳"),
    ("第一名", "比较靠前"), ("第一", "比较靠前"), ("绝对", "基本"), ("100%", "绝大多数"),
    ("国家级", ""), ("药到病除", "有帮助"), ("包治", ""),
]


# ==================== 二、素材汇总 ====================

def _kws(pain):
    """用于标题/热搜匹配的关键词：单字词（陪、选、坡…）噪声太大，只留 2 字及以上。"""
    return [k for k in pain.get("关键词", []) if len(k) >= 2]


def _rows(con, sql, args=()):
    return [dict(r) for r in con.execute(sql, args).fetchall()]


def _cut(s, n=MAX_TITLE_FOR_PROMPT):
    s = (s or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[:n] + "…"


def scrub_topic_text(s):
    """选题文本净化：去疗效/极限/夸张词，顺带清掉标题尾巴上的 #话题。"""
    t = (s or "").strip()
    if not t:
        return ""
    i = t.find(" #")
    if i >= 6:
        t = t[:i].strip()
    for bad, good in TOPIC_SCRUB:
        if bad in t:
            t = t.replace(bad, good)
    t = re.sub(r"\s{2,}", " ", t).strip(" ，。、-—")
    return t


def _fit_topic_title(title, limit=22):
    """选题标题压到 limit 字内：优先在标点/空格处断，保留完整语义。"""
    t = scrub_topic_text(title)
    if len(t) <= limit:
        return t
    win = t[:limit + 2]
    for p in ("，", "、", "？", "！", "："):
        i = win.rfind(p)
        if i >= limit * 0.6:
            return win[:i]
    return t[:limit]


def collect_material(platform=None):
    """从 hot_items / search_hits / works 汇总素材，返回中文可读的素材字典。"""
    con = db.connect()
    p = platform
    own = db.get_accounts(platform=p, kind="own")
    own_ids = [a["id"] for a in own]
    kw_rows = db.get_keywords(platform=p)
    keywords = [k["keyword"] for k in kw_rows]

    def _own_filter():
        if not own_ids:
            return " AND 1=0", []
        qs = ",".join("?" * len(own_ids))
        return f" AND w.account_id IN ({qs})", own_ids

    # 自有高赞作品（全部历史 top）
    f_sql, f_args = _own_filter()
    own_top = _rows(con, f"""
        SELECT w.account_id, a.name AS 账号, a.owner AS 负责人, a.role AS 角色,
               w.title, w.digg, w.comment, w.share, w.publish_time
        FROM works w LEFT JOIN accounts a ON a.id = w.account_id
        WHERE w.digg IS NOT NULL {f_sql}
        ORDER BY w.digg DESC LIMIT 12""", f_args)

    # 自有近期作品
    own_recent = _rows(con, f"""
        SELECT w.account_id, a.name AS 账号, w.title, w.digg, w.comment, w.share, w.publish_time
        FROM works w LEFT JOIN accounts a ON a.id = w.account_id
        WHERE 1=1 {f_sql}
        ORDER BY w.publish_ts DESC LIMIT 15""", f_args)

    # 对标账号爆款（works 里 kind=rival 的作品）
    rival_top = _rows(con, """
        SELECT a.name AS 账号, a.platform, w.title, w.digg, w.comment, w.share, w.publish_time
        FROM works w JOIN accounts a ON a.id = w.account_id
        WHERE a.kind='rival' AND w.digg IS NOT NULL
        """ + (" AND a.platform=? " if p else " ") + """
        ORDER BY w.digg DESC LIMIT 12""", ([p] if p else []))

    hits = _rows(con, """
        SELECT platform, keyword, author_name, title, digg, comment, share, publish_time
        FROM search_hits WHERE 1=1 """ + (" AND platform=? " if p else "") + """
        ORDER BY digg DESC LIMIT 20""", ([p] if p else []))

    # 热搜：优先取目标平台，没有就取全部（标注为站外热点）
    hot_platform_has = con.execute(
        "SELECT COUNT(*) FROM hot_items WHERE 1=1" + (" AND platform=?" if p else ""),
        ([p] if p else [])).fetchone()[0]
    hot_p = p if (p and hot_platform_has) else None
    latest = con.execute(
        "SELECT MAX(snap_date) FROM hot_items" + (" WHERE platform=?" if hot_p else ""),
        ([hot_p] if hot_p else [])).fetchone()[0]
    hots = _rows(con, """
        SELECT platform, kind, rank, title, score, snap_date FROM hot_items
        WHERE snap_date=? """ + (" AND platform=? " if hot_p else "") + " ORDER BY rank ASC",
        ([latest, hot_p] if hot_p else [latest])) if latest else []
    con.close()

    # 相关 / 泛热点拆分：相关 = 命中监控关键词或品类词
    category_words = set(k for k in keywords if len(k) >= 2)
    for it in PAIN_LIB:
        category_words.update(_kws(it))
    hot_rel, hot_other = [], []
    for h in hots:
        t = h.get("title") or ""
        (hot_rel if any(w and w in t for w in category_words) else hot_other).append(h)

    # 数据缺口说明
    gaps = []
    if not hits:
        gaps.append("search_hits 为空：还没有跑关键词搜索采集，对标爆款素材缺失")
    if not rival_top:
        gaps.append("对标账号（kind=rival）没有作品数据：config/rivals.json 里还是示例号，填好链接后才有对标素材")
    if not own_top:
        gaps.append("自有作品库为空：先跑一次 snapshot.py 采集")
    if not hot_rel:
        gaps.append("当日热搜里没有与品类直接相关的话题，只能做泛热点借势或纯品类内容")
    if not keywords:
        gaps.append("监控关键词为空：可在 config/rivals.json 补充后重跑")

    material = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "平台": PLATFORM_LABEL.get(p, p or "全部平台"),
        "自有账号数": len(own),
        "监控关键词": keywords,
        "自有高赞作品": own_top,
        "自有近期作品": own_recent,
        "对标爆款作品": rival_top,
        "关键词搜索爆款": hits,
        "相关热点": hot_rel[:20],
        "泛热点": hot_other[:20],
        "数据缺口": gaps,
        "热搜日期": latest,
    }
    material["摘要"] = _digest(material)
    return material


def _digest(m):
    """把素材压成一段中文摘要（给 LLM 当输入，也便于人读）。"""
    lines = [f"生成时间：{m['生成时间']}；范围：{m['平台']}；监控关键词：{'、'.join(m['监控关键词']) or '（空）'}"]
    if m["自有高赞作品"]:
        lines.append("【自有账号高赞作品】")
        for w in m["自有高赞作品"][:8]:
            lines.append(f"- {w.get('账号')}（{w.get('角色')}）《{_cut(w.get('title'))}》"
                         f" 赞{w.get('digg')} 评{w.get('comment')} 转{w.get('share')} {w.get('publish_time')}")
    if m["自有近期作品"]:
        lines.append("【自有账号近期作品】")
        for w in m["自有近期作品"][:8]:
            lines.append(f"- {w.get('账号')}《{_cut(w.get('title'))}》赞{w.get('digg')} {w.get('publish_time')}")
    if m["对标爆款作品"]:
        lines.append("【对标账号爆款】")
        for w in m["对标爆款作品"][:6]:
            lines.append(f"- {w.get('账号')}《{_cut(w.get('title'))}》赞{w.get('digg')}")
    if m["关键词搜索爆款"]:
        lines.append("【关键词搜索到的爆款】")
        for h in m["关键词搜索爆款"][:8]:
            lines.append(f"- 关键词「{h.get('keyword')}」{h.get('author_name')}"
                         f"《{_cut(h.get('title') or h.get('author_name'))}》赞{h.get('digg')}")
    if m["相关热点"]:
        lines.append("【当日相关热点】")
        for h in m["相关热点"][:8]:
            lines.append(f"- {h.get('platform')} 第{h.get('rank')}名 {h.get('title')}（热度{h.get('score')}）")
    if m["泛热点"]:
        lines.append("【当日泛热点（可借势）】" + "；".join(f"{h.get('title')}" for h in m["泛热点"][:6]))
    if m["数据缺口"]:
        lines.append("【数据缺口】" + "；".join(m["数据缺口"]))
    return "\n".join(lines)


# ==================== 三、规则版选题生成 ====================

def _pick_account(accounts, pain, idx, fixed=None, used=None):
    """按 role 适配 + 用量均衡挑账号；挑不到就轮转。"""
    if fixed:
        for a in accounts:
            if a["id"] == fixed:
                return a
        return {"id": fixed, "name": fixed, "role": "", "platform": ""}
    if not accounts:
        return {"id": None, "name": "（无自有账号）", "role": "", "platform": ""}
    used = used if used is not None else {}
    cands = []
    for kw in pain.get("适配角色", []):
        for a in accounts:
            blob = f"{a.get('role') or ''}{a.get('name') or ''}"
            if kw in blob and a not in cands:
                cands.append(a)
    if not cands:
        cands = list(accounts)
    # 用量最少的优先；同用量时按 idx 轮转，避免全压在一个账号上
    cands.sort(key=lambda a: (used.get(a["id"], 0), accounts.index(a) - idx % len(accounts)))
    return cands[0]


def _score(pain, m, account, platform):
    """0-100 推荐度：基准 40 + 各类证据加权。"""
    score = 40.0
    ev = []
    kws = _kws(pain)
    titles_own = " ".join((w.get("title") or "") for w in (m["自有高赞作品"] + m["自有近期作品"]))
    hit_kw = [k for k in kws if k in titles_own]
    if hit_kw:
        score += 10
        ev.append(f"自有作品已出现同类词：{'、'.join(hit_kw[:4])}")
    top = m["自有高赞作品"][0] if m["自有高赞作品"] else None
    if top and (top.get("digg") or 0) >= 100:
        score += 8
        ev.append(f"矩阵最高赞《{_cut(top.get('title'), 24)}》{top.get('digg')}赞，题材可延展")
    elif top and (top.get("digg") or 0) >= 20:
        score += 4
        ev.append(f"矩阵高赞《{_cut(top.get('title'), 24)}》{top.get('digg')}赞")

    titles_rival = " ".join((w.get("title") or "") for w in m["对标爆款作品"])
    titles_hits = " ".join(((h.get("title") or "") + (h.get("author_name") or "")) for h in m["关键词搜索爆款"])
    if any(k in titles_rival for k in kws):
        score += 10
        ev.append("对标账号同类题材已出爆款")
    if any(k in titles_hits for k in kws):
        hits = [h for h in m["关键词搜索爆款"]
                if any(k in ((h.get("title") or "") + (h.get("author_name") or "")) for k in kws)]
        best = max(hits, key=lambda x: x.get("digg") or 0)
        score += 8
        ev.append(f"关键词「{best.get('keyword')}」下《{_cut(best.get('title') or best.get('author_name'), 24)}》{best.get('digg')}赞")

    if any(any(k in (h.get("title") or "") for k in kws) for h in m["相关热点"]):
        score += 6
        ev.append("当日热搜出现同类话题，可蹭时间窗口")

    score += 4 if platform == "xiaohongshu" else 3
    if account and account.get("id"):
        for kw in pain.get("适配角色", []):
            if kw in f"{account.get('role') or ''}{account.get('name') or ''}":
                score += 4
                ev.append(f"与账号「{account.get('name')}」（{account.get('role')}）定位匹配")
                break
    return min(round(score, 1), 100.0), ev


HOOK_TEMPLATES = [
    "{人群}最容易被忽略的一点：{痛点}。前 3 秒直接抛结论，后面再讲怎么判断。",
    "先说结论：{痛点}，问题多半出在{角度}上。",
    "别急着下单，{场景}这件事先弄清{角度}，能省不少事。",
    "这条只讲一件事：{场景}到底该怎么安排，一条讲透。",
    "{痛点}？三个动作现场演示，看完你自己就能判断。",
]


def _rule_topics(m, platform=None, account_id=None, n=10):
    """规则模板版：痛点库 × 账号轮转，拼装素材证据。无 LLM 时也产出完整中文选题。"""
    con = db.connect()
    accounts = db.get_accounts(platform=platform, kind="own")
    con.close()
    # 平台未知时按素材范围兜底
    pains = [p for p in PAIN_LIB if not platform or platform in p["平台"]]
    if not pains:
        pains = PAIN_LIB
    # 用素材顺序微扰，避免每次生成完全一致的排序
    random.Random(datetime.now().strftime("%Y%m%d")).shuffle(pains)

    out, seen, used = [], set(), {}
    idx = 0
    for pain in pains:
        if len(out) >= n:
            break
        acc = _pick_account(accounts, pain, idx, fixed=account_id, used=used)
        used[acc.get("id")] = used.get(acc.get("id"), 0) + 1
        idx += 1
        score, ev = _score(pain, m, acc, platform or (acc.get("platform") or "douyin"))
        title = pain["标题"][idx % len(pain["标题"])]
        if title in seen:
            continue
        seen.add(title)
        source = "own_hit" if any("自有" in e for e in ev) else ("rival" if any("对标" in e or "关键词" in e for e in ev) else "rule")
        out.append({
            "source": source,
            "platform": platform or acc.get("platform") or "douyin",
            "account_id": acc.get("id"),
            "account_name": acc.get("name"),
            "title": title,
            "hook": HOOK_TEMPLATES[idx % len(HOOK_TEMPLATES)].format(**{k: pain[k] for k in ("人群", "痛点", "场景", "角度")}),
            "outline": f"1) 场景复现：{pain['场景']}；2) 判断标准：{pain['角度']}；"
                       f"3) 现场演示/实测对比；4) 结尾引导互动（{pain['人群']}你们家是怎么选的）",
            "score": score,
            "evidence": "；".join(ev[:2]) if ev else "依据品类痛点库（当前缺少对标与搜索数据）",
            "生成方式": "规则模板",
            "痛点库标识": pain["key"],
        })
    # 不够 n 时补通用模板
    extra = 0
    while len(out) < n and extra < len(PAIN_LIB):
        pain = PAIN_LIB[extra]
        extra += 1
        title = f"{pain['场景']}怎么安排？{pain['角度']}"
        if title in seen:
            continue
        seen.add(title)
        acc = _pick_account(accounts, pain, extra, fixed=account_id, used=used)
        used[acc.get("id")] = used.get(acc.get("id"), 0) + 1
        out.append({
            "source": "rule", "platform": platform or acc.get("platform") or "douyin",
            "account_id": acc.get("id"), "account_name": acc.get("name"), "title": title,
            "hook": f"一句话说清：{pain['痛点']}，问题多半出在{pain['角度']}。",
            "outline": f"1) 痛点；2) {pain['角度']}；3) 选购/使用建议；4) 互动引导",
            "score": 45.0, "evidence": "通用模板（素材不足时的兜底）",
            "生成方式": "规则模板", "痛点库标识": pain["key"],
        })
    return out[:n]


# ==================== 四、LLM 版选题生成 ====================

_SYS = ("你是佳康顺（电动轮椅、助行器、护理床等康复辅具厂商）新媒体账号矩阵的选题策划，"
        "服务抖音与小红书。你的输出必须是可直接开拍的选题，语言口语化、具体、不空泛。"
        "合规要求：不承诺疗效、不做医疗诊断表述、不使用「治疗/治愈/疗效/最/第一/绝对」等词，不出现价格与联系方式。")


def _account_lines(platform=None):
    accs = db.get_accounts(platform=platform, kind="own")
    return "\n".join(f"- {a['id']}｜{PLATFORM_LABEL.get(a['platform'], a['platform'])}｜{a['name']}"
                     f"｜负责人 {a.get('owner') or '未填'}｜定位 {a.get('role') or '未填'}" for a in accs)


def _llm_topics(m, platform=None, account_id=None, n=10):
    prompt = f"""矩阵自带账号（account_id 只能从这里选）：
{_account_lines(platform)}

当前素材（真实采集数据）：
{m['摘要']}

请输出一个 JSON 数组（只输出 JSON，不要任何解释文字），最多 {n} 条选题，按推荐度从高到低排。
每条字段严格如下：
{{"title": "16 字以内的中文选题标题", "platform": "douyin 或 xiaohongshu", "account_id": "上面的账号 id", "hook": "开头 3 秒钩子，口语化，30 字内", "outline": "3 条结构要点，用 1) 2) 3) 分开", "score": 85, "evidence": "为什么值得拍，必须引用上面素材里的具体数据（账号名/点赞数/热点词）"}}

选题要求：
1. 紧扣电动轮椅 / 助行器 / 骨折代步车 / 护理床 / 适老化改造的**具体使用场景**，不要泛泛而谈品牌；
2. 优先复用素材里已经验证过高赞的题材方向；
3. 标题要像真人起的：带数字、带场景、带反差，禁止「XX推荐」「你知道么」这类模板腔；
4. platform 与 account_id 必须成对匹配（抖音选抖音号、小红书选小红书号）；
5. 标题里不要出现 # 话题标签，不要用「神器/一秒/活力满格/最好/第一/绝对」这类夸张或极限词；
6. 不要蹭与品类无关的热点（体育、明星、饮料等一律不要）。"""
    if account_id:
        prompt += f"\n5. 本次只给账号 {account_id} 出选题，所有 account_id 都填 {account_id}。"
    raw = llm.chat([{"role": "system", "content": _SYS}, {"role": "user", "content": prompt}],
                   temperature=0.85, max_tokens=3000)
    if not raw:
        return []
    data = llm.extract_json(raw, expect="array")
    if not isinstance(data, list):
        return []
    out, seen = [], set()
    for it in data:
        if not isinstance(it, dict):
            continue
        title = _fit_topic_title(it.get("title") or "")
        if not title or len(title) < 6 or title in seen:
            continue
        seen.add(title)
        plat = (it.get("platform") or platform or "douyin").strip()
        if plat not in PLATFORM_LABEL:
            plat = platform or "douyin"
        acc = (it.get("account_id") or account_id or "").strip() or None
        try:
            score = float(it.get("score") or 70)
        except Exception:
            score = 70.0
        out.append({
            "source": "llm", "platform": plat, "account_id": acc,
            "account_name": None, "title": title,
            "hook": scrub_topic_text(it.get("hook") or ""),
            "outline": scrub_topic_text(it.get("outline") or ""),
            "score": min(max(round(score, 1), 0.0), 100.0),
            "evidence": scrub_topic_text(it.get("evidence") or "") or "LLM 依据素材摘要推荐",
            "生成方式": "LLM", "痛点库标识": "",
        })
    return out[:n]


# ==================== 五、对外主函数 ====================

def generate_topics(platform=None, account_id=None, n=10, use_llm=True):
    """生成选题并落库 topics 表，返回选题列表（list[dict]）。

    有可用 key 且 use_llm=True 时走 LLM（不足 n 条时用规则模板补齐），否则整体走规则模板。
    """
    n = max(1, int(n))
    material = collect_material(platform)

    topics = []
    if use_llm and llm.available():
        topics = _llm_topics(material, platform, account_id, n)

    if len(topics) < n:
        rule = _rule_topics(material, platform, account_id, n)
        have = {t["title"] for t in topics}
        for t in rule:
            if len(topics) >= n:
                break
            if t["title"] in have:
                continue
            have.add(t["title"])
            topics.append(t)

    if not topics:  # 极端兜底，绝不返回空壳
        topics = _rule_topics(material, platform, account_id, n)

    con = db.connect()
    db.save_topics(con, topics)
    con.commit()
    con.close()
    return topics


# ==================== 六、CLI ====================

def main():
    import argparse
    ap = argparse.ArgumentParser(description="选题生成（佳康顺新媒体矩阵）")
    ap.add_argument("--n", type=int, default=10, help="生成条数，默认 10")
    ap.add_argument("--platform", help="douyin / xiaohongshu")
    ap.add_argument("--account-id", help="只给某个自有账号出选题")
    ap.add_argument("--no-llm", action="store_true", help="强制走规则模板版")
    ap.add_argument("--material", action="store_true", help="只打印素材汇总，不生成选题")
    ap.add_argument("--json", action="store_true", help="以 JSON 打印结果")
    args = ap.parse_args()

    if args.material:
        m = collect_material(args.platform)
        if args.json:
            print(json.dumps(m, ensure_ascii=False, indent=2))
        else:
            print(m["摘要"])
            for g in m["数据缺口"]:
                print(f"[缺口] {g}")
        return

    if not args.no_llm:
        llm.available(verbose=True)
    topics = generate_topics(platform=args.platform, account_id=args.account_id,
                             n=args.n, use_llm=not args.no_llm)

    if args.json:
        print(json.dumps(topics, ensure_ascii=False, indent=2))
    else:
        print(f"\n生成选题 {len(topics)} 条（已落库 topics 表）：")
        for i, t in enumerate(topics, 1):
            print(f"\n{i}. [{t['score']}] {t['title']}  （{t['platform']} / {t.get('account_id')} / {t['生成方式']}）")
            print(f"   钩子：{t['hook']}")
            print(f"   结构：{t['outline']}")
            print(f"   证据：{t['evidence']}")


if __name__ == "__main__":
    main()
