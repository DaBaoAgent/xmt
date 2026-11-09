# -*- coding: utf-8 -*-
r"""口播号 014：套《爆款开头公式》第五条「痛点罗列型」写定改制轮椅（软版）。

公式原文：嫌弃什么什么的人，一定要试试这个什么什么。
         罗列这个产品能解决的三个痛点，后面推出产品。
用法：.venv/Scripts/python.exe tools/make_oral_20261026_003.py
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

TITLE = "嫌弃轮椅硌得慌的人，一定要试试按人做的"

LINES = [
    "嫌弃轮椅硌得慌、闷得慌、又抬不动的，一定要试试按人做的那种。",
    "这三种嫌法，我一个月听二十回。",
    "先说硌。",
    "多数车坐垫就一层薄布，人一坐，尾椎正好顶在横杆上。",
    "坐半小时挪一次，挪完又滑回去，一天下来人是累的。",
    "换成一块撑得住的硬板，受力摊开，就没那么硌。",
    "再说闷。",
    "后背和屁股捂一天，起身衣服是潮的。",
    "硬板配透气垫，比软塌塌的垫子干爽，夏天尤其明显。",
    "第三是笨。",
    "上车下车得两个人抬，出趟门先商量谁有空。",
    "车架换成轻料，十二公斤多，一个人拎得起来，才谈得上常出门。",
    "车是按标准身形做的，出厂什么样就什么样，改不动。",
    "定改制留了余地，坐宽、坐深、脚踏、靠背，量完再定。",
    "销售一般不讲这些，他讲能坐多重、能折多小。",
    "买之前别急着定。",
    "让他坐满十分钟，看尾椎硌不硌、后背潮不潮、还往前蹭不蹭。",
    "坐得住，才愿意出门。",
    "家里老人正嫌这嫌那的，评论区说说他最嫌哪一条。",
    "我是翔哥，十年辅具，不吹不绕。",
]

TIPS = [
    "第一句把「硌得慌、闷得慌、又抬不动」三个短句连着砸出来，快、脆，别拖",
    "说「我一个月听二十回」时看镜头，语气像真在数",
    "「先说硌」三个字后面停半拍，再往下讲，节奏一条一条来",
    "讲薄布硌尾椎时手往身后下方一指，再说「半小时挪一次」，身体真的挪一下",
    "讲闷的时候手掌扇两下，不解释原理",
    "讲笨的时候两手往上一抬做「两个人抬车」的动作，再单手拎一下示意轻重",
    "说「销售一般不讲这些」时压低声，这是翔哥的判断句",
    "结尾看镜头放慢语速，字幕只标「坐满十分钟再定」，不写价格、不写型号",
]

FACT_TEXT = (
    "轮椅适配常识（不代入型号与参数）：普通轮椅坐垫多为薄布面，"
    "久坐时尾椎与坐骨受力集中、透气性有限；坐垫材质与支撑方式会影响久坐感受。"
    "整车重量影响搬运动作，轻一些的车架更便于单人上下车。"
    "定改制轮椅可按使用者实际坐姿调整坐宽、坐深、靠背角度与脚踏高度；"
    "选购试坐应持续足够时间，观察是否出现下滑、局部受压或闷热不适。"
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

    code = "SG-20261026-003"
    target = 85.0
    now = util.now_iso()
    publish = {"disclaimer": disclaimer,
               "douyin": {"title": TITLE,
                          "tags": "#轮椅 #养老辅具 #居家照护",
                          "cover_top": "硌、闷、搬不动",
                          "cover_bottom": "不是人挑剔，是车不合适"},
               "channels": {"title": "老人嫌轮椅不舒服，多半是这三件事",
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
             "7658243572831695807", "https://v.douyin.com/27KMPHMfeUs/",
             "爆款开头公式 所有品类都可以直接拿去套用！",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False), json.dumps(publish, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "对标《爆款开头公式》第五条「嫌弃…的人，一定要试试这个…」："
             "开场圈痛点人群，罗列硌/闷/笨三个痛点，后段落定改制按人量尺寸；"
             "软版弱广告，不点名型号、不写价格"))
        print("已新建", code)
    con.commit()
    con.close()

    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 82.2s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
