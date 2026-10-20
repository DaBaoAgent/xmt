"""把 sg_scripts 的定稿整理成「对标 | 改稿」左右对照表的数据。

供腾讯文档表格导入用：每行一条稿，左列对标、右列改稿。
用法：
  python tools/build_tencent_table.py          # 打印 JSON（预览）
  python tools/build_tencent_table.py --md     # 打印 markdown（本地备用版）
"""
import os
import re
import sys
import json
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "xmt.db")

COLUMNS = [
    "序号",
    "账号｜出镜",
    "标题",
    "对标链接（点击看原片）",
    "对标信息",
    "对标结构拆解",
    "我的逐字稿",
    "时长 / 字数",
    "拍摄提示",
    "合规自检",
    "状态",
]

ACCOUNT_MAP = {
    "oral": "翔哥号（单人口播）｜翔哥",
    "brand": "品牌号（双人问答）｜心悦+小冯",
    "personal": "个人号（单人口播）｜小冯",
}


def _flat(text):
    return " ".join(str(text or "").split())


def load():
    if not os.path.exists(DB):
        print("找不到数据库：%s" % DB)
        return []
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        "SELECT * FROM sg_scripts ORDER BY created_at, id")]
    con.close()
    keep = {}
    for r in rows:
        keep[r["code"]] = r          # 同编号只留最新版本
    return [keep[c] for c in sorted(
        keep, key=lambda c: (keep[c].get("created_at") or "", c))]


def _keep_md_lines(text):
    """保留 markdown 的列表层级与换行，只压掉行内多余空格。"""
    lines = []
    for raw in str(text or "").splitlines():
        s = re.sub(r"[ \t]+", " ", raw).rstrip()
        if s:
            lines.append(s)
    return "\n".join(lines)


def _json_field(raw, *names):
    """从 breakdown_json 里取第一个存在的字段。"""
    try:
        d = json.loads(raw or "{}")
    except Exception:
        return ""
    for n in names:
        v = d.get(n)
        if v:
            return v
    return ""


def reference_of(con, script):
    """按 video_key 取对标元数据。"""
    key = script.get("video_key") or ""
    if not key:
        return {}
    cur = con.execute(
        "SELECT * FROM sg_reference_videos WHERE video_key=? ORDER BY id DESC LIMIT 1",
        (key,))
    row = cur.fetchone()
    return dict(row) if row else {}


def breakdown_of(con, script):
    """取该脚本对应的对标拆解（按 video_key 关联）。"""
    key = script.get("video_key") or ""
    if not key:
        return {}
    cur = con.execute(
        "SELECT * FROM sg_breakdowns WHERE video_key=? ORDER BY id DESC LIMIT 1",
        (key,))
    row = cur.fetchone()
    return dict(row) if row else {}


def _cta_text(val):
    """CTA 可能是 {type,text,mapping} 字典，拼成可读文本。"""
    if isinstance(val, dict):
        t = _flat(val.get("text") or val.get("cta") or "")
        m = _flat(val.get("mapping") or "")
        kind = _flat(val.get("type") or "")
        parts = [x for x in (t, m) if x]
        s = " ｜ ".join(parts)
        return ("（%s）%s" % (kind, s)) if kind and s else s
    return _flat(val)


def _text_lines(val):
    """把卖点列表渲染成可读文本（拆解里存的是 [{point,evidence,order}] 结构）。"""
    if isinstance(val, list):
        lines = []
        for i, x in enumerate(val, 1):
            if isinstance(x, dict):
                pt = _flat(x.get("point") or x.get("text") or x.get("claim") or "")
                ev = _flat(x.get("evidence") or x.get("source") or "")
                if pt and ev:
                    lines.append("%d. %s\n   原话：%s" % (i, pt, ev))
                elif pt:
                    lines.append("%d. %s" % (i, pt))
                elif ev:
                    lines.append("%d. %s" % (i, ev))
            else:
                lines.append("%d. %s" % (i, _flat(x)))
        return "\n".join(lines)
    return _flat(val)


def build():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    scripts = [r for r in load()
               if (r.get("status") or "") in ("待审", "已通过")
               and (r.get("body_md") or "").strip()]
    out = []
    for i, r in enumerate(scripts, 1):
        b = breakdown_of(con, r)
        ref = reference_of(con, r)
        bj = b.get("breakdown_json") or "{}"
        structure = _keep_md_lines(b.get("summary_md") or "")
        selling = _text_lines(_json_field(bj, "selling_points", "sellingPoints"))
        pace = _flat(_json_field(bj, "pace", "rhythm"))
        cta = _cta_text(_json_field(bj, "cta", "cta_text", "call_to_action"))
        platform = {"douyin": "抖音", "channels": "视频号",
                    "xiaohongshu": "小红书"}.get(r.get("source_platform") or "",
                                                 r.get("source_platform") or "")
        author = _flat(ref.get("author") or "")
        secs = ref.get("duration_sec")
        info_lines = ["平台：%s" % platform,
                      "作者：%s" % (author or "—"),
                      "原时长：%s" % (("%.1f 秒" % float(secs)) if secs else "—")]
        if pace:
            info_lines.append("节奏：%s" % pace)
        if cta:
            info_lines.append("")
            info_lines.append("【CTA】%s" % cta)
        url = r.get("benchmark_url") or ""
        out.append({
            "序号": i,
            "账号｜出镜": ACCOUNT_MAP.get(r.get("account_id"),
                                          r.get("account_label") or ""),
            "标题": r.get("title") or "",
            "对标链接（点击看原片）": url,
            "对标信息": "\n".join(info_lines),
            "对标结构拆解": structure or "（无）",
            "我的逐字稿": r.get("body_md") or "",
            "时长 / 字数": "约 %.1f 秒 ｜ %s 字" % (
                float(r.get("estimated_seconds") or 0), r.get("word_count") or "—"),
            "拍摄提示": "\n".join(
                "%d. %s" % (n, t) for n, t in
                enumerate(json.loads(r.get("shooting_tips_json") or "[]"), 1)) or "（无）",
            "合规自检": _compliance_text(r.get("compliance_json")),
            "状态": "%s ｜ 编号 %s ｜ v%s" % (
                r.get("status") or "", r.get("code"), r.get("version")),
        })
    con.close()
    return out


def _compliance_text(raw):
    try:
        c = json.loads(raw or "{}")
    except Exception:
        return "（无）"
    counts = c.get("counts") or {}
    head = "高危 %s ｜ 中危 %s ｜ 低危 %s → %s" % (
        counts.get("high", 0), counts.get("medium", 0), counts.get("low", 0),
        "通过" if c.get("ok") else "需处理")
    fs = c.get("findings") or []
    lines = [head]
    for f in fs:
        lines.append("· [%s] %s ｜「%s」%s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            ("→ " + str(f.get("suggest"))[:60]) if f.get("suggest") else ""))
    return "\n".join(lines)


def main():
    rows = build()
    if "--md" in sys.argv:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print("# 对标 vs 改稿 对照表\n")
        for r in rows:
            print("## 【%s】%s\n" % (r["序号"], r["标题"]))
            for k in COLUMNS[1:]:
                print("**%s**\n%s\n" % (k, r[k]))
            print("---\n")
        return
    out = {"columns": COLUMNS, "rows": rows}
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
