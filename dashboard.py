"""读取 SQLite 快照，生成自包含看板 HTML v2（无外部依赖）。

v2 新增分区：自有账号矩阵 / 对标账号对比 / 今日爆款榜（关键词搜索 top）/ 热搜词 / 分析结论。
"""
import os
import json
import html
from datetime import datetime

import db

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "dashboard.html")

PLATFORM_LABEL = {"douyin": "抖音", "xiaohongshu": "小红书", "channels": "视频号"}
PLATFORM_ORDER = ["douyin", "xiaohongshu", "channels"]
CHANNELS_NOTE = "视频号无网页前台，免费免登录不可行"


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


def esc(s):
    return html.escape(str(s or ""))


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
    con = db.connect()
    cfg = [dict(r) for r in con.execute("SELECT * FROM accounts ORDER BY kind, platform, id")]
    snaps = con.execute("SELECT * FROM account_snapshots ORDER BY account_id, snap_date").fetchall()
    works = con.execute("SELECT * FROM works ORDER BY account_id, publish_ts DESC").fetchall()
    hits = con.execute(
        """SELECT * FROM search_hits
           WHERE snap_date = (SELECT MAX(snap_date) FROM search_hits)
           ORDER BY digg DESC""").fetchall()
    hot = con.execute(
        """SELECT * FROM hot_items
           WHERE snap_date = (SELECT MAX(snap_date) FROM hot_items)
           ORDER BY platform, rank""").fetchall()
    ins = con.execute("SELECT * FROM insights ORDER BY created_at DESC LIMIT 6").fetchall()
    con.close()
    return cfg, snaps, works, hits, hot, ins


def _work_rows(ws, n=30):
    return "".join(
        f'<tr><td class="mono">{(x["publish_time"] or "")[:10]}</td>'
        f'<td class="t">{esc((x["title"] or "")[:34])}</td>'
        f'<td class="num">{fmt(x["digg"])}</td>'
        f'<td class="num">{fmt(x["comment"])}</td>'
        f'<td class="num">{fmt(x["share"])}</td></tr>' for x in ws[:n])


def _card(a, s, hist, ws, kind="own"):
    detail = (f'<details><summary>最近 {min(len(ws), 30)} 条作品明细</summary>'
              f'<table><thead><tr><th>发布日期</th><th>标题</th>'
              f'<th class="num">点赞</th><th class="num">评论</th><th class="num">分享</th>'
              f'</tr></thead><tbody>{_work_rows(ws) or "<tr><td colspan=5>无</td></tr>"}</tbody></table></details>')
    tag = "对标" if kind == "rival" else PLATFORM_LABEL.get(a["platform"], a["platform"])
    return (f'<div class="card {"rival" if kind == "rival" else ""}">'
            f'<div class="cname">{esc(a["name"])}<span class="plat">{tag}</span></div>'
            f'<div class="muted">{esc(a.get("owner"))} · {esc(a.get("role"))}'
            f'{" · 蓝V" if a.get("blue_v") else ""}</div>'
            f'<div class="metrics">'
            f'<div><span class="mv">{fmt(s["followers"])}</span><span class="mk">粉丝</span></div>'
            f'<div><span class="mv">{fmt(s["total_likes"])}</span><span class="mk">总获赞</span></div>'
            f'<div><span class="mv">{fmt(s["works_count"])}</span><span class="mk">作品数</span></div>'
            f'</div>'
            f'<div class="trend">粉丝趋势 {sparkline(hist)}</div>{detail}</div>')


def platform_section(cfg, latest, by_acct, works_by, platform, kind="own"):
    plat_accts = [a for a in cfg if a["platform"] == platform and a["kind"] == kind]
    if not plat_accts:
        return ""
    label = PLATFORM_LABEL.get(platform, platform) + ("（对标）" if kind == "rival" else "")
    active = [a for a in plat_accts if a["id"] in latest]

    if not active:
        reason = plat_accts[0].get("note") or "未开启采集"
        if platform == "xiaohongshu":
            reason = "小红书需登录态，未配置 cookie 或本次未取到"
        elif platform == "channels":
            reason = CHANNELS_NOTE
        cards = "".join(
            f'<div class="card off"><div class="cname">{esc(a["name"])}</div>'
            f'<div class="muted">{esc(a.get("owner"))} · {esc(a.get("role"))}</div>'
            f'<div class="off-tag">未接入</div></div>' for a in plat_accts)
        return (f'<section><h2>{label} <span class="badge off">{len(plat_accts)} 个号 · 未接入</span></h2>'
                f'<p class="reason">{esc(reason)}</p><div class="grid">{cards}</div></section>')

    f = sum(latest[a["id"]]["followers"] or 0 for a in plat_accts if a["id"] in latest)
    like = sum(latest[a["id"]]["total_likes"] or 0 for a in plat_accts if a["id"] in latest)
    w = sum(latest[a["id"]]["works_count"] or 0 for a in plat_accts if a["id"] in latest)
    cards = []
    for a in plat_accts:
        aid = a["id"]
        if aid not in latest:
            cards.append(f'<div class="card off"><div class="cname">{esc(a["name"])}</div>'
                         f'<div class="off-tag">本次未取到</div></div>')
            continue
        hist = [r["followers"] for r in by_acct.get(aid, [])]
        cards.append(_card(a, latest[aid], hist, works_by.get(aid, []), kind))
    return (f'<section><h2>{label} <span class="badge">{len(active)} 个号</span></h2>'
            f'<div class="kpi"><div><b>{fmt(f)}</b><span>合计粉丝</span></div>'
            f'<div><b>{fmt(like)}</b><span>合计获赞</span></div>'
            f'<div><b>{fmt(w)}</b><span>合计作品</span></div></div>'
            f'<div class="grid">{"".join(cards)}</div></section>')


def hits_section(hits):
    if not hits:
        return ('<section><h2>今日爆款榜 <span class="badge off">暂无数据</span></h2>'
                '<p class="reason">运行 collectors/rival.py --search 后出现（按监控关键词抓对标爆款）</p></section>')
    by_kw = {}
    for h in hits:
        by_kw.setdefault((h["platform"], h["keyword"]), []).append(dict(h))
    blocks = []
    for (plat, kw), rows in by_kw.items():
        trs = "".join(
            f'<tr><td class="num">{fmt(r["digg"])}</td><td class="num">{fmt(r["comment"])}</td>'
            f'<td class="t">{esc((r["title"] or "")[:38])}</td>'
            f'<td class="muted">{esc(r["author_name"])}</td>'
            f'<td class="mono">{(r["publish_time"] or "")[:10]}</td></tr>' for r in rows[:10])
        blocks.append(f'<div class="kwblock"><h3>{PLATFORM_LABEL.get(plat, plat)} · 「{esc(kw)}」'
                      f'<span class="muted"> top {min(len(rows),10)}/{len(rows)}</span></h3>'
                      f'<table><thead><tr><th class="num">点赞</th><th class="num">评论</th>'
                      f'<th>标题</th><th>作者</th><th>发布</th></tr></thead><tbody>{trs}</tbody></table></div>')
    return ('<section><h2>今日爆款榜（对标搜索） <span class="badge">'
            f'{len(by_kw)} 个关键词</span></h2>' + "".join(blocks) + '</section>')


def hot_section(hot):
    if not hot:
        return ""
    by_plat = {}
    for h in hot:
        by_plat.setdefault(h["platform"], []).append(dict(h))
    cols = []
    for plat, rows in by_plat.items():
        items = "".join(
            f'<li><span class="rk">{r["rank"]}</span>{esc(r["title"])}</li>' for r in rows[:20])
        cols.append(f'<div class="hotcol"><h3>{esc(plat)} 热搜</h3><ol class="hotlist">{items}</ol></div>')
    return f'<section><h2>平台热搜词 <span class="badge">{len(hot)} 条</span></h2><div class="hotcols">{"".join(cols)}</div></section>'


def insight_section(ins):
    if not ins:
        return ""
    blocks = []
    for i in ins:
        body = esc((i["body_md"] or "")[:1200]).replace("\n", "<br>")
        blocks.append(f'<details><summary>{esc(i["title"] or i["kind"])} '
                      f'<span class="muted">{esc(i["created_at"])}</span></summary>'
                      f'<div class="insbody">{body}</div></details>')
    return f'<section><h2>分析结论与拍摄方向 <span class="badge">{len(ins)} 条</span></h2>{"".join(blocks)}</section>'


CSS = """
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
background:#0f1420;color:#e8ecf4}
header{padding:22px 28px;background:linear-gradient(120deg,#1b2740,#0f1420);
border-bottom:1px solid #223052}
h1{margin:0 0 4px;font-size:20px}
h2{font-size:15px;margin:26px 28px 10px;display:flex;align-items:center;gap:10px}
h3{font-size:13px;margin:14px 0 8px;color:#c3d0ea}
.sub,.muted{color:#8a97b1;font-size:12px}
.badge{background:#213055;color:#9db4e8;font-size:11px;padding:2px 8px;border-radius:10px}
.badge.off{background:#3a2331;color:#e79db4}
.reason{margin:0 28px 10px;color:#c99;font-size:12px}
.top{display:flex;gap:26px;flex-wrap:wrap;padding:14px 28px;border-bottom:1px solid #1c2740}
.top .k{font-size:11px;color:#8a97b1}
.top .v{font-size:20px;font-weight:700;margin-top:2px}
section{padding-bottom:12px}
.kpi{display:flex;gap:26px;margin:0 28px 12px;background:#141b2b;border:1px solid #1f2b45;border-radius:10px;padding:12px 18px}
.kpi div{display:flex;flex-direction:column}
.kpi b{font-size:18px} .kpi span{font-size:11px;color:#8a97b1}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin:0 28px}
.card{background:#141b2b;border:1px solid #1f2b45;border-radius:12px;padding:14px 16px}
.card.rival{border-color:#3a3352;background:#171a2c}
.card.off{opacity:.55}
.cname{font-weight:600;font-size:14px;display:flex;justify-content:space-between;align-items:center}
.plat{font-size:10px;color:#7d8db3;background:#1c2740;border-radius:8px;padding:2px 7px}
.metrics{display:flex;gap:18px;margin:12px 0 6px}
.mv{font-size:19px;font-weight:700;display:block} .mk{font-size:11px;color:#8a97b1}
.trend{font-size:11px;color:#8a97b1;display:flex;align-items:center;gap:8px;margin-top:6px}
details{margin-top:10px} summary{cursor:pointer;font-size:12px;color:#9db4e8}
table{width:100%;border-collapse:collapse;margin-top:8px;font-size:12px}
th,td{text-align:left;padding:5px 6px;border-bottom:1px solid #1c2740}
th{color:#8a97b1;font-weight:500}
.num{text-align:right} .t{max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mono{font-family:ui-monospace,Consolas,monospace;color:#9db4e8}
.off-tag{margin-top:8px;font-size:11px;color:#e79db4}
.kwblock{margin:0 28px 18px;background:#141b2b;border:1px solid #1f2b45;border-radius:12px;padding:10px 16px}
.hotcols{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin:0 28px}
.hotcol{background:#141b2b;border:1px solid #1f2b45;border-radius:12px;padding:10px 16px}
.hotlist{list-style:none;margin:0;padding:0;font-size:12px}
.hotlist li{padding:3px 0;border-bottom:1px solid #1c2740;display:flex;gap:8px}
.rk{color:#6b7ba0;min-width:18px;text-align:right}
.insbody{background:#111726;border:1px solid #1c2740;border-radius:8px;padding:10px;margin-top:8px;
font-size:12px;line-height:1.7;color:#c8d3e8;max-height:340px;overflow:auto}
footer{color:#5f6b86;font-size:11px;padding:18px 28px;border-top:1px solid #1c2740;margin-top:20px}
"""


def build():
    cfg, snaps, works, hits, hot, ins = load()
    by_acct = {}
    for s in snaps:
        by_acct.setdefault(s["account_id"], []).append(dict(s))
    works_by = {}
    for w in works:
        works_by.setdefault(w["account_id"], []).append(dict(w))
    latest = {aid: rows[-1] for aid, rows in by_acct.items() if rows}

    own_ids = [a["id"] for a in cfg if a["kind"] == "own"]
    rival_ids = [a["id"] for a in cfg if a["kind"] == "rival"]
    tf = sum(latest[i]["followers"] or 0 for i in own_ids if i in latest)
    tl = sum(latest[i]["total_likes"] or 0 for i in own_ids if i in latest)
    tw = sum(latest[i]["works_count"] or 0 for i in own_ids if i in latest)
    rf = sum(latest[i]["followers"] or 0 for i in rival_ids if i in latest)

    sections = []
    sections.append('<section><h2>自有账号矩阵 <span class="badge">'
                    f'{len([i for i in own_ids if i in latest])} / {len(own_ids)} 已接入</span></h2></section>')
    for p in PLATFORM_ORDER:
        sections.append(platform_section(cfg, latest, by_acct, works_by, p, "own"))
    if rival_ids:
        sections.append('<section><h2>对标账号 <span class="badge">'
                        f'{len([i for i in rival_ids if i in latest])} / {len(rival_ids)} 已接入</span></h2></section>')
        for p in PLATFORM_ORDER:
            sections.append(platform_section(cfg, latest, by_acct, works_by, p, "rival"))
    sections.append(hits_section(hits))
    sections.append(hot_section(hot))
    sections.append(insight_section(ins))

    gen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>佳康顺新媒体数据看板 v2</title>
<style>{CSS}</style></head><body>
<header>
<h1>佳康顺新媒体数据看板 <span class="muted" style="font-size:12px">v2</span></h1>
<div class="sub">数据日期 {today} · 生成于 {gen} · 累计快照 {len(snaps)} 条 · 作品 {len(works)} 条 ·
对标搜索素材 {len(hits)} 条 · 前台免登录采集</div>
</header>
<div class="top">
<div><div class="k">自有合计粉丝</div><div class="v">{fmt(tf)}</div></div>
<div><div class="k">自有合计获赞</div><div class="v">{fmt(tl)}</div></div>
<div><div class="k">自有合计作品</div><div class="v">{fmt(tw)}</div></div>
<div><div class="k">对标合计粉丝</div><div class="v">{fmt(rf)}</div></div>
<div><div class="k">账号（自有/对标）</div><div class="v">{len(own_ids)} / {len(rival_ids)}</div></div>
</div>
{"".join(sections)}
<footer>采集口径：抖音/小红书=前台公开数据（粉丝/总获赞/作品数/作品点赞）；播放量与单条评论/分享平台前台多不公开故可能为空。
对标素材来自监控关键词搜索结果（search_hits），热搜来自微博/百度/抖音热榜。视频号无网页前台，未接入。</footer>
</body></html>"""

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print("dashboard written:", OUT)
    return OUT


if __name__ == "__main__":
    build()
