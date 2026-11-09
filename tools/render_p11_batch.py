# -*- coding: utf-8 -*-
import os
import sqlite3
import sys

ROOT = r"D:\kaifa\xmt"
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from scriptgen import store, pipeline  # noqa: E402

CODES = ["SG-20261023-080", "SG-20261023-081", "SG-20261023-082",
         "SG-20261023-083", "SG-20261023-084"]

con = sqlite3.connect("data/xmt.db")
con.row_factory = sqlite3.Row
for code in CODES:
    s = store.get_script(con, code)
    p = store.script_path(s)
    print(code, "id=%s" % s["id"], p)
    store.update_script(con, code, file_path=p)
    con.commit()
    pipeline._render_script(con, code)
con.close()
