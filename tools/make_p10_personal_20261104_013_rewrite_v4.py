# -*- coding: utf-8 -*-
"""个人号 013 三改（v4）：P10 碳纤维电动轮椅 · 换角度＝轮胎（免充气实心胎）。

用户 2026-11-04 指令链：重新写 → 没有吸引力 → 「不写这个脚本 换一个」
即废掉 SOS/求救角度，换一个没写过的卖点。

P10 已归档个人号角度（074-078）：全介绍、能带上飞机、爬坡、老人自己会用、
重量（十五公斤）。口播 026 讲过三款对比。以上都不再用。

v4 选角度：免充气实心防爆胎（资料原文：「免充气实心防爆轮胎，不怕扎胎，
适应草地、泥土、坑洼、减速带」）。
选它的理由：老人用车最烦胎瘪了找修车摊打气，这是真痛点，且能在镜头前
用手摁、拿钥匙戳、推过石子路直接演示，属于「不用讲参数也看得懂」的卖点。
钩子用主张句「买轮椅先看轮子，别光看车架」——给观众一个反常规的挑选常识，
比平铺报卖点更留人。

合规处理：
- 不写价格（到手价 6680 元禁写）
- 不写重量（15.8kg 为不含电池口径）
- 不提「美国 PRIDE 同款」、不写疾病名、「不会摔倒/安全」不写
- 「防爆/不怕扎」不照抄广告词，改成可验证的动作描述（没有内胎 / 摁 / 碾）
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

CODE = "SG-20261104-013"
TITLE = "买轮椅先看轮子"

LINES = [
    "爷爷奶奶，买轮椅先看轮子，别光看车架。",
    "这台的轮子是实心的，一个内胎都没有。",
    "扎上小石子也不瘪，推起来照走。",
    "不用隔三差五找修车摊打气。",
    "手一松它自己停，坡上也不溜。",
    "展厅在苏州阳光大厦，来摸摸这轮子。",
]

TIPS = [
    "开头就蹲下来拍轮子，手摁胎面，让人看见按下去是硬的、不回弹",
    "拿钥匙或石子对着胎面比划一下，不用真扎，让镜头交代「没有内胎」",
    "推过一段石子路或减速带，让轮子自己说话，别配解说",
]

FACT_TEXT = (
    "佳康顺P10碳纤维电动轮椅（10AH锂电）：碳纤维车架，整车净重15.8KG（不含电池）；"
    "免充气实心防爆轮胎，前轮17.8cm、后轮33cm，适应草地、泥土、坑洼、减速带；"
    "智能电磁刹车，松手即停、双向制动、断电自动刹车；最大承重150KG；"
    "10Ah三元锂电（LG电芯）续航15km；170W×2无刷双电机合计340W；SOS一键求救语音。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号简单档（约90-105字/21-25秒）+ 口语唠嗑腔。产品：P10 碳纤维电动轮椅。"
    "角度：免充气实心胎（不用打气、没有内胎、扎不瘪）——2026-11-04 用户否掉 SOS/求救"
    "角度后换的卖点，P10 此前个人号未写过（074 全介绍/075 飞机/076 爬坡/077 会用/"
    "078 重量）。钩子用主张句「买轮椅先看轮子」。"
    "不写价格（到手价 6680 元禁写）；不写重量（15.8kg 为不含电池口径）；"
    "不提美国 PRIDE 同款；不写疾病名；不照抄「防爆/不怕扎」广告词。"
    "只 B 出镜，不标说话人。尾句已全库查重。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（口语唠嗑·实心胎角度·v4）",
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

    print("=== %s（%s v4）===" % (TITLE, CODE))
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
