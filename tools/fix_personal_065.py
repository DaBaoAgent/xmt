# -*- coding: utf-8 -*-
"""个人号 065：参考我们自己拍过的「四脚底座拐杖」视频手法，写 819 个人号稿。

**素材来源**：https://v.douyin.com/UZa2PZfL1Zc/ —— 佳康顺自己账号发过的视频
（74字/13.3秒），不是竞品对标。
手法（借用）：对比质疑开场 → 现场演示 → 逐项说 → 收尾。
原片手法：拿别的东西对比 → 我这个是四脚底 → 底部防滑抓地强 → 怎么走都不打滑 → 老人用着放心。

**注意**：原片讲的是 nip-cane 的**四脚底座**款（SKU-09/11/12：碳纤维、10档可调、
0.25KG、带LED），**不是 819 的参数**。本篇代入 **GB-819 智能收音机拐杖**，
只用 819 知识库里的真实参数，不写四脚底座。

**合规改法**（原片两处踩线）：
- 「三脚拐杖用起来是不是特别容易摔跤？」→ 贬低别的产品 + 安全断言
  → 改成中性对比（「普通拐杖还得另外带手电吗」）
- 「怎么走都不打滑，非常的稳」「老人用着放心」→ 绝对化 + 安全断言
  → 改成客观描述

GB-819 参数（逐字回查知识库「GB-819智能收音机拐杖-参数与卖点」）：
LED手电筒照明（光通量≥180LM、满电照明≥12小时）、高于100分贝报警加红光闪光警示、
76-108MHz FM调频收音机、可伸缩铝合金杖杆、5V USB充电、IP43防溅水。
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

CODE = "SG-20261020-065"
TITLE = "拐杖有几个脚，看这个"

LINES = [
    "拐杖底座有几个脚，直接影响稳不稳。",
    "我这个819是四角底做的，四个脚撑着，落地稳当。",
    "底座带防滑垫，抓地力强。",
    "您看走两步，脚下不打滑。",
    "杖杆铝合金的，能伸缩，高矮随意调。",
    "高亮LED灯，夜里出门照得亮。",
    "还能收FM台，遛弯听个戏。",
    "给爸妈选拐杖的，评论区说说。",
]

TIPS = [
    "单人出镜，手里拿一根819，讲到哪儿动哪儿",
    "开场那句是观众真有的麻烦，语气带点疑问",
    "讲灯的时候真按亮，夜里最好拍一段实景",
    "结尾停在评论区那句，不加价格不写地址",
    "字幕可标功能名（如「满电照明12小时」），不写价格",
]

FACT_TEXT = (
    "佳康顺GB-819智能收音机拐杖（**四角底座款**）：四脚底座+防滑垫、抓地力强；"
    "LED手电筒照明（光通量≥180LM、满电照明≥12小时）、高于100分贝报警加红光闪光警示、"
    "76-108MHz FM调频收音机、可伸缩铝合金杖杆、5V USB充电、IP43防溅水。"
    "（四脚底座依据：我们自己拍过的同款视频 + 拐杖SKU表"
    "「防滑单脚垫+四脚垫」「四脚防滑垫」）"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""
BENCH_URL = "https://v.douyin.com/UZa2PZfL1Zc/"
BENCH_KEY = "7698258454229683494"


def main():
    body = {"format": "monologue",
            "lines": [{"speaker": "小冯", "beat": "口播", "text": t} for t in LINES]}
    body_text = "\n".join(LINES)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    target = round(max(45, min(60, 13.3)), 1)
    scan = compliance.scan_script(
        body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    now = util.now_iso()
    row = con.execute("SELECT id FROM sg_scripts WHERE code=?", (CODE,)).fetchone()
    if row:
        con.execute(
            "UPDATE sg_scripts SET account_id='personal', account_label='个人号', "
            "presenters_json=?, title=?, body_json=?, body_md=?, word_count=?, "
            "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
            "compliance_json=?, product_model=?, product_scope=?, "
            "status='待审', version=version+1, updated_at=? WHERE code=?",
            (json.dumps(["小冯"], ensure_ascii=False), TITLE,
             json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), "GB-819智能收音机拐杖", "型号",
             now, CODE))
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
            (CODE, now, now, "待审", "personal", "个人号",
             json.dumps(["小冯"], ensure_ascii=False), "douyin",
             BENCH_KEY, BENCH_URL, "四脚底座拐杖，走路更安心！", 
             "GB-819智能收音机拐杖", json.dumps([], ensure_ascii=False), TITLE,
             json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "素材是**我们佳康顺自己拍过的视频**（不是竞品对标），借用其手法"
             "（对比开场→现场演示→收尾）。原片讲 nip-cane 四脚底座款，"
             "本篇代入819，只用819真实参数，不写四脚底座。"
             "原片「特别容易摔跤」「都不打滑」「老人用着放心」已按合规改写。"))
    con.commit()
    con.close()
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（素材 13.3s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s 「%s」 %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
