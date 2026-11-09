# -*- coding: utf-8 -*-
"""个人号 11-09 第 1 篇（v2）：P10 · 单人口播 · 换角度＝扶手抬 90° 上下车。

用户指令链：
  2026-11-09「帮我写个P10的脚本 单人的个人号」→ 写 v1「控制器能换到另一只手上」
  → 2026-11-09「我一个人拍 没办法换方向」

为什么废 v1：控制器换边要「拆下来 → 换到另一边 → 插回去」，成片里这个动作必须
正反两个方向都拍到才说得清，一个人一台机器换不了方向就拍不出来。

为什么换扶手：P10 两侧扶手可抬起 90°，老人腿抬不高、跨不过去时，扶手一抬人从
侧面横着挪进去即可。整套动作全在原地、单人、单方向、不出画框，一条镜头能吃下来。

资料口径（jiaoben/P10碳纤维电动轮椅10AH锂电_产品信息总结.txt）：
「两侧扶手可抬起 90°；脚踏三档高低可调」→ 只写扶手抬 90°、横着挪进去、放下来
胳膊有地方搁，不虚构扶手锁扣、不写「轻松」「一根手指」等绝对化词。

合规：不写价格（6680 禁）、不写重量（15.8kg 不含电池口径）、不提 PRIDE 同款、
不写疾病名。尾句「扶着您上来试」已全库比对，不与既有收尾重复。
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

CODE = "SG-20261109-001"
TITLE = "这轮椅的扶手，能整个抬起来"

LINES = [
    "爷爷奶奶，这轮椅的扶手，能往上抬起来。",
    "抬手一掀，它就立起来了，九十度停住。",
    "不用跨，人从侧面横着挪进去就行。",
    "腿抬不高的，这一步最省劲。",
    "坐好了把扶手放下来，胳膊有地方搁。",
    "展厅在苏州阳光大厦，扶着您上来试。",
]

TIPS = [
    "机位固定不动，人站在车侧方，全程脚不挪、不出画框，一条镜头吃下来不剪",
    "第一句说完手就搭到扶手上，说「抬手一掀」当场把它抬到九十度，抬到位停半秒让镜头看清立起来",
    "说「横着挪进去」时人就侧身坐进去，动作做完整、别提速，中间不剪",
    "说「放下来」把扶手压回原位，压到底听一声，再把手搁上去停一下",
    "全程不换方向、不绕到车另一边，镜头略前倾把人和扶手都框在正中",
    "收尾说完就停，不催不劝不喊口号",
]

FACT_TEXT = (
    "佳康顺P10碳纤维电动轮椅（10AH锂电）：碳纤维车架，整车净重15.8KG（不含电池）；"
    "两侧扶手可抬起90°，脚踏三档高低可调；免弯腰一体式一键折叠，折叠后宽34cm×高80cm；"
    "展开尺寸103×60×90cm；智能电磁刹车，松手即停、双向制动、断电自动刹车；"
    "最大承重150KG；10AH三元锂电（LG电芯）续航15km；170W×2无刷双电机合计340W；"
    "免充气实心防爆轮胎；电动/手推/APP遥控三模式；控制器可左右互换。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号单人口播（只 B 出镜，不标说话人）+ 简单档（约95-105字/22-25秒）+ 口语唠嗑腔。"
    "产品：P10 碳纤维电动轮椅。角度：两侧扶手可抬 90°，老人不用跨、侧身横着挪上车。"
    "2026-11-09 用户口径「我一个人拍 没办法换方向」→ 废 v1 控制器换边（拆下换边插回，"
    "需正反两个方向才说得清），改为扶手抬 90° 上下车：单人、固定机位、原地动作、不出画框。"
    "不写价格（到手价 6680 元禁写）；不写重量（15.8kg 为不含电池口径）；"
    "不提美国 PRIDE 同款；不虚构锁扣与「轻松」类绝对化词。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（单人口播·扶手抬90°·v2）",
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
    row = con.execute("SELECT id FROM sg_scripts WHERE code=?", (CODE,)).fetchone()
    assert row, "库里没有 %s" % CODE
    con.execute(
        "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
        "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
        "compliance_json=?, product_model=?, product_scope=?, notes=?, "
        "status='待审', version=version+1, updated_at=? WHERE code=?",
        (TITLE, json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
         json.dumps(TIPS, ensure_ascii=False),
         json.dumps(scan, ensure_ascii=False), "P10碳纤维电动轮椅10AH锂电",
         "型号", NOTES, now, CODE))
    con.commit()
    con.close()

    print("=== %s（%s v2）===" % (TITLE, CODE))
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
