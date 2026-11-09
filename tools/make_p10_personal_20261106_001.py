# -*- coding: utf-8 -*-
"""个人号 11-06 第 1 篇：P10 碳纤维电动轮椅 · 单人口播 · 控制器换手角度。

用户 2026-11-06 指令：「帮我写个P10的脚本 单人的个人号」
→ 新增一篇（新 code SG-20261106-001），不覆盖 11-04 的 013「买轮椅先看轮子」。

单人口播体例：只 B（小冯）出镜，正文不标说话人，不出现 A/B、不写「拍摄」。

角度选择（P10 已用角度盘点）：
- 074 全介绍 / 075 能带上飞机 / 076 爬坡 / 077 老人自己会用 / 078 十五公斤（已归档）
- 013 实心免充气胎（待审）
- 口播 026 三款对比（已归档）
- F2Q 009 已用「没电也能推」、A3 012 已用「折叠」→ 跨产品也不重复选用
本次新角度：控制器左右互换（资料原文「控制器可左右互换」，P10 个人号从未写过）。
选它的理由：现场一拧一放就能演示，观众几乎没在别家见过；对右手不便/惯用左手
的老人是实打实的差别，不用堆参数就能说清。

合规处理：
- 不写价格（到手价 6680 元禁写）、不写重量（15.8kg 为不含电池口径）
- 不提「美国 PRIDE 同款」、不写疾病名（不用「中风/偏瘫」，只写「右手不得劲」）
- 不写「不会摔倒/安全」，刹车只写客观动作「手一松自己刹住」
- 尾句已全库查重（库 + 稿子/**/*.txt 均无重复）
"""
import io
import json
import os
import sqlite3
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scriptgen import util  # noqa: E402
from scriptgen import compliance  # noqa: E402

DB = os.path.join(ROOT, "data", "xmt.db")

CODE = "SG-20261106-001"
TITLE = "这台车的控制器能换手"

LINES = [
    "爷爷奶奶，这台车的控制器，能换手。",
    "右手不得劲，就挪到左手边。",
    "一提一放，几分钟就换过来。",
    "摇杆往前轻轻一推就走，手一松它自己刹住。",
    "谁用着顺手，就搁哪边。",
    "展厅在苏州阳光大厦，来换一次手。",
]

TIPS = [
    "上手就把控制器从右边拧下来，动作要真做，别只比划",
    "换到左边装好，立刻用左手推摇杆让车走两步，让人看见真能用",
    "「手一松自己刹住」拍在斜坡上：松手、车停住、镜头停两秒",
]

FACT_TEXT = (
    "佳康顺P10碳纤维电动轮椅（10AH锂电）：碳纤维车架，整车净重15.8KG（不含电池）；"
    "控制器可左右互换，万向摇杆；智能电磁刹车，松手即停、双向制动、断电自动刹车；"
    "三种控制方式：电动行走/手推行走/APP手机遥控；最大承重150KG；"
    "10Ah三元锂电（LG电芯）续航15km；170W×2无刷双电机合计340W；"
    "免充气实心防爆轮胎；SOS一键求救语音。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号单人口播（只 B 出镜，不标说话人）+ 简单档（约90-105字/21-25秒）+ 口语唠嗑腔。"
    "产品：P10 碳纤维电动轮椅。角度：控制器左右互换（P10 个人号首次写；074 全介绍/075 飞机/"
    "076 爬坡/077 会用/078 重量/013 实心胎均未用过此角度）。"
    "不写价格（到手价 6680 元禁写）；不写重量（15.8kg 为不含电池口径）；"
    "不提美国 PRIDE 同款；不写疾病名（用「右手不得劲」，不用中风/偏瘫）；"
    "刹车只写客观动作「手一松自己刹住」。尾句已全库查重。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（单人口播·控制器换手）",
            "lines": [{"speaker": "", "text": t} for t in LINES]}
    body_text = "\n".join(LINES)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    target = 30.0
    scan = compliance.scan_script(
        body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    now = util.now_iso()
    exists = con.execute("SELECT id FROM sg_scripts WHERE code=?", (CODE,)).fetchone()
    assert not exists, "%s 已存在，先确认是否要覆盖" % CODE
    con.execute(
        "INSERT INTO sg_scripts (code, created_at, updated_at, status, account_id, "
        "account_label, presenters_json, source_platform, product_model, "
        "product_doc_ids_json, title, body_json, body_md, shooting_tips_json, "
        "compliance_json, facts_json, word_count, estimated_seconds, "
        "target_seconds, version, product_scope, notes) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (CODE, now, now, "待审", "personal", "个人号",
         json.dumps(["小冯"], ensure_ascii=False), "original",
         "P10碳纤维电动轮椅10AH锂电", json.dumps([], ensure_ascii=False),
         TITLE, json.dumps(body, ensure_ascii=False), body_text,
         json.dumps(TIPS, ensure_ascii=False),
         json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
         wc, sec, target, 1, "型号", NOTES))
    con.commit()
    con.close()

    print("=== %s（%s）===" % (TITLE, CODE))
    print("%d 字 / %.1f 秒（目标 %.1f 秒）｜ 合规 %s" % (
        wc, sec, target, scan.get("counts")))
    print()
    print(body_text)
    findings = scan.get("findings") or []
    if findings:
        for f in findings:
            print("  [%s] %s 「%s」 %s" % (
                f.get("severity"), f.get("rule_id"), f.get("match"),
                f.get("suggest") or ""))
    else:
        print("  （无合规命中）")


if __name__ == "__main__":
    main()
