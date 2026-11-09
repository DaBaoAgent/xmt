# -*- coding: utf-8 -*-
"""品牌号对话稿「弱智问题」体检。

背景：用户退回过多篇对话稿，问题都是提问环节写了陪衬废话
（问上一轮的余味、答案空转「过得去」、跟上一轮卖点复读、自问自答式解释）。

本脚本只做机检提示，不阻断。三条规则：

R1 卖点复读：同一篇里，本轮答句与上一轮答句的实词重合 >= 2 个
   —— 说明两轮在讲同一个特点，第二问是浪费。
R2 抽象问句：问句里没有任何具体锚点（数字 / 中文数字 / 人物称谓 / 场景名词表命中）
   —— 说明这问不像真人挑刺，像给答案铺路。
R3 答案空转：答句 <= 6 字且不含数字/规格单位
   —— 说明答的是情绪话（「过得去」「没问题」），没给事实。

用法：
    python tools/check_dialogue_quality.py                # 体检全部品牌号对话稿
    python tools/check_dialogue_quality.py SG-20261024-107 ...
    python tools/check_dialogue_quality.py --quiet        # 只列有问题的
"""
import io
import json
import os
import re
import sqlite3
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "xmt.db")

# 具体锚点：数字、人物称谓、常见生活场景词
ANCHOR_WORDS = (
    "我妈", "我爸", "我爷", "我奶", "老人", "老伴", "家里", "楼上", "楼下",
    "菜场", "买菜", "赶集", "医院", "复查", "超市", "电梯", "楼道", "门槛",
    "卫生间", "厨房", "阳台", "卧室", "门口", "后备箱", "车上", "出门",
    "天黑", "下雨", "晚上", "早上", "冬天", "夏天", "坡", "台阶", "瓷砖",
    "砖", "地砖", "水泥", "夜里", "上路", "公交", "地铁",
)
NUM_RE = re.compile(r"[0-9０-９一二两三四五六七八九十百千万几半]+")
UNIT_RE = re.compile(r"公斤|kg|斤|厘米|公分|cm|毫米|mm|寸|米|档|度|伏|瓦|安|小时|分钟|秒|个字|元|块")


def _segments(body_md):
    lines = [l.strip() for l in body_md.splitlines() if l.strip()]
    pairs, cur = [], None
    for l in lines:
        if "：" not in l:
            continue
        sp, tx = l.split("：", 1)
        if cur is None:
            cur = {"q_by": sp, "q": tx, "a_by": "", "a": ""}
        elif not cur["a"]:
            cur["a_by"], cur["a"] = sp, tx
            pairs.append(cur)
            cur = None
    return pairs


def _tokens(text):
    """粗粒度实词：去标点后的 2 字以上片段，用于判断两句话是否在讲同一件事。"""
    chunks = re.split(r"[，。？！、；：“”‘’\s（）()…—]+", text)
    return {c for c in chunks if len(c) >= 2}


def check_one(code, title, body_md):
    problems, pairs = [], _segments(body_md)
    prev_answer_tokens = set()
    for i, p in enumerate(pairs, 1):
        q, a = p["q"], p["a"]
        # R1 卖点复读
        if prev_answer_tokens:
            overlap = (prev_answer_tokens & _tokens(a))
            if len(overlap) >= 2:
                problems.append(("R1", i, "与上一轮卖点复读: " + "/".join(sorted(overlap)[:3])))
        # R2 抽象问句：极短且无任何锚点，才像「光秃秃问一句好不好」
        if len(q) <= 6 and not NUM_RE.search(q) and not any(w in q for w in ANCHOR_WORDS):
            problems.append(("R2", i, "问句没有具体锚点（无数字/人物/场景）: " + q))
        # R3 答案空转
        if len(a) <= 6 and not UNIT_RE.search(a) and not NUM_RE.search(a):
            problems.append(("R3", i, "答句空转、没给事实: " + a))
        prev_answer_tokens = _tokens(a)
    return problems


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    quiet = "--quiet" in sys.argv
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    sql = ("SELECT code, title, body_json, body_md FROM sg_scripts "
           "WHERE account_id='brand' ORDER BY code")
    rows = con.execute(sql).fetchall()
    if args:
        rows = [r for r in rows if r["code"] in args]
    con.close()

    bad = 0
    for r in rows:
        try:
            fmt = (json.loads(r["body_json"] or "{}") or {}).get("format")
        except Exception:
            fmt = None
        if fmt != "dialogue":
            continue
        body_md = r["body_md"] or ""
        probs = check_one(r["code"], r["title"], body_md)
        if probs:
            bad += 1
            print("[%s] %s" % (r["code"], r["title"]))
            for rule, idx, msg in probs:
                print("   %s 第%d来回 %s" % (rule, idx, msg))
        elif not quiet:
            print("[%s] %s  OK" % (r["code"], r["title"]))
    total = len(rows)
    print("\n对话稿 %d 篇，问题稿 %d 篇。" % (total, bad))
    return 0


if __name__ == "__main__":
    sys.exit(main())
