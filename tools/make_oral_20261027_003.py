# -*- coding: utf-8 -*-
r"""口播号 017：套《抖音改版详解系列18：教会你无限复制爆款》写定改制轮椅（软版）。

对标骨架（只作隐形结构，正文不出现"爆款/公式/方法论"等元叙事）：
  反常识断言（别把长期的事当成一次输赢）→ 自证经验 → 大多数人怎么错 →
  错在哪（不是人挑，是前提没做）→ 错的代价 → 正确做法 → 试出来的判断标准
落地转换：
  对标"把单条爆款当目标＝把无限游戏玩成有限游戏"
  → 本品类"把买轮椅当一锤子买卖＝把三五年的事当成一次消费"
用法：.venv/Scripts/python.exe tools/make_oral_20261027_003.py
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

TITLE = "买轮椅最容易犯的错是把它当成一锤子买卖"

LINES = [
    "给老人买轮椅，最容易犯的错，是把它当成一锤子买卖。",
    "我干辅具这行十年，这话我说得不客气。",
    "很多人图省事，先买一台差不多的，想着不行再换。",
    "结果半年不到，第二台又抬进门。",
    "不是老人挑。是第一台压根没量过尺寸。",
    "坐深做大了，人一坐就往前出溜，后背找不着靠的地方。",
    "坐深做小了，大腿悬在外头，压出一道印子。",
    "脚踏高一点低一点，膝盖就顶着，脚也放不平。",
    "这些毛病，销售一般不讲。",
    "他讲的是这车结实、便宜、好推。",
    "可这台车要在老人身边待三五年，天天用。",
    "买错一回，老人不肯坐，钱就压在墙角。",
    "我一个月听二十回家属说，早知道当时量一下。",
    "按人做的车，坐宽留一指，坐深留两指。",
    "脚踏按小腿长短调，靠背顶到肩胛骨。",
    "老人坐上去不往前出溜，才坐得住。",
    "试的时候别客气，让他坐满十分钟。",
    "站起来走两步，再坐回去。",
    "合不合身，这十分钟最清楚。",
    "急着省下的那点，最后都得拿第二台车来补。",
    "关注翔哥，了解更多辅具知识。",
]

TIPS = [
    "第一句「一锤子买卖」四个字咬住，停半拍，别急着往下解释",
    "「我干辅具这行十年」抬头看镜头，语气平，不要炫耀",
    "「先买一台差不多的」时手往下压一下，这是多数人的心态",
    "「第二台又抬进门」重读「又」，停一拍，反差就在这里",
    "「压根没量过尺寸」把「压根」说狠一点，这是全片判断句",
    "讲坐深两段时左右手比宽窄，一大一小两个手势分开做",
    "「这些毛病，销售一般不讲」压低声音，像说内行话，别喊",
    "「钱就压在墙角」可以往墙角方向偏一下头，具体感就出来了",
    "「一个月听二十回」时点头，这是经验背书，不要说成数据",
    "「留一指」「留两指」真的伸出手指比，观众能记住这个动作",
    "试坐十分钟那段放慢语速，这是留给家属照做的动作",
    "结尾「拿第二台车来补」说完停顿，再接固定尾句，不要连读",
]

FACT_TEXT = (
    "轮椅适配常识（不代入型号与参数）：通用轮椅多按标准身形设定坐宽、坐深与脚踏高度，"
    "使用者体型差异会造成坐姿不稳、身体前滑、局部受压等情况，进而减少主动坐姿时间；"
    "定改制轮椅可按使用者实测尺寸调整坐宽、坐深、靠背与脚踏位置，选购前应测量并在"
    "实际坐姿下试坐足够时长再决定。"
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

    code = "SG-20261027-003"
    target = 85.0
    now = util.now_iso()
    publish = {"disclaimer": disclaimer,
               "douyin": {"title": TITLE,
                          "tags": "#轮椅 #养老辅具 #居家照护",
                          "cover_top": "别当一锤子买卖",
                          "cover_bottom": "量过尺寸的轮椅，老人才肯坐"},
               "channels": {"title": "给老人买轮椅，别图省事", "tags": "#轮椅 #居家养老"}}

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
             "", "https://v.douyin.com/kwJj_9F8nKk/",
             "抖音改版详解系列18：教会你无限复制爆款",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False), json.dumps(publish, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "对标《抖音改版详解系列18：教会你无限复制爆款》，只借其骨架："
             "反常识断言→自证经验→多数人怎么做错→错在前提没做→错的代价→正确做法→判断标准；"
             "把「别把长期的事当一次输赢」转成「别把买轮椅当一锤子买卖」；"
             "正文不提爆款/公式/方法论；软版弱广告，不点名型号、不写价格、不写服务承诺"))
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
