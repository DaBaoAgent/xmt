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
ORDER_FILE = os.path.join(ROOT, "config", "export_order.json")


def load_order():
    """出稿顺序从 config/export_order.json 读（由 finish_script.py 自动维护），
    不再硬编码在本文件里——新 code 由收尾脚本按账号自动插入，不会再漏。"""
    import json
    with io.open(ORDER_FILE, encoding="utf-8") as f:
        return json.load(f)["order"]


def collect_archived():
    """扫描 稿子/{账号}/ 下的子目录（用户的归档区，如「1 已用」），
    返回 {(账号, 标题)} 集合。

    用户的归档习惯（2026-10-23 明确）：用过的稿子自己移进 {账号}/1 已用/，
    导出工具**不把这些稿子再写回账号根目录**——移出来是他不想要的。
    子目录里的文件一律只读不动。"""
    archived = set()
    for sub in ACCOUNT_DIRS:
        d = os.path.join(OUT_DIR, sub)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            sd = os.path.join(d, name)
            if not os.path.isdir(sd):
                continue
            for f in os.listdir(sd):
                if not f.endswith(".txt"):
                    continue
                title = f[:-4]
                if "_" in title:                 # 文件名格式 NNN_标题.txt
                    title = title.split("_", 1)[1]
                archived.add((sub, title))
    return archived


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
    archived = collect_archived()
    if archived:
        print("归档区（不导出到根目录）：%d 篇" % len(archived))
    seq = {sub: 0 for sub in ACCOUNT_DIRS}
    n = 0
    for code in load_order():
        r = by.get(code)
        if not r:
            print("跳过（库里没有）:", code)
            continue
        if (r["account_label"], r["title"]) in archived:
            print("跳过（已归档到子目录）: %s %s" % (r["account_label"], r["title"]))
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
