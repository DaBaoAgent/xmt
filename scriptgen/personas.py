"""三号人设卡：读取、展示、用现有作品提炼草案。"""
import json

from . import util


def load():
    data = util.personas_config()
    personas = data.get("personas") or []
    return {p.get("id"): p for p in personas if p.get("id")}


def get(persona_id):
    return load().get(persona_id)


def label(persona_id):
    p = get(persona_id) or {}
    return p.get("label") or persona_id or "—"


def labels():
    return {k: v.get("label") or k for k, v in load().items()}


def summaries():
    out = []
    for p in load().values():
        out.append(
            f"- {p.get('id')} / {p.get('label')}：{p.get('positioning')}；"
            f"出镜 {'、'.join(p.get('presenters') or [])}；"
            f"语感 {p.get('voice')}; "
            f"适合 {p.get('fit_keywords')}；不适合 {p.get('avoid_keywords')}"
        )
    return "\n".join(out)


def _works_for(account_ids, limit=30):
    import db
    if not account_ids:
        return []
    con = db.connect()
    q = ",".join("?" for _ in account_ids)
    rows = con.execute(
        f"""SELECT account_id,title,digg,comment,share,publish_time
            FROM works WHERE account_id IN ({q}) AND platform='douyin'
            ORDER BY COALESCE(publish_ts,0) DESC LIMIT ?""",
        (*account_ids, int(limit))).fetchall()
    top = con.execute(
        f"""SELECT account_id,title,digg,comment,share,publish_time
            FROM works WHERE account_id IN ({q}) AND platform='douyin'
            ORDER BY COALESCE(digg,0) DESC LIMIT ?""",
        (*account_ids, int(limit))).fetchall()
    con.close()
    return {"recent": [dict(r) for r in rows], "top": [dict(r) for r in top]}


def _samples_text(works, limit=18):
    lines = []
    seen = set()
    for bucket, label in (("top", "高赞"), ("recent", "最近")):
        lines.append(f"【{label}】")
        for w in (works.get(bucket) or [])[:limit]:
            t = (w.get("title") or "").strip().replace("\n", " ")
            if not t or t in seen:
                continue
            seen.add(t)
            lines.append(f"- {t}（赞 {w.get('digg')} / 评 {w.get('comment')} / 转 {w.get('share')}）")
    return "\n".join(lines)


def derive(use_llm=True, force=False):
    """分析三个抖音号近作 + 高赞作品，刷新人设卡草案。

    已确认（status=confirmed）的人设默认不覆盖；--force 才覆盖。
    """
    data = util.personas_config()
    if (data.get("status") or "").lower() == "confirmed" and not force:
        return {"ok": False, "reason": "人设卡已确认；如确需重提炼加 --force"}
    personas = load()
    evidence = {}
    for pid, p in personas.items():
        evidence[pid] = _works_for(p.get("account_ids") or [])

    if not use_llm:
        data["status"] = "draft"
        data["derived_at"] = util.now_iso()
        data["sources"] = evidence
        util.save_json("config/personas.json", data)
        return {"ok": True, "personas": personas, "reason": "未调用 LLM，仅刷新作品证据"}

    from insight import llm as xllm
    prompt = f"""你在为佳康顺三号矩阵提炼人设卡。只根据下面的事实，不要编造。

现有草案：
{json.dumps({'personas': list(personas.values())}, ensure_ascii=False)[:9000]}

三个号近期作品/高赞作品：
{json.dumps(evidence, ensure_ascii=False)[:12000]}

拍摄条件（硬约束）：
- 默认拍摄地：苏州阳光大厦展厅（姑苏区西环路717号运智路阳光大厦911室）。
- 口播号出镜：翔哥；品牌号出镜：心悦 + 小冯（双人问答）；个人号出镜：小冯。
- 只做佳康顺，不做爱优护；不写具体价格；不承诺疗效。
- 视频号生态：45-60秒要更沉稳、有转发钩子；抖音可更冲、更快。

请返回 JSON（不要 markdown 代码块），结构：
{{"personas": [
  {{"id":"oral|brand|personal","label":"口播号|品牌号|个人号",
    "identity":"...","audience":["..."],"positioning":"...",
    "voice":["..."],"sentence_patterns":["..."],"structure_pref":["..."],
    "cta_style":"...","fit_keywords":["..."],"avoid_keywords":["..."],
    "shoot_notes":["..."],"evidence":["..."]}}
], "notes":"需要老板确认的点"}}
每个字段要具体、可执行；保留现有字段里正确的部分，只改需要改的。"""
    text = xllm.ask(prompt, system="你是短视频人设与内容策略编辑，只输出严格 JSON。",
                    temperature=0.4, max_tokens=3500)
    parsed = xllm.extract_json(text, expect="object") if text else None
    new_list = (parsed or {}).get("personas") if isinstance(parsed, dict) else None
    if not new_list:
        return {"ok": False, "reason": "LLM 未返回可解析的人设 JSON，保留原草案"}

    by_id = {p.get("id"): p for p in new_list if p.get("id")}
    for pid, old in personas.items():
        new = by_id.get(pid)
        if not new:
            continue
        for k in ("identity", "audience", "positioning", "voice", "sentence_patterns",
                  "structure_pref", "cta_style", "fit_keywords", "avoid_keywords",
                  "shoot_notes", "evidence"):
            if new.get(k) not in (None, "", []):
                old[k] = new[k]
        old["status"] = "draft"
    data["personas"] = list(personas.values())
    data["status"] = "draft"
    data["derived_at"] = util.now_iso()
    data["notes"] = (parsed or {}).get("notes") if isinstance(parsed, dict) else None
    util.save_json("config/personas.json", data)
    return {"ok": True, "personas": personas, "notes": data.get("notes")}


def render_cards():
    data = util.personas_config()
    lines = [f"# 三号人设卡（{data.get('status') or 'draft'}）", ""]
    if data.get("derived_at"):
        lines.append(f"提炼时间：{data['derived_at']}")
        lines.append("")
    for p in data.get("personas") or []:
        lines.append(f"## {p.get('label')}（{p.get('id')}）")
        lines.append("")
        lines.append(f"- 出镜：{'、'.join(p.get('presenters') or [])} ｜ 形式：{p.get('format') or '—'}")
        lines.append(f"- 人设：{p.get('identity') or '—'}")
        lines.append(f"- 受众：{'；'.join(p.get('audience') or [])}")
        lines.append(f"- 定位：{p.get('positioning') or '—'}")
        lines.append(f"- 语感：{'；'.join(p.get('voice') or [])}")
        lines.append(f"- 常用句式：{'；'.join(p.get('sentence_patterns') or [])}")
        lines.append(f"- 结构偏好：{'；'.join(p.get('structure_pref') or [])}")
        lines.append(f"- CTA：{p.get('cta_style') or '—'}")
        lines.append(f"- 适合：{'、'.join(p.get('fit_keywords') or [])}")
        lines.append(f"- 不适合：{'、'.join(p.get('avoid_keywords') or [])}")
        lines.append(f"- 拍摄备注：{'；'.join(p.get('shoot_notes') or [])}")
        lines.append("")
    if data.get("notes"):
        lines.append(f"> 待确认：{data['notes']}")
        lines.append("")
    return "\n".join(lines)
