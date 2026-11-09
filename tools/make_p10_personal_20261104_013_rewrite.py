# -*- coding: utf-8 -*-
"""个人号 013 重写：P10 碳纤维电动轮椅 · 简单档 + 口语唠嗑腔（SOS 求救）。

用户 2026-11-04 指令「重新写」，覆盖 SG-20261104-013 正文，code 不变。

风格基准：037 F2Q / 038 A3 / 011 F2Q / 012 A3（6 行、85-105 字、21-25 秒）
角度：扶手红钮 SOS 一键语音「请帮帮我」+ 电磁刹车松手即停（本次把 SOS 从
      「说功能」改成「说情境」。原版开头「最怕啥」偏空，重写版开头落到
      「一个人出门喊不到人」，按钮变成具体解法）。

合规处理：
- 不写价格（到手价 6680 元禁写）
- 不写重量（15.8kg 为不含电池口径，含电池约十八九公斤）
- 不提「美国 PRIDE 同款」
- 不写疾病名、不写「不会摔倒/安全」
- 尾句已全库查重（库 + 稿子/**/*.txt 尾行均无重复）

P10 参数来源：jiaoben/P10碳纤维电动轮椅10AH锂电_产品信息总结.txt
            docs/产品参数档案.md（P10 段）
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

CODE = "SG-20261104-013"
TITLE = "爷爷奶奶 按个红钮它自己会喊人"

LINES = [
    "爷爷奶奶，一个人出门，喊不到人咋办？",
    "这台P10的扶手上，有个红钮。",
    "手一按，它自己就开口：请帮帮我。",
    "声音大，旁边路过的人都听得见。",
    "手一松它自己停，坡上停着也不往下溜。",
    "展厅在苏州阳光大厦，您来按一下试试。",
]

TIPS = [
    "红钮必须给特写，手指按下去那一下要清清楚楚",
    "「请帮帮我」收现场原声，别后期配音，老人信的就是这台车真在喊",
    "松手停那一下放在斜坡上拍：松手、车不动、镜头停两秒",
]

FACT_TEXT = (
    "佳康顺P10碳纤维电动轮椅（10AH锂电）：碳纤维车架，整车净重15.8KG（不含电池）；"
    "SOS一键求救语音播报「请帮帮我」；智能电磁刹车，松手即停、双向制动、断电自动刹车；"
    "最大承重150KG；10Ah三元锂电（LG电芯）续航15km；170W×2无刷双电机合计340W；"
    "免充气实心防爆胎。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号简单档（90-105字/21-25秒）+ 口语唠嗑腔（对齐 037 F2Q / 038 A3 调子）。"
    "产品：P10 碳纤维电动轮椅。角度：SOS 一键求救语音 + 电磁刹车松手即停。"
    "2026-11-04 按用户「重新写」指令重写：原版开头「最怕啥」偏空，改写落到"
    "「一个人出门喊不到人」，红钮变成具体解法；句数不变仍 6 句。"
    "不写价格（到手价 6680 元禁写）；不写重量（15.8kg 为不含电池口径）；"
    "不提美国 PRIDE 同款；不写疾病名。只 B 出镜，不标说话人。尾句已全库查重。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（口语唠嗑·SOS求救·重写版）",
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

    print("=== %s（%s 重写）===" % (TITLE, CODE))
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
