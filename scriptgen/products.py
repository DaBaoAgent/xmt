"""选品：只从阳光展厅可拍清单里选，硬信息才查公司知识库。

规则：
  - confirmed 才能自动选；
  - candidate 必须有用户覆盖才写具体型号；
  - pending（未到展厅）永不自动选；
  - 通用选购指南返回 category，不硬绑型号。
"""
import re
import json

from . import util
from .company_kb import CompanyKB, CompanyKBError

CATEGORY_HINTS = [
    ("老年代步车", ["代步车", "老年代步", "四轮", "买菜", "遛弯", "公园", "代步"]),
    ("电动轮椅", ["电动轮椅", "轮椅", "碳纤维", "续航", "电磁刹车", "轻便"]),
    ("助行器", ["助行器", "助行", "骨折", "单脚", "小福车", "朋友2", "NIP", "拐杖"]),
    ("移位机", ["移位机", "天轨", "转移", "护理", "起身"]),
    ("手动轮椅", ["手动轮椅", "手推", "自走"]),
    ("护理床", ["护理床", "起身床", "电动床"]),
    ("爬楼机", ["爬楼", "上下楼"]),
]

GENERAL_GUIDE_WORDS = [
    "怎么选", "如何选", "选购", "避坑", "指南", "注意", "几个问题", "判断标准",
    "买之前", "别急着买", "对比", "科普", "知识", "清单",
]


def inventory():
    return util.inventory_config()


def _flat(statuses=("confirmed", "candidate", "pending")):
    inv = inventory()
    out = []
    for key in statuses:
        for p in inv.get(key) or []:
            q = dict(p)
            q["inventory_status"] = key
            out.append(q)
    return out


def get_product(model):
    if not model:
        return None
    m = str(model).strip().lower()
    for p in _flat():
        aliases = [str(a).lower() for a in (p.get("aliases") or [])]
        if m == str(p.get("model") or "").lower() or m in aliases:
            return p
    return None


def _alias_pattern(alias):
    a = str(alias or "").strip()
    if not a:
        return None
    if re.search(r"[A-Za-z0-9]", a):
        return re.compile(r"(?<![A-Za-z0-9])" + re.escape(a) + r"(?![A-Za-z0-9])", re.I)
    return re.compile(re.escape(a))


def find_mentions(text, statuses=("confirmed", "candidate", "pending")):
    blob = str(text or "")
    hits = []
    for p in _flat(statuses):
        for alias in [p.get("model")] + list(p.get("aliases") or []):
            pat = _alias_pattern(alias)
            if pat and pat.search(blob):
                hits.append(p)
                break
    return hits


def _category_from(breakdown, ref, transcript_text):
    hint = (breakdown or {}).get("product_hint") or {}
    cat = hint.get("category") or (breakdown or {}).get("product_category")
    if cat:
        for name, _ in CATEGORY_HINTS:
            if name in str(cat):
                return name
    blob = " ".join([
        str((ref or {}).get("title") or ""),
        str((ref or {}).get("description") or ""),
        str((breakdown or {}).get("topic") or ""),
        str(transcript_text or "")[:1600],
    ])
    scores = []
    for name, words in CATEGORY_HINTS:
        score = sum(1 for w in words if w in blob)
        if score:
            scores.append((score, name))
    scores.sort(reverse=True)
    return scores[0][1] if scores else None


def _confirmed_list_text():
    inv = inventory()
    lines = []
    for p in inv.get("confirmed") or []:
        note = p.get("model_note") or p.get("note") or ""
        lines.append(f"- {p.get('model')}｜{p.get('name')}｜{p.get('category')}｜别名 {', '.join(p.get('aliases') or [])}｜{note}")
    for p in inv.get("pending") or []:
        lines.append(f"- [未到展厅，不可选] {p.get('model')}｜{p.get('name')}｜{p.get('category')}")
    for p in inv.get("candidates") or []:
        lines.append(f"- [未确认在展厅，不可自动选] {p.get('model')}｜{p.get('name')}｜{p.get('category')}")
    return "\n".join(lines)


def _looks_general_guide(breakdown, ref, transcript_text):
    blob = " ".join([
        str((ref or {}).get("title") or ""),
        str((ref or {}).get("description") or ""),
        str((breakdown or {}).get("topic") or ""),
        str((breakdown or {}).get("hook", {}).get("text") or ""),
        str(transcript_text or "")[:500],
    ])
    return any(w in blob for w in GENERAL_GUIDE_WORDS)


def _is_product_doc(hit):
    doc_id = str(hit.get("doc_id") or "").lower()
    title = str(hit.get("title") or "")
    blob = (doc_id + " " + title).lower()
    if any(blob.endswith(x) for x in (".mp3", ".m4a", ".wav", ".jpg", ".jpeg", ".png", ".webp", ".heic", ".mp4")):
        return False
    if any(x in blob for x in ("李厂长", "护卫神", "王师傅", "大脸", "铁车vs", "挑战", "测评", "直播回放")):
        return False
    return True


def _doc_score(hit):
    doc_id = str(hit.get("doc_id") or "").lower()
    title = str(hit.get("title") or "")
    score = 0.0
    if "参数与卖点" in title or "产品详细信息" in title:
        score += 6
    if "参数" in title or "卖点" in title:
        score += 2
    if "产品目录" in title or "样册" in title or "报价" in title:
        score += 3
    if doc_id.endswith((".md", ".txt")):
        score += 2
    if doc_id.endswith((".pdf", ".docx")):
        score += 1
    score += float(hit.get("score") or 0) * 2
    return score


def _kb_hits(query, kb=None):
    if not kb:
        return []
    try:
        hits = kb.search(query, kbs=["jks-product"], top_k=15)
    except Exception:
        return []
    hits = [h for h in hits if _is_product_doc(h)]
    hits.sort(key=_doc_score, reverse=True)
    return hits[:6]


def _read_doc(kb, doc_id, max_chars=5000):
    if not kb or not doc_id:
        return ""
    try:
        return kb.read_text(doc_id, max_chars=max_chars)
    except Exception:
        return ""


def extract_facts(text, source, limit=8):
    out, seen = [], set()
    keywords = ("重量", "整车", "续航", "电池", "电机", "刹车", "折叠", "承重", "材质",
                "尺寸", "适用", "配置", "功能", "卖点", "坐垫", "轮胎", "踏板", "扶手")
    for raw in str(text or "").splitlines():
        line = raw.strip().strip("|").strip()
        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"^[-*]\s*", "", line)
        line = re.sub(r"\s*\|\s*", " ", line).strip()
        if len(line) < 12 or len(line) > 240:
            continue
        if line.startswith(("http", ">", '"', "{", "}", "原件：", "来源：", "文件:", "相对路径", "目录:")):
            continue
        if any(x in line for x in ("电商宣传参考", "工作资料库", "自动索引导出", "MEMORY_FIELDS",
                                   "与用户的关联", "基本信息", "资料文档", "存于", "内容按",
                                   "同目录", "同属", "归档", "原文件名", "索引", "知识库",
                                   "source_extraction", '"version"')):
            continue
        if line in seen:
            continue
        has_digit = bool(re.search(r"\d", line))
        hits = sum(1 for k in keywords if k in line)
        if hits < 2 and not (has_digit and hits >= 1):
            continue
        seen.add(line)
        out.append({"claim": line, "source": source})
        if len(out) >= limit:
            break
    return out


def _facts_for(product, kb):
    doc_id = product.get("doc_id")
    texts = []
    if doc_id:
        t = _read_doc(kb, doc_id)
        if t:
            texts.append((doc_id, t))
    if not texts:
        model = product.get("model") or product.get("name") or ""
        hits = _kb_hits(f"{model} 参数与卖点", kb)
        for h in hits[:1]:
            t = _read_doc(kb, h.get("doc_id"))
            if t:
                texts.append((h.get("doc_id"), t))
    if not texts:
        return "", [], []
    doc_id, text = texts[0]
    facts = extract_facts(text, doc_id)
    return text[:5000], facts, [doc_id]


def _selected(product, confidence, reason, kb, alternatives=None):
    fact_text, facts, doc_ids = _facts_for(product, kb)
    needs = (product.get("inventory_status") == "candidate"
             or product.get("inventory_status") == "pending"
             or bool(product.get("needs_confirmation")))
    status = "selected"
    if product.get("inventory_status") == "pending":
        status = "pending_arrival"
    elif needs:
        status = "uncertain"
    return {
        "status": status,
        "model": product.get("model"),
        "name": product.get("name"),
        "category": product.get("category"),
        "confidence": round(float(confidence or 0), 2),
        "reason": reason,
        "alternatives": alternatives or [],
        "doc_id": product.get("doc_id") or (doc_ids[0] if doc_ids else None),
        "doc_ids": doc_ids,
        "facts": facts,
        "fact_text": fact_text,
        "needs_confirmation": needs,
        "warning": product.get("model_note") or product.get("note"),
        "inventory_status": product.get("inventory_status"),
    }


def _category(category, confidence, reason, alternatives=None):
    return {
        "status": "category",
        "model": None,
        "name": f"{category}（品类通用，不写具体型号）" if category else "品类通用",
        "category": category,
        "confidence": round(float(confidence or 0), 2),
        "reason": reason,
        "alternatives": alternatives or [],
        "doc_id": None,
        "doc_ids": [],
        "facts": [],
        "fact_text": "",
        "needs_confirmation": False,
        "warning": "",
        "inventory_status": None,
    }


def _uncertain(category, confidence, reason, candidates, kb=None):
    candidates = [c for c in candidates if c]
    return {
        "status": "uncertain",
        "model": None,
        "name": f"{category}（待确认型号）" if category else "待确认产品",
        "category": category,
        "confidence": round(float(confidence or 0), 2),
        "reason": reason,
        "alternatives": candidates,
        "doc_id": None,
        "doc_ids": [],
        "facts": [],
        "fact_text": "",
        "needs_confirmation": True,
        "warning": "需要人工指定型号后才能写具体参数",
        "inventory_status": None,
    }


def select_manual(model, kb=None):
    """用户显式指定产品/品类。"""
    if not model:
        return None
    m = str(model).strip()
    if m.lower() in ("category", "品类", "通用", "auto"):
        return _category("品类通用", 0.9, "用户指定品类通用")
    p = get_product(m)
    if p:
        return _selected(p, 0.99, "用户指定型号", kb)
    # 不在展厅清单，仍允许按知识库写，但必须标注
    hits = _kb_hits(f"{m} 参数与卖点", kb)
    doc_id = hits[0].get("doc_id") if hits else None
    text = _read_doc(kb, doc_id) if doc_id else ""
    facts = extract_facts(text, doc_id) if text else []
    return {
        "status": "manual_unlisted",
        "model": m,
        "name": m,
        "category": None,
        "confidence": 0.6,
        "reason": "用户指定，但不在阳光展厅可拍清单",
        "alternatives": [],
        "doc_id": doc_id,
        "doc_ids": [doc_id] if doc_id else [],
        "facts": facts,
        "fact_text": text[:5000],
        "needs_confirmation": True,
        "warning": "不在展厅清单，拍摄前确认样机是否在展厅",
        "inventory_status": None,
    }


def match(breakdown, ref, transcript_text="", kb=None, use_llm=True):
    """自动选品。返回 dict，不抛异常。"""
    category = _category_from(breakdown, ref, transcript_text)
    blob = " ".join([
        str((ref or {}).get("title") or ""),
        str((ref or {}).get("description") or ""),
        str(breakdown.get("topic") or ""),
        json.dumps(breakdown.get("product_hint") or {}, ensure_ascii=False),
        str(transcript_text or "")[:2000],
    ])
    mentions = find_mentions(blob)
    confirmed_mentions = [p for p in mentions if p.get("inventory_status") == "confirmed"]
    if len(confirmed_mentions) == 1:
        return _selected(confirmed_mentions[0], 0.9,
                         f"对标文本明确提到 {confirmed_mentions[0].get('model')}", kb)

    query = " ".join(x for x in [
        category or "", (breakdown.get("product_hint") or {}).get("category") or "",
        " ".join((breakdown.get("product_hint") or {}).get("features") or []),
        breakdown.get("topic") or "",
        " ".join((breakdown.get("product_features") or [])[:5]),
    ] if x).strip()
    hits = _kb_hits(query, kb) if query else []

    if use_llm:
        choice = _llm_choice(breakdown, ref, transcript_text, category, hits)
        if choice:
            raw_choice = str(choice.get("choice") or "").strip()
            conf = util.clamp(choice.get("confidence") or 0, 0, 1)
            reason = str(choice.get("reason") or "").strip()
            alternatives = [str(x) for x in (choice.get("alternatives") or []) if x][:3]
            if raw_choice.lower() in ("category", "品类", "通用"):
                cat = choice.get("category") or category or "品类通用"
                return _category(cat, max(conf, 0.65), reason or "对标是通用选购内容，品类级写作", alternatives)
            if raw_choice.lower() in ("uncertain", "待确认", "none", ""):
                return _uncertain(category, conf, reason or "清单里没有明确对应款", alternatives or _default_candidates(category))
            p = get_product(raw_choice)
            if p:
                if p.get("inventory_status") == "confirmed" and not p.get("needs_confirmation"):
                    return _selected(p, max(conf, 0.75), reason, kb, alternatives)
                return _selected(p, conf, reason, kb, alternatives)
            # LLM 编了一个不在清单的型号 -> 不采信
            return _uncertain(category, min(conf, 0.4),
                              f"模型选择未通过清单校验：{raw_choice}",
                              alternatives or _default_candidates(category))

    # 规则兜底
    if confirmed_mentions:
        return _selected(confirmed_mentions[0], 0.8, "对标文本提到展厅确认款", kb)
    if _looks_general_guide(breakdown, ref, transcript_text) and category:
        return _category(category, 0.75, "对标是通用选购指南，不硬绑型号")
    cands = _default_candidates(category)
    if cands:
        return _uncertain(category, 0.4, "LLM 不可用，且清单里有多款候选", cands, kb)
    return _category(category or "品类通用", 0.6, "没有明确型号匹配，按品类通用处理")


def _default_candidates(category):
    inv = inventory()
    out = []
    for p in inv.get("confirmed") or []:
        if not category or p.get("category") == category or category in str(p.get("name") or ""):
            out.append(p.get("model"))
    return out[:3]


def _llm_choice(breakdown, ref, transcript_text, category, hits):
    try:
        from insight import llm as xllm
    except Exception:
        return None
    hit_lines = []
    for h in hits or []:
        hit_lines.append(f"- {h.get('doc_id')}｜{h.get('title')}｜{(h.get('snippet') or '')[:180]}")
    prompt = f"""你是佳康顺的选品助理。只能从「展厅确认款」里选，不能发明型号。

展厅可拍清单：
{_confirmed_list_text()}

对标视频：
- 标题：{(ref or {}).get('title') or '—'}
- 简介：{(ref or {}).get('description') or '—'}
- 账号猜测：{(breakdown.get('account_selection') or {}).get('account') or '—'}
- 主题：{breakdown.get('topic') or '—'}
- 品类：{category or breakdown.get('product_category') or '—'}
- 对标产品特征：{breakdown.get('product_features') or (breakdown.get('product_hint') or {}).get('features') or []}
- 结构/卖点：{json.dumps(breakdown.get('selling_points') or [], ensure_ascii=False)[:700]}
- 口播开头：{str(transcript_text or '')[:700]}

知识库候选产品文档（只能用来核对事实，不能改变选品边界）：
{chr(10).join(hit_lines) if hit_lines else '（无）'}

规则：
1. 对标是通用选购/避坑/科普，没有具体产品 -> choice="category"，category 填品类。
2. 对标是具体产品演示，且展厅确认款里有明确对应 -> choice=型号。
3. 对标有明确功能（如四合一、康复、助推），但展厅确认款里没有对应款 -> choice="uncertain"，列出 2-3 个最接近的确认款到 alternatives，不要硬选。
4. 未到展厅（pending）和未确认在展厅（candidate）永远不能自动选。
5. 不允许编造型号、参数、库存。

返回严格 JSON：
{{"choice":"型号或 category 或 uncertain","confidence":0.0,"category":"品类或空","reason":"一句话理由","alternatives":["型号1","型号2"],"needs_confirmation":true}}"""
    text = xllm.ask(prompt, system="你是严谨的选品助理，只输出严格 JSON。", temperature=0.2, max_tokens=900)
    parsed = xllm.extract_json(text, expect="object") if text else None
    return parsed if isinstance(parsed, dict) else None
