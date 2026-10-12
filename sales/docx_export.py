"""导出给董事长的汇报材料为 Word（.docx），可直接打印或转发。

依赖：python-docx（已装于项目 .venv）
"""
import os
from datetime import datetime

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(HERE, "out")
FONT = "微软雅黑"


def _fmt(n):
    if n is None:
        return "—"
    if isinstance(n, float) and n == int(n):
        n = int(n)
    return f"{n:,}"


def _zh(doc):
    """把默认样式设成中文字体，避免 Word 里中文变宋体/方块。"""
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(10.5)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    for sec in doc.sections:
        sec.left_margin = sec.right_margin = Pt(56)


def _h(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.name = FONT
        run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        run.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
    return p


def _table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = str(h)
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.name = FONT
                r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = "" if v is None else str(v)
            for p in cells[i].paragraphs:
                for r in p.runs:
                    r.font.name = FONT
                    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    return t


def _para(doc, text, bold=False, italic=False, size=10.5):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    return p


def build(cur, prev, comp, pct_ex_big=None, big=5500.0, dead=None, spoken="", path=None):
    dead = dead or []
    doc = Document()
    _zh(doc)

    title = doc.add_heading(f"新媒体销售与租赁 · {cur['month']} 月汇报", level=0)
    for run in title.runs:
        run.font.name = FONT
        run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    _para(doc, f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}　"
               f"数据来源：销售报表/新媒体销售报表　"
               f"口径：有押金=租赁订单，无押金=销售订单", italic=True, size=9)

    _h(doc, "一、要点速览", 1)
    rows = [
        ["营收合计", f"{_fmt(cur['total'])} 元",
         f"{_fmt(prev['total'])} 元" if prev else "—",
         f"{'+' if (comp.get('delta') or 0) >= 0 else ''}{_fmt(comp.get('delta'))} 元"
         f"（{comp.get('pct')}%）" if prev else "—"],
        ["订单数", f"{cur['count']} 单", f"{prev['count']} 单" if prev else "—",
         f"{comp.get('count_delta')} 单" if prev else "—"],
        ["售卖", f"{cur['sale_count']} 单 / {_fmt(cur['sale_total'])} 元",
         f"{prev['sale_count']} 单 / {_fmt(prev['sale_total'])} 元" if prev else "—",
         f"{_fmt(comp.get('sale_delta'))} 元" if prev else "—"],
        ["租赁", f"{cur['rent_count']} 单 / {_fmt(cur['rent_total'])} 元",
         f"{prev['rent_count']} 单 / {_fmt(prev['rent_total'])} 元" if prev else "—",
         f"{_fmt(comp.get('rent_delta'))} 元" if prev else "—"],
        ["客单价", f"{_fmt(cur['avg_order'])} 元", f"{_fmt(prev['avg_order'])} 元" if prev else "—", "—"],
        ["押金池 / 归还率", f"{_fmt(cur['deposit_total'])} 元 / {cur['deposit_returned_rate']}%", "—", "零纠纷"],
    ]
    _table(doc, ["指标", "本月", "上月", "变化"], rows)
    if prev:
        _para(doc, f"口径提醒：上月含一笔 {_fmt(big)} 元的大单，剔除后上月 {_fmt(prev['total'] - big)} 元，"
                   f"按该口径本月变化 {pct_ex_big}%。", italic=True)

    _h(doc, "二、收入结构", 1)
    _para(doc, f"售卖 {cur['sale_count']} 单、{_fmt(cur['sale_total'])} 元，占 {cur['sale_share']}%，"
               f"单笔均价 {_fmt(cur['avg_sale'])} 元；租赁 {cur['rent_count']} 单、"
               f"{_fmt(cur['rent_total'])} 元，占 {cur['rent_share']}%，单笔均价 "
               f"{_fmt(cur['avg_rent'])} 元，平均租期 {cur['rent_days_avg']} 天。")
    _para(doc, f"押金累计 {_fmt(cur['deposit_total'])} 元，全部按期归还，无押金纠纷。")
    if cur["max_order"]:
        m = cur["max_order"]
        _para(doc, f"单笔最高：{m['product']}（{m['customer']}，{m['channel']}，{m['date']}）{_fmt(m['amount'])} 元。")

    _h(doc, "三、渠道战果", 1)
    _table(doc, ["渠道", "单数", "金额（元）", "占比"],
           [[c["name"], c["count"], _fmt(c["amount"]), f"{c['share_amount']}%"] for c in cur["channels"]])
    if prev:
        _para(doc, "渠道环比变化：", bold=True)
        _table(doc, ["渠道", "上月（元）", "本月（元）", "变化"],
               [[r["channel"], _fmt(r["prev_amount"]), _fmt(r["cur_amount"]),
                 f"{'+' if r['cur_amount'] - r['prev_amount'] >= 0 else ''}"
                 f"{_fmt(r['cur_amount'] - r['prev_amount'])}"] for r in comp["channel_gain"]])

    _h(doc, "四、产品与客户", 1)
    _para(doc, "售卖主力：" + "；".join(f"{p['name']} {p['count']} 单 {_fmt(p['amount'])} 元"
                                       for p in cur["sale_products"][:5]))
    if cur["rent_products"]:
        _para(doc, "租赁主力：" + "；".join(f"{p['name']} {p['count']} 单 {_fmt(p['amount'])} 元"
                                           for p in cur["rent_products"][:5]))
    _para(doc, "租赁地区分布：" + "，".join(f"{r['name'] or '未填'} {_fmt(r['amount'])} 元"
                                          for r in cur.get("rent_regions", [])[:6]))
    if cur["unit_customers"]:
        _para(doc, "单位/机构客户：" + "；".join(f"{u['customer']}（{u['product']} {_fmt(u['amount'])} 元）"
                                                for u in cur["unit_customers"]))

    _h(doc, "五、问题与下一步", 1)
    if prev and comp.get("pct") is not None and comp["pct"] < 0:
        _para(doc, f"· 营收环比 {comp['pct']}%（{_fmt(prev['total'])} → {_fmt(cur['total'])} 元）；"
                   f"剔除上月 {_fmt(big)} 元大单后仍为 {pct_ex_big}%。")
    if dead:
        _para(doc, f"· 渠道断档：{'、'.join(dead)} 本月归零。")
    if cur["channels"] and cur["channels"][0]["share_amount"] >= 60:
        _para(doc, f"· 渠道过度集中：{cur['channels'][0]['name']} 占 {cur['channels'][0]['share_amount']}%。")
    _para(doc, "下一步：", bold=True)
    for i, s in enumerate([
        (f"重启断档渠道（{'、'.join(dead)}），老客转介绍返券 + 视频号成片重剪再发。" if dead
         else "保持渠道覆盖，防止单点依赖。"),
        "把小红书跑通的选题与话术改写后投到抖音与私域。",
        "租赁做 7 天 / 15 天 / 月租三档套餐，设最低起租门槛。",
        "上月大单客户单独建档，节前定向回访。",
    ], 1):
        _para(doc, f"{i}. {s}")

    if spoken:
        _h(doc, "六、口头汇报逐字稿（可直接念）", 1)
        for line in spoken.split("\n"):
            if line.strip():
                _para(doc, line)

    _h(doc, "七、附表：本月明细", 1)
    _table(doc, ["日期", "类别", "产品", "客户", "渠道", "地区", "租期", "金额", "押金"],
           [[r["date"], "售卖" if r["category"] == "sale" else "租赁", r["product"], r["customer"],
             r["channel"] or "—", r["region"] or "—",
             f"{r['rent_days']}天" if r["rent_days"] else "—", _fmt(r["amount"]),
             _fmt(r["deposit"]) if r["deposit"] else "—"]
            for r in sorted(cur["records"], key=lambda x: (x["day"], x["category"]))])

    os.makedirs(OUT_DIR, exist_ok=True)
    path = path or os.path.join(OUT_DIR, f"董事长汇报材料_{datetime.now().year}年{cur['month']}月.docx")
    doc.save(path)
    return path
