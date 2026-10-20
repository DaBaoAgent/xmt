"""把当前定稿导出成技能范例文件（对标原句 → 改后）。

用法：
  .venv/Scripts/python.exe .workbuddy/skills/scriptgen-writing/build_examples.py
"""
import os
import io
import sys
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, ROOT)

from scriptgen.sources import RedFoxExtractor  # noqa: E402

OUT = os.path.join(HERE, "examples", "四篇定稿范例.md")

HEADER = """# 四篇定稿范例（对标原句 → 改后）

每篇都按「骨架照搬 + 词级近义替换」改写：保留对标每句的句式骨架、语序、节奏，
但每个词换成我们的近义表达。新稿可直接参照这四篇的改法。

看的时候重点关注：改之前先读「对标原句」，再看「改后」是怎么一句对一句替换的。
"""


def main():
    con = sqlite3.connect(os.path.join(ROOT, "data", "xmt.db"))
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        "SELECT * FROM sg_scripts ORDER BY code")]
    con.close()

    ex = RedFoxExtractor()
    parts = [HEADER]
    for r in rows:
        try:
            t = ex.extract_channels(r["benchmark_url"])
            segs = (t.get("transcript") or {}).get("segments") or []
            src = "\n".join(s.get("text", "") for s in segs)
            meta = "%s ｜ %s ｜ 时长 %.1fs" % (
                t.get("author") or "—",
                " ".join(str(t.get("title") or "").split())[:30],
                float(t.get("duration_sec") or 0))
        except Exception as e:
            src = "(提取失败：%s)" % e
            meta = "—"

        scope = r.get("product_model") or r.get("product_scope") or "品类"
        parts.append("\n---\n")
        parts.append("## %s ｜ %s\n" % (r["account_label"], r["title"]))
        parts.append("**成稿**：%s 字 / %.1f 秒（目标 %.0f 秒）｜ 产品口径：%s\n" % (
            r["word_count"], r["estimated_seconds"],
            r["target_seconds"], scope))
        parts.append("**对标**：%s\n\n" % meta)
        parts.append("### 对标原句\n\n```\n%s\n```\n\n" % src)
        parts.append("### 改后\n\n```\n%s\n```\n" % r["body_md"])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("已生成：%s（%d 篇）" % (OUT, len(rows)))


if __name__ == "__main__":
    main()
