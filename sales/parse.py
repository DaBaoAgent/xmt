"""销售报表 → 结构化记录。

输入：销售报表/*.xlsx（WPS 导出，每个 sheet 一个月，如「九月销售」）
输出：记录列表

字段：month / month_label / date / day / product / customer / channel / region /
      purpose / rent_days / amount / deposit / deposit_returned / category /
      phone / delivery / sheet

数据清洗规则（针对真实报表里的口语化填写）：
  - 日期 "9.8" / "9·8" / "10·8" 混写 → 统一正则解析月份与日
  - 金额 "13·5" 这类误用小圆点的 → 还原为 13.5
  - 押金 "600{已归还}" / "2000（已归还）" → 数值 + 是否归还
  - 类别：**有押金 = 租赁订单，无押金 = 销售订单**（业务口径）。
    表里的「售卖」分隔行与「租赁时间」列只用于交叉校验并标记 warning，
    不参与类别判定；历史数据里曾按"有租期即租赁"推断，会与押金口径冲突。
  - 去重：同一（月, 日期, 客户, 金额, 渠道）只保留一条，保留产品名中文更全的那条
    （真实案例：9 月「4D坐垫 范国全 168」与「范国全 微信小店 168」重复记录）
"""
import os
import re

from .xlsx import read_sheets

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(HERE, "销售报表")

CN_MONTH = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
            "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12}

DATE_RE = re.compile(r"(\d{1,2})\s*[.·．]\s*(\d{1,2})")
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")
DAYS_RE = re.compile(r"(\d+)\s*天")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _month_from_sheet(name):
    m = re.search(r"([一二三四五六七八九十]{1,3})月", name)
    if m and m.group(1) in CN_MONTH:
        return CN_MONTH[m.group(1)]
    m = re.search(r"(\d{1,2})\s*月", name)
    return int(m.group(1)) if m else None


def _cjk_len(s):
    return len(CJK_RE.findall(s or ""))


def _parse_amount(raw):
    """金额：'13·5' → 13.5；'153' → 153.0；'/' 或空 → 0.0"""
    if raw is None:
        return 0.0
    s = str(raw).strip()
    if not s or s in ("/", "-", "—"):
        return 0.0
    s = re.sub(r"[·．]", ".", s)
    m = NUM_RE.search(s)
    if not m:
        return 0.0
    try:
        return float(m.group(0))
    except ValueError:
        return 0.0


def _parse_deposit(raw):
    """押金：'600{已归还}' → (600, True)；'/' → (None, None)"""
    if raw is None:
        return None, None
    s = str(raw).strip()
    if not s or s in ("/", "-"):
        return None, None
    m = NUM_RE.search(s)
    amount = float(m.group(0)) if m else None
    returned = ("归还" in s)
    return amount, returned


def _parse_rent_days(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s in ("/", "-"):
        return None
    m = DAYS_RE.search(s)
    if m:
        return int(m.group(1))
    m = NUM_RE.search(s)
    return int(float(m.group(0))) if m else None


def _clean(v):
    s = str(v).strip() if v is not None else ""
    return "" if s in ("/", "-", "—") else s


def _header_index(rows, sheet_name):
    """定位表头行 → 列名到索引的映射。"""
    for i, row in enumerate(rows[:6]):
        cells = [str(c) for c in row]
        if any("日期" in c for c in cells) and any("金额" in c for c in cells):
            idx = {}
            for j, c in enumerate(cells):
                c = c.strip()
                if c:
                    idx[c] = j
            return i, idx
    return None, {}


def _pick(idx, row, *names):
    for n in names:
        for key, j in idx.items():
            if n in key:
                if j < len(row):
                    return row[j]
    return ""


def parse_sheet(rows, sheet_name):
    month = _month_from_sheet(sheet_name)
    hdr_i, idx = _header_index(rows, sheet_name)
    if hdr_i is None:
        return []
    records = []
    in_sale_block = False
    for row in rows[hdr_i + 1:]:
        cells = [_clean(c) for c in row]
        if not any(cells):
            continue
        # 分隔行：「售卖」
        joined = "".join(cells)
        if joined == "售卖":
            in_sale_block = True
            continue
        date_raw = cells[0] if cells else ""
        m = DATE_RE.search(date_raw)
        product = _clean(_pick(idx, row, "产品"))
        amount_raw = _pick(idx, row, "金额")
        amount = _parse_amount(amount_raw)
        # 合计行（无日期、只有金额）跳过
        if not m:
            # 有些合计行把总额放在金额列
            if amount and not product:
                continue
            continue
        day = int(m.group(2))
        rent_raw = _clean(_pick(idx, row, "租赁时间"))
        rent_days = _parse_rent_days(rent_raw)
        deposit, deposit_ret = _parse_deposit(_pick(idx, row, "押金"))
        # 类别判定（业务口径，2026-10-12 董事长口径确认）：
        #   有押金 = 租赁订单；无押金 = 销售订单。
        # 「售卖」分隔行与租期仅作交叉校验，用于标记数据异常。
        has_deposit = deposit is not None and deposit > 0
        category = "rent" if has_deposit else "sale"
        warning = None
        if in_sale_block and has_deposit:
            warning = "售卖区内却填了押金"
        elif not in_sale_block and not has_deposit and rent_days is not None:
            warning = "填了租期却没有押金"
        records.append({
            "sheet": sheet_name,
            "month": month,
            "month_label": f"{month}月" if month else sheet_name,
            "date": re.sub(r"[·．]", ".", date_raw),
            "day": day,
            "product": product,
            "customer": _clean(_pick(idx, row, "客户")),
            "channel": _clean(_pick(idx, row, "销售渠道", "渠道")),
            "region": _clean(_pick(idx, row, "地区")),
            "purpose": _clean(_pick(idx, row, "用途")),
            "rent_days": rent_days,
            "amount": amount,
            "deposit": deposit,
            "deposit_returned": deposit_ret,
            "category": category,
            "phone": _clean(_pick(idx, row, "联系方式")),
            "delivery": _clean(_pick(idx, row, "送货")),
            "raw_amount": str(amount_raw).strip(),
            "warning": warning,
        })
    return _dedupe(records)


def _dedupe(records):
    """同一（月, 日期, 客户, 金额, 渠道）只保留一条，产品名中文更全者优先。

    必须带日期：同一客户可能在不同日期发生两笔金额相同的真实业务
    （真实案例：9.7 与 9.15 张佳怡各租飞机轮椅 99 元，是两笔，不能合并）。
    而不带日期的差异才能识别重复录入：9.7「范国全 微信小店 168」在表里出现两次。
    """
    best = {}
    order = []
    for r in records:
        key = (r["month"], r["date"], r["customer"], round(r["amount"], 2), r["channel"])
        if key not in best:
            best[key] = r
            order.append(key)
            continue
        if _cjk_len(r["product"]) > _cjk_len(best[key]["product"]):
            best[key] = r
    return [best[k] for k in order]


def latest_report_file():
    """取销售报表目录里最新修改的 xlsx。"""
    if not os.path.isdir(REPORT_DIR):
        return None
    files = [os.path.join(REPORT_DIR, f) for f in os.listdir(REPORT_DIR)
             if f.lower().endswith((".xlsx", ".xlsm")) and not f.startswith("~$")]
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def load(path=None):
    """读取报表 → 全部记录（跨所有月份 sheet）。"""
    path = path or latest_report_file()
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"未找到销售报表文件：{path}")
    sheets = read_sheets(path)
    out = []
    for name, rows in sheets.items():
        if _month_from_sheet(name) is None and "销售" not in name:
            continue
        out += parse_sheet(rows, name)
    return out, path


def by_month(records):
    months = {}
    for r in records:
        if r["month"] is None:
            continue
        months.setdefault(r["month"], []).append(r)
    return months


if __name__ == "__main__":
    recs, path = load()
    print("报表文件:", path)
    print("记录总数:", len(recs))
    for m, rs in sorted(by_month(recs).items()):
        rent = [r for r in rs if r["category"] == "rent"]
        sale = [r for r in rs if r["category"] == "sale"]
        print(f"  {m} 月: {len(rs)} 条 | 租赁 {len(rent)} 条 {sum(r['amount'] for r in rent):.2f} 元 "
              f"| 售卖 {len(sale)} 条 {sum(r['amount'] for r in sale):.2f} 元 "
              f"| 合计 {sum(r['amount'] for r in rs):.2f} 元")
