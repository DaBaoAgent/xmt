"""Markdown 渲染：对标知识库、逐字稿脚本、批次报告、索引。"""
import os
import json
from datetime import datetime

from . import util


def _yaml(v):
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_yaml(x) for x in v) + "]"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return json.dumps("" if v is None else str(v), ensure_ascii=False)


def _fmt_time(sec):
    if sec is None:
        return "—"
    try:
        sec = float(sec)
    except Exception:
        return "—"
    if sec < 60:
        return f"{sec:.1f}s"
    return f"{int(sec // 60)}m{int(round(sec % 60)):02d}s"


def _stat_line(stats):
    s = stats or {}
    bits = []
    for k, label in (("like", "赞"), ("comment", "评论"), ("share", "转发"),
                     ("collect", "收藏"), ("play", "播放")):
        if s.get(k) is not None:
            bits.append(f"{label} {s[k]}")
    return " · ".join(bits) if bits else "—"


# ---------------- 对标知识库 ----------------

def render_reference(ref, transcript=None, breakdown=None):
    stats = ref.get("stats") or {}
    lines = []
    lines.append("---")
    lines.append(f"type: 对标视频")
    lines.append(f"platform: {_yaml(ref.get('platform'))}")
    lines.append(f"video_id: {_yaml(ref.get('video_id'))}")
    lines.append(f"author: {_yaml(ref.get('author'))}")
    lines.append(f"title: {_yaml(ref.get('title'))}")
    lines.append(f"url: {_yaml(ref.get('url'))}")
    lines.append(f"publish_time: {_yaml(ref.get('publish_time'))}")
    lines.append(f"duration_sec: {_yaml(ref.get('duration_sec'))}")
    lines.append(f"collected_at: {_yaml(ref.get('last_seen') or util.now_iso())}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {ref.get('title') or (ref.get('author') or '对标视频')}")
    lines.append("")
    lines.append("## 作品元数据")
    lines.append("")
    lines.append("| 字段 | 值 |")
    lines.append("|---|---|")
    for label, key in (("平台", "platform"), ("作者", "author"), ("作者ID", "author_id"),
                       ("作品ID", "video_id"), ("发布时间", "publish_time"),
                       ("时长", "duration_sec"), ("链接", "url"),
                       ("元数据来源", "metadata_source")):
        val = ref.get(key)
        if key == "duration_sec":
            val = _fmt_time(val)
        if key == "platform":
            val = util.platform_label(val)
        lines.append(f"| {label} | {util.md_escape_cell(val)} |")
    lines.append(f"| 互动 | {util.md_escape_cell(_stat_line(stats))} |")
    tags = ref.get("tags") or []
    if tags:
        lines.append(f"| 话题 | {' '.join('#' + str(t).lstrip('#') for t in tags)} |")
    lines.append("")

    if breakdown:
        lines.append("## 结构拆解摘要")
        lines.append("")
        lines.append(summarize_breakdown_md(breakdown))
        lines.append("")

    if transcript:
        lines.append("## 口播全文")
        lines.append("")
        text = transcript.get("text") or ""
        for p in str(text).split("\n"):
            if p.strip():
                lines.append("> " + p.strip())
        lines.append("")
        segs = transcript.get("segments") or []
        if segs:
            lines.append("## 逐句时间轴")
            lines.append("")
            lines.append("| # | 开始 | 结束 | 台词 |")
            lines.append("|---|---|---|---|")
            for i, s in enumerate(segs, 1):
                lines.append(f"| {i} | {_fmt_time(s.get('start'))} | {_fmt_time(s.get('end'))} | "
                             f"{util.md_escape_cell(s.get('text'))} |")
            lines.append("")
        meta_bits = [f"转写来源：{transcript.get('source') or '—'}"]
        if transcript.get("task_id"):
            meta_bits.append(f"任务：{transcript['task_id']}")
        lines.append("> " + " ｜ ".join(meta_bits))
        lines.append("")

    lines.append("## 使用说明")
    lines.append("")
    lines.append("- 本文件是本地对标素材，含第三方口播原文，仅用于内部结构学习，不对外发布。")
    lines.append("- 生成新脚本时只学钩子/节奏/卖点顺序/CTA，必须重写每一句话。")
    lines.append("")
    return "\n".join(lines)


def summarize_breakdown_md(b):
    if not b:
        return "（未拆解）"
    lines = []
    hook = b.get("hook") or {}
    lines.append(f"- **钩子**：{hook.get('type') or '—'} ｜ {hook.get('text') or '—'}")
    lines.append(f"  - 为什么有效：{hook.get('why_it_works') or '—'}")
    if b.get("audience"):
        lines.append(f"- **受众**：{b['audience']}")
    if b.get("topic"):
        lines.append(f"- **主题/品类**：{b['topic']} ｜ {b.get('product_category') or '—'}")
    struct = b.get("structure") or []
    if struct:
        lines.append("- **结构**：")
        for s in struct:
            lines.append(f"  - {s.get('beat') or '—'}（{_fmt_time(s.get('start'))}–{_fmt_time(s.get('end'))}）："
                         f"{s.get('summary') or '—'}；作用：{s.get('function') or '—'}")
    sp = b.get("selling_points") or []
    if sp:
        lines.append("- **卖点顺序**：")
        for i, s in enumerate(sp, 1):
            if isinstance(s, dict):
                lines.append(f"  {i}. {s.get('point') or '—'}（证据：{s.get('evidence') or '—'}）")
            else:
                lines.append(f"  {i}. {s}")
    cta = b.get("cta") or {}
    if cta:
        lines.append(f"- **CTA**：{cta.get('type') or '—'} ｜ {cta.get('text') or '—'} ｜ 映射：{cta.get('mapping') or '—'}")
    pacing = b.get("pacing") or {}
    if pacing:
        lines.append(f"- **节奏**：时长 {_fmt_time(pacing.get('duration_sec'))} ｜ 分段 {pacing.get('segments') or '—'} ｜ "
                     f"平均 {pacing.get('avg_segment_sec') or '—'}s")
    if b.get("tone"):
        lines.append(f"- **语感**：{b['tone']}")
    copy = b.get("copy_structure_for_us") or []
    if copy:
        lines.append("- **可学的结构**：")
        for x in copy:
            lines.append(f"  - {x}")
    avoid = b.get("avoid_copying") or []
    if avoid:
        lines.append("- **不要复刻**：")
        for x in avoid:
            lines.append(f"  - {x}")
    acc = b.get("account_selection") or {}
    if acc:
        lines.append(f"- **账号判断**：{acc.get('account_label') or acc.get('account') or '—'} ｜ "
                     f"置信度 {acc.get('confidence', '—')} ｜ {acc.get('reason') or '—'}")
    prod = b.get("product_selection") or {}
    if prod:
        lines.append(f"- **选品判断**：{prod.get('model') or prod.get('category') or '—'} ｜ "
                     f"置信度 {prod.get('confidence', '—')} ｜ {prod.get('reason') or '—'}")
    return "\n".join(lines)


# ---------------- 逐字稿脚本 ----------------

def _body_lines(body):
    """兼容 body 为 dict / list / str。"""
    if isinstance(body, dict):
        lines = body.get("lines") or []
        if lines:
            return lines, body.get("format") or "monologue"
        text = body.get("plain_text") or body.get("text") or ""
    elif isinstance(body, list):
        return body, "monologue"
    else:
        text = str(body or "")
    return [{"speaker": "", "text": text, "beat": ""}], "monologue"


def _line_seconds(line):
    return util.estimate_seconds(line.get("text") or "")


def _timeline_lines(body):
    lines, fmt = _body_lines(body)
    t = 0.0
    out = []
    for line in lines:
        if not isinstance(line, dict):
            line = {"text": str(line)}
        sec = max(0.8, _line_seconds(line))
        out.append((t, t + sec, line))
        t += sec
    return out, fmt, t


def render_script(script):
    s = script
    title = s.get("title") or "未命名脚本"
    status = s.get("status") or "待审"
    presenters = s.get("presenters") or []
    compliance = s.get("compliance") or {}
    facts = s.get("facts") or []
    lines = []
    lines.append("---")
    lines.append(f"code: {_yaml(s.get('code'))}")
    lines.append(f"status: {_yaml(status)}")
    lines.append(f"account: {_yaml(s.get('account_label'))}")
    lines.append(f"account_id: {_yaml(s.get('account_id'))}")
    lines.append(f"presenters: {_yaml(presenters)}")
    lines.append(f"product: {_yaml(s.get('product_model') or '品类通用')}")
    lines.append(f"source_platform: {_yaml(s.get('source_platform'))}")
    lines.append(f"benchmark_url: {_yaml(s.get('benchmark_url'))}")
    lines.append(f"word_count: {_yaml(s.get('word_count'))}")
    lines.append(f"estimated_seconds: {_yaml(s.get('estimated_seconds'))}")
    lines.append(f"created_at: {_yaml(s.get('created_at'))}")
    lines.append(f"version: {_yaml(s.get('version'))}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"> 账号：**{s.get('account_label') or '—'}** ｜ 出镜：{'、'.join(presenters) or '—'} ｜ "
                 f"拍摄地：苏州阳光大厦展厅（姑苏区西环路717号运智路阳光大厦911室）")
    lines.append(f"> 产品：**{s.get('product_model') or '品类通用（不写具体型号）'}** ｜ "
                 f"对标：{s.get('benchmark_title') or '—'}（{util.platform_label(s.get('source_platform'))}）")
    lines.append(f"> 时长：约 {s.get('estimated_seconds') or '—'} 秒 ｜ 字数：{s.get('word_count') or '—'} ｜ "
                 f"状态：**{status}**")
    lines.append("")

    bd = s.get("breakdown") or {}
    if bd:
        lines.append("## 一、对标结构（只学结构，不抄内容）")
        lines.append("")
        lines.append(summarize_breakdown_md(bd))
        lines.append("")

    lines.append("## 二、口播逐字稿")
    lines.append("")
    timeline, fmt, total = _timeline_lines(s.get("body"))
    if fmt == "dialogue":
        for start, end, line in timeline:
            sp = line.get("speaker") or "—"
            beat = line.get("beat") or ""
            beat_txt = f"［{beat}］" if beat else ""
            lines.append(f"**{sp}（{_fmt_time(start)}–{_fmt_time(end)}）**：{beat_txt}{line.get('text') or ''}")
            lines.append("")
    else:
        for start, end, line in timeline:
            beat = line.get("beat") or ""
            beat_txt = f"［{beat}］" if beat else ""
            lines.append(f"**【{_fmt_time(start)}–{_fmt_time(end)}】** {beat_txt}{line.get('text') or ''}")
            lines.append("")
    if total:
        lines.append(f"> 预计口播时长：约 {total:.1f} 秒（按 {4.2} 字/秒估算；实际以试读为准）")
        lines.append("")

    tips = s.get("shooting_tips") or []
    if tips:
        lines.append("## 三、拍摄提示")
        lines.append("")
        for i, t in enumerate(tips, 1):
            lines.append(f"{i}. {t}")
        lines.append("")

    lines.append("## 四、合规自检")
    lines.append("")
    findings = compliance.get("findings") or []
    if findings:
        lines.append("| 等级 | 命中 | 说明 | 建议 |")
        lines.append("|---|---|---|---|")
        for f in findings:
            lines.append(f"| {f.get('severity') or '—'} | {util.md_escape_cell(f.get('match'))} | "
                         f"{util.md_escape_cell(f.get('message'))} | {util.md_escape_cell(f.get('suggest'))} |")
        lines.append("")
    else:
        lines.append("- 自动扫描：未命中禁用词/高风险表述。")
    lines.append(f"- 自动扫描结论：**{'通过' if compliance.get('ok') else '需人工修改'}**")
    review = (compliance.get("medical_review_note")
              or util.compliance_config().get("medical_review_note"))
    if review:
        lines.append(f"- 医疗器械广告审查提示：{review}")
    disclaimer = (compliance.get("disclaimer")
                  or util.compliance_config().get("disclaimer"))
    if disclaimer:
        lines.append(f"- 发布文案末尾固定追加：{disclaimer}")
    checks = (compliance.get("publish_checks")
              or util.compliance_config().get("publish_checks") or [])
    for c in checks:
        lines.append(f"- [ ] {c}")
    lines.append("")

    if facts:
        lines.append("## 五、事实来源")
        lines.append("")
        lines.append("| 事实 | 来源 |")
        lines.append("|---|---|")
        for f in facts:
            if isinstance(f, dict):
                lines.append(f"| {util.md_escape_cell(f.get('claim'))} | {util.md_escape_cell(f.get('source'))} |")
            else:
                lines.append(f"| {util.md_escape_cell(f)} | — |")
        lines.append("")

    lines.append(f"## {'六' if facts else '五'}、修改记录")
    lines.append("")
    lines.append("| 版本 | 时间 | 指令 |")
    lines.append("|---|---|---|")
    for v in s.get("versions") or []:
        lines.append(f"| v{v.get('version')} | {util.md_escape_cell(v.get('created_at'))} | "
                     f"{util.md_escape_cell(v.get('instruction') or '初稿')} |")
    if not s.get("versions"):
        lines.append(f"| v1 | {util.md_escape_cell(s.get('created_at'))} | 初稿 |")
    lines.append("")
    lines.append("---")
    lines.append(f"生成时间：{util.now_iso()} ｜ 文件：`{s.get('file_path') or ''}`")
    lines.append("")
    return "\n".join(lines)


# ---------------- 批次 ----------------

def render_batch(batch):
    b = batch
    lines = []
    lines.append(f"# 脚本批次 {b.get('batch_code')}")
    lines.append("")
    lines.append(f"- 生成时间：{b.get('created_at')}")
    lines.append(f"- 总条数：{b.get('total')} ｜ 成功：{b.get('succeeded')} ｜ 失败：{b.get('failed')} ｜ "
                 f"待确认：{b.get('pending_confirmation')}")
    lines.append(f"- RedFox 计费调用：{(b.get('result') or {}).get('billable_calls', '—')} ｜ "
                 f"轮询：{(b.get('result') or {}).get('poll_calls', '—')}")
    lines.append("")
    items = (b.get("result") or {}).get("items") or []
    lines.append("## 处理结果")
    lines.append("")
    lines.append("| # | 平台 | 对标 | 账号 | 产品 | 状态 | 脚本 | Word |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for i, it in enumerate(items, 1):
        word = os.path.basename(it.get("docx_path") or "")
        lines.append(f"| {i} | {util.platform_label(it.get('platform'))} | "
                     f"{util.md_escape_cell(it.get('title') or it.get('url'))} | "
                     f"{util.md_escape_cell(it.get('account_label') or '—')} | "
                     f"{util.md_escape_cell(it.get('product') or '—')} | "
                     f"{util.md_escape_cell(it.get('status'))} | "
                     f"{util.md_escape_cell(it.get('code') or '—')} | "
                     f"{util.md_escape_cell(word or '—')} |")
    lines.append("")
    lines.append("> 打印版 Word 在 `out/`；内部 Markdown、批次报告在 `data/scriptgen/`。")
    lines.append("")
    pending = (b.get("result") or {}).get("pending") or []
    if pending:
        lines.append("## 待确认（回复编号 + 选择）")
        lines.append("")
        lines.append("| # | 平台 | 对标 | 候选账号 | 候选产品 | 理由 |")
        lines.append("|---|---|---|---|---|---|")
        for it in pending:
            lines.append(f"| {it.get('index')} | {util.platform_label(it.get('platform'))} | "
                         f"{util.md_escape_cell(it.get('title') or it.get('url'))} | "
                         f"{util.md_escape_cell('、'.join(it.get('account_candidates') or []))} | "
                         f"{util.md_escape_cell('、'.join(it.get('product_candidates') or []))} | "
                         f"{util.md_escape_cell(it.get('reason'))} |")
        lines.append("")
    failures = [it for it in items if it.get("status") == "失败"]
    if failures:
        lines.append("## 失败明细")
        lines.append("")
        for it in failures:
            lines.append(f"- {it.get('url')}：{it.get('error') or '未知错误'}")
        lines.append("")
    lines.append("## 使用提示")
    lines.append("")
    lines.append("- 低置信度条目不生成最终稿；选好账号/产品后用 `python -m scriptgen resolve <批次号> ...` 补写。")
    lines.append("- 脚本默认「待审」；确认后用 `python -m scriptgen approve <编号>`。")
    lines.append("- 只有「已通过」的脚本才能 `sync` 到公司知识库。")
    lines.append("")
    return "\n".join(lines)


def render_index(scripts):
    lines = ["# 脚本索引", "", f"更新时间：{util.now_iso()}", ""]
    lines.append("| 编号 | 日期 | 账号 | 标题 | 状态 | 产品 | 预估秒 | 版本 | Word |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for s in scripts:
        path = s.get("docx_path") or ""
        rel = os.path.relpath(path, util.ROOT).replace(os.sep, "/") if path else ""
        lines.append(f"| {s.get('code')} | {(s.get('created_at') or '')[:10]} | "
                     f"{util.md_escape_cell(s.get('account_label'))} | "
                     f"{util.md_escape_cell(s.get('title'))} | {util.md_escape_cell(s.get('status'))} | "
                     f"{util.md_escape_cell(s.get('product_model') or '品类')} | "
                     f"{s.get('estimated_seconds') or '—'} | v{s.get('version') or 1} | "
                     f"{util.md_escape_cell(rel)} |")
    lines.append("")
    return "\n".join(lines)
