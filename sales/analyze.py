"""月度汇总指标：营收结构、渠道 / 产品 / 地区分布、客单价、租赁健康度、环比。

所有金额单位：元。不引入第三方库。
"""
import re
from collections import defaultdict

from . import parse

UNIT_HINTS = ("大厦", "领导", "本地推", "公司", "店", "中心", "医院", "养老", "物业")


def _pct(a, b):
    if not b:
        return None
    return round(a / b * 100, 1)


def month_metrics(records, month):
    rs = [r for r in records if r["month"] == month]
    rent = [r for r in rs if r["category"] == "rent"]
    sale = [r for r in rs if r["category"] == "sale"]
    total = round(sum(r["amount"] for r in rs), 2)
    rent_total = round(sum(r["amount"] for r in rent), 2)
    sale_total = round(sum(r["amount"] for r in sale), 2)

    def dist(rows, field):
        agg = defaultdict(lambda: {"count": 0, "amount": 0.0})
        for r in rows:
            k = r.get(field) or "未填"
            agg[k]["count"] += 1
            agg[k]["amount"] += r["amount"]
        out = [{"name": k, "count": v["count"], "amount": round(v["amount"], 2),
                "share_amount": _pct(v["amount"], total),
                "share_count": _pct(v["count"], len(rows))}
               for k, v in agg.items()]
        return sorted(out, key=lambda x: (-x["amount"], -x["count"]))

    deposits = [r for r in rs if r["deposit"]]
    deposit_total = round(sum(r["deposit"] for r in deposits), 2)
    returned = [r for r in deposits if r["deposit_returned"] is True]
    rent_days = [r["rent_days"] for r in rent if r["rent_days"]]

    max_order = max(rs, key=lambda r: r["amount"], default=None)
    days = sorted({r["day"] for r in rs})
    unit_customers = [r for r in rs if any(h in (r["customer"] or "") for h in UNIT_HINTS)]

    return {
        "month": month,
        "label": f"{month}月",
        "count": len(rs),
        "total": total,
        "rent_count": len(rent), "rent_total": rent_total,
        "sale_count": len(sale), "sale_total": sale_total,
        "rent_share": _pct(rent_total, total),
        "sale_share": _pct(sale_total, total),
        "avg_order": round(total / len(rs), 2) if rs else 0,
        "avg_sale": round(sale_total / len(sale), 2) if sale else 0,
        "avg_rent": round(rent_total / len(rent), 2) if rent else 0,
        "max_order": ({"amount": max_order["amount"], "product": max_order["product"],
                       "customer": max_order["customer"], "channel": max_order["channel"],
                       "date": max_order["date"]} if max_order else None),
        "channels": dist(rs, "channel"),
        "products": dist(rs, "product"),
        "regions": dist(rs, "region"),
        "rent_regions": dist(rent, "region"),
        "sale_products": dist(sale, "product"),
        "rent_products": dist(rent, "product"),
        "deposit_total": deposit_total,
        "deposit_count": len(deposits),
        "deposit_returned": len(returned),
        "deposit_returned_rate": _pct(len(returned), len(deposits)),
        "rent_days_avg": round(sum(rent_days) / len(rent_days), 1) if rent_days else None,
        "active_days": len(days),
        "first_day": days[0] if days else None,
        "last_day": days[-1] if days else None,
        "unit_customers": [{"customer": r["customer"], "product": r["product"],
                            "amount": r["amount"], "channel": r["channel"]} for r in unit_customers],
        "records": rs,
    }


def mom(records, month):
    """与上月对比。"""
    cur = month_metrics(records, month)
    prev = month_metrics(records, month - 1) if month > 1 else None
    if not prev or not prev["count"]:
        return {"cur": cur, "prev": prev, "delta": None, "pct": None,
                "prev_available": False}
    delta = round(cur["total"] - prev["total"], 2)
    return {
        "cur": cur, "prev": prev, "prev_available": True,
        "delta": delta,
        "pct": round(delta / prev["total"] * 100, 1) if prev["total"] else None,
        "count_delta": cur["count"] - prev["count"],
        "sale_delta": round(cur["sale_total"] - prev["sale_total"], 2),
        "rent_delta": round(cur["rent_total"] - prev["rent_total"], 2),
        "channel_gain": _channel_diff(prev, cur),
    }


def _channel_diff(prev, cur):
    pm = {c["name"]: c for c in prev["channels"]}
    cm = {c["name"]: c for c in cur["channels"]}
    rows = []
    for name in sorted(set(pm) | set(cm)):
        p, c = pm.get(name), cm.get(name)
        rows.append({
            "channel": name,
            "prev_amount": p["amount"] if p else 0,
            "cur_amount": c["amount"] if c else 0,
            "prev_count": p["count"] if p else 0,
            "cur_count": c["count"] if c else 0,
        })
    return sorted(rows, key=lambda x: -(x["prev_amount"] + x["cur_amount"]))


def fmt(n):
    if n is None:
        return "—"
    return f"{n:,.2f}".rstrip("0").rstrip(".") if isinstance(n, float) else f"{n:,}"


if __name__ == "__main__":
    recs, path = parse.load()
    print("报表:", path, "| 记录", len(recs))
    months = sorted({r["month"] for r in recs if r["month"]})
    for m in months:
        d = month_metrics(recs, m)
        print("=" * 70)
        print(f"{d['label']}：{d['count']} 单 | 营收 {fmt(d['total'])} 元 "
              f"| 卖 {d['sale_count']} 单 {fmt(d['sale_total'])} | 租 {d['rent_count']} 单 {fmt(d['rent_total'])}")
        print(f"  客单价 {fmt(d['avg_order'])}（售卖 {fmt(d['avg_sale'])} / 租赁 {fmt(d['avg_rent'])}）")
        print("  渠道:", "，".join(f"{c['name']} {c['count']}单/{fmt(c['amount'])}" for c in d["channels"]))
        print("  押金:", fmt(d["deposit_total"]), f"归还率 {d['deposit_returned_rate']}%",
              "| 平均租期", d["rent_days_avg"], "天")
    for m in months[1:]:
        r = mom(recs, m)
        if r["prev_available"]:
            print("=" * 70)
            print(f"{m}月环比：{fmt(r['total'] if 'total' in r else 0)}", end=" ")
            print(f"营收 {fmt(r['cur']['total'])} vs 上月 {fmt(r['prev']['total'])} → "
                  f"{'+' if r['delta'] >= 0 else ''}{fmt(r['delta'])}（{r['pct']}%）")
