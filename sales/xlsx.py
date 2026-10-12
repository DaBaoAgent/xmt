"""零依赖 XLSX 读取。

为什么不用 openpyxl：本项目的销售报表由 WPS 导出，样式表里含空 `<fill/>` 元素，
openpyxl 3.0.10 与 3.1.5 都会在 apply_stylesheet 阶段抛
`TypeError: Fill() takes no arguments`。这里直接读 OOXML（zip + XML），
只取单元格文本值，不解析样式，因此对 WPS/Excel 任何版本都稳。

返回格式：{sheet_name: [[cell, cell, ...], ...]}，行内按列索引对齐（缺列补空串）。
"""
import re
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _col_index(ref):
    m = re.match(r"([A-Z]+)", ref or "")
    if not m:
        return 0
    n = 0
    for ch in m.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _shared_strings(z):
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    out = []
    for si in root.findall(NS + "si"):
        out.append("".join(t.text or "" for t in si.iter(NS + "t")))
    return out


def _sheet_rows(z, target, shared):
    if target not in z.namelist():
        # 有些包的 target 带前导斜杠或相对路径差异，兜底按名字匹配
        cand = [n for n in z.namelist() if n.endswith(target.split("/")[-1])]
        if not cand:
            return []
        target = cand[0]
    root = ET.fromstring(z.read(target))
    rows = []
    for row in root.iter(NS + "row"):
        vals = {}
        for c in row.findall(NS + "c"):
            t = c.get("t")
            v = c.find(NS + "v")
            if t == "s" and v is not None and v.text is not None:
                idx = int(v.text)
                val = shared[idx] if 0 <= idx < len(shared) else ""
            elif t == "inlineStr":
                node = c.find(NS + "is")
                val = "".join(x.text or "" for x in node.iter(NS + "t")) if node is not None else ""
            else:
                val = v.text if v is not None else ""
            vals[_col_index(c.get("r"))] = (val or "").strip()
        if vals:
            width = max(vals) + 1
            rows.append([vals.get(i, "") for i in range(width)])
    return rows


def read_sheets(path):
    """读取整个工作簿 → {sheet_name: rows}。"""
    with zipfile.ZipFile(path) as z:
        shared = _shared_strings(z)
        rels = {}
        root = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        for r in root:
            rels[r.get("Id")] = r.get("Target")
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        out = {}
        sheets = wb.find(NS + "sheets")
        if sheets is None:
            return out
        for sh in sheets.findall(NS + "sheet"):
            name = sh.get("name")
            target = rels.get(sh.get(RNS + "id"), "")
            target = target.lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            out[name] = _sheet_rows(z, target, shared)
        return out


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "销售报表/新媒体销售报表-2026.8.xlsx"
    for name, rows in read_sheets(path).items():
        print(f"=== {name} ({len(rows)} 行)")
        for r in rows[:8]:
            print("  ", " | ".join(r))
