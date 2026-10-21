r"""把库里所有稿子导出成「一篇一个单独 txt」，放在 稿子/{账号}/ 目录。

用法：
  .venv/Scripts/python.exe tools/export_standalone.py

产出：
  D:\kaifa\xmt\稿子\口播号\001_标题.txt
  D:\kaifa\xmt\稿子\品牌号\001_标题.txt
  D:\kaifa\xmt\稿子\个人号\001_标题.txt
（序号跟 out/ 的 Word 全局序号一致，账号由文件夹标明，文件名不再重复账号段）
文件内容：标题 + 账号/字数/时长 + 台词正文（单人口播无前缀，双人稿带「说话人：」）
"""
import os
import io
import sys
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from scriptgen import store  # noqa: E402
from scriptgen import pipeline  # noqa: E402

DB = os.path.join(ROOT, "data", "xmt.db")
OUT_DIR = os.path.join(ROOT, "稿子")
ACCOUNT_DIRS = ("口播号", "品牌号", "个人号")

# 出稿顺序：跟 out/*.docx 的文件序号保持一致
ORDER = [
    "SG-20261020-019", "SG-20261020-020", "SG-20261020-021", "SG-20261020-022",
    "SG-20261020-023", "SG-20261020-024", "SG-20261020-025", "SG-20261020-026",
    "SG-20261020-027", "SG-20261020-028",
    "SG-20261020-029", "SG-20261020-003", "SG-20261020-005",
    "SG-20261020-012", "SG-20261020-013", "SG-20261020-014", "SG-20261020-015",
    "SG-20261020-016", "SG-20261020-017", "SG-20261020-007", "SG-20261020-008",
    "SG-20261020-009", "SG-20261020-010", "SG-20261020-011", "SG-20261020-002",
    "SG-20261020-001", "SG-20261020-004", "SG-20261020-018",
    "SG-20261020-030", "SG-20261020-031", "SG-20261020-032",
    "SG-20261020-033", "SG-20261020-034",
    "SG-20261020-035", "SG-20261020-036", "SG-20261020-037",
    "SG-20261020-038", "SG-20261020-039",
]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    os.makedirs(OUT_DIR, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    by = {dict(r)["code"]: dict(r) for r in con.execute(
        "SELECT * FROM sg_scripts")}
    con.close()

    # 清掉旧的：根下的 txt，以及三个账号子目录里的 txt
    for f in os.listdir(OUT_DIR):
        p = os.path.join(OUT_DIR, f)
        if os.path.isfile(p) and f.endswith(".txt"):
            os.remove(p)
    for sub in ACCOUNT_DIRS:
        d = os.path.join(OUT_DIR, sub)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".txt"):
                    os.remove(os.path.join(d, f))
        else:
            os.makedirs(d, exist_ok=True)

    # 编号改为「账号内连续序号」：每个子文件夹从 001 开始，ORDER 定先后
    seq = {sub: 0 for sub in ACCOUNT_DIRS}
    n = 0
    for code in ORDER:
        r = by.get(code)
        if not r:
            print("跳过（库里没有）:", code)
            continue
        n += 1
        sub = r["account_label"]          # 口播号 / 品牌号 / 个人号
        seq[sub] = seq.get(sub, 0) + 1
        name = "%03d_%s.txt" % (seq[sub], r["title"])
        path = os.path.join(OUT_DIR, sub, name)
        with io.open(path, "w", encoding="utf-8") as f:
            f.write("%s\n" % r["title"])
            f.write("%s ｜ %d 字 / %.1f 秒\n" % (
                r["account_label"], r["word_count"], r["estimated_seconds"]))
            f.write("=" * 46 + "\n\n")
            f.write(r["body_md"])
            f.write("\n")
        print("%s\\%s" % (sub, name))
    print("\n共 %d 篇 → %s" % (n, OUT_DIR))
    for sub in ACCOUNT_DIRS:
        print("  %s：%d 篇" % (sub, seq.get(sub, 0)))


if __name__ == "__main__":
    main()
