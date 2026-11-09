# -*- coding: utf-8 -*-
"""个人号 11-06 第 1 篇（v2）：P10 · 单人口播 · 换角度＝一键折叠（好展示）。

用户 2026-11-06 指令链：「帮我写个P10的脚本 单人的个人号」→「换一个 这个不好展示」
即废掉 v1 控制器换手角度，换成镜头前一眼能看懂的卖点。

为什么换折叠：
- v1 控制器换手要拧、要拆、要换边再装，成片里观众看不出差别
- 折叠是「一个动作看完」的卖点：手往上一提 → 车收住 → 折后 34cm → 一只手拖走，
  全程不用解说，镜头跟着走就说明白了；老人刷视频停留靠的就是这种可见变化
- P10 个人号此前没有单独写过折叠（074 只在报长处时带一句；A3 的 012 是另一台车）

资料口径（jiaoben/P10碳纤维电动轮椅10AH锂电_产品信息总结.txt）：
免弯腰一体式折叠，一键快速折叠，折叠后宽 34cm × 高 80cm，可推行、可拉行。
→ 只说「手往上一提就收住」「折完三十四公分宽」「抓着拖着走」，
  不虚构拉杆、不写「一根手指」「轻松」等绝对化词。

合规：不写价格（6680 禁）、不写重量（15.8kg 不含电池口径）、不提 PRIDE 同款、
不写疾病名。尾句已全库查重（「来折一次试试」与 008 重复，已避开）。
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
TITLE = "这车折起来跟行李箱一样"

LINES = [
    "爷爷奶奶，这车折起来，跟行李箱一样。",
    "手往上一提，它自己就收住了，不用弯腰。",
    "折完三十四公分宽，门后头就能搁。",
    "抓着把手，一只手拖着走。",
    "出远门塞后备箱，也不占地方。",
    "展厅在苏州阳光大厦，来拖一圈。",
]

TIPS = [
    "折叠必须一镜到底：手往上提、车身收住，中间别剪",
    "折完拿卷尺或者一把椅子比一下三十四公分，让宽度有个参照",
    "最后抓着车拖走三步，镜头低一点拍轮子滚过去，观众才信能拖",
]

FACT_TEXT = (
    "佳康顺P10碳纤维电动轮椅（10AH锂电）：碳纤维车架，整车净重15.8KG（不含电池）；"
    "免弯腰一体式一键折叠，折叠后宽34cm×高80cm，可推行、可拉行；"
    "展开尺寸103×60×90cm；智能电磁刹车，松手即停、双向制动、断电自动刹车；"
    "最大承重150KG；10Ah三元锂电（LG电芯）续航15km；170W×2无刷双电机合计340W；"
    "免充气实心防爆轮胎。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号单人口播（只 B 出镜，不标说话人）+ 简单档（约90-105字/21-25秒）+ 口语唠嗑腔。"
    "产品：P10 碳纤维电动轮椅。角度：免弯腰一键折叠 + 折后34cm + 可拖着走。"
    "2026-11-06 用户否掉 v1「控制器换手」（理由：不好展示），改为镜头前一眼能看懂的折叠角度。"
    "不写价格（到手价 6680 元禁写）；不写重量（15.8kg 为不含电池口径）；"
    "不提美国 PRIDE 同款；不虚构拉杆、「一根手指」等；尾句已全库查重。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（单人口播·一键折叠·v2）",
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
