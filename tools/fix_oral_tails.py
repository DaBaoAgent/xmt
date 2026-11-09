# -*- coding: utf-8 -*-
"""口播号全量统一尾句：关注翔哥，了解更多辅具知识。"""
import io
import json
import os
import sqlite3
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\kaifa\xmt"
sys.path.insert(0, ROOT)
from scriptgen import util  # noqa: E402
from scriptgen.writer import body_plain_text  # noqa: E402

DB = os.path.join(ROOT, "data", "xmt.db")
BACKUP = r"D:\Marvis\AppData\User\oAN1i2fa3mCDdNRLFxcCY547Ub5Q\workspace\conv_ce289dbbc01b4d1ca4195f00f09cbc8a\temp\backup_oral_tails.json"

TAIL = "关注翔哥，了解更多辅具知识。"

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
rows = con.execute("select code,title,body_json from sg_scripts where account_id='oral' order by code").fetchall()

backup = {}
changed = []
for r in rows:
    code = r["code"]
    body = json.loads(r["body_json"])
    backup[code] = body["lines"]
    lines = body["lines"]
    old = lines[-1]["text"]
    if "翔哥" in old or "关注" in old:
        if old.strip() == TAIL:
            continue
        lines[-1]["text"] = TAIL
        act = "替换"
    else:
        if old.strip() == TAIL:
            continue
        lines.append({"speaker": "", "beat": "口播", "text": TAIL})
        act = "追加"
    body_text = body_plain_text(body)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    con.execute("UPDATE sg_scripts SET body_json=?, body_md=?, word_count=?, estimated_seconds=?, "
                "version=version+1, updated_at=? WHERE code=?",
                (json.dumps(body, ensure_ascii=False), body_text, wc, sec, util.now_iso(), code))
    changed.append((code, act, old, wc, sec))

os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
with open(BACKUP, "w", encoding="utf-8") as f:
    json.dump(backup, f, ensure_ascii=False, indent=1)
con.commit()

print("已更新 %d 篇（备份：%s）" % (len(changed), BACKUP))
for code, act, old, wc, sec in changed:
    print("  %s %s  「%s」→ %d字/%.1f秒" % (code, act, old, wc, sec))
print("CODES=" + " ".join(c for c, *_ in changed))
con.close()
