# -*- coding: utf-8 -*-
r"""口播号 016：套《短视频爆款结构 两大模型》PREP 模型写定改制轮椅（软版）。

公式骨架（只作隐形结构，不进正文）：
  P 观点先抛出 → R 讲理由 → E 讲一个跟自己有关的案例 → P 重申同一句观点
用法：.venv/Scripts/python.exe tools/make_oral_20261027_002.py
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

TITLE = "轮椅凑合着用，最后贵的是人"

LINES = [
    "干轮椅这行十年，我最想说一句，凑合最贵。",
    "车是便宜了几千块，可人一天要在上面坐八个小时。",
    "尺寸不对，坐半小时就想站起来，站起来就回床上躺着。",
    "躺得多，越不想动，一台车慢慢就成了摆设。",
    "钱花了，人也没出门。",
    "我见过太多这样的车，买回去半年，轮子还跟新的一样。",
    "原厂车按大多数人的身形做，不是照这一个人做的。",
    "每个人的坐宽、腿长、腿上还有多少劲，差得远。",
    "上个月有个客户，家里先买了台现成的。",
    "坐不到两个月，老人说不坐了，屁股底下硌得慌，坐一会儿就往下滑。",
    "家里人还以为是他不爱坐，其实老人是坐不住。",
    "我给他量了坐宽、坐深、膝后高度、靠背，位置重新定了一遍。",
    "现在一下午坐着看电视，不用人扶。",
    "所以这话我再说一遍，凑合最贵。",
    "买之前花二十分钟量人，比买回来再换车省事。",
    "量的时候让他穿平时的裤子，坐姿也照平时的样子，别挺着。",
    "我是翔哥，十年辅具，别让老人凑合。",
]

TIPS = [
    "第一句「凑合最贵」四个字咬住，停半拍再往下，观点要立得住",
    "讲「一天坐八个小时」时伸手指比个八，别解释",
    "「坐半小时就想站起来」说完真的起身一下，观众就懂了",
    "「躺得多，越不想动」语速放慢，这句是危害，别说快",
    "讲原厂尺寸时手在身前比一个宽窄，再说「差得远」，别堆术语",
    "案例段换成聊天口气，「上个月有个客户」可以带一点笑，别念稿",
    "说「家里人还以为是他不爱坐」时摇头，这是替家属说话的判断句",
    "重申「凑合最贵」时看镜头，语气比第一句更重；结尾不提价格、不提型号",
]

FACT_TEXT = (
    "轮椅适配常识（不代入型号与参数）：通用轮椅多按标准身形设定坐宽、坐深与脚踏高度，"
    "使用者体型与坐姿差异会造成受力集中、坐姿不稳、身体前滑等情况，进而减少主动坐姿时间。"
    "定改制轮椅可按使用者实测尺寸调整坐宽、坐深、靠背与脚踏位置，改善久坐舒适度与稳定性；"
    "选购前应先测量使用者体型，并安排足够时长的试坐观察。"
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

    code = "SG-20261027-002"
    target = 85.0
    now = util.now_iso()
    publish = {"disclaimer": disclaimer,
               "douyin": {"title": TITLE,
                          "tags": "#轮椅 #养老辅具 #居家照护",
                          "cover_top": "轮椅凑合，最贵",
                          "cover_bottom": "钱省了几千，人少了几年出门"},
               "channels": {"title": "给老人买轮椅，最怕一句「先凑合用」",
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
             "7662733170772544778", "https://v.douyin.com/o4gmtzqfyYM/",
             "短视频爆款结构，两大模型！",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False), json.dumps(publish, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "对标《短视频爆款结构 两大模型》PREP 模型："
             "开头直给观点「凑合最贵」→ 讲便宜几千但一天坐八小时 / 越不坐越不动的理由"
             "→ 举一个客户买现成车两个月后重量的案例 → 结尾原句重申观点；"
             "软版弱广告，不点名型号、不写价格、不写服务承诺"))
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
