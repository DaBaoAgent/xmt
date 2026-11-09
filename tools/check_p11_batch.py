# -*- coding: utf-8 -*-
import sqlite3
con = sqlite3.connect(r"D:\kaifa\xmt\data\xmt.db")
con.row_factory = sqlite3.Row
lasts = {}
for r in con.execute("select code,title,body_md from sg_scripts where account_label='个人号' order by id"):
    lines = [x for x in (r["body_md"] or "").split("\n") if x.strip()]
    if not lines:
        continue
    lasts.setdefault(lines[-1].strip(), []).append((r["code"], r["title"]))
print("--- 收尾句重复检查 ---")
dup = 0
for k, v in lasts.items():
    if len(v) > 1:
        dup += 1
        print("重复:", k, v)
print("重复组数:", dup)
print("--- 新稿字数/时长 ---")
for r in con.execute("select code,title,word_count,estimated_seconds,target_seconds,status,docx_path from sg_scripts where code like 'SG-20261023-%' order by code"):
    print(r["code"], r["word_count"], "字", round(r["estimated_seconds"], 1), "秒", r["target_seconds"], r["status"], r["docx_path"])
