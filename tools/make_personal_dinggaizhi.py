# -*- coding: utf-8 -*-
"""个人号 097：定改制轮椅（品类通用，不写具体型号）。

用户：「帮我写定改制轮椅的 个人号的 简单一点的」
对标：https://v.douyin.com/tqJZWSdWFWE/
      《通用公式来了，快抄作业》douyin_7686136931687968507（629字/115.8秒）
      对标讲 5 个开头公式，只借骨架、不进正文（不出现「公式/套路」等元叙事）。

取的骨架（第二式 精准人群锁定式 + 第三式 痛点对比替换式，一句对一句换词）：
  只有某一类人才懂 → 只有常年坐轮椅的人才明白
  才懂这款产品真正的价值 → 才明白合不合身比配置要紧
  比如…的人才知道…多好用 → 比如坐垫高一点、胳膊一直架着这几个细节
  嫌弃旧款不好用又怕踩坑的直接换成 → 嫌弃现成车别扭、又怕乱改坏了的来看定改制
  一边说旧款缺点一边亮新品优势 → 先量人再调车，调完再试

定改制的做法（品类通用，不报型号、不报价格、不报数字参数）：
量身高/腿长/坐宽 → 问谁推、走什么路 → 调坐高、坐深、脚踏高低、扶手位置 →
坐上去再试、再微调。手动款，全篇无电动词。

简单一点：压到 190 字上下 / 43 秒左右（个人号 45-60s 下调一档），单主线，
只说「合不合身」一件事，不铺展厅、不报参数。
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
    "定改制轮椅：按使用者的身高、腿长、坐宽实测，再结合由谁推、日常走什么路，"
    "调整坐高、坐深、脚踏高低、扶手位置，属于手动轮椅的尺寸与结构定改制，"
    "成品坐上去不合适可继续微调。品类通用口径，不涉及具体型号参数。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

BATCH = [
    ("SG-20261027-004", "轮椅合不合身坐久了才知道", [
        "只有常年坐轮椅的人才明白，车合不合身，比添什么配置都紧要。",
        "现成的车，尺寸是照大多数人做的，不一定照着您。",
        "坐垫高了，脚够不着地；靠背直了，腰上就空着。",
        "这么坐半个钟头，人就酸了。",
        "嫌弃现成车别扭、又怕乱改改坏的，来看看定改制怎么做的。",
        "头一步是量，身高、腿长、坐多宽，再问一句平时谁推。",
        "坐高、坐深、脚踏高低、扶手位置，一样一样对着人调。",
        "调完坐上去试，哪儿差一点，就再动一动。",
        "车是买来过日子的，尺寸对了，人才愿意天天出门。",
    ], [
        "单人出镜，站在一台轮椅旁边说，别坐着念",
        "讲到坐垫、靠背、扶手时手要指到对应位置，观众要看得见是哪一处",
        "「量身高、量腿长、量坐着多宽」三句可以配卷尺实拍，比说更清楚",
        "全程不报价格、不报具体型号，结尾不写门牌地址",
    ]),
]


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    for code, title, lines, tips in BATCH:
        body = {"format": "monologue",
                "lines": [{"speaker": "小冯", "beat": "口播", "text": t}
                          for t in lines]}
        body_text = "\n".join(lines)
        spoken = util.strip_speakers(body_text)
        wc = util.count_chars(spoken)
        sec = util.estimate_seconds(spoken)
        target = 45.0
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
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), "定改制轮椅",
                 "品类", now, code))
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
                 BENCH_KEY, BENCH_URL, BENCH_TITLE,
                 "定改制轮椅", json.dumps([], ensure_ascii=False),
                 title, json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, target, 1, "品类",
                 "对标《通用公式来了，快抄作业》只借开头公式骨架（精准人群锁定+痛点对比替换），"
                 "正文不提公式；定改制品类通用，不写型号不报价格；用户要求「简单一点」，"
                 "单主线只说合不合身，190 字上下。"))
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
