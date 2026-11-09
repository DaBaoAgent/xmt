# -*- coding: utf-8 -*-
"""把 080-084 的 Word 序号接到 out/ 现有最大号后面（082→079 ... 086→083）。"""
import glob
import os
import re
import sqlite3
import sys

ROOT = r"D:\kaifa\xmt"
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from scriptgen import store  # noqa: E402

PAIRS = [
    ("082_个人号_这台折叠代步车能干四件事.docx", "079_个人号_这台折叠代步车能干四件事.docx"),
    ("083_个人号_轮子这么小过坎行不行.docx", "080_个人号_轮子这么小过坎行不行.docx"),
    ("084_个人号_折叠代步车到底怎么折怎么展开.docx", "081_个人号_折叠代步车到底怎么折怎么展开.docx"),
    ("085_个人号_送爸妈代步车别只问要不要.docx", "082_个人号_送爸妈代步车别只问要不要.docx"),
    ("086_个人号_买折叠代步车先避开这三个坑.docx", "083_个人号_买折叠代步车先避开这三个坑.docx"),
]

con = sqlite3.connect("data/xmt.db")
con.row_factory = sqlite3.Row
codes = ["SG-20261023-080", "SG-20261023-081", "SG-20261023-082",
         "SG-20261023-083", "SG-20261023-084"]
for (old, new), code in zip(PAIRS, codes):
    src = os.path.join("out", old)
    dst = os.path.join("out", new)
    if os.path.exists(src):
        if os.path.exists(dst):
            os.remove(dst)
        os.rename(src, dst)
        print("renamed:", old, "->", new)
    else:
        print("missing:", old)
    store.update_script(con, code, docx_path=os.path.abspath(dst))
con.commit()
con.close()
print("--- out/*.docx 现状 ---")
for f in sorted(glob.glob("out/*.docx"))[-8:]:
    print(" ", f)
