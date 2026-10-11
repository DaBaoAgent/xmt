"""读取 SQLite 快照，生成自包含看板 HTML（无外部依赖）。"""
import os
import json
import html
from datetime import datetime

import db

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "config", "accounts.json")
OUT = os.path.join(HERE, "out", "dashboard.html")

PLATFORM_LABEL = {"douyin": "抖音", "xiaohongshu": "小红书", "channels": "视频号"}
PLATFORM_ORDER = ["douyin", "xiaohongshu", "channels"]


def fmt(n):
    if n is None:
        return "—"
    try:
        n = int(n)
    except Exception:
        return str(n)
    if n >= 100000000:
        return f"{n/100000000:.2f}亿"
    if n >= 10000:
        return f"{n/10000:.1f}万"
    return f"{n:,}"


def sparkline(values, w=120, h=28, color="#4f7cff"):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return '<span class="muted">—</span>'
    mn, mx = min(vals), max(vals)
    rng = (mx - mn) or 1
    step = w / (len(vals) - 1)
    pts = []
    for i, v in enumerate(vals):
        x = i * step
        y = h - 2 - (v - mn) / rng * (h - 4)
        pts.append(f"{x:.1f},{y:.1f}")
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{" ".join(pts)}"/></svg>')


def load():
    with open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)["accounts"]
    con = db.connect()
    snaps = con.execute("SELECT * FROM account_snapshots ORDER BY account_id, snap_date").fetchall()
    works = con.execute("SELECT * FROM works ORDER BY account_id, publish_ts DESC").fetchall()
    con.close()
    return cfg, snaps, works


def build():
    cfg, snaps, works = load()
    by_acct = {}
    for s in snaps:
        by_acct.setdefault(s["account_id"], []).append(dict(s))
    works_by = {}
    for w in works:
        works_by.setdefault(w["account_id"], []).append(dict(w))

    latest = {}
    for aid, rows in by_acct.items():
        latest[aid] = rows[-1]

    gen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")

    def kpi(aids):
        f = sum(latest[a]["followers"] or 0 for a in aids if a in latest)
        l = sum(latest[a]["total_likes"] or 0 for a in aids if a in latest)
        w = sum(latest[a]["works_count"] or 0 for a in aids if a in latest)
        return f, l, w

    def platform_section(platform):
        plat_accts = [a for a in cfg if a["platform"] == platform]
        active = [a for a in plat_accts if a["id"] in latest]
        label = PLATFORM_LABEL[platform]

        if not active:
            reason = plat_accts[0].get("note", "未开启采集") if plat_accts else "无账号"
            if platform == "xiaohongshu":
                reason = "小红书需登录态，未配置 cookie 或本次未取到"
            elif platform == "channels":
                reason = "视频号无网页前台，免费免登录不可行"
            cards = "".join(
                f'<div class="card off"><div class="cname">{html.escape(a["name"])}</div>'
                f'<div class="muted">{html.escape(a.get("owner",""))} · {html.escape(a.get("role",""))}</div>'
                f'<div class="off-tag">未接入</div></div>'
                for a in plat_accts)
            return (f'<section><h2>{label} <span class="badge off">{len(plat_accts)} 个号 · 未接入</span></h2>'
                    f'<p class="reason">{reason}</p><div class="grid">{cards}</div></section>')

        f, l, w = kpi([a["id"] for a in plat_accts])
        cards = []
        for a in plat_accts:
            aid = a["id"]
            if aid not in latest:
                cards.append(f'<div class="card off"><div class="cname">{html.escape(a["name"])}</div>'
                             f'<div class="off-tag">本次未取到</div></div>')
                continue
            s = latest[aid]
            hist = [r["followers"] for r in by_acct.get(aid, [])]
            ws = works_by.get(aid, [])
            rows = "".join(
                f'<tr><td class="mono">{html.escape((x["publish_time"] or "")[:10])}</td>'
                f'<td class="t">{html.escape((x["title"] or "")[:34])}</td>'
                f'<td class="num">{fmt(x["digg"])}</td>'
                f'<td class="num">{fmt(x["comment"])}</td>'
                f'<td class="num">{fmt(x["share"])}</td></tr>' for x in ws[:30])
            detail = (f'<details><summary>最近 {min(len(ws),30)} 条作品明细</summary>'
                      f'<table><thead><tr><th>发布日期</th><th>标题</th>'
                      f'<th class="num">点赞</th><th class="num">评论</th><th class="num">分享</th>'
                      f'</tr></thead><tbody>{rows or "<tr><td colspan=5>无</td></tr>"}</tbody></table></details>')
            cards.append(
                f'<div class="card"><div class="cname">{html.escape(a["name"])}'
                f'<span class="plat">{PLATFORM_LABEL[platform]}</span></div>'
                f'<div class="muted">{html.escape(a.get("owner",""))} · {html.escape(a.get("role",""))}'
                f'{" · 蓝V" if a.get("blue_v") else ""}</div>'
                f'<div class="metrics">'
                f'<div><span class="mv">{fmt(s["followers"])}</span><span class="mk">粉丝</span></div>'
                f'<div><span class="mv">{fmt(s["total_likes"])}</span><span class="mk">总获赞</span></div>'
                f'<div><span class="mv">{fmt(s["works_count"])}</span><span class="mk">作品数</span></div>'
                f'</div>'
                f'<div class="trend">粉丝趋势 {sparkline(hist)}</div>'
                f'{detail}</div>')
        return (f'<section><h2>{label} <span class="badge">{len(active)} 个号</span></h2>'
                f'<div class="kpi"><div><b>{fmt(f)}</b><span>合计粉丝</span></div>'
                f'<div><b>{fmt(l)}</b><span>合计获赞</span></div>'
                f'<div><b>{fmt(w)}</b><span>合计作品</span></div></div>'
                f'<div class="grid">{"".join(cards)}</div></section>')

    sections = "".join(platform_section(p) for p in PLATFORM_ORDER)

    all_aids = list(latest.keys())
    tf, tl, tw = kpi(all_aids)
    snap_n = len(snaps)

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>佳康顺新媒体数据看板</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
background:#0f1420;color:#e8ecf4}}
header{{padding:22px 28px;background:linear-gradient(120deg,#1b2740,#0f1420);
border-bottom:1px solid #223052}}
h1{{margin:0 0 4px;font-size:20px}}
h2{{font-size:15px;margin:26px 28px 10px;display:flex;align-items:center;gap:10px}}
.sub,.muted{{color:#8a97b1;font-size:12px}}
.badge{{background:#213055;color:#9db4e8;font-size:11px;padding:2px 8px;border-radius:10px}}
.badge.off{{background:#3a2331;color:#e79db4}}
.reason{{margin:0 28px 10px;color:#c99;font-size:12px}}
.top{{display:flex;gap:26px;flex-wrap:wrap;padding:14px 28px;border-bottom:1px solid #1c2740}}
.top .k{{font-size:11px;color:#8a97b1}}
.top .v{{font-size:20px;font-weight:700;margin-top:2px}}
section{{padding-bottom:12px}}
.kpi{{display:flex;gap:26px;margin:0 28px 12px;background:#141b2b;border:1px solid #1f2b45;border-radius:10px;padding:12px 18px}}
.kpi div{{display:flex;flex-direction:column}}
.kpi b{{font-size:18px}} .kpi span{{font-size:11px;color:#8a97b1}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin:0 28px}}
.card{{background:#141b2b;border:1px solid #1f2b45;border-radius:12px;padding:14px 16px}}
.card.off{{opacity:.55}}
.cname{{font-weight:600;font-size:14px;display:flex;justify-content:space-between;align-items:center}}
.plat{{font-size:10px;color:#7d8db3;background:#1c2740;border-radius:8px;padding:2px 7px}}
.metrics{{display:flex;gap:18px;margin:12px 0 6px}}
.mv{{font-size:19px;font-weight:700;display:block}} .mk{{font-size:11px;color:#8a97b1}}
.trend{{font-size:11px;color:#8a97b1;display:flex;align-items:center;gap:8px;margin-top:6px}}
details{{margin-top:10px}} summary{{cursor:pointer;font-size:12px;color:#9db4e8}}
table{{width:100%;border-collapse:collapse;margin-top:8px;font-size:12px}}
th,td{{text-align:left;padding:5px 6px;border-bottom:1px solid #1c2740}}
th{{color:#8a97b1;font-weight:500}}
.num{{text-align:right}} .t{{max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.mono{{font-family:ui-monospace,Consolas,monospace;color:#9db4e8}}
.off-tag{{margin-top:8px;font-size:11px;color:#e79db4}}
footer{{color:#5f6b86;font-size:11px;padding:18px 28px;border-top:1px solid #1c2740;margin-top:20px}}
</style></head><body>
<header>
<h1>佳康顺新媒体数据看板</h1>
<div class="sub">数据日期 {today} · 生成于 {gen} · 累计快照 {snap_n} 条 · 前台免登录采集</div>
</header>
<div class="top">
<div><div class="k">已接入合计粉丝</div><div class="v">{fmt(tf)}</div></div>
<div><div class="k">已接入合计获赞</div><div class="v">{fmt(tl)}</div></div>
<div><div class="k">已接入合计作品</div><div class="v">{fmt(tw)}</div></div>
<div><div class="k">已接入账号</div><div class="v">{len(all_aids)} / {len(cfg)}</div></div>
</div>
{sections}
<footer>采集口径：抖音/小红书=前台公开数据（粉丝/总获赞/作品数/最近30条单条点赞）；播放量、单条评论/分享平台前台不公开故为空。视频号无网页前台，未接入。</footer>
</body></html>"""

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print("dashboard written:", OUT)
    return OUT


if __name__ == "__main__":
    build()
