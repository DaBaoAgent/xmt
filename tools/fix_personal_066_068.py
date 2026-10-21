# -*- coding: utf-8 -*-
"""个人号 066-068：819 拐杖（个人号·小冯·单人口播），沿用 065 形式，三个不同角度。

形式：单人口播、约 120 字、不加 CTA 不加地址、结尾落到评论区互动。
角度：①夜里起夜照明 ②独居出门报警 ③照明+收音+防溅水（一根顶三样）

819 完整可用参数（依据：知识库「GB-819智能收音机拐杖-参数与卖点」+
我们佳康顺自己拍过的同款视频 + 拐杖 SKU 表）：
- 四角底座 + 防滑垫（抓地力强）  ← 视频 + SKU表「防滑单脚垫+四脚垫」
- LED 手电筒照明：≥180LM、满电照明≥12小时
- 高于100分贝报警 + 红光闪光警示
- 76-108MHz FM 调频收音
- 可伸缩铝合金杖杆
- 5V USB 充电
- IP43 防溅水
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

BATCH = [
    ("SG-20261020-066", "夜里起夜也得拄根拐杖", [
        "夜里起来摸黑，拐杖放哪儿了？",
        "819自带LED灯，一按就亮，一百八流通明。",
        "满电能照十二个钟头，一晚上够使。",
        "底座是四角的，四个脚撑着，落地稳当。",
        "还能收FM台，早上听个新闻。",
        "充电用手机线，不用另买充电器。",
        "夜里起夜用的，评论区说说。",
    ]),
    ("SG-20261020-067", "一个人出门心里不踏实", [
        "老人一个人出门，出点事没人知道。",
        "819上带报警键，一摁一百多分贝，老远都听得见。",
        "还带红光闪光，一闪一闪的，夜里头特别显眼。",
        "底座是四角的，落地稳当，走路不打晃。",
        "杖杆能伸缩，携带也方便。",
        "家里老人一个人住的，评论区说说。",
    ]),
    ("SG-20261020-068", "一根拐杖照明收音全带了", [
        "给爸妈买拐杖，照明收音能一块儿带就更省事。",
        "819前面是高亮LED灯，夜里回家照路。",
        "76到108兆赫的调频台随便挑，遛弯听个戏。",
        "底座四角带防滑垫，落地稳当不滑。",
        "IP43防溅水，下点小雨不打紧。",
        "充电用手机线，跟手机共用一个头。",
        "给爸妈选拐杖的，评论区说说。",
    ]),
]

TIPS = [
    "单人出镜，手里拿一根819，讲到哪儿动哪儿",
    "开场那句是观众真有的麻烦，语气带点疑问",
    "讲灯的时候真按亮，讲报警键就真摁一下",
    "结尾停在评论区那句，不加价格不写地址",
    "字幕可标功能名（如「四角底座」），不写价格",
]

FACT_TEXT = (
    "佳康顺GB-819智能收音机拐杖（四角底座款）：四脚底座+防滑垫、抓地力强；"
    "LED手电筒照明（光通量≥180LM、满电照明≥12小时）、"
    "高于100分贝报警加红光闪光警示、76-108MHz FM调频收音机、"
    "可伸缩铝合金杖杆、5V USB充电、IP43防溅水。"
    "（四脚底座依据：我们自己拍过的同款视频 + 拐杖SKU表"
    "「防滑单脚垫+四脚垫」「四脚防滑垫」）"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""
BENCH_URL = "https://v.douyin.com/UZa2PZfL1Zc/"
BENCH_KEY = "7698258454229683494"


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    for code, title, lines in BATCH:
        body = {"format": "monologue",
                "lines": [{"speaker": "小冯", "beat": "口播", "text": t}
                          for t in lines]}
        body_text = "\n".join(lines)
        spoken = util.strip_speakers(body_text)
        wc = util.count_chars(spoken)
        sec = util.estimate_seconds(spoken)
        target = round(max(45, min(60, 13.3)), 1)
        scan = compliance.scan_script(
            body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])
        now = util.now_iso()
        row = con.execute("SELECT id FROM sg_scripts WHERE code=?",
                          (code,)).fetchone()
        if row:
            con.execute(
                "UPDATE sg_scripts SET account_id='personal', account_label='个人号', "
                "presenters_json=?, title=?, body_json=?, body_md=?, word_count=?, "
                "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
                "compliance_json=?, product_model=?, product_scope=?, "
                "status='待审', version=version+1, updated_at=? WHERE code=?",
                (json.dumps(["小冯"], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
                 json.dumps(TIPS, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), "GB-819智能收音机拐杖",
                 "型号", now, code))
        else:
            con.execute(
                "INSERT INTO sg_scripts (code, created_at, updated_at, status, "
                "account_id, account_label, presenters_json, source_platform, "
                "video_key, benchmark_url, benchmark_title, product_model, "
                "product_doc_ids_json, title, body_json, body_md, "
                "shooting_tips_json, publish_json, compliance_json, facts_json, "
                "word_count, estimated_seconds, target_seconds, version, "
                "product_scope, notes) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (code, now, now, "待审", "personal", "个人号",
                 json.dumps(["小冯"], ensure_ascii=False), "douyin",
                 BENCH_KEY, BENCH_URL, "四脚底座拐杖，走路更安心！",
                 "GB-819智能收音机拐杖", json.dumps([], ensure_ascii=False),
                 title, json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(TIPS, ensure_ascii=False),
                 json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, target, 1, "型号",
                 "沿用 065 形式（个人号·单人口播·约120字），819 四角底座款，"
                 "三个不同角度：夜里起夜照明/独居出门报警/照明收音防溅水。"
                 "参数依据知识库GB-819+我们自己的同款视频+拐杖SKU表。"))
        print("%s %s ｜ %d 字 / %.1f 秒 ｜ 合规 %s" % (
            code, title, wc, sec, scan.get("counts")))
        for f in scan.get("findings") or []:
            print("  [%s] %s 「%s」 %s" % (
                f.get("severity"), f.get("rule_id"), f.get("match"),
                f.get("suggest") or ""))
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
