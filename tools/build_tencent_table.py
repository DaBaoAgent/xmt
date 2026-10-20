"""把 sg_scripts 的定稿整理成「对标 | 改稿」左右对照表。

供腾讯文档表格导入，或生成本地 HTML / markdown 备用版。
用法：
  python tools/build_tencent_table.py            # 打印 JSON（预览 / 供腾讯文档导入）
  python tools/build_tencent_table.py --md       # 输出 markdown
  python tools/build_tencent_table.py --html     # 生成 out/对标对照表.html（双击浏览器打开）
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

# 账号 id → (显示名, 出镜, 拍摄形式, 文件名, 卡片主色)
ACCOUNT_CARDS = {
    "oral": ("翔哥号", "翔哥", "单人口播", "对标对照表-翔哥号.html", "#f0d9bd"),
    "brand": ("品牌号", "心悦 + 小冯", "双人问答", "对标对照表-品牌号.html", "#c9b6e4"),
    "personal": ("个人号", "小冯", "单人口播", "对标对照表-个人号.html", "#b8d4ea"),
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
            "_account_id": r.get("account_id") or "oral",
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


HTML_TMPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>对标 vs 改稿 · 左右对照表</title>
<style>
  :root{
    --bg:#f6f7f9; --card:#fff; --ink:#1a1d21; --ink2:#5d6672; --line:#e2e5ea;
    --left:#fff8f0; --leftline:#f0d9bd; --right:#f0f7ff; --rightline:#c5dcf5;
    --ok:#0a7d3e; --okbg:#e8f6ed; --warn:#9a6100; --warnbg:#fff5e0;
    --accent:#1f5fd0;
  }
  *{box-sizing:border-box}
  body{margin:0;padding:26px 20px 60px;background:var(--bg);color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;
    line-height:1.6;font-size:14px}
  .wrap{max-width:1500px;margin:0 auto}
  h1{font-size:23px;margin:0 0 4px;letter-spacing:-.3px}
  .sub{color:var(--ink2);font-size:13px;margin-bottom:8px}
  .tip{background:#fff;border:1px solid var(--line);border-left:3px solid var(--accent);
    border-radius:0 8px 8px 0;padding:10px 14px;font-size:13px;margin:12px 0 20px;color:var(--ink2)}
  .tip b{color:var(--ink)}
  .card{background:var(--card);border:1px solid var(--line);border-radius:12px;
    margin-bottom:20px;overflow:hidden}
  .chead{display:flex;align-items:flex-start;gap:12px;padding:15px 20px;
    border-bottom:1px solid var(--line);background:#fbfcfd}
  .no{flex:none;width:30px;height:30px;border-radius:8px;background:var(--accent);
    color:#fff;font-weight:700;font-size:14px;display:flex;align-items:center;
    justify-content:center}
  .ctitle{font-size:17px;font-weight:600;line-height:1.4}
  .cmeta{font-size:12.5px;color:var(--ink2);margin-top:3px}
  .pill{display:inline-block;padding:1.5px 8px;border-radius:999px;font-size:11.5px;
    font-weight:600;white-space:nowrap}
  .p-ok{background:var(--okbg);color:var(--ok)}
  .p-info{background:#eaf1fd;color:var(--accent)}
  .cols{display:grid;grid-template-columns:1fr 1fr}
  .col{padding:16px 20px;min-width:0}
  .col.left{background:var(--left);border-right:1px solid var(--line)}
  .col.right{background:var(--right)}
  .coltag{font-size:11.5px;font-weight:700;letter-spacing:.06em;
    color:var(--ink2);margin-bottom:11px;display:flex;align-items:center;gap:6px}
  .coltag:before{content:"";width:3px;height:12px;border-radius:2px;background:var(--ink2)}
  .col.left .coltag:before{background:#c9873f}
  .col.right .coltag:before{background:var(--accent)}
  h4{font-size:12px;color:var(--ink2);font-weight:700;margin:14px 0 6px;
    letter-spacing:.03em}
  h4:first-of-type{margin-top:0}
  .body{white-space:pre-wrap;word-break:break-word;font-size:13.5px;line-height:1.75}
  .script{background:#fff;border:1px solid var(--rightline);border-radius:9px;
    padding:13px 15px;white-space:pre-wrap;word-break:break-word;
    font-size:14.5px;line-height:1.95}
  a.vlink{display:inline-flex;align-items:center;gap:6px;background:#fff;
    border:1px solid var(--leftline);border-radius:8px;padding:7px 12px;
    color:#b1620e;text-decoration:none;font-size:13px;font-weight:600}
  a.vlink:hover{background:#fff3e2}
  details{margin-top:8px}
  summary{cursor:pointer;font-size:12.5px;font-weight:600;color:var(--accent);
    padding:5px 0;user-select:none}
  summary:hover{text-decoration:underline}
  details[open] summary{margin-bottom:7px}
  .detail{background:#fff;border:1px solid var(--line);border-radius:8px;padding:11px 13px;
    font-size:12.5px;line-height:1.7;max-height:460px;overflow:auto}
  .kvlist{background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px 13px;
    font-size:12.5px;line-height:1.75}
  .kvlist div+div{margin-top:3px}
  .badge{display:inline-block;background:var(--okbg);color:var(--ok);font-weight:700;
    padding:1px 7px;border-radius:5px;margin-right:5px}
  .foot{color:var(--ink2);font-size:12.5px;text-align:center;margin-top:26px}
  .empty{color:var(--ink2);font-size:13px}
  a.acct{display:flex;align-items:center;gap:12px;background:var(--card);
    border:1px solid var(--line);border-radius:12px;padding:15px 20px;margin-bottom:14px;
    text-decoration:none;color:inherit;transition:box-shadow .15s,border-color .15s}
  a.acct:hover{border-color:var(--accent);box-shadow:0 2px 10px rgba(31,95,208,.12)}
  a.acct .no{background:var(--accent)}
  @media(max-width:1000px){.cols{grid-template-columns:1fr}.col.left{border-right:none;
    border-bottom:1px solid var(--line)}}
</style>
</head>
<body>
<div class="wrap">
  <h1>__ACCT__ · 对标 vs 改稿</h1>
  <div class="sub">出镜：__PRES__ ｜ 形式：__FORM__ ｜ __COUNT__ ｜ 生成于 __TIME__</div>
  <div class="tip">
    <b>用法</b>：点左侧「▶ 看原片」跳到视频 → 对着右侧逐字稿看结构怎么改的 → 右边是可直接拿去拍的版本。
    对标原片有价格和数字的，<b>一个都不能照抄</b>，只能学它的结构。
  </div>
  __CARDS__
  <div class="foot">由 tools/build_tencent_table.py 自动生成 ｜ 出新稿后重跑即可刷新</div>
</div>
</body>
</html>
"""


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _kv_html(text):
    """把「平台：xxx」这类行渲染成小列表。"""
    lines = [x.strip() for x in str(text or "").splitlines() if x.strip()]
    if not lines:
        return '<div class="empty">（无）</div>'
    return '<div class="kvlist">' + "".join(
        "<div>%s</div>" % _esc(x) for x in lines) + "</div>"


def _card_html(r, idx=None):
    url = str(r.get("对标链接（点击看原片）") or "")
    url_html = ('<a class="vlink" href="%s" target="_blank" rel="noopener">▶ 看原片</a>'
                % _esc(url)) if url.startswith("http") else '<div class="empty">（无链接）</div>'
    structure = str(r.get("对标结构拆解") or "")
    tips = str(r.get("拍摄提示") or "")
    comp = str(r.get("合规自检") or "")
    passed = "通过" in comp
    no = idx if idx is not None else r.get("序号")
    meta_bits = [str(r.get("时长 / 字数") or ""), str(r.get("状态") or "")]
    return f"""
<div class="card">
  <div class="chead">
    <div class="no">{no}</div>
    <div>
      <div class="ctitle">{_esc(r.get('标题'))}</div>
      <div class="cmeta">{_esc(' ｜ '.join(b for b in meta_bits if b))}</div>
    </div>
  </div>
  <div class="cols">
    <div class="col left">
      <div class="coltag">对标（原片）</div>
      <h4>视频</h4>
      {url_html}
      <h4>基本信息</h4>
      {_kv_html(r.get('对标信息'))}
      <h4>结构拆解</h4>
      <details{' open' if len(structure) < 700 else ''}>
        <summary>{'收起' if len(structure) < 700 else '展开看完整拆解（%d 字）' % len(structure)}</summary>
        <div class="detail">{_esc(structure)}</div>
      </details>
    </div>
    <div class="col right">
      <div class="coltag">改稿（可拍）</div>
      <h4>逐字稿</h4>
      <div class="script">{_esc(r.get('我的逐字稿'))}</div>
      <h4>拍摄提示</h4>
      <div class="body">{_esc(tips)}</div>
      <h4>合规自检</h4>
      <div class="body"><span class="badge">{'通过' if passed else '需处理'}</span>{_esc(comp)}</div>
    </div>
  </div>
</div>"""


def _render_html(rows, acct_id):
    """把某账号的稿子渲染成完整 HTML。"""
    from datetime import datetime
    label, present, form, _fname, tone = ACCOUNT_CARDS[acct_id]
    cards = "\n".join(_card_html(r, idx) for idx, r in enumerate(rows, 1))
    if not cards:
        cards = ('<div class="card"><div class="coltag">暂无定稿</div>'
                 '<p class="empty">给我对标链接并说明是这个号，出稿后会自动出现在这里。</p></div>')
    html = (HTML_TMPL
            .replace("__ACCT__", label)
            .replace("__PRES__", present)
            .replace("__FORM__", form)
            .replace("__CARDS__", cards)
            .replace("__COUNT__", ("共 %d 条定稿" % len(rows)) if rows else "暂无定稿")
            .replace("__N__", str(len(rows)))
            .replace("__TONE__", tone)
            .replace("__TIME__", datetime.now().strftime("%Y-%m-%d %H:%M")))
    return html


def write_html(rows_by_acc, out_dir=None):
    """按账号分别生成 HTML，返回 [(文件名, 条数), ...]。"""
    out_dir = out_dir or os.path.join(ROOT, "out", "对标对照表")
    os.makedirs(out_dir, exist_ok=True)
    made = []
    for acct_id, (label, _p, _f, fname, _t) in ACCOUNT_CARDS.items():
        rows = rows_by_acc.get(acct_id) or []
        # 每号内部按创建顺序重新编号
        path = os.path.join(out_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(_render_html(rows, acct_id))
        made.append((fname, len(rows)))
    # 留一个入口页，方便一次打开三个
    index = os.path.join(out_dir, "index.html")
    links = "".join(
        '<a class="acct" href="%s"><div class="no">%d</div><div>'
        '<div class="ctitle">%s</div><div class="cmeta">%s</div></div></a>'
        % (fn, n, ACCOUNT_CARDS[a][0], _acc_note(n))
        for a, (fn, n) in zip(ACCOUNT_CARDS, made))
    with open(index, "w", encoding="utf-8") as f:
        f.write(_index_html(links))
    made.append(("index.html", -1))
    return made


def _acc_note(n):
    return ("共 %d 条定稿" % n) if n else "暂无定稿"


def _index_html(links):
    from datetime import datetime
    return HTML_TMPL.replace("__ACCT__", "全部账号") \
        .replace("__PRES__", "翔哥 / 心悦+小冯 / 小冯") \
        .replace("__FORM__", "三个号分开管理") \
        .replace("__CARDS__", links) \
        .replace("__COUNT__", "点下面卡片进各自的文档") \
        .replace("__N__", "3") \
        .replace("__TONE__", "#f0d9bd") \
        .replace("__TIME__", datetime.now().strftime("%Y-%m-%d %H:%M"))


def main():
    rows = build()
    if "--html" in sys.argv:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        rows_by_acc = {}
        for r in rows:
            rows_by_acc.setdefault(
                r.get("_account_id") or "oral", []).append(r)
        made = write_html(rows_by_acc)
        base = os.path.join(ROOT, "out", "对标对照表")
        for fn, n in made:
            print("%-32s %s" % (fn, ("%d 条" % n) if n >= 0 else "（入口页）"))
        print("目录：%s" % base)
        return
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
