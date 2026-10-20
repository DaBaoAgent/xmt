"""文本级对标拆解 + 自动判号。

只分析口播/文案/时间戳/元数据，不做抽帧。
"""
import json
import re

from . import util
from . import personas as personas_mod
from . import render

ACCOUNT_IDS = ("oral", "brand", "personal")


def _transcript_with_time(transcript):
    segs = (transcript or {}).get("segments") or []
    if segs:
        lines = []
        for s in segs:
            lines.append(f"[{s.get('start')}-{s.get('end')}s] {s.get('text')}")
        return "\n".join(lines)
    return (transcript or {}).get("text") or ""


def analyze(ref, transcript, use_llm=True):
    text = (transcript or {}).get("text") or ""
    timed = _transcript_with_time(transcript)
    b = None
    if use_llm:
        b = _llm_analyze(ref, transcript, timed)
    if not b:
        b = _rule_analyze(ref, transcript)
    b = _normalize(b, ref, transcript)
    b["summary_md"] = render.summarize_breakdown_md(b)
    return b


def _llm_analyze(ref, transcript, timed):
    try:
        from insight import llm as xllm
    except Exception:
        return None
    stats = (ref or {}).get("stats") or {}
    prompt = f"""你在拆解一条养老辅具对标视频的口播结构。只根据给出的口播/文案/元数据，不要臆测画面。

视频元数据：
- 平台：{util.platform_label((ref or {}).get('platform'))}
- 作者：{(ref or {}).get('author') or '—'}
- 标题：{(ref or {}).get('title') or '—'}
- 简介：{(ref or {}).get('description') or '—'}
- 时长：{(ref or {}).get('duration_sec') or '—'} 秒
- 点赞/评论/转发/收藏：{stats.get('like')}/{stats.get('comment')}/{stats.get('share')}/{stats.get('collect')}
- 发布时间：{(ref or {}).get('publish_time') or '—'}

口播（带时间戳）：
{timed[:7000]}

三个号的定位（用于判断这条适合谁）：
{personas_mod.summaries()}

账号判断口径：
- oral（口播号/翔哥）：单人观点、避坑、选购标准、科普、清单；强判断，不依赖双人互动。
- brand（品牌号/心悦+小冯）：产品演示、双人问答、到店试车、功能讲解、品牌活动；需要两个人配合。
- personal（个人号/小冯）：第一人称、工厂/展厅日常、真实故事、幕后、街坊式服务；重人味。

请输出严格 JSON（不要 markdown 代码块，不要解释），字段如下：
{{
  "topic": "这条视频一句话主题",
  "product_category": "老年代步车/电动轮椅/助行器/移位机/手动轮椅/护理床/其他",
  "product_features": ["对标里出现的产品功能，最多 6 个"],
  "hook": {{"type": "反常识/警告/提问/故事/利益/身份", "text": "原片钩子原句", "why_it_works": "一句话"}},
  "audience": "最可能被打动的人",
  "structure": [{{"beat": "钩子/展开/卖点1/转折/高潮/CTA", "start": 0, "end": 3, "summary": "这一段做了什么", "function": "为什么放在这里"}}],
  "selling_points": [{{"point": "卖点", "evidence": "原片怎么说", "order": 1}}],
  "transitions": ["转折句/过渡句"],
  "cta": {{"type": "关注/评论/私信/到店/购买/无", "text": "原片 CTA", "mapping": "映射到佳康顺的同类动作"}},
  "pacing": {{"duration_sec": 0, "segments": 0, "avg_segment_sec": 0}},
  "tone": "语感/节奏",
  "copy_structure_for_us": ["可以学的结构，不要写原句"],
  "avoid_copying": ["不要复刻的内容：原句/未核实数据/他人形象/品牌等"],
  "account_fit": {{"oral": 0.0, "brand": 0.0, "personal": 0.0, "reason": "为什么"}},
  "account_candidates": ["最可能的两个账号 id"],
  "product_hint": {{"category": "品类", "features": ["功能"], "specific_model": null}},
  "pacing_note": "口播节奏的描述"
}}

要求：
- 每条 structure 的 start/end 用秒；没有时间戳就按句子顺序估算。
- account_fit 三个分数在 0-1，必须有区分度；不要三个都 0.8。
- 如果这条是通用选购指南，product_hint.specific_model 为 null。
- 不要编造原片没有的信息。"""
    text = xllm.ask(prompt, system="你是严谨的短视频结构分析师，只输出严格 JSON。",
                    temperature=0.3, max_tokens=2800)
    parsed = xllm.extract_json(text, expect="object") if text else None
    if isinstance(parsed, dict):
        return parsed
    # 一次重试，强调 JSON
    text2 = xllm.ask("把上一条分析压缩成严格 JSON，只输出 JSON，不要任何解释：\n" + prompt,
                     system="只输出 JSON。", temperature=0.1, max_tokens=2200)
    parsed2 = xllm.extract_json(text2, expect="object") if text2 else None
    return parsed2 if isinstance(parsed2, dict) else None


def _rule_analyze(ref, transcript):
    text = (transcript or {}).get("text") or ""
    segs = (transcript or {}).get("segments") or []
    sentences = util.split_sentences(text) or [text] if text else []
    duration = (ref or {}).get("duration_sec")
    if not duration and segs:
        duration = segs[-1].get("end")
    hook = sentences[0] if sentences else ""
    cta_text = " ".join(sentences[-2:]) if sentences else ""
    cta_type = "无"
    for t, words in (("关注", ["关注", "了解更多"]), ("评论", ["评论区", "评论区聊聊"]),
                     ("私信", ["私信", "找我"]), ("到店", ["到店", "来展厅", "试驾"]),
                     ("购买", ["下单", "买得到", "小黄车"])):
        if any(w in cta_text for w in words):
            cta_type = t
            break
    selling = []
    for s in sentences:
        if any(k in s for k in ("车架", "电池", "电机", "刹车", "轮胎", "折叠", "功能", "承重", "续航", "材质", "助行", "康复", "助推")):
            if s not in [x["point"] for x in selling]:
                selling.append({"point": s[:80], "evidence": "原片口播", "order": len(selling) + 1})
    if not selling:
        selling = [{"point": s[:80], "evidence": "原片口播", "order": i + 1}
                   for i, s in enumerate(sentences[:3])]
    structure = []
    if segs:
        n = min(6, max(2, len(segs)))
        chunk = max(1, len(segs) // n)
        for i in range(n):
            part = segs[i * chunk:(i + 1) * chunk] if i < n - 1 else segs[i * chunk:]
            if not part:
                continue
            structure.append({
                "beat": "钩子" if i == 0 else ("CTA" if i == n - 1 else f"展开{i}"),
                "start": part[0].get("start") or 0,
                "end": part[-1].get("end") or duration or 0,
                "summary": "".join(x.get("text") or "" for x in part)[:90],
                "function": "开场/递进/收束",
            })
    if not structure:
        structure = [{"beat": "钩子", "start": 0, "end": 3,
                      "summary": hook[:90], "function": "开场"},
                     {"beat": "展开", "start": 3, "end": max(3, (duration or 30) - 5),
                      "summary": text[:90], "function": "讲卖点"},
                     {"beat": "CTA", "start": max(0, (duration or 30) - 5), "end": duration or 30,
                      "summary": cta_text[:90], "function": "收束"}]
    scores = _rule_account_scores(ref, text)
    return {
        "topic": (ref or {}).get("title") or (sentences[0] if sentences else "对标视频"),
        "product_category": _guess_category(ref, text),
        "product_features": _guess_features(text),
        "hook": {"type": _guess_hook_type(hook), "text": hook, "why_it_works": "直接抛出问题/判断"},
        "audience": "给父母选辅具的子女、行动不便的老人",
        "structure": structure,
        "selling_points": selling[:5],
        "transitions": [],
        "cta": {"type": cta_type, "text": cta_text, "mapping": _cta_mapping(cta_type)},
        "pacing": {"duration_sec": duration, "segments": len(segs) or len(sentences),
                   "avg_segment_sec": round((duration or 0) / max(1, len(segs) or len(sentences)), 1)},
        "tone": "口语、直给" if scores["oral"] >= max(scores["brand"], scores["personal"]) else "演示/讲解",
        "copy_structure_for_us": ["开头先给判断/问题", "中段按点展开", "结尾给动作"],
        "avoid_copying": ["不要复用原句", "不要照搬未核实的数据", "不要使用原作者形象/品牌"],
        "account_fit": {**scores, "reason": "按口播文本关键词粗判"},
        "account_candidates": sorted(scores, key=scores.get, reverse=True)[:2],
        "product_hint": {"category": _guess_category(ref, text), "features": _guess_features(text),
                         "specific_model": None},
        "pacing_note": "按文本长度估算",
    }


def _guess_hook_type(hook):
    if any(w in hook for w in ("别", "不要", "坑", "注意", "警告")):
        return "警告/避坑"
    if any(w in hook for w in ("你知道吗", "你敢信", "为什么", "什么")):
        return "提问/反常识"
    if "?" in hook or "？" in hook:
        return "提问"
    return "判断/陈述"


def _guess_category(ref, text):
    blob = " ".join([str((ref or {}).get("title") or ""), str((ref or {}).get("description") or ""), str(text)[:1000]])
    for name, words in (
        ("老年代步车", ("代步车", "老年代步", "四轮", "遛弯", "买菜")),
        ("电动轮椅", ("电动轮椅", "轮椅", "碳纤维", "续航")),
        ("助行器", ("助行器", "助行", "骨折", "小福车", "朋友2", "NIP")),
        ("移位机", ("移位机", "天轨", "转移")),
        ("手动轮椅", ("手动轮椅", "手推")),
        ("护理床", ("护理床",)),
    ):
        if any(w in blob for w in words):
            return name
    return "其他"


def _guess_features(text):
    out = []
    for k in ("折叠", "助力", "助行", "康复", "电磁刹车", "实心胎", "锂电池", "碳纤维",
              "铝合金", "原地转弯", "助推", "续航", "轻便", "扶手调节"):
        if k in str(text) and k not in out:
            out.append(k)
    return out[:6]


def _cta_mapping(cta_type):
    return {
        "关注": "关注翔哥/关注账号，了解更多辅具知识",
        "评论": "评论区聊聊你的情况",
        "私信": "私信咨询/预约",
        "到店": "到苏州阳光大厦展厅试车/体验",
        "购买": "到店试车或私信了解，不写价格",
        "无": "按对标节奏自然收束，可加一个轻 CTA",
    }.get(cta_type, "按对标映射")


def _rule_account_scores(ref, text):
    blob = " ".join([str((ref or {}).get("title") or ""), str(text or "")])
    scores = {"oral": 0.28, "brand": 0.28, "personal": 0.28}
    oral = ("避坑", "怎么选", "如何选", "选购", "知识", "注意", "清单", "判断", "科普",
            "买之前", "别急", "干货", "指南", "必看", "几个问题", "问我")
    brand = ("演示", "到店", "试车", "功能", "双人", "问答", "品牌", "活动", "展厅",
             "心悦", "小冯", "对比", "这款", "我们")
    personal = ("工厂", "展厅", "日常", "故事", "真实", "老板", "小冯", "送货", "维修",
                "街坊", "我是", "那天", "客户", "阿姨", "奶奶", "爷爷")
    for w in oral:
        if w in blob:
            scores["oral"] += 0.07
    for w in brand:
        if w in blob:
            scores["brand"] += 0.055
    for w in personal:
        if w in blob:
            scores["personal"] += 0.06
    # 双人问答/产品功能演示更偏品牌
    if any(w in blob for w in ("一车能顶", "接下来我们看看", "给你看", "我给您演示", "来，我")):
        scores["brand"] += 0.08
        scores["personal"] += 0.04
    # 通用避坑/清单明显偏口播
    if any(w in blob for w in ("避坑", "干货", "必看", "几个问题", "选购指南")):
        scores["oral"] += 0.12
    for k in scores:
        scores[k] = round(min(0.98, scores[k]), 2)
    return scores


def _normalize(b, ref, transcript):
    b = dict(b or {})
    text = (transcript or {}).get("text") or ""
    segs = (transcript or {}).get("segments") or []
    duration = (ref or {}).get("duration_sec") or (segs[-1].get("end") if segs else None)
    b.setdefault("topic", (ref or {}).get("title") or "")
    b.setdefault("product_category", _guess_category(ref, text))
    b.setdefault("product_features", _guess_features(text))
    hook = b.get("hook") or {}
    if not isinstance(hook, dict):
        hook = {"type": "判断", "text": str(hook), "why_it_works": ""}
    if not hook.get("text"):
        hook["text"] = (util.split_sentences(text) or [""])[0]
    b["hook"] = hook
    b["structure"] = _normalize_structure(b.get("structure"), segs, duration, text)
    sp = b.get("selling_points") or []
    b["selling_points"] = [
        ({"point": x.get("point") or x.get("evidence") or str(x),
          "evidence": x.get("evidence") or "",
          "order": i + 1} if isinstance(x, dict) else {"point": str(x), "evidence": "", "order": i + 1})
        for i, x in enumerate(sp)
    ][:8]
    cta = b.get("cta") or {}
    if not isinstance(cta, dict):
        cta = {"type": str(cta), "text": "", "mapping": ""}
    cta.setdefault("mapping", _cta_mapping(cta.get("type") or "无"))
    b["cta"] = cta
    pacing = b.get("pacing") or {}
    if not isinstance(pacing, dict):
        pacing = {}
    if not pacing.get("duration_sec"):
        pacing["duration_sec"] = duration
    if not pacing.get("segments"):
        pacing["segments"] = len(segs) or len(util.split_sentences(text))
    try:
        if not pacing.get("avg_segment_sec") and pacing.get("duration_sec"):
            pacing["avg_segment_sec"] = round(float(pacing["duration_sec"]) / max(1, int(pacing["segments"])), 1)
    except Exception:
        pass
    b["pacing"] = pacing
    fit = b.get("account_fit") or {}
    if not isinstance(fit, dict):
        fit = {}
    rule = _rule_account_scores(ref, text)
    for k in ACCOUNT_IDS:
        try:
            fit[k] = util.clamp(fit.get(k, rule.get(k, 0.3)), 0, 1)
        except Exception:
            fit[k] = rule.get(k, 0.3)
    if "reason" not in fit:
        fit["reason"] = "按文本特征判断"
    b["account_fit"] = fit
    b["account_selection"] = select_account(b, cfg=util.config(), forced=None)
    ph = b.get("product_hint") or {}
    if not isinstance(ph, dict):
        ph = {}
    ph.setdefault("category", b.get("product_category"))
    ph.setdefault("features", b.get("product_features") or [])
    ph.setdefault("specific_model", None)
    b["product_hint"] = ph
    b["meta"] = {
        "platform": (ref or {}).get("platform"),
        "author": (ref or {}).get("author"),
        "title": (ref or {}).get("title"),
        "stats": (ref or {}).get("stats") or {},
        "duration_sec": duration,
        "publish_time": (ref or {}).get("publish_time"),
    }
    return b


def _normalize_structure(structure, segs, duration, text):
    out = []
    for i, s in enumerate(structure or []):
        if not isinstance(s, dict):
            continue
        try:
            start = float(s.get("start") or 0)
        except Exception:
            start = 0.0
        try:
            end = float(s.get("end") or 0)
        except Exception:
            end = 0.0
        if end <= start:
            end = start + 3
        out.append({
            "beat": str(s.get("beat") or f"段落{i + 1}"),
            "start": round(start, 2),
            "end": round(end, 2),
            "summary": str(s.get("summary") or "")[:160],
            "function": str(s.get("function") or "")[:120],
        })
    if out:
        return out
    if segs:
        return [{"beat": "钩子", "start": segs[0].get("start") or 0,
                 "end": segs[min(2, len(segs) - 1)].get("end") or 3,
                 "summary": "".join(x.get("text") or "" for x in segs[:3])[:160],
                 "function": "开场"},
                {"beat": "展开", "start": segs[min(3, len(segs) - 1)].get("start") or 0,
                 "end": (duration or (segs[-1].get("end") or 0)),
                 "summary": "中段展开", "function": "讲卖点/给证据"}]
    return [{"beat": "全文", "start": 0, "end": duration or 30,
             "summary": text[:160], "function": "整体"}]


def select_account(breakdown, cfg=None, forced=None):
    cfg = cfg or util.config()
    sel = cfg.get("selection") or {}
    min_score = float(sel.get("account_min_score") or 0.72)
    min_margin = float(sel.get("account_min_margin") or 0.15)
    labels = personas_mod.labels()
    if forced and forced in ACCOUNT_IDS:
        return {
            "account": forced,
            "account_label": labels.get(forced, forced),
            "confidence": 1.0,
            "selected": True,
            "reason": "用户指定账号",
            "candidates": [{"id": forced, "label": labels.get(forced, forced), "score": 1.0}],
        }
    fit = (breakdown or {}).get("account_fit") or {}
    scores = {k: util.clamp(fit.get(k, 0), 0, 1) for k in ACCOUNT_IDS}
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_id, top = ranked[0]
    second_id, second = ranked[1]
    margin = top - second
    reason = fit.get("reason") or ""
    candidates = [{"id": k, "label": labels.get(k, k), "score": round(v, 2)}
                  for k, v in ranked[:2]]
    if top >= min_score and margin >= min_margin:
        return {
            "account": top_id,
            "account_label": labels.get(top_id, top_id),
            "confidence": round(top, 2),
            "selected": True,
            "reason": reason or f"{labels.get(top_id, top_id)} 匹配度最高（{top:.2f}）",
            "candidates": candidates,
        }
    return {
        "account": None,
        "account_label": None,
        "confidence": round(top, 2),
        "selected": False,
        "reason": (reason or "账号判断不够明确") + f"；最高 {labels.get(top_id, top_id)} {top:.2f}，"
                  f"第二 {labels.get(second_id, second_id)} {second:.2f}",
        "candidates": candidates,
    }
