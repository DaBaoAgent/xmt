"""analytics 分析层：只读 SQLite，产出「增长 / 爆款 / 对标」三类分析。

本包所有模块都只读数据（db.connect()），唯一的写入发生在 report.py 落洞察（db.save_insight）。
数据可能为空（首次运行），因此所有函数在空数据下返回空结构而不抛异常。

共享工具（供 growth / hits / bench / report 复用）：
  disp_width(s)            文本显示宽度（中文按 2 列计）
  pad(s, width, align)     按显示宽度补齐 / 右对齐 / 居中
  fmt_num(n)               中文数字：万 / 亿 / 千分位
  fmt_delta(n)             带符号的增量：+1.2万 / -3
  fmt_pct(x)               百分比：+12.3% / — 
  fmt_ratio(x)             小数比率（保留位数可调）
  render_table(...)        生成对齐的中文纯文本表格
  parse_date(s)            "YYYY-MM-DD" -> date
  date_str(d)              date -> "YYYY-MM-DD"
  today_str()              今天 "YYYY-MM-DD"
  parse_time(s)            解析多种发布时间字符串 -> datetime
  work_dt(row)             从作品行取发布时间（优先 publish_ts，回退 publish_time）
  clean_title(s, limit)    取首行 + 去话题标签 + 压缩空白（抖音「标题」常是整段文案）
"""
import re
import unicodedata
from datetime import datetime, date, timedelta

# 平台中文名
PLATFORM_LABEL = {"douyin": "抖音", "xiaohongshu": "小红书", "channels": "视频号"}

# ---------- 文本清洗 ----------

_HASHTAG_STRIP = re.compile(r"#[^\s#]+")
_WS_RE = re.compile(r"\s+")


def clean_title(text, limit=None):
    """抖音/小红书的「标题」字段常是整段文案（含换行与 #话题标签）。

    取首行 + 去掉话题标签 + 压缩空白，用于长度/句式统计与列表展示。
    原始数据不动（统计话题标签时仍用原文）。
    """
    if not text:
        return ""
    t = str(text).replace("\r", "\n").split("\n")[0]
    t = _HASHTAG_STRIP.sub("", t)
    t = _WS_RE.sub(" ", t).strip(" -—·|，,。.")
    return t[:limit] if limit else t


# ---------- 显示宽度与格式化 ----------

def disp_width(s):
    """显示宽度：东亚宽/全角字符按 2 列，其余按 1 列。用于中文表格对齐。"""
    w = 0
    for ch in str(s):
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


def pad(s, width, align="left"):
    """按显示宽度补齐到 width。align ∈ {left, right, center}。"""
    s = "" if s is None else str(s)
    gap = width - disp_width(s)
    if gap <= 0:
        return s
    if align == "right":
        return " " * gap + s
    if align == "center":
        left = gap // 2
        return " " * left + s + " " * (gap - left)
    return s + " " * gap


def fmt_num(n):
    """中文数字格式化：亿 / 万 / 千分位；None -> —。"""
    if n is None:
        return "—"
    try:
        f = float(n)
    except (TypeError, ValueError):
        return str(n)
    if f != f:  # NaN
        return "—"
    a = abs(f)
    if a >= 1e8:
        return f"{f / 1e8:.2f}亿"
    if a >= 1e4:
        return f"{f / 1e4:.1f}万"
    if a == int(a):
        return f"{int(f):,}"
    return f"{f:,.1f}"


def fmt_delta(n):
    """带符号增量：正数补 +。"""
    if n is None:
        return "—"
    if n > 0:
        return "+" + fmt_num(n)
    if n < 0:
        return "-" + fmt_num(abs(n))
    return "0"


def fmt_pct(x, signed=True):
    """百分比：None -> —。"""
    if x is None:
        return "—"
    return f"{x:+.1f}%" if signed else f"{x:.1f}%"


def fmt_ratio(x, nd=3):
    """小数比率（如互动效率），None -> —。"""
    if x is None:
        return "—"
    return f"{x:.{nd}f}"


def render_table(headers, rows, aligns=None):
    """生成对齐的中文纯文本表格（自动按显示宽度对齐）。"""
    headers = [str(h) for h in headers]
    aligns = aligns or ["left"] * len(headers)
    ncol = len(headers)
    data = [["" if c is None else str(c).replace("\n", " ").replace("\r", " ") for c in r]
            for r in rows]
    widths = [disp_width(h) for h in headers]
    for r in data:
        for i in range(min(ncol, len(r))):
            widths[i] = max(widths[i], disp_width(r[i]))
    sep = "-+-".join("-" * w for w in widths)
    lines = [" | ".join(pad(h, widths[i], aligns[i]) for i, h in enumerate(headers)), sep]
    for r in data:
        cells = [pad(r[i] if i < len(r) else "", widths[i], aligns[i]) for i in range(ncol)]
        lines.append(" | ".join(cells))
    return "\n".join(lines)


# ---------- 时间解析 ----------

_TIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d",
    "%Y.%m.%d %H:%M",
    "%Y.%m.%d",
)


def parse_date(s):
    """解析 "YYYY-MM-DD"（取前 10 位）为 date；失败返回 None。"""
    if not s:
        return None
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def date_str(d):
    """date/datetime -> "YYYY-MM-DD"；None -> None。"""
    if d is None:
        return None
    return d.strftime("%Y-%m-%d")


def today_str():
    return date.today().strftime("%Y-%m-%d")


def parse_time(s):
    """解析多种发布时间字符串为 datetime；失败返回 None。"""
    if not s:
        return None
    s = str(s).strip()
    for f in _TIME_FORMATS:
        try:
            return datetime.strptime(s, f)
        except ValueError:
            continue
    # 兜底：ISO 带 T
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _row_get(row, key):
    """兼容 dict 与 sqlite3.Row 的取值。"""
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def work_dt(row):
    """从作品行取发布时间：优先 publish_ts(秒级时间戳)，回退 publish_time 字符串。"""
    ts = _row_get(row, "publish_ts")
    if ts:
        try:
            return datetime.fromtimestamp(int(ts))
        except (ValueError, OSError, OverflowError, TypeError):
            pass
    return parse_time(_row_get(row, "publish_time"))
