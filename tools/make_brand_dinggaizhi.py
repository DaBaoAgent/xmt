# -*- coding: utf-8 -*-
"""品牌号 117：定改制轮椅（品类通用，不写具体型号）。

用户：「再根据这个写一版品牌号的，简单一点」
同一对标：https://v.douyin.com/tqJZWSdWFWE/
      《通用公式来了，快抄作业》douyin_7686136931687968507（629字/115.8秒）
只借骨架、不进正文（不出现「公式/套路」等元叙事）。

取的骨架：精准人群锁定式 + 痛点对比替换式，落到品牌号的一问一答里——
  只有某类人才懂 → 坐现成车的老人，半个钟头就喊腰酸
  嫌弃旧款又怕踩坑 → 能不能按她的身架调
  一边说旧款缺点一边亮做法 → 先量再调，调完试，不顺再动

定改制口径同 015：品类通用，不报型号、不报价格、不报数字；手动款，无电动词。
品牌号人设：心悦提问、小冯答（SKILL 铁律二，不能反），到店试车不写门牌。
简单一点：3 回 6 句，120 字上下 / 30 秒左右，只说「合不合身」一件事。
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

BENCH_URL = "https://v.douyin.com/tqJZWSdWFWE/"
BENCH_KEY = "7686136931687968507"
BENCH_TITLE = "通用公式来了，快抄作业#短视频带货 #爆款开头"

FACT_TEXT = (
    "定改制轮椅：按使用者的身高、腿长、坐宽实测，结合由谁推、日常走什么路，"
    "调整坐高、坐深、脚踏高低、扶手位置，属于手动轮椅的尺寸与结构定改制，"
    "坐上去不合适可继续微调。品类通用口径，不涉及具体型号参数。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

CODE = "SG-20261027-005"
TITLE = "现成买的轮椅能按人改吗"

LINES = [
    ("心悦", "我妈坐现成买的车，半个钟头就喊腰酸，是车不行吗？"),
    ("小冯", "不是车不好，是厂里照常见身量做的，坐垫一高，脚就离地了。"),
    ("心悦", "那这车能按她的身架调吗？"),
    ("小冯", "能，先把她的身高、腿长、屁股坐多宽量下来，再定平时谁来推。"),
    ("心悦", "调完她坐着还觉得别扭呢？"),
    ("小冯", "坐上去试，够不着就降一点，挤着了就松一点，直到她自己说顺。"),
]

TIPS = [
    "两人出镜，心悦问、小冯答，站在一台轮椅旁边说，别对着提词器念",
    "小冯说到坐垫、脚踏、扶手时手要指到对应位置",
    "「量身高、腿长、坐多宽」配卷尺实拍，比嘴上说清楚",
    "全程不报价格、不报型号、不写字幕门牌地址",
]


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    body = {"format": "dialogue",
            "lines": [{"speaker": s, "beat": "口播", "text": t} for s, t in LINES]}
    body_text = "\n".join("%s：%s" % (s, t) for s, t in LINES)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    target = 30.0
    scan = compliance.scan_script(
        body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])
    now = util.now_iso()
    row = con.execute("SELECT id FROM sg_scripts WHERE code=?", (CODE,)).fetchone()
    if row:
        con.execute(
            "UPDATE sg_scripts SET account_id='brand', account_label='品牌号', "
            "presenters_json=?, title=?, body_json=?, body_md=?, word_count=?, "
            "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
            "compliance_json=?, product_model=?, product_scope=?, "
            "status='待审', version=version+1, updated_at=? WHERE code=?",
            (json.dumps(["心悦", "小冯"], ensure_ascii=False), TITLE,
             json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), "定改制轮椅", "品类", now, CODE))
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
            (CODE, now, now, "待审", "brand", "品牌号",
             json.dumps(["心悦", "小冯"], ensure_ascii=False), "douyin",
             BENCH_KEY, BENCH_URL, BENCH_TITLE,
             "定改制轮椅", json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "对标《通用公式来了，快抄作业》只借开头公式骨架（精准人群锁定+痛点对比替换），"
             "正文不提公式；定改制品类通用，不写型号不报价格；3 回 6 句简单版；"
             "与个人号 015 同母题，收尾句不同。"))
    print("%s %s ｜ %d 字 / %.1f 秒 ｜ 合规 %s" % (
        CODE, TITLE, wc, sec, scan.get("counts")))
    for f in scan.get("findings") or []:
        print("  [%s] %s 「%s」 %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
