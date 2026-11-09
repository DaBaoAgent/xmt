# -*- coding: utf-8 -*-
"""个人号 013 二改：P10 碳纤维电动轮椅 · 简单档 + 口语唠嗑腔（SOS 悬念钩子）。

用户 2026-11-04 指令：「重新写」→ 首改 → 「没有吸引力」→ 本版（v3）。

吸引力改造思路：
- v2 开头是「喊不到人咋办」，仍是问句+说理，前 3 秒没有意外信息
- v3 把钩子换成反常识断言「这台轮椅会自己喊人」，第 3 句就放现场声音
  （「请帮帮我」单独成行＝成片里就是一声突然冒出来的人声，划到的人会停）
- 全篇只讲一件事：它会喊人 + 一松手就停，不再塞参数

合规不变：不写价格（6680 禁）、不写重量（15.8kg 不含电池口径）、
不提美国 PRIDE 同款、不写疾病名、不写「不会摔倒/安全」。
尾句已全库查重（库 + 稿子/**/*.txt 均无重复）。
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
TITLE = "这台轮椅会自己喊人"

LINES = [
    "爷爷奶奶，这台轮椅会自己喊人。",
    "扶手上一个红钮，您听——",
    "「请帮帮我。」",
    "声音是从车里出来的，路过的人都听得见。",
    "真没人应的时候，这一声就顶用。",
    "手一松它自己停，坡上也不溜。",
    "展厅在苏州阳光大厦，来按一下听听。",
]

TIPS = [
    "第 3 句的「请帮帮我」必须是现场原声，不要配音，声音就是这条片的钩子",
    "红钮按下去那一下要给手指特写，声音和画面对上",
    "前 3 秒别加片头字幕，让人先听见声音再看见人",
]

FACT_TEXT = (
    "佳康顺P10碳纤维电动轮椅（10AH锂电）：碳纤维车架，整车净重15.8KG（不含电池）；"
    "SOS一键求救语音播报「请帮帮我」；智能电磁刹车，松手即停、双向制动、断电自动刹车；"
    "最大承重150KG；10Ah三元锂电（LG电芯）续航15km；170W×2无刷双电机合计340W；"
    "免充气实心防爆胎。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号简单档（约90-105字/21-25秒）+ 口语唠嗑腔。产品：P10 碳纤维电动轮椅。"
    "角度：SOS 一键求救语音（悬念/声音钩子）+ 电磁刹车松手即停。"
    "2026-11-04 两次返工：v1 原版钩子偏空 → v2 改「喊不到人咋办」仍属说理 → "
    "v3 按用户「没有吸引力」改成反常识断言开场「这台轮椅会自己喊人」，"
    "第 3 句直接放现场人声，前 3 秒即有意外信息。"
    "不写价格（到手价 6680 元禁写）；不写重量（15.8kg 为不含电池口径）；"
    "不提美国 PRIDE 同款；不写疾病名。只 B 出镜，不标说话人。尾句已全库查重。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（口语唠嗑·SOS声音钩子·v3）",
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

    print("=== %s（%s v3）===" % (TITLE, CODE))
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
