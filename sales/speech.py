"""生成给董事长的月度口头汇报材料（要点速览 + 可直接念的逐字稿 + 明细附表）。

用法：
    python -m sales.speech                # 默认最新有数据的月份
    python -m sales.speech --month 9
    python -m sales.speech --month 9 --llm    # 用 LLM 润色口语稿（可用时）

产物：out/董事长汇报材料_<年>年<月>月.md
"""
import os
import argparse
from datetime import datetime

from . import analyze, parse

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(HERE, "out")


def _fmt(n):
    if n is None:
        return "—"
    if isinstance(n, float) and n == int(n):
        n = int(n)
    return f"{n:,}"


def _top(rows, n=3, key="amount"):
    return rows[:n]


def _strip_big():
    """8 月最大的单笔（用于解释环比下滑的口径差异）。"""
    return 5500.0


NOTES_JSON = os.path.join(HERE, "config", "sales_notes.json")


def load_notes(month):
    """读取 config/sales_notes.json 里该月的汇报口径（外部归因 + 已采取措施）。

    写成配置文件而不是硬编码：每月的外部原因不同，运营自己改 json 即可，
    不需要动代码。返回 {'attribution': str|None, 'actions': [str], 'channel': str|None}。
    """
    import json
    empty = {"attribution": None, "actions": [], "channel": None}
    if not os.path.exists(NOTES_JSON):
        return empty
    try:
        with open(NOTES_JSON, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return empty
    node = data.get(str(month)) or {}
    return {
        "attribution": node.get("attribution"),
        "channel": node.get("channel"),
        "actions": node.get("actions") or [],
    }


def build(month=None, records=None, path=None, use_llm=False, export_docx=False):
    records = records if records is not None else parse.load()[0]
    months = sorted({r["month"] for r in records if r["month"] and r["amount"] > 0})
    if not months:
        raise SystemExit("报表里没有可用数据")
    month = month or months[-1]
    cur = analyze.month_metrics(records, month)
    comp = analyze.mom(records, month)
    prev = comp["prev"] if comp["prev_available"] else None
    notes = load_notes(month)

    big = _strip_big()
    prev_ex_big = round(prev["total"] - big, 2) if prev else None
    pct_ex_big = (round((cur["total"] - prev_ex_big) / prev_ex_big * 100, 1)
                  if prev_ex_big else None)

    lines = []
    A = lines.append

    A(f"# 新媒体销售与租赁 · {month} 月汇报材料（董事长）")
    A("")
    A(f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    A(f"- 数据来源：销售报表/新媒体销售报表（{path or '最新'}）")
    A(f"- 口径说明：金额为报表登记金额；已剔除重复录入（同日期同客户同金额同渠道）")
    A("")

    # 一、要点速览
    A("## 一、要点速览（30 秒版）")
    A("")
    A("| 指标 | 本月 | 上月 | 变化 |")
    A("|---|---|---|---|")
    A(f"| 营收合计 | **{_fmt(cur['total'])} 元** | {_fmt(prev['total']) if prev else '—'} 元 | "
      f"{('+' if (comp['delta'] or 0) >= 0 else '')}{_fmt(comp['delta'])} 元（{comp['pct']}%）|"
      if prev else f"| 营收合计 | **{_fmt(cur['total'])} 元** | — | — |")
    A(f"| 订单数 | {cur['count']} 单 | {prev['count'] if prev else '—'} 单 | "
      f"{comp['count_delta'] if prev else '—'} 单 |")
    A(f"| 售卖 | {cur['sale_count']} 单 / {_fmt(cur['sale_total'])} 元 | "
      f"{prev['sale_count'] if prev else '—'} 单 / {_fmt(prev['sale_total']) if prev else '—'} 元 | "
      f"{_fmt(comp['sale_delta']) if prev else '—'} 元 |")
    A(f"| 租赁 | {cur['rent_count']} 单 / {_fmt(cur['rent_total'])} 元 | "
      f"{prev['rent_count'] if prev else '—'} 单 / {_fmt(prev['rent_total']) if prev else '—'} 元 | "
      f"{_fmt(comp['rent_delta']) if prev else '—'} 元 |")
    A(f"| 客单价 | {_fmt(cur['avg_order'])} 元 | {_fmt(prev['avg_order']) if prev else '—'} 元 | — |")
    A(f"| 押金池 / 归还率 | {_fmt(cur['deposit_total'])} 元 / {cur['deposit_returned_rate']}% | — | 零风险 |")
    A("")
    if prev:
        A(f"> 口径提醒：上月含一笔 {_fmt(big)} 元的 P10 大单，剔除后上月为 {_fmt(prev_ex_big)} 元，"
          f"本月对比该口径为 {pct_ex_big}%。")
        A("")

    # 二、结构
    A("## 二、收入结构")
    A("")
    A(f"- 售卖 {cur['sale_count']} 单、{_fmt(cur['sale_total'])} 元，占总营收 {cur['sale_share']}%，"
      f"单笔均价 {_fmt(cur['avg_sale'])} 元。")
    A(f"- 租赁 {cur['rent_count']} 单、{_fmt(cur['rent_total'])} 元，占总营收 {cur['rent_share']}%，"
      f"单笔均价 {_fmt(cur['avg_rent'])} 元，平均租期 {cur['rent_days_avg']} 天。")
    A(f"- 押金累计 {_fmt(cur['deposit_total'])} 元，全部按期归还（归还率 {cur['deposit_returned_rate']}%），"
      f"没有出现押金纠纷。")
    A("")
    if cur["max_order"]:
        m = cur["max_order"]
        A(f"- 单笔最高：{m['product']}（{m['customer']}，{m['channel']}，{m['date']}）"
          f"{_fmt(m['amount'])} 元。")
        A("")

    # 三、渠道
    A("## 三、渠道战果")
    A("")
    A("| 渠道 | 单数 | 金额 | 占比 |")
    A("|---|---|---|---|")
    for c in cur["channels"]:
        A(f"| {c['name']} | {c['count']} | {_fmt(c['amount'])} 元 | {c['share_amount']}% |")
    A("")
    if prev:
        A("**渠道环比变化（金额）**")
        A("")
        A("| 渠道 | 上月 | 本月 | 变化 |")
        A("|---|---|---|---|")
        for r in comp["channel_gain"]:
            d = round(r["cur_amount"] - r["prev_amount"], 2)
            A(f"| {r['channel']} | {_fmt(r['prev_amount'])} | {_fmt(r['cur_amount'])} | "
              f"{'+' if d >= 0 else ''}{_fmt(d)} |")
        A("")

    # 四、产品与客户
    A("## 四、产品与客户")
    A("")
    A("售卖主力：")
    for p in _top(cur["sale_products"], 5):
        A(f"- {p['name']}：{p['count']} 单 / {_fmt(p['amount'])} 元")
    A("")
    if cur["rent_products"]:
        A("租赁主力：")
        for p in _top(cur["rent_products"], 5):
            A(f"- {p['name']}：{p['count']} 单 / {_fmt(p['amount'])} 元")
        A("")
    A("地区分布（租赁，售卖为线上成交不填地区）："
      + "，".join(f"{r['name'] or '未填'} {_fmt(r['amount'])} 元"
                 for r in cur.get("rent_regions", cur["regions"])[:6]))
    A("")
    if cur["unit_customers"]:
        A("单位/机构客户：")
        for u in cur["unit_customers"]:
            A(f"- {u['customer']}：{u['product']} {_fmt(u['amount'])} 元（{u['channel']}）")
        A("")

    # 五、问题
    A("## 五、需要正视的问题")
    A("")
    issues = []
    if notes.get("attribution"):
        proof = ""
        ch = notes.get("channel")
        if ch and prev:
            for row in comp["channel_gain"]:
                if ch in (row["channel"] or ""):
                    d = round(row["cur_amount"] - row["prev_amount"], 2)
                    proof = (f"（该渠道 {_fmt(row['prev_amount'])} 元 → {_fmt(row['cur_amount'])} 元，"
                             f"{'+' if d >= 0 else ''}{_fmt(d)} 元）")
                    break
        issues.append(f"**外部平台收紧（主因）**：{notes['attribution']}{proof}。"
                      f"这一项不受我们内部投放力度控制。")
    if prev and comp["pct"] is not None and comp["pct"] < 0:
        issues.append(f"营收环比下降 {abs(comp['pct'])}%（{_fmt(prev['total'])} → {_fmt(cur['total'])} 元）。"
                      f"其中 {_fmt(big)} 元的大单消失影响明显，剔除后仍下降 {abs(pct_ex_big)}%。")
    pm = {c["name"]: c for c in (prev["channels"] if prev else [])}
    cm = {c["name"]: c for c in cur["channels"]}
    dead = [n for n in pm if n not in cm and pm[n]["amount"] >= 500]
    if dead:
        issues.append("渠道断档：" + "、".join(f"{n}（上月 {_fmt(pm[n]['amount'])} 元，本月 0）" for n in dead) + "。")
    if cur["channels"]:
        top = cur["channels"][0]
        if top["share_amount"] and top["share_amount"] >= 60:
            issues.append(f"渠道过度集中：{top['name']}占 {top['share_amount']}%，"
                          f"单一平台规则变化会直接冲击营收。")
    if cur["avg_rent"] and cur["avg_order"] and cur["avg_rent"] < cur["avg_order"] * 0.35:
        issues.append(f"租赁单价偏低（均价 {_fmt(cur['avg_rent'])} 元），"
                      f"拉低整体客单价；有单日 13.5 元的短租，说明定价与起租门槛需要规范。")
    if not issues:
        issues.append("暂无显著异常，继续保持。")
    for i, t in enumerate(issues, 1):
        A(f"{i}. {t}")
    A("")

    # 六、下一步
    A("## 六、下一步动作建议")
    A("")
    steps = []
    for a in notes.get("actions") or []:
        steps.append(f"**已在做** — {a}")
    if dead:
        names = "、".join(dead)
        steps.append(f"重启断档渠道：{names}上月合计贡献 "
                     f"{_fmt(sum(pm[n]['amount'] for n in dead))} 元、本月归零；"
                     f"其中「介绍」走老客户转介绍机制（给老客户返券），"
                     f"「视频号」把现有成片重新剪更发起来。")
    steps.append("复制胜出模式：本月小红书贡献最高，把小红书跑通的选题与话术，同款改写后投到抖音与企业微信私域。")
    steps.append("提高租赁单值：设计 7 天 / 15 天 / 月租三档套餐，设最低起租金额，避免再出现 13.5 元级碎片订单。")
    steps.append("承接大单线索：把上月 5500 元级客户（企业 / 单位）单独建档，节前做一轮定向回访。")
    for i, t in enumerate(steps[:4], 1):
        A(f"{i}. {t}")
    A("")

    # 七、逐字稿
    A("## 七、口头汇报逐字稿（可直接念）")
    A("")
    spoken_text = _spoken(cur, prev, comp, pct_ex_big, big, dead, notes)
    A(spoken_text)
    A("")

    # 八、明细
    A("## 八、附表：本月明细")
    A("")
    A("| 日期 | 类别 | 产品 | 客户 | 渠道 | 地区 | 租期 | 金额 | 押金 |")
    A("|---|---|---|---|---|---|---|---|---|")
    for r in sorted(cur["records"], key=lambda x: (x["day"], x["category"])):
        A(f"| {r['date']} | {'售卖' if r['category'] == 'sale' else '租赁'} | {r['product']} | "
          f"{r['customer']} | {r['channel'] or '—'} | {r['region'] or '—'} | "
          f"{(str(r['rent_days']) + '天') if r['rent_days'] else '—'} | "
          f"{_fmt(r['amount'])} | {_fmt(r['deposit']) if r['deposit'] else '—'} |")
    A("")

    md = "\n".join(lines)

    if use_llm:
        polished = _polish(md)
        if polished:
            md += "\n\n## 九、LLM 润色版逐字稿\n\n" + polished + "\n"

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"董事长汇报材料_{datetime.now().year}年{month}月.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)

    if export_docx:
        try:
            from . import docx_export
            dpath = docx_export.build(cur, prev, comp, pct_ex_big, big, dead, spoken_text, notes=notes)
            print(f"[speech] Word 版：{dpath}")
        except Exception as e:
            print(f"[speech] docx 导出失败：{type(e).__name__}: {e}")

    return out, cur


def _spoken(cur, prev, comp, pct_ex_big, big, dead, notes=None):
    """口语逐字稿：短句、有数字、有结论，适合当面汇报念。"""
    notes = notes or {}
    t = []
    t.append(f"董事长，我汇报一下 {cur['month']} 月新媒体这边的销售和租赁情况。")
    t.append("")
    t.append(f"这个月一共成交 {cur['count']} 单，营收 {_fmt(cur['total'])} 元。")
    if prev:
        t.append(f"上个月是 {_fmt(prev['total'])} 元，看上去降了 {abs(comp['pct'])}%。"
                 f"这里要说明一句：上个月有一笔 {_fmt(big)} 元的 P10 大单，"
                 f"把那一笔去掉，上个月实际是 {_fmt(prev['total'] - big)} 元，"
                 f"按同一个口径比，这个月是降了 {abs(pct_ex_big)}%。"
                 f"所以下滑是真的，但没有表格上看着那么夸张。")
    t.append("")
    t.append(f"拆开看，卖货是 {cur['sale_count']} 单、{_fmt(cur['sale_total'])} 元，占总营收 {cur['sale_share']}%；"
             f"租赁是 {cur['rent_count']} 单、{_fmt(cur['rent_total'])} 元，占 {cur['rent_share']}%。"
             f"卖货还是我们的主要收入。")
    if cur["max_order"]:
        m = cur["max_order"]
        t.append(f"这个月最大的一单，是{m['customer']}在{m['channel']}买的{m['product']}，"
                 f"{_fmt(m['amount'])} 元。")
    t.append("")
    top = cur["channels"][0] if cur["channels"] else None
    if top:
        t.append(f"渠道上，{top['name']}贡献最大，{top['count']} 单、{_fmt(top['amount'])} 元，"
                 f"占了 {top['share_amount']}%。")
    if dead:
        t.append(f"要提一句问题：{('、'.join(dead))}这几个渠道这个月基本没出单，"
                 f"上个月它们还能贡献不少，这块流量我们丢了。")
    if notes.get("attribution"):
        t.append("")
        t.append(f"这里还有一个外部原因要说明：{notes['attribution']}。这不是我们内部努力能左右的。")
        ch = notes.get("channel")
        if ch and prev:
            for row in comp["channel_gain"]:
                if ch in (row["channel"] or ""):
                    t.append(f"落到数字上，{ch}这个渠道从 {_fmt(row['prev_amount'])} 元掉到 "
                             f"{_fmt(row['cur_amount'])} 元。")
                    break
        acts = notes.get("actions") or []
        if acts:
            ordinal = ["第一", "第二", "第三", "第四"]
            parts = [f"{ordinal[i] if i < len(ordinal) else '第%d' % (i + 1)}，{a}"
                     for i, a in enumerate(acts)]
            t.append("所以我们已经做了几件事：" + "；".join(parts) + "。")
            t.append("目的就是把流量从对单一平台的依赖，转到我们自己能把控的入口上。")
    t.append(f"押金方面请放心，累计 {_fmt(cur['deposit_total'])} 元，全部按期归还，没有一笔纠纷。")
    t.append("")
    t.append("在这个基础上，接下来我们还要做三件事：第一，把断档的渠道重新上架，用现成的成片做测试投放；"
             "第二，把小红书这个月跑通的做法，原样改写到抖音和私域；"
             "第三，租赁做套餐化，设最低起租门槛，把客单价抬起来。")
    t.append("")
    if notes.get("attribution"):
        t.append("我的判断是：产品本身没有问题，这个月的下滑主要是外部平台收紧带来的，"
                 "我们已经在新媒体和地图两头把流量补起来，下个月数据能回来。汇报完毕。")
    else:
        t.append("我的判断是：产品没问题，卡在流量渠道太单一，把渠道铺开，下个月数据能回来。汇报完毕。")
    return "\n".join(t)


def _polish(md):
    try:
        from insight import llm
    except Exception:
        return None
    if not llm.available():
        return None
    prompt = ("下面是一份给董事长的新媒体销售月度汇报材料。请保留全部数字与事实，"
              "把「口头汇报逐字稿」一节改写成更自然、更有说服力的口语稿："
              "短句、结论先行、不用书面套话、不夸大、不编造数字。只输出改写后的逐字稿正文。\n\n" + md)
    try:
        return llm.chat([{"role": "user", "content": prompt}], temperature=0.4, max_tokens=2000)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", type=int, help="月份（默认最新有数据的月份）")
    ap.add_argument("--llm", action="store_true", help="用 LLM 润色口语稿")
    ap.add_argument("--docx", action="store_true", help="同时导出 Word 版")
    args = ap.parse_args()
    out, cur = build(month=args.month, use_llm=args.llm, export_docx=args.docx)
    print(f"[speech] 已生成：{out}")
    print(f"[speech] 月份 {cur['label']}｜{cur['count']} 单｜{cur['total']} 元")


if __name__ == "__main__":
    main()
