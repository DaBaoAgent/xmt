"""三号逐字稿生成 + 合规修正（不再生成三平台发布包）。

学结构、全重写；不使用对标原句；硬事实只来自产品知识库事实片段。
"""
import re
import json

from . import util
from . import compliance
from . import personas as personas_mod


# ---------------- 目标时长 ----------------

def target_duration(persona, benchmark_duration):
    d = persona.get("duration") or {}
    lo = float(d.get("min") or 45)
    hi = float(d.get("max") or 60)
    if benchmark_duration:
        return round(max(lo * 0.8, min(hi * 1.2, float(benchmark_duration))), 1)
    return round((lo + hi) / 2.0, 1)


def _char_range(seconds):
    c = float(seconds or 60) * 4.2
    return int(c * 0.85), int(c * 1.15)


# ---------------- 结构和事实 ----------------

def _sanitize_breakdown(b):
    hook = b.get("hook") or {}
    return {
        "topic": b.get("topic"),
        "product_category": b.get("product_category"),
        "product_features": b.get("product_features") or [],
        "hook_type": hook.get("type"),
        "hook_function": hook.get("why_it_works"),
        "audience": b.get("audience"),
        "structure": [
            {k: s.get(k) for k in ("beat", "start", "end", "summary", "function")}
            for s in (b.get("structure") or [])
        ],
        "selling_points": [
            {"point": s.get("point"), "order": s.get("order")}
            for s in (b.get("selling_points") or [])
        ],
        "cta": {"type": (b.get("cta") or {}).get("type"),
                "mapping": (b.get("cta") or {}).get("mapping")},
        "tone": b.get("tone"),
        "copy_structure_for_us": b.get("copy_structure_for_us") or [],
        "avoid_copying": b.get("avoid_copying") or [],
        "pacing": b.get("pacing") or {},
    }


def _product_brief(product):
    if not product:
        return {"mode": "category", "name": "品类通用", "model": None, "facts": [], "fact_text": ""}
    status = product.get("status")
    if status == "category":
        return {"mode": "category", "name": product.get("name") or "品类通用",
                "category": product.get("category"), "model": None,
                "facts": [], "fact_text": ""}
    if status in ("uncertain", "pending_arrival"):
        return {"mode": "category", "name": "品类通用（产品型号待确认）",
                "category": product.get("category"), "model": None,
                "facts": [], "fact_text": "", "warning": product.get("warning")}
    return {
        "mode": "model",
        "name": product.get("name"),
        "model": product.get("model"),
        "category": product.get("category"),
        "facts": product.get("facts") or [],
        "fact_text": (product.get("fact_text") or "")[:5000],
        "doc_id": product.get("doc_id"),
        "warning": product.get("warning"),
    }


# ---------------- 生成 ----------------

def generate(account_id, persona, ref, transcript, breakdown, product, options=None):
    options = options or {}
    use_llm = options.get("use_llm", True)
    previous_body = options.get("previous_body")
    instruction = options.get("instruction")
    auto_fix = options.get("auto_fix", True)
    duration = target_duration(persona, (ref or {}).get("duration_sec"))
    cmin, cmax = _char_range(duration)
    brief = _product_brief(product)
    out = None
    if use_llm:
        out = _llm_generate(account_id, persona, ref, breakdown, brief,
                            duration, cmin, cmax, previous_body, instruction)
    if not out:
        out = _rule_generate(account_id, persona, ref, breakdown, brief, duration)
    out = _normalize(out, account_id, persona, brief)
    out = _fit_length(out, account_id, persona, brief, duration, cmin, cmax, use_llm)
    body_text = body_plain_text(out.get("body"))
    scan = compliance.scan_script(
        body_text, out.get("publish"), (transcript or {}).get("text") or "",
        brief.get("fact_text") or "", brief.get("facts") or [])
    if auto_fix and use_llm and scan.get("findings"):
        fixed = _llm_fix(out, scan.get("findings"), account_id, persona,
                         brief, duration, cmin, cmax)
        if fixed:
            fixed = _normalize(fixed, account_id, persona, brief)
            out = fixed
            body_text = body_plain_text(out.get("body"))
            scan = compliance.scan_script(
                body_text, out.get("publish"), (transcript or {}).get("text") or "",
                brief.get("fact_text") or "", brief.get("facts") or [])
    word_count = util.count_chars(body_text)
    estimated = util.estimate_seconds(body_text)
    out["word_count"] = word_count
    out["estimated_seconds"] = estimated
    out["target_seconds"] = duration
    out["char_range"] = [cmin, cmax]
    out["compliance"] = scan
    out["status"] = "待审" if scan.get("ok") else "合规待修"
    out["account_id"] = account_id
    out["account_label"] = persona.get("label")
    out["presenters"] = persona.get("presenters") or []
    out["body_text"] = body_text
    out["product"] = brief
    return out


def _llm_generate(account_id, persona, ref, breakdown, brief, duration, cmin, cmax,
                  previous_body=None, instruction=None):
    try:
        from insight import llm as xllm
    except Exception:
        return None
    mode = persona.get("format") or "monologue"
    mode = "dialogue" if mode in ("dialogue", "two_person_dialogue") else "monologue"
    presenters = persona.get("presenters") or []
    sanitized = _sanitize_breakdown(breakdown)
    stats = (ref or {}).get("stats") or {}
    facts_block = brief.get("fact_text") or "（无具体产品事实；只能写品类通用判断，不要写任何具体参数/型号）"
    facts_list = brief.get("facts") or []
    revision = ""
    if previous_body or instruction:
        revision = f"""
这是一次改稿。上一版：
{json.dumps(previous_body, ensure_ascii=False)[:5000]}

运营的修改指令：{instruction or '按合规/平台要求优化'}
请在保留对标结构和人设的前提下改，不要整篇重写成另一个主题。
"""
    if mode == "dialogue":
        format_rules = f"""- 双人问答：出镜 {'、'.join(presenters)}。心悦负责提问/总结，小冯负责演示/回答。
- body.format 必须是 "dialogue"；每行带 speaker（只能是 {'/'.join(presenters)}）。
- 至少一次真实操作：坐下、折叠、转向、刹车、调扶手、推一圈等，用一句台词带出来。
- 不要两个人同时讲长段独白。"""
    elif account_id == "oral":
        format_rules = """- 单人口播：出镜翔哥，第一人称，直接、短句、有判断。
- 开头 3 秒先给警告/反常识/判断，不要自我介绍、不要念品牌名。
- 中段 3-5 个判断点，每点一句结论 + 一句解释；不要堆参数。
- 如果发视频号，结尾自然加一个转发理由（转给要给爸妈选辅具的人）；不要在口播里说“点赞关注”超过一次。"""
    else:
        format_rules = """- 单人第一人称：出镜小冯，像跟街坊聊天，朴实、诚恳，允许少量昆山/江浙口语。
- 开头写一个可泛化的展厅观察或现场动作，不要编造“今天来了个老哥/阿姨”的具体客户故事。
- 只讲一个核心判断，用一个具体动作/细节支撑；不要写成参数播报。
- 结尾自然邀请到阳光大厦展厅看看，不硬推价格。"""
    prompt = f"""你在为佳康顺三号矩阵写一条原创口播逐字稿。

【账号人设】
- 账号：{persona.get('label')}（{account_id}）
- 人设：{persona.get('identity')}
- 受众：{'；'.join(persona.get('audience') or [])}
- 定位：{persona.get('positioning')}
- 语感：{'；'.join(persona.get('voice') or [])}
- 常用句式：{'；'.join(persona.get('sentence_patterns') or [])}
- 结构偏好：{'；'.join(persona.get('structure_pref') or [])}
- 默认 CTA：{persona.get('cta_style')}
- 拍摄地：苏州阳光大厦展厅（姑苏区西环路717号运智路阳光大厦911室）
- 拍摄备注：{'；'.join(persona.get('shoot_notes') or [])}

【对标视频】
- 平台：{util.platform_label((ref or {}).get('platform'))}
- 标题：{(ref or {}).get('title') or '—'}
- 作者：{(ref or {}).get('author') or '—'}
- 时长：{(ref or {}).get('duration_sec') or '—'} 秒
- 互动：赞 {stats.get('like')} / 评 {stats.get('comment')} / 转 {stats.get('share')}
- 结构拆解（只学结构，不要复用其中的措辞）：
{json.dumps(sanitized, ensure_ascii=False)[:6000]}

【产品事实】
- 模式：{brief.get('mode')} ｜ 型号：{brief.get('model') or '不写具体型号'} ｜ 名称：{brief.get('name')}
- 允许使用的事实片段（只能从这里取硬信息；没有的事实一律不写）：
{facts_block[:5000]}
- 可用事实列表：{json.dumps(facts_list, ensure_ascii=False)[:1800]}
{revision}
【硬要求】
- 目标时长 {duration} 秒，正文 {cmin}-{cmax} 字（按 4.2 字/秒）。
- 只写原创句子：保留对标的钩子类型、节奏、卖点顺序、CTA 类型，但每一句都重写；不得搬运原句、独特比喻、口头禅。
- 不写具体价格、优惠、到手价。
- 不承诺疗效/治愈/恢复行走/替代治疗；不出现患者/专家/医生推荐或见证；不与其他品牌对比；不用“最/第一/唯一/100%/绝对安全”等绝对化、保证性表述。
- 不编造数字、参数、案例；如果产品事实里没有数字，就只写定性判断。
- 不编造具体客户姓名、疾病诊断、成交细节、具体日期或“今天来了个……”的事件；个人号只写可泛化的展厅观察，除非运营明确提供了真实素材。
- 产品模式为 category 时，不要写具体型号和参数，只写品类选购逻辑。
- 产品模式为 model 时，型号只能写“{brief.get('model')}”，硬信息只能来自上面的片段。
- CTA 映射：{(breakdown.get('cta') or {}).get('mapping') or '按对标映射'}；落在真实地点/平台动作上。
{format_rules}

【发布说明】
- 不需要写标题、话题标签、封面文字或任何平台发布文案；运营会单独处理发布。
- 发布文案末尾由系统固定追加免责声明：{util.compliance_config().get('disclaimer')}

【输出】严格 JSON，不要 markdown 代码块：
{{
  "title": "脚本工作标题",
  "body": {{
    "format": "{mode}",
    "lines": [
      {{"speaker": "翔哥或心悦或小冯", "beat": "钩子/判断1/演示/转折/CTA", "text": "一句口播"}}
    ]
  }},
  "shooting_tips": ["3-5 条具体拍摄提示：景别/动作/道具/字幕"],
  "facts_used": [{{"claim": "用到的产品事实", "source": "doc_id"}}],
  "compliance_notes": ["需要人工注意的点"],
  "account_reason": "为什么这条适合该号",
  "product_reason": "为什么选这个产品/品类"
}}"""
    text = xllm.ask(prompt, system="你是佳康顺资深口播编剧，严格合规、只输出严格 JSON。",
                    temperature=0.7, max_tokens=3200)
    parsed = xllm.extract_json(text, expect="object") if text else None
    if isinstance(parsed, dict):
        return parsed
    text2 = xllm.ask("上一条没有返回可解析 JSON。请重新输出严格 JSON，只输出 JSON：\n" + prompt[-6000:],
                     system="只输出 JSON。", temperature=0.3, max_tokens=2800)
    parsed2 = xllm.extract_json(text2, expect="object") if text2 else None
    return parsed2 if isinstance(parsed2, dict) else None


def _llm_fix(out, findings, account_id, persona, brief, duration, cmin, cmax):
    try:
        from insight import llm as xllm
    except Exception:
        return None
    high = [f for f in findings if f.get("severity") == "high"]
    if not high:
        return None
    prompt = f"""下面这条口播稿命中了合规问题。请在不改变人设、结构、时长和产品事实的前提下改写。

账号：{persona.get('label')}（{account_id}）
目标：{duration} 秒 / {cmin}-{cmax} 字
产品：{brief.get('model') or '品类通用'}
产品事实（只能使用这些）：{(brief.get('fact_text') or '')[:3500]}

当前稿件 JSON：
{json.dumps({'title': out.get('title'), 'body': out.get('body'), 'shooting_tips': out.get('shooting_tips'), 'facts_used': out.get('facts_used')}, ensure_ascii=False)[:7000]}

合规问题：
{json.dumps(high, ensure_ascii=False)[:4000]}

要求：
- 删除/改写所有疗效、安全保证、绝对化、对比、患者/专家推荐、价格、未核实数字。
- 保留原有结构、卖点顺序、人设和 CTA 类型。
- 不得引入新的事实或数字。
- 不生成标题/标签/封面，只写口播逐字稿和拍摄提示。
- 只输出与原结构相同的严格 JSON：title/body/shooting_tips/facts_used/compliance_notes/account_reason/product_reason。"""
    text = xllm.ask(prompt, system="你是医疗广告合规编辑，只输出严格 JSON。",
                    temperature=0.2, max_tokens=2600)
    parsed = xllm.extract_json(text, expect="object") if text else None
    return parsed if isinstance(parsed, dict) else None


# ---------------- 规则兜底 ----------------

def _rule_generate(account_id, persona, ref, breakdown, brief, duration):
    title = (ref or {}).get("title") or "辅具怎么选"
    category = brief.get("category") or (breakdown.get("product_category") or "辅具")
    model = brief.get("model")
    product_name = brief.get("name") or category
    cta_map = (breakdown.get("cta") or {}).get("mapping") or "到苏州阳光大厦展厅试一圈"
    facts = brief.get("facts") or []
    fact_line = ""
    if facts:
        fact_line = "像" + str(facts[0].get("claim") or "")[:80] + "。"
    if account_id == "brand":
        lines = [
            {"speaker": "心悦", "beat": "钩子", "text": f"很多叔叔阿姨一来就问，{category}到底怎么选？"},
            {"speaker": "小冯", "beat": "演示", "text": f"来，我拿这台{product_name}给您演示一下，光看参数不如上手试。"},
            {"speaker": "心悦", "beat": "判断", "text": "那最该看哪几点？"},
            {"speaker": "小冯", "beat": "判断", "text": f"先看稳不稳、好不好操作、折叠收纳方不方便，再看坐上去舒不舒服。{fact_line}"},
            {"speaker": "心悦", "beat": "收束", "text": "明白了，还是要自己坐一坐、推一圈。"},
            {"speaker": "小冯", "beat": "CTA", "text": f"对，{cta_map}。"},
        ]
        fmt = "dialogue"
    elif account_id == "personal":
        lines = [
            {"speaker": "小冯", "beat": "场景", "text": "我是小冯，在苏州阳光大厦展厅。"},
            {"speaker": "小冯", "beat": "观察", "text": f"在展厅待久了你会发现，很多人选{category}，第一眼只看外观，回去用两天才发现不顺手。"},
            {"speaker": "小冯", "beat": "判断", "text": f"其实先看三件事：稳不稳、操作顺不顺手、收纳方不方便。{fact_line}"},
            {"speaker": "小冯", "beat": "收束", "text": "别急着买，来展厅坐一坐、推一圈，适不适合身体最知道。"},
            {"speaker": "小冯", "beat": "CTA", "text": cta_map + "。"},
        ]
        fmt = "monologue"
    else:
        lines = [
            {"speaker": "翔哥", "beat": "钩子", "text": f"买{category}之前，先别急着听销售怎么说。"},
            {"speaker": "翔哥", "beat": "判断1", "text": "第一，看稳不稳。车架、轮距、刹车，比花哨功能更重要。"},
            {"speaker": "翔哥", "beat": "判断2", "text": "第二，看好不好操作。老人能不能自己上手，比参数漂不漂亮重要。"},
            {"speaker": "翔哥", "beat": "判断3", "text": f"第三，看收纳和售后。{fact_line}"},
            {"speaker": "翔哥", "beat": "收束", "text": "记住这几条，能避开大部分坑。"},
            {"speaker": "翔哥", "beat": "CTA", "text": cta_map + "；关注翔哥，了解更多辅具知识。"},
        ]
        fmt = "monologue"
    body = {"format": fmt, "lines": lines}
    publish = {"disclaimer": util.compliance_config().get("disclaimer") or ""}
    return {
        "title": title,
        "body": body,
        "shooting_tips": [
            "在阳光大厦展厅实拍，背景带真车/真展厅，不要纯白墙。",
            "开头 3 秒人物入画，手里有产品细节或动作，不要空镜。",
            "关键判断句上字幕，字号大、对比强。",
            "至少一次真实操作：试坐、推车、折叠或刹车。",
        ],
        "publish": publish,
        "facts_used": facts[:3],
        "compliance_notes": ["规则兜底稿，建议人工润色后再拍。"],
        "account_reason": "按人设关键词规则匹配。",
        "product_reason": brief.get("name") or "品类通用。",
    }


# ---------------- 规范化 ----------------

def body_plain_text(body):
    if isinstance(body, dict):
        lines = body.get("lines") or []
        return "\n".join(str(x.get("text") or "").strip() for x in lines if isinstance(x, dict))
    if isinstance(body, list):
        return "\n".join(str(x.get("text") if isinstance(x, dict) else x) for x in body)
    return str(body or "")


def _normalize_publish(pub):
    pub = pub if isinstance(pub, dict) else {}
    return {"disclaimer": util.compliance_config().get("disclaimer") or pub.get("disclaimer") or ""}


def _ensure_cta(out, account_id, cmax=None):
    body = out.get("body") or {}
    lines = [x for x in (body.get("lines") or []) if isinstance(x, dict)]
    text_all = " ".join(str(x.get("text") or "") for x in lines)
    keys = ("关注", "评论区", "私信", "来展厅", "到展厅", "试一圈", "转给", "到店")
    if any(k in text_all for k in keys):
        return out
    cta = {
        "oral": "关注翔哥，了解更多辅具知识。",
        "brand": "来苏州阳光大厦展厅，坐一坐、试一圈。",
        "personal": "拿不准就来苏州阳光大厦展厅，我带你试一圈。",
    }.get(account_id, "来苏州阳光大厦展厅试一圈。")
    speaker = {
        "oral": "翔哥", "brand": "心悦", "personal": "小冯",
    }.get(account_id, "")
    lines.append({"speaker": speaker, "beat": "CTA", "text": cta})
    total = sum(util.count_chars(x.get("text") or "") for x in lines)
    while cmax and total > cmax and len(lines) > 3:
        removed = lines.pop(-2)
        total -= util.count_chars(removed.get("text") or "")
    out["body"] = {"format": body.get("format") or ("dialogue" if account_id == "brand" else "monologue"),
                   "lines": lines}
    return out


def _normalize(out, account_id, persona, brief):
    out = dict(out or {})
    if not out.get("title"):
        out["title"] = "未命名脚本"
    body = out.get("body")
    if isinstance(body, str):
        body = {"format": persona.get("format") or "monologue",
                "lines": [{"speaker": (persona.get("presenters") or [""])[0],
                           "beat": "", "text": body}]}
    if not isinstance(body, dict):
        body = {"format": persona.get("format") or "monologue", "lines": []}
    lines = []
    for x in (body.get("lines") or []):
        if isinstance(x, str):
            x = {"speaker": (persona.get("presenters") or [""])[0], "beat": "", "text": x}
        if not isinstance(x, dict):
            continue
        text = str(x.get("text") or "").strip()
        if not text:
            continue
        speaker = x.get("speaker") or (persona.get("presenters") or [""])[0]
        lines.append({"speaker": speaker, "beat": str(x.get("beat") or "")[:20], "text": text})
    fmt = body.get("format") or persona.get("format") or "monologue"
    if account_id == "brand":
        fmt = "dialogue"
    body = {"format": fmt, "lines": lines}
    out["body"] = body
    tips = out.get("shooting_tips") or []
    if isinstance(tips, str):
        tips = [tips]
    out["shooting_tips"] = [str(t).strip() for t in tips if str(t).strip()][:5]
    if len(out["shooting_tips"]) < 3:
        out["shooting_tips"] = (out["shooting_tips"] + [
            "在阳光大厦展厅实拍，背景带真车/真展厅。",
            "开头 3 秒人物入画，手里有产品细节或动作。",
            "关键判断句上大字号字幕。",
        ])[:3]
    out["publish"] = _normalize_publish(out.get("publish"))
    facts = out.get("facts_used") or []
    if not isinstance(facts, list):
        facts = []
    norm_facts = []
    for f in facts:
        if isinstance(f, dict):
            norm_facts.append({"claim": str(f.get("claim") or "")[:240],
                               "source": str(f.get("source") or "")})
        else:
            norm_facts.append({"claim": str(f)[:240], "source": ""})
    out["facts_used"] = norm_facts[:8]
    out["compliance_notes"] = [str(x) for x in (out.get("compliance_notes") or [])][:8]
    out["account_reason"] = str(out.get("account_reason") or "")[:300]
    out["product_reason"] = str(out.get("product_reason") or "")[:300]
    out = _ensure_cta(out, account_id)
    return out


# ---------------- 长度约束 ----------------

def _fit_length(out, account_id, persona, brief, duration, cmin, cmax, use_llm):
    text = body_plain_text(out.get("body"))
    n = util.count_chars(text)
    if n <= max(cmax + 12, int(cmax * 1.08)):
        return out
    if use_llm:
        compressed = _llm_compress(out, account_id, duration, cmin, cmax)
        if compressed:
            out["body"] = compressed
            out = _normalize(out, account_id, persona, brief)
            n = util.count_chars(body_plain_text(out.get("body")))
    if n > cmax:
        out["body"] = _trim_body(out.get("body"), cmax, account_id)
        out = _normalize(out, account_id, persona, brief)
    out.setdefault("compliance_notes", [])
    out["compliance_notes"] = list(out["compliance_notes"]) + [
        f"已按目标时长压缩：{duration} 秒 / 正文 {cmin}-{cmax} 字。"
    ]
    out = _ensure_cta(out, account_id, cmax)
    return out


def _llm_compress(out, account_id, duration, cmin, cmax):
    try:
        from insight import llm as xllm
    except Exception:
        return None
    body = out.get("body") or {}
    n = util.count_chars(body_plain_text(body))
    prompt = f"""把下面的口播逐字稿压缩到 {cmin}-{cmax} 字（目标 {duration} 秒）。

要求：
- 保留钩子、3-5 个判断点、转折、CTA 的顺序和功能。
- 不新增事实、不改变说话人、不改变人设。
- 删掉重复解释、例子和形容词，只留判断句和关键理由。
- {"双人问答保留一问一答，不要变成单人独白。" if account_id == "brand" else "保持单人语气。"}
- 只输出 body JSON：{{"format":"monologue 或 dialogue","lines":[{{"speaker":"...","beat":"...","text":"..."}}]}}

当前 {n} 字：
{json.dumps(body, ensure_ascii=False)[:7000]}"""
    text = xllm.ask(prompt, system="你是口播稿压缩编辑，只输出严格 JSON。",
                    temperature=0.2, max_tokens=1800)
    parsed = xllm.extract_json(text, expect="object") if text else None
    if not isinstance(parsed, dict):
        return None
    if isinstance(parsed.get("body"), dict):
        parsed = parsed["body"]
    if not isinstance(parsed.get("lines"), list):
        return None
    return parsed


def _trim_body(body, cmax, account_id):
    if not isinstance(body, dict):
        body = {"format": "monologue", "lines": [{"text": str(body)}]}
    lines = [x for x in (body.get("lines") or []) if isinstance(x, dict) and str(x.get("text") or "").strip()]
    # 同 beat 只留第一句；CTA 必须保留
    selected, seen = [], set()
    for line in lines:
        beat = str(line.get("beat") or "")
        if beat and beat in seen:
            continue
        selected.append(line)
        if beat:
            seen.add(beat)
    ctas = [x for x in lines if "CTA" in str(x.get("beat") or "")]
    if ctas:
        cta = ctas[-1]
        if not any(x is cta for x in selected):
            selected.append(cta)
    out, total = [], 0
    for line in selected:
        text = str(line.get("text") or "").strip()
        n = util.count_chars(text)
        if total + n > cmax and out:
            remain = cmax - total
            if remain >= 18:
                cut = re.split(r"[。！？!?；;]", text[:remain + 8])[0]
                if util.count_chars(cut) >= 10:
                    out.append({"speaker": line.get("speaker") or "", "beat": line.get("beat") or "",
                                "text": cut.rstrip("，,、 ") + "。"})
                    total += util.count_chars(cut)
            break
        out.append({"speaker": line.get("speaker") or "", "beat": line.get("beat") or "", "text": text})
        total += n
    if not out and lines:
        first = lines[0]
        out = [{"speaker": first.get("speaker") or "", "beat": first.get("beat") or "",
                "text": str(first.get("text") or "")[:cmax]}]
    return {"format": body.get("format") or ("dialogue" if account_id == "brand" else "monologue"),
            "lines": out}


# ---------------- 改稿 ----------------

def revise(script, instruction, use_llm=True, target_seconds=None):
    """基于已存脚本改稿，返回更新字段；不碰 DB。"""
    account_id = script.get("account_id") or "oral"
    persona = personas_mod.get(account_id) or {}
    body = script.get("body") or {}
    publish = script.get("publish") or {}
    facts = script.get("facts") or []
    product_brief = {
        "model": script.get("product_model"),
        "name": script.get("product_model") or "品类通用",
        "mode": "model" if script.get("product_model") else "category",
        "facts": facts,
        "fact_text": "；".join(f.get("claim") or "" for f in facts),
    }
    duration = float(target_seconds or script.get("target_seconds")
                     or script.get("estimated_seconds") or 60)
    cmin, cmax = _char_range(duration)
    out = None
    if use_llm:
        mini_breakdown = {
            "topic": script.get("benchmark_title"),
            "product_category": product_brief.get("name"),
            "cta": {"mapping": ""},
            "hook": {},
            "structure": [],
            "selling_points": [],
            "copy_structure_for_us": [],
            "avoid_copying": [],
        }
        out = _llm_generate(account_id, persona,
                            {"title": script.get("benchmark_title"),
                             "platform": script.get("source_platform"),
                             "duration_sec": duration},
                            mini_breakdown, product_brief, duration, cmin, cmax,
                            previous_body=body, instruction=instruction)
    if not out:
        out = {"title": script.get("title"), "body": body, "shooting_tips": script.get("shooting_tips"),
               "publish": publish, "facts_used": facts, "compliance_notes": ["规则兜底：仅按指令微调失败，保留原稿"],
               "account_reason": script.get("account_label") or "", "product_reason": ""}
    out = _normalize(out, account_id, persona, product_brief)
    out = _fit_length(out, account_id, persona, product_brief, duration, cmin, cmax, use_llm)
    body_text = body_plain_text(out.get("body"))
    scan = compliance.scan_script(body_text, out.get("publish"), "",
                                  product_brief.get("fact_text") or "", facts)
    out["compliance"] = scan
    out["status"] = "待审" if scan.get("ok") else "合规待修"
    out["word_count"] = util.count_chars(body_text)
    out["estimated_seconds"] = util.estimate_seconds(body_text)
    out["body_text"] = body_text
    return out
