# -*- coding: utf-8 -*-
r"""口播号 015：套《短视频开头第一句全教学》方向一「替观众说出他的处境」写定改制轮椅（软版）。

公式骨架（只作隐形结构，不进正文）：
  开场第一句 = 把观众的处境说到他自己认领，细节要具体到"这说的就是我"
  → 反转指出真正原因 → 讲清机制 → 给出解法 → 给一个可立即执行的判断动作
用法：.venv/Scripts/python.exe tools/make_oral_20261027_001.py
"""
import io
import json
import os
import sqlite3
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scriptgen import util, compliance  # noqa: E402
from scriptgen.writer import body_plain_text  # noqa: E402

DB = os.path.join(ROOT, "data", "xmt.db")

TITLE = "老人一坐轮椅就往前出溜，多半是尺寸没量对"

LINES = [
    "老人一坐上轮椅就往前出溜，扶回去，二十分钟又滑下来。",
    "家里人一般以为是人没劲、坐不住。",
    "其实多数时候，是车不合身。",
    "我干这行十年，出问题的不是质量，是尺寸。",
    "坐宽大两指，人左右晃，得靠两条胳膊撑着；",
    "坐深长三指，膝盖后面被顶着，腿放不平，人自然往下滑；",
    "脚踏高两公分，大腿被架起来，重量全落到坐骨那两个点上。",
    "三样凑一块，坐半小时挪一次，挪完还得扶。",
    "一天下来，人是乏的。",
    "原厂车按标准身形做，出厂什么样就什么样，动不了。",
    "定改制反过来，先量人，再定车。",
    "坐宽留一指，坐深量到膝后留两指，脚踏落下来让大腿放平，靠背贴住腰。",
    "尺寸对上了，人坐得住，也不用一直撑。",
    "定之前记住一件事。",
    "让他坐满十分钟，看滑不滑、腿麻不麻、手要不要扶。",
    "十分钟坐得住，这车才算合适。",
    "我是翔哥，十年辅具，尺寸上的事问我就行。",
]

TIPS = [
    "第一句不说「很多老人」，直接说「一坐上就往前出溜，扶回去，二十分钟又滑下来」，让他对号入座",
    "「以为是没劲」说轻一点，别否定家属，紧接一句「其实是车不合身」把话接过来",
    "讲坐宽、坐深、脚踏三条时，每条点头收一下，节奏一二三，别连成一段",
    "说「坐深长三指」时手在膝盖后面比一下位置，观众马上懂",
    "「重量全落到坐骨那两个点上」压低声，这是翔哥的专业判断",
    "说「出厂什么样就什么样，动不了」时手一摊，别解释工艺",
    "量尺寸那段语速放慢，一个字一个字给，字幕只标「坐宽留一指、坐深留两指」",
    "结尾「问我就行」看镜头，不推销、不报价格、不提型号",
]

FACT_TEXT = (
    "轮椅适配常识（不代入型号与参数）：轮椅坐宽、坐深、脚踏高度与靠背角度会直接影响坐姿稳定性；"
    "坐宽过大易左右晃动，坐深过长会压迫膝后，脚踏偏高会抬高大腿并使坐骨受力集中，"
    "这些都会造成身体前滑、需要用上肢支撑。定改制轮椅可按使用者实际体型测量后调整上述尺寸，"
    "试坐应持续足够时间，观察是否出现下滑、下肢麻木或持续受压不适。"
)


def main():
    body = {"format": "monologue",
            "lines": [{"speaker": "", "beat": "口播", "text": t} for t in LINES]}
    body_text = body_plain_text(body)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    disclaimer = util.compliance_config().get("disclaimer") or ""
    scan = compliance.scan_script(body_text, {"disclaimer": disclaimer}, "", FACT_TEXT, [])

    code = "SG-20261027-001"
    target = 85.0
    now = util.now_iso()
    publish = {"disclaimer": disclaimer,
               "douyin": {"title": TITLE,
                          "tags": "#轮椅 #养老辅具 #居家照护",
                          "cover_top": "一坐就往前出溜",
                          "cover_bottom": "不是人没劲，是尺寸没量对"},
               "channels": {"title": "老人坐轮椅总往下滑，先量这四个尺寸",
                            "tags": "#轮椅 #居家养老"}}

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    exists = con.execute("SELECT id FROM sg_scripts WHERE code=?", (code,)).fetchone()
    if exists:
        con.execute(
            "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
            "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
            "publish_json=?, compliance_json=?, version=version+1, updated_at=? WHERE code=?",
            (TITLE, json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
             json.dumps(TIPS, ensure_ascii=False), json.dumps(publish, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), now, code))
        print("已更新", code)
    else:
        con.execute(
            "INSERT INTO sg_scripts (code, created_at, updated_at, status, account_id, "
            "account_label, presenters_json, source_platform, video_key, benchmark_url, "
            "benchmark_title, product_model, product_doc_ids_json, title, body_json, body_md, "
            "shooting_tips_json, publish_json, compliance_json, facts_json, word_count, "
            "estimated_seconds, target_seconds, version, product_scope, notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (code, now, now, "待审", "oral", "口播号",
             json.dumps(["翔哥"], ensure_ascii=False), "douyin",
             "7678017235408309331", "https://v.douyin.com/OnSVWC1l6ZQ/",
             "全网最全关于短视频开头第一句全教学！",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False), json.dumps(publish, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "对标《短视频开头第一句全教学》方向一「替观众说出他的处境」："
             "第一句直接把「一坐就往前出溜」的处境说到观众认领，再反转指认尺寸问题，"
             "讲坐宽/坐深/脚踏三条机制，落到定改制按人量尺，收在「坐满十分钟」试坐动作；"
             "软版弱广告，不点名型号、不写价格"))
        print("已新建", code)
    con.commit()
    con.close()

    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒 ｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
