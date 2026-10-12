"""文案生成：小红书图文笔记（标题≤19字 + 正文300-500字 + 正好5个话题标签 + 视觉风格建议）、
抖音口播稿（3 秒钩子 + 口语正文 + 拍摄提示）。

风格库只读 D:\\@kaifa\\xhs\\小红书爆款风格指南.md（不修改它）；
风格使用历史落在 data/xhs_style_history.json，用于「禁止连续两篇同风格」。

用法：
    python -m insight.copy --mode xhs --topic-id 3 --account-id sxy_brand_xhs
    python -m insight.copy --mode xhs --title "骨折车支持租赁啦" --platform xiaohongshu
    python -m insight.copy --mode douyin --topic-id 3 --out out/douyin_3.md
    python -m insight.copy --list-topics
    python -m insight.copy --list-styles
"""

import os
import re
import sys
import json
import random
import hashlib
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import db                      # noqa: E402
from insight import llm        # noqa: E402

# 复用选题库的品类痛点库，让规则版文案贴着真实痛点写
try:
    from insight.topics import PAIN_LIB
except Exception:  # pragma: no cover
    PAIN_LIB = []

STYLE_GUIDE = os.environ.get("XMT_STYLE_GUIDE") or r"D:\@kaifa\xhs\小红书爆款风格指南.md"
STYLE_HISTORY = os.path.join(ROOT, "data", "xhs_style_history.json")

PLATFORM_LABEL = {"douyin": "抖音", "xiaohongshu": "小红书", "channels": "视频号"}

XHS_TITLE_MAX = 19          # 小红书标题硬上限（字符）
XHS_BODY_MIN, XHS_BODY_MAX = 300, 500
XHS_TAG_COUNT = 5

# 合规替换表（医疗器械类内容红线，避免承诺疗效、极限词与夸张词）
COMPLIANCE_MAP = [
    ("家康顺", "佳康顺"), ("康佳顺", "佳康顺"),
    ("治疗", "辅助改善"), ("治愈", "恢复期陪伴"), ("疗效", "使用效果"), ("根治", "长期使用"),
    ("药到病除", "有帮助"), ("神器", "实用好物"), ("简直", "确实"), ("一秒", "轻松"),
    ("最好的", "比较合适的"), ("最好别", "别"), ("最好", "比较合适"),
    ("第一名", "比较靠前"), ("第一", "比较靠前"), ("绝对", "基本"), ("100%", "绝大多数"),
    ("国家级", ""), ("包治", ""), ("特效", "实用"),
]
BANNED_TAIL = ["首先", "其次", "再次强调", "综上", "总而言之", "在当今", "随着", "众所周知",
               "赋能", "闭环", "抓手", "一方面", "另一方面"]

# 反 AI 味禁用的模板腔词（自检用）
AI_FLAVOR_WORDS = BANNED_TAIL + ["值得一提", "不难看出", "由此可见", "综上所述", "深度赋能", "再次强调"]


# ==================== 一、风格库（只读外部指南） ====================

_FALLBACK_STYLES = [
    {"代号": "A1", "名称": "实证档案风", "气质": "奶白档案纸 + 电蓝强调 + 备案印章",
     "色板": "纸张#F7F6F2 / 文字#1A1A1A / 强调#2F5EA7", "排版": "备案印章、证据卡细边框、黑体标题"},
    {"代号": "B3", "名称": "奶油拿铁风", "气质": "拿铁奶咖底 + 暖棕文字 + 圆润元素",
     "色板": "纸张#F0E6D8 / 文字#5C4A3A / 强调#B8956A", "排版": "圆角16-24px、柔和阴影、圆润无衬线标题"},
    {"代号": "I1", "名称": "银发友好风", "气质": "大字号 + 高对比 + 暖色调 + 简洁布局",
     "色板": "纸张#FFF8E7 / 文字#1A1A1A / 强调#D84315", "排版": "标题≥72px、正文≥24px、元素少、易读优先"},
]


def load_styles():
    """解析风格指南里的 50 套风格（只读，不改文件）；解析失败时用内置三套兜底。"""
    if not os.path.exists(STYLE_GUIDE):
        return list(_FALLBACK_STYLES)
    try:
        with open(STYLE_GUIDE, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return list(_FALLBACK_STYLES)

    styles, cur, buf = [], None, []
    blocks = re.split(r"\n(?=####\s)", text)
    for blk in blocks:
        m = re.match(r"####\s*([A-J]\d)\s*([^（(]+)[（(]([^）)]*)[）)]", blk.strip())
        if not m:
            continue
        st = {"代号": m.group(1), "名称": m.group(2).strip(), "英文": m.group(3).strip(),
              "气质": "", "色板": "", "排版": "", "适用": ""}
        for field, key in (("气质", "气质"), ("色板", "色板"), ("排版", "排版"), ("适用", "适用")):
            mm = re.search(r"\*\*" + field + r"\*\*：(.+)", blk)
            if mm:
                st[key] = mm.group(1).strip()
        styles.append(st)
    return styles or list(_FALLBACK_STYLES)


def _style_history():
    if not os.path.exists(STYLE_HISTORY):
        return []
    try:
        with open(STYLE_HISTORY, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except Exception:
        return []


def _push_style_history(entry):
    hist = _style_history()
    hist.append(entry)
    hist = hist[-50:]
    try:
        os.makedirs(os.path.dirname(STYLE_HISTORY), exist_ok=True)
        with open(STYLE_HISTORY, "w", encoding="utf-8") as f:
            json.dump(hist, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def pick_style(topic=None, account=None, record=True):
    """挑一套视觉风格：不与上一篇相同，尽量不与同账号最近几篇相同（按指南的随机挑选机制）。"""
    styles = load_styles()
    hist = _style_history()
    used_recent = []
    acc_id = (account or {}).get("id") or ""
    for h in hist[-6:]:
        if h.get("账号id") == acc_id:
            used_recent.append(h.get("风格代号"))
    last = hist[-1].get("风格代号") if hist else None

    pool = [s for s in styles if s["代号"] != last and s["代号"] not in used_recent]
    if not pool:
        pool = [s for s in styles if s["代号"] != last] or styles

    # 用选题做种子：同一选题结果稳定，不同选题自然分散
    seed_src = f"{(topic or {}).get('title') or ''}|{(topic or {}).get('id') or ''}|{acc_id}"
    seed = int(hashlib.md5(seed_src.encode("utf-8")).hexdigest()[:8], 16)
    st = dict(pool[seed % len(pool)])
    st["五图序列"] = [
        "P1 封面钩子（产品展开）", "P2 核心卖点（展开）", "P3 使用场景（展开）",
        "P4 细节参数（展开）", "P5 品牌收尾（唯一一张折叠 + 折叠尺寸对比）",
    ]
    if record and st.get("代号"):
        _push_style_history({"风格代号": st["代号"], "风格名": st["名称"], "账号id": acc_id,
                             "主题": (topic or {}).get("title"), "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    return st


# ==================== 二、公共小工具 ====================

def _count(text):
    """正文字数：不计空白（与「500字以内」的口径一致）。"""
    return len(re.sub(r"\s+", "", text or ""))


def _emoji_count(text):
    return len(re.findall(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]", text or ""))


def _fit_title(title, limit=XHS_TITLE_MAX):
    """把标题压到 limit 字符内：优先在标点/语气词处断句，去掉结尾悬空标点。"""
    t = re.sub(r"\s+", "", (title or "").strip())
    t = t.strip("，。！？、；：·-—|")
    if len(t) <= limit:
        return t
    window = t[:limit + 1]
    for p in "，。！？；、":
        i = window.rfind(p)
        if i >= limit // 2:
            return window[:i]
    return window[:limit]


def _stringify(v):
    """把 LLM 可能返回的 dict/list 提示项压成一行可读中文。"""
    if isinstance(v, dict):
        parts = [f"{k}：{_stringify(x)}" for k, x in v.items() if str(x).strip()]
        return "｜".join(parts)
    if isinstance(v, (list, tuple)):
        return "｜".join(_stringify(x) for x in v if str(x).strip())
    return str(v).strip()


def _strip_inline_tags(text):
    """去掉正文里内嵌的 #话题（话题统一由 tags 字段承载）。"""
    t = re.sub(r"#[^\s#，。！？、；：]{1,12}", "", text or "")
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def scrub_compliance(text):
    """合规净化：替换疗效承诺与极限词。"""
    t = text or ""
    for bad, good in COMPLIANCE_MAP:
        if bad in t:
            t = t.replace(bad, good)
    return re.sub(r"[ \t]{2,}", " ", t).strip()


# 模板腔软化：把 AI 爱写的套话换成口语说法（真去 AI 味，而不是只做检测）
AI_FLAVOR_MAP = [
    ("嗨，大家好！", ""), ("大家好！", ""), ("大家好，", ""), ("各位好，", ""),
    ("总而言之，", "说到底，"), ("总而言之", "说到底"),
    ("综上所述，", "总的来说，"), ("综上所述", "总的来说"), ("综上，", "总的来说，"),
    ("值得一提的是，", "另外，"), ("值得一提的是", "另外"),
    ("由此可见，", "这么看，"), ("不难看出，", "这么看，"), ("众所周知，", ""),
    ("首先，", ""), ("其次，", ""),
]


def soften(text):
    """去 AI 味：清掉套话式开头与连接词，保留口语表达。"""
    t = text or ""
    for bad, good in AI_FLAVOR_MAP:
        if bad in t:
            t = t.replace(bad, good)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def _ensure_len(text, lo, hi, fillers, seed_text=""):
    """把正文长度收进 [lo, hi]（按 _count 口径）。

    不足时补一段「细节块」（带引导语的项目符号段落，比散句好看），插在最后一段之前，
    保证结尾互动始终落在最后；超长时按句末截断，仍超则硬截。
    """
    t = (text or "").strip()
    pool = [f for f in fillers if f and f not in t]
    rnd = random.Random(int(hashlib.md5(seed_text.encode("utf-8")).hexdigest()[:8], 16))
    rnd.shuffle(pool)
    if _count(t) < lo and pool:
        picked, guard = [], 0
        while pool and _count(t) + sum(_count(x) for x in picked) < lo and guard < 6:
            picked.append(pool.pop())
            guard += 1
        if picked:
            block = ("顺手把几个容易被忽略的细节也记下来🔎：\n"
                     + "\n".join("· " + x for x in picked) + "🌿")
            blocks = t.split("\n\n")
            if len(blocks) > 1 and blocks[-1].strip():
                t = "\n\n".join(blocks[:-1] + [block, blocks[-1]])
            else:
                t = (t + "\n\n" + block).strip()
    while _count(t) > hi:
        idxs = [t.rfind(m) for m in "。！？"]
        cut = max(idxs)
        if cut <= 0 or cut < _count(t) * 0.55:
            break
        t = t[:cut + 1]
    if _count(t) > hi:  # 兜底硬截断，保证不超上限
        chars, acc = list(t), 0
        for i, ch in enumerate(chars):
            if not ch.isspace():
                acc += 1
            if acc >= hi:
                t = "".join(chars[:i + 1])
                break
        t = t.rstrip("，、；：" + " \n")
    return t.strip()


# ==================== 三、小红书：规则降级版 ====================

_OBJ = ["爸妈", "家里长辈", "奶奶", "老妈", "婆婆"]
_SCENE = ["出门", "散步", "遛弯", "买菜", "逛公园"]
_PROD = ["折叠轮椅", "助行器", "骨折代步车", "电动代步车"]
_START = ["拄拐挪步", "走两百米就得歇"]

# 8 种标题钩子公式（≤19 字，来自风格指南，轮换使用）
TITLE_FORMULAS = [
    ("数字冲击", "给{对象}挑了3台，终于选对"),
    ("痛点直击", "{对象}{场景}不便？先看这3点"),
    ("清单型", "{产品}怎么选？只看3个尺寸"),
    ("情绪共鸣", "陪{对象}{场景}，别劝他们少出门"),
    ("悬念反差", "康复期{场景}，反而走得更久"),
    ("痛点直击", "康复期{场景}，手不够用怎么办"),
    ("对比型", "从{起点}到轻松{场景}"),
    ("权威身份", "给{对象}选{产品}，先量这3处"),
]

DETAIL_POOL = [
    "重量这事别听形容词，看数字：能一只手从后备箱拎上拎下，才算真的轻便。",
    "折叠后的尺寸我实测了一遍，玄关能不能放下、电梯里转不转得开，量完再决定。",
    "握把高度是可调的，先按使用者的身高调顺了再试推，不弯腰、不耸肩才对。",
    "刹车就在握把下方，手指一勾就停、松手即刹，上坡下坡都先试一脚再放心用。",
    "轮子大小直接决定过坎的体感，减速带、小台阶、土路都走一遍，差别马上出来。",
    "座椅的宽度和深度要对得上体型，坐得挤、坐得硌，再轻便也白搭。",
    "电池是可拆的，充电位置在哪儿、能不能拆下来单独充，用之前先问清楚。",
    "出门随手放的手机、水杯、钥匙，有分层挂袋就不用背包，手能空出来扶人。",
    "转弯半径要看家里最窄的那个门，卫生间进不进得去，现场推一圈最直观。",
    "座垫偏硬偏软上手一摸就知道，久坐的人对这点特别敏感，宁可选能加垫的。",
    "售后和备案信息是可以查的，买之前问一句，比买完之后找不到人强。",
    "康复期用车上车、停车、收车这三个动作，都要能一个人完成，才叫省心。",
]

SHORTFALL_POOL = [
    "说句实话，这类车不是没有缺点：车身为了轻便，储物空间就比较有限，出门东西多还是得配个挂袋。",
    "一个小不足也讲：太软的路面（比如松土、碎石）推起来还是费力，别让长辈单独走这种路。",
    "不足也要说：折叠后虽然能进后备箱，但后备箱小的车还是得斜着放，这点提前量好尺寸。",
]

SCENE_POOL = [
    "上周带{对象}去公园，走两步就要找椅子坐下，那次之后我才认真去挑车。",
    "以前每次说带{对象}出门，得到的回答都是「不去，太麻烦你们」。",
    "{对象}术后那段时间最难受的不是疼，是连去阳台晒个太阳都得等人在家。",
    "每天买菜来回两公里，走回来两条腿都是沉的，这是我们家当时的日常。",
    "复查那天在医院走廊站了一个多小时，回来就下定决心不能再靠走了。",
]


def _ctx(topic, account):
    seed_src = f"{(topic or {}).get('title') or ''}{(account or {}).get('id') or ''}"
    rnd = random.Random(int(hashlib.md5(seed_src.encode("utf-8")).hexdigest()[:8], 16))
    blob = json.dumps(topic or {}, ensure_ascii=False) + json.dumps(account or {}, ensure_ascii=False)
    prod = None
    for k, v in (("骨折", "骨折代步车"), ("助行", "助行器"), ("护理", "护理床"),
                 ("轮椅", "折叠轮椅"), ("代步", "电动代步车"), ("租赁", "租赁代步车")):
        if k in blob:
            prod = v
            break
    prod = prod or "电动代步车"
    return {
        "对象": rnd.choice(_OBJ), "场景": rnd.choice(_SCENE), "产品": prod,
        "起点": rnd.choice(_START), "rnd": rnd,
    }


def _rule_xhs_title(topic, account):
    ctx = _ctx(topic, account)
    idx = int(hashlib.md5((str((topic or {}).get("title")) + str((account or {}).get("id"))).encode("utf-8")).hexdigest()[:6], 16)
    formula, tpl = TITLE_FORMULAS[idx % len(TITLE_FORMULAS)]
    return _fit_title(tpl.format(**{k: v for k, v in ctx.items() if k != "rnd"})), formula


GENERIC_PROBLEMS = [
    "太重，一个人搬不动上下车", "折叠后放不进后备箱", "握把高度不合适，推着得弯腰",
    "刹车不顺手，不敢让老人自己用", "不会自己收，每次都得等人帮忙",
]

_LEAK_LABELS = ("场景复现", "判断标准", "痛点", "角度", "钩子", "结构", "卖点", "开头", "结尾引导")


def _pain_of(topic):
    """按痛点库标识 / 关键词把选题对回品类痛点库条目。"""
    key = (topic or {}).get("痛点库标识")
    for p in PAIN_LIB:
        if key and p["key"] == key:
            return p
    blob = json.dumps(topic or {}, ensure_ascii=False)
    for p in PAIN_LIB:
        if p["key"] in blob:
            return p
    for p in PAIN_LIB:
        if any(k in blob for k in p.get("关键词", []) if len(k) >= 2):
            return p
    return None


def _clean_points(outline):
    """清洗 outline：去掉「场景复现：」这类机器标签，剔除纯拍摄动作项。"""
    raw = re.split(r"[；;\n]|1\)|2\)|3\)|4\)|①|②|③", outline or "")
    pts = []
    for p in raw:
        s = p.strip().strip("。").strip()
        for lab in _LEAK_LABELS:
            if s.startswith(lab):
                s = s[len(lab):].lstrip("：: ")
        s = s.split("：", 1)[-1] if s.startswith(_LEAK_LABELS) else s
        if any(k in s for k in ("现场演示", "实测对比", "结尾引导", "互动", "你们家是怎么选")):
            continue
        if len(s) < 6:
            continue
        pts.append(s if s.endswith(("。", "？", "！")) else s + "。")
    # 保序去重
    seen, out = set(), []
    for p in pts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _points(topic, pain, rnd, n=3):
    """构造 3 条可读的内容要点：优先用选题结构，缺的用痛点角度 + 细节池补；近似重复的丢掉。"""
    pts = _clean_points((topic or {}).get("outline") or "")
    if pain:
        pts.insert(0, f"{pain['角度']}，这一步先确认，比单纯看参数直观得多。")

    def _dup(a, b):
        ka = re.sub(r"[，。、；：+\-—\s]", "", a)
        kb = re.sub(r"[，。、；：+\-—\s]", "", b)
        return ka[:8] in kb or kb[:8] in ka or ka[:12] == kb[:12]

    uniq = []
    for p in pts:
        if not any(_dup(p, q) for q in uniq):
            uniq.append(p)
    pool = [d for d in DETAIL_POOL if not any(_dup(d, q) for q in uniq)]
    rnd.shuffle(pool)
    while len(uniq) < n and pool:
        uniq.append(pool.pop())
    return uniq[:n]


def _rule_xhs_body(topic, account):
    ctx = _ctx(topic, account)
    rnd = ctx["rnd"]
    pain = _pain_of(topic)
    pts = _points(topic, pain, rnd)
    struct = rnd.choice(["故事+方法型", "痛点+解法型", "测评清单型"])
    scene = rnd.choice(SCENE_POOL).format(**{k: v for k, v in ctx.items() if k != "rnd"})
    short = rnd.choice(SHORTFALL_POOL)
    subj, prod = ctx["对象"], ctx["产品"]
    probs = [p for p in ([pain["痛点"]] if pain else []) + GENERIC_PROBLEMS if p not in pts]
    rnd.shuffle(probs)

    if struct == "故事+方法型":
        body = f"""{scene}🛞

后来换了{prod}，先说结论：不是越快越好，能按自己的节奏出门就很好。🌿

用下来这三点最实在：
1）{pts[0]}
2）{pts[1]}
3）{pts[2]}

{short}

挑的时候我主要看三样🔎：重量能不能一个人拎、折叠后家里放不放得下、刹车够不够顺手。这三样都过关了，剩下的就是习惯问题。✨
家里长辈出门方便吗？你们是怎么解决的，评论区聊聊～💬"""
    elif struct == "痛点+解法型":
        body = f"""给{subj}挑代步工具，绕不开这几个麻烦：{probs[0]}、{probs[1]}、{probs[2]}。🧐

我最后是这么一条条排掉的：
1）{pts[0]}
2）{pts[1]}
3）{pts[2]}

对应看三件事就够了：整车重量和折叠后尺寸、家里最窄那道门的宽度、收放动作是不是一个人能完成。📏

{short}

{subj}用起来顺不顺手，其实取决于有没有按身高把高度调好。调顺了再试推，比什么参数都直观。✨👍
你们家是在纠结买还是租？说说看～💬"""
    else:
        body = f"""给{subj}挑了3台，最后留下这一台。用了两周，说说真实感受，也说说不足。📝

{scene}🛞

优点三条：
1）{pts[0]}
2）{pts[1]}
3）{pts[2]}

{short}

适合谁：{subj}腿脚还行、但走不了远路的家庭；需要长期卧床照护的，可以直接去看护理床。👌
不适合谁：天天要上台阶、路面又坑洼还没人陪的情况，先别急着下单，到店试一圈更稳。🚶

挑这类车没有标准答案，量好家里的门宽、调好高度、试好刹车，心里就有数了。你们家老人出门方便吗？💬"""
    return body, struct


def _default_tags(topic, account):
    """正好 5 个话题标签：大词 + 长尾组合。"""
    blob = json.dumps(topic or {}, ensure_ascii=False) + json.dumps(account or {}, ensure_ascii=False)
    big = ["#电动轮椅", "#老人代步车", "#适老化改造", "#康复辅具", "#养老辅具"]
    long_map = [
        (("骨折", "术后", "扭伤", "脚伤", "康复"), ["#骨折康复期", "#术后出行", "#康复出行"]),
        (("折叠", "轻便", "便携", "后备箱"), ["#折叠轮椅", "#便携代步车", "#后备箱收纳"]),
        (("陪", "爸妈", "长辈", "老人", "奶奶"), ["#陪爸妈散步", "#老人出行", "#适老好物"]),
        (("护理床", "照护", "卧床"), ["#居家照护", "#护理床怎么选", "#照护日常"]),
        (("租赁", "租"), ["#轮椅租赁", "#短期代步", "#康复期用车"]),
        (("选购", "怎么选", "参数", "避坑"), ["#代步车怎么选", "#辅具选购", "#适老改造"]),
        (("高铁", "飞机", "地铁", "电池"), ["#带轮椅出行", "#电池可拆", "#长途出行"]),
    ]
    tags = []
    for keys, lst in long_map:
        if any(k in blob for k in keys):
            tags += lst
    if len(tags) < 3:
        tags += ["#老人出行", "#适老好物", "#居家收纳"]
    out = big[:2] + tags
    # 去重 + 控制长度
    seen, final = set(), []
    for t in out:
        t = t.strip()
        if not t.startswith("#"):
            t = "#" + t
        if t in seen or len(t) > 12:
            continue
        seen.add(t)
        final.append(t)
        if len(final) == XHS_TAG_COUNT:
            break
    while len(final) < XHS_TAG_COUNT:
        for t in ["#电动轮椅", "#老人出行", "#适老化改造", "#康复辅具", "#适老好物"]:
            if t not in seen:
                seen.add(t)
                final.append(t)
            if len(final) == XHS_TAG_COUNT:
                break
    return final[:XHS_TAG_COUNT]


# ==================== 四、小红书：LLM 版 ====================

_XHS_SYS = ("你是小红书上写真实体验的博主，不是文案机器。为佳康顺（昆山，电动轮椅/助行器/护理床等康复辅具厂商）"
            "写一篇笔记，读者是要给长辈挑代步工具的家属。"
            "硬要求：标题≤19个字符；正文300-500字（不计空格）；正好5个话题标签（大词+长尾组合）。"
            "风格：第一人称、具体场景、带数字、短句、口语；允许少量emoji（5-10个，每段不超过2个）。"
            "禁止：首先/其次/综上/在当今/随着/赋能这类模板腔；禁止纯白描产品参数堆砌；禁止硬广标签式开头。"
            "禁止编造数据：不要写「xx%的用户」「据统计」「调研显示」这类无法核实的数字，只用真实使用场景和可核查参数。"
            "合规：不承诺疗效、不做医疗诊断，禁用治疗/治愈/疗效/最/第一/绝对，不提价格、不提联系方式。")


def _llm_xhs(topic, account, style):
    prompt = f"""选题：{topic.get('title')}
建议投放账号：{account.get('name') or '（未指定）'}（{PLATFORM_LABEL.get(account.get('platform'), '')}，定位 {account.get('role') or '未填'}）
参考钩子：{topic.get('hook') or ''}
参考结构：{topic.get('outline') or ''}
数据证据：{topic.get('evidence') or ''}

本篇要求的视觉风格（配图用，正文里不用描述风格）：{style.get('代号')} {style.get('名称')}｜{style.get('气质')}

请输出 JSON（只输出 JSON）：
{{"title": "≤19字符的标题", "body": "350-460字正文，段落之间用换行分隔；必须含 5-10 个 emoji，分散在不同段落（不要堆在一句里）；结尾一句自然互动提问；正文里不要再写 #话题", "tags": ["#标签1","#标签2","#标签3","#标签4","#标签5"]}}"""
    raw = llm.chat([{"role": "system", "content": _XHS_SYS}, {"role": "user", "content": prompt}],
                   temperature=0.9, max_tokens=1800)
    if not raw:
        return None
    data = llm.extract_json(raw, expect="object")
    if not isinstance(data, dict) or not data.get("body"):
        return None
    return data


# ==================== 五、抖音口播稿 ====================

_DY_SYS = ("你是抖音上做养老辅具科普的口播写手，说话口语化、有数字钩子、敢下判断但不夸张。"
           "为佳康顺（电动轮椅/助行器/护理床等康复辅具厂商）写一条 60-90 秒口播稿。"
           "结构：开头 3 秒钩子 → 分点讲清楚（每点一个具体场景或数字）→ 结尾引导。"
           "不要用「嗨大家好」这类开场，直接进内容。"
           "禁止编造数据：不要写「xx%的用户」「据统计」「调研显示」这类无法核实的统计，只用真实场景和可核查的产品参数。"
           "合规：不承诺疗效、不做医疗诊断，禁用治疗/治愈/疗效/最/第一/绝对，不提价格与联系方式。")


def _rule_douyin(topic, account):
    ctx = _ctx(topic, account)
    rnd = ctx["rnd"]
    pain = _pain_of(topic)
    pts = _points(topic, pain, rnd)
    subj, prod, scene = ctx["对象"], ctx["产品"], ctx["场景"]

    second = pts[1]
    if len(second) <= 22 and not second.startswith(("先", "使用", "上车")):
        second = f"先想想使用场景——{second.rstrip('。')}。"
    hook = f"{subj}{scene}最怕的不是走得慢，是{pick_short_problem(topic)}。这条讲清楚三件事，看完你自己就能判断。"
    body = f"""一是重量和尺寸。{pts[0]}

二是动作能不能一个人完成。{second}上车、停车、收车这三个动作，让{subj}自己试一遍，比什么参数都准。

三是刹车和路面。{pts[2]}减速带、小坡、湿地面都走一遍，心里才有底。

最后说一句实在的：这类车没有标准答案，只有合不合使用者的身形和家里的门宽。先量三个数——身高、门的宽度、电梯或者后备箱的空间，量完再挑。

你家老人出门方便吗？评论区说一下你们最卡的是哪一步，我下条视频专门讲。"""
    tips = [
        "开场 0-3 秒：直接给判断，不要自我介绍、不要念品牌名。",
        f"3-15 秒：手持镜头跟着{prod}走一段真实路面（减速带/小坡），同期声收轮胎和刹车声。",
        "15-40 秒：三个点各配一个特写镜头（折叠动作、握把调高、刹车捏合），画面盖住口播。",
        "40-55 秒：数字上字幕（重量 kg、折叠尺寸 cm、门宽 cm），大字号居中偏左。",
        "55-75 秒：到店或实景收尾，让长辈本人出镜做一个动作，比讲解更有说服力。",
        "字幕全程口语原话，不出现“功效”“治疗”等字样；结尾引导互动，不加联系方式。",
    ]
    return hook, body, tips


def pick_short_problem(topic):
    """从选题里抽一个短痛点词，用于钩子。"""
    blob = json.dumps(topic or {}, ensure_ascii=False)
    for k in ("太重", "放不进后备箱", "手不够用", "走两步就累", "进不了门", "不会收",
              "怕被拦", "没地方歇", "不划算", "不敢用"):
        if k in blob:
            return k
    return "走两步就累、出门还得等人陪"


def _llm_douyin(topic, account):
    prompt = f"""选题：{topic.get('title')}
投放账号：{account.get('name') or '（未指定）'}（{PLATFORM_LABEL.get(account.get('platform'), '')}，定位 {account.get('role') or '未填'}）
参考钩子：{topic.get('hook') or ''}
参考结构：{topic.get('outline') or ''}
数据证据：{topic.get('evidence') or ''}

请输出 JSON（只输出 JSON）：
{{"hook": "开头3秒钩子，口语化，30字内", "正文": "200-400字口播正文，分点，每点带具体场景或数字，结尾引导互动", "拍摄提示": ["4-6条具体可执行的拍摄提示，含景别/动作/字幕要求"]}}"""
    raw = llm.chat([{"role": "system", "content": _DY_SYS}, {"role": "user", "content": prompt}],
                   temperature=0.85, max_tokens=1600)
    if not raw:
        return None
    data = llm.extract_json(raw, expect="object")
    if not isinstance(data, dict) or not (data.get("正文") or data.get("body")):
        return None
    return data


# ==================== 六、自检 ====================

def _self_check(title, body, tags, is_xhs=True):
    checks = []
    if is_xhs:
        checks.append(f"标题 {len(title)} 字，{'≤19 ✓' if len(title) <= XHS_TITLE_MAX else '超过19 ✗'}")
        n = _count(body)
        checks.append(f"正文 {n} 字，{'在300-500 ✓' if XHS_BODY_MIN <= n <= XHS_BODY_MAX else '超出区间 ✗'}")
        checks.append(f"话题标签 {len(tags)} 个，{'正好5 ✓' if len(tags) == XHS_TAG_COUNT else '不是5个 ✗'}")
        e = _emoji_count(body)
        checks.append(f"emoji {e} 个，{'在5-10 ✓' if 5 <= e <= 10 else '不在5-10 ⚠（建议人工调一下）'}")
    hit = [w for w in AI_FLAVOR_WORDS if w in (title + body)]
    checks.append("模板腔词：" + ("无 ✓" if not hit else "命中 " + "、".join(hit) + " ✗"))
    bad = [w for w in ["治疗", "治愈", "疗效", "最好", "第一", "绝对", "100%"] if w in (title + body)]
    checks.append("合规红线：" + ("无 ✓" if not bad else "命中 " + "、".join(bad) + " ✗"))
    if re.search(r"(微信|vx|VX|加我|电话|二维码|元|价格|￥|¥)", title + body):
        checks.append("价格/引流：发现疑似字样 ⚠ 请人工复核")
    else:
        checks.append("价格/引流：无 ✓")
    fake = re.findall(r"(?:\d{1,3}%|据统计|数据显示|权威认证|官方数据|调研显示|用户反馈)", title + body)
    checks.append("数据来源：无无法核实的表述 ✓" if not fake
                  else "数据来源：发现 " + "、".join(sorted(set(fake))[:4]) + " ⚠ 若无依据请删除（不可编造统计）")
    return checks


# ==================== 七、对外主函数 ====================

def write_xhs_note(topic, account, use_llm=True):
    """生成小红书图文笔记：title(≤19字) + body(300-500字) + tags(正好5个) + 视觉风格建议。"""
    topic = topic or {}
    account = account or {}
    style = pick_style(topic, account, record=use_llm)  # 记录风格使用，避免连续同风格

    data = None
    source = "规则降级"
    if use_llm and llm.available():
        data = _llm_xhs(topic, account, style)
        if data:
            source = "LLM"

    if data:
        title = _fit_title(scrub_compliance(_stringify(data.get("title") or topic.get("title") or "")))
        body = soften(scrub_compliance(_strip_inline_tags(_stringify(data.get("body") or ""))))
        formula = "LLM 自选"
        struct = "LLM 自选"
        tags = [_stringify(t) for t in (data.get("tags") or []) if _stringify(t)]
    else:
        title, formula = _rule_xhs_title(topic, account)
        title = scrub_compliance(title)
        body, struct = _rule_xhs_body(topic, account)
        body = scrub_compliance(body)
        tags = _default_tags(topic, account)

    # 标签：去重、补 #、补齐/裁剪到正好 5 个
    seen, fixed = set(), []
    for t in tags:
        t = t if t.startswith("#") else "#" + t
        t = re.sub(r"\s+", "", t)
        if t in seen:
            continue
        seen.add(t)
        fixed.append(t)
    if len(fixed) < XHS_TAG_COUNT:
        for t in _default_tags(topic, account):
            if t not in seen:
                seen.add(t)
                fixed.append(t)
            if len(fixed) == XHS_TAG_COUNT:
                break
    tags = fixed[:XHS_TAG_COUNT]

    body = _ensure_len(body, XHS_BODY_MIN, XHS_BODY_MAX,
                       DETAIL_POOL + SHORTFALL_POOL, seed_text=(title or "") + str(account.get("id")))
    body = scrub_compliance(body)      # 补齐段落也过一遍合规，防止模板里混入极限词
    body = soften(body)                # 再清一遍套话
    title = _fit_title(scrub_compliance(title))

    note = {
        "平台": "小红书",
        "账号": account.get("name") or "（未指定）",
        "账号id": account.get("id"),
        "定位": account.get("role") or "",
        "选题": topic.get("title") or "",
        "选题id": topic.get("id"),
        "title": title,
        "title_len": len(title),
        "body": body,
        "body_len": _count(body),
        "tags": tags,
        "tag_count": len(tags),
        "视觉风格": style,
        "标题公式": formula,
        "正文结构": struct,
        "来源": source,
        "合规提示": "医疗器械类内容：只讲使用场景与出行帮助，不承诺疗效、不做诊断表述、不提价格与联系方式。",
    }
    note["自检"] = _self_check(title, body, tags, is_xhs=True)
    return note


def write_douyin_script(topic, account, use_llm=True):
    """生成抖音口播稿：hook（3 秒钩子） + 正文 + 拍摄提示。"""
    topic = topic or {}
    account = account or {}
    data = None
    source = "规则降级"
    if use_llm and llm.available():
        data = _llm_douyin(topic, account)
        if data:
            source = "LLM"

    if data:
        hook = soften(scrub_compliance(_stringify(data.get("hook") or "")))
        body = soften(scrub_compliance(_stringify(data.get("正文") or data.get("body") or "")))
        tips = [_stringify(t) for t in (data.get("拍摄提示") or data.get("shooting_tips") or []) if _stringify(t)]
    else:
        hook, body, tips = _rule_douyin(topic, account)
        hook, body = soften(scrub_compliance(hook)), soften(scrub_compliance(body))
    if not tips:
        _, _, tips = _rule_douyin(topic, account)

    n = _count(body)
    script = {
        "平台": "抖音",
        "账号": account.get("name") or "（未指定）",
        "账号id": account.get("id"),
        "定位": account.get("role") or "",
        "选题": topic.get("title") or "",
        "选题id": topic.get("id"),
        "hook": hook,
        "正文": body,
        "口播字数": n,
        "口播时长": f"约 {max(20, round(n / 4))} 秒（按 4 字/秒估算）｜建议成片 60-90 秒",
        "拍摄提示": tips,
        "来源": source,
        "合规提示": "医疗器械类内容：不承诺疗效、不做诊断表述，禁用「治疗/治愈/最/第一」；画面不出现价格与联系方式。",
    }
    script["自检"] = [f"口播正文 {n} 字，{'在200-400 ✓' if 200 <= n <= 400 else '建议调整到 200-400 ⚠'}",
                      f"开头钩子 {len(hook)} 字，{'≤45 ✓' if len(hook) <= 45 else '偏长 ⚠'}",
                      f"拍摄提示 {len(tips)} 条，{'≥4 ✓' if len(tips) >= 4 else '偏少 ⚠'}"] + \
        _self_check(hook, body, [], is_xhs=False)
    return script


# ==================== 八、CLI ====================

def _load_topic(topic_id=None, title=None, platform=None):
    if topic_id:
        con = db.connect()
        row = con.execute("SELECT * FROM topics WHERE id=?", (int(topic_id),)).fetchone()
        con.close()
        if not row:
            raise SystemExit(f"topics 表里没有 id={topic_id} 的选题")
        return dict(row)
    return {"id": None, "title": title or "（未指定选题）", "platform": platform,
            "hook": "", "outline": "", "evidence": ""}


def _load_account(account_id=None, platform=None, kind="own"):
    con = db.connect()
    if account_id:
        row = con.execute("SELECT * FROM accounts WHERE id=?", (account_id,)).fetchone()
        con.close()
        if not row:
            raise SystemExit(f"accounts 表里没有 id={account_id} 的账号")
        return dict(row)
    con.close()
    accs = db.get_accounts(platform=platform, kind=kind)
    return accs[0] if accs else {}


def _render_note(t):
    lines = [f"# 小红书笔记｜{t['选题']}", "",
             f"- 账号：{t['账号']}（{t['账号id']} / {t['定位']}）",
             f"- 标题（{t['title_len']}字）：{t['title']}",
             f"- 话题标签（{t['tag_count']}个）：{' '.join(t['tags'])}",
             f"- 视觉风格：{t['视觉风格']['代号']} {t['视觉风格']['名称']}｜{t['视觉风格']['气质']}",
             f"- 色板：{t['视觉风格']['色板']}", f"- 排版：{t['视觉风格']['排版']}",
             f"- 五图序列：{' → '.join(t['视觉风格']['五图序列'])}",
             f"- 标题公式：{t['标题公式']}；正文结构：{t['正文结构']}；生成方式：{t['来源']}", "",
             "## 正文", "", t["body"], "", "## 自检", ""]
    lines += [f"- {c}" for c in t["自检"]]
    lines += ["", f"> {t['合规提示']}"]
    return "\n".join(lines)


def _render_script(s):
    lines = [f"# 抖音口播稿｜{s['选题']}", "",
             f"- 账号：{s['账号']}（{s['账号id']} / {s['定位']}）",
             f"- 时长：{s['口播时长']}（正文 {s['口播字数']} 字）",
             f"- 生成方式：{s['来源']}", "",
             "## 开头 3 秒钩子", "", s["hook"], "", "## 口播正文", "", s["正文"], "",
             "## 拍摄提示", ""]
    lines += [f"{i}. {t}" for i, t in enumerate(s["拍摄提示"], 1)]
    lines += ["", "## 自检", ""]
    lines += [f"- {c}" for c in s["自检"]]
    lines += ["", f"> {s['合规提示']}"]
    return "\n".join(lines)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="文案生成：小红书图文笔记 / 抖音口播稿（佳康顺）")
    ap.add_argument("--mode", choices=["xhs", "douyin"], default="xhs")
    ap.add_argument("--topic-id", type=int, help="从 topics 表按 id 取选题")
    ap.add_argument("--title", help="直接用文字题目（不查库）")
    ap.add_argument("--account-id", help="投放账号 id")
    ap.add_argument("--platform", help="douyin / xiaohongshu（不给账号时按平台自动挑第一个自有号）")
    ap.add_argument("--no-llm", action="store_true", help="强制规则降级版")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    ap.add_argument("--out", help="同时写入文件（utf-8）")
    ap.add_argument("--list-topics", action="store_true", help="列出 topics 表最近的选题")
    ap.add_argument("--list-styles", action="store_true", help="列出可选视觉风格")
    args = ap.parse_args()

    if args.list_styles:
        for s in load_styles():
            print(f"{s['代号']} {s['名称']}｜{s.get('气质', '')}｜{s.get('色板', '')}")
        return

    if args.list_topics:
        con = db.connect()
        rows = con.execute("SELECT id,title,platform,account_id,score,status FROM topics ORDER BY id DESC LIMIT 30").fetchall()
        con.close()
        if not rows:
            print("topics 表还是空的，先跑：python -m insight.topics --n 10")
        for r in rows:
            print(f"{r['id']}. [{r['score']}] {r['title']}（{r['platform']} / {r['account_id']} / {r['status']}）")
        return

    topic = _load_topic(args.topic_id, args.title, args.platform)
    platform = args.platform or topic.get("platform")
    if not args.account_id and topic.get("account_id"):
        args.account_id = topic["account_id"]
    account = _load_account(args.account_id, platform)
    if not args.no_llm:
        llm.available(verbose=True)

    if args.mode == "xhs":
        res = write_xhs_note(topic, account, use_llm=not args.no_llm)
        text = _render_note(res)
    else:
        res = write_douyin_script(topic, account, use_llm=not args.no_llm)
        text = _render_script(res)

    if args.json:
        text = json.dumps(res, ensure_ascii=False, indent=2)
    print(text)
    if args.out:
        path = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\n[已写入] {path}")


if __name__ == "__main__":
    main()
