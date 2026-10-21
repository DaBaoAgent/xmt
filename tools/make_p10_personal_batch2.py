# -*- coding: utf-8 -*-
"""个人号 075-077：P10 碳纤维电动轮椅再写 3 篇（角度不同，句子更简单）。

用户：「帮我在写3个不一样的脚本 稍微简单一点」
→ 承接 074《这电动轮椅五个长处一块儿占全了》（244字/58秒），这批压到
  **150-170 字 / 36-41 秒**，句子更短、每条只说一件事，参数不堆。

对标账号：陈大脸甄选（C1585273.6019）
对标视频：四合一代步车完整版介绍（douyin_7680137001514286309，746字/105秒）
骨架（沿用，三篇都是）：报品类 → 抛「三个长处」 → 逐条报数（头一个/第二个/
第三个）→ 现场演示一句 → 报一个具体参数 → 收尾（各篇不同）

三篇角度与收尾互不重复：
- 075 这轮椅能带上飞机吗 → 轻/小/能充（便携收纳）
- 076 这轮椅爬坡行不行 → 有劲/停得住/不硌（动力通过性）
- 077 这轮椅老人自己会用吗 → 上手快/顺手/能搭把手（操控易用）

P10 参数（逐字回查知识库 jks-product/P10碳纤维电动轮椅10AH锂电-产品详细信息
及 详情页 Z:\\7 详情页\\18 P10碳纤维电动轮椅10AH锂电）：
整车净重 15.8KG（不含电池，车架约 10KG）｜航空级真碳纤维+铝合金车架｜
免弯腰一键折叠，折叠后宽 34cm × 高 80cm｜10 股弹簧减震 + 加厚弹簧坐垫｜
电磁刹车，松手即停，断电自动刹车｜170W×2 无刷双电机合计 340W，30° 陡坡、
3cm 门槛｜10Ah 三元锂电（LG 电芯），续航 15km，可拆卸充电｜
免充气实心防爆轮胎，后轮 33cm｜承重 150KG｜万向摇杆控制器，控制器左右可换，
APP 手机遥控｜SOS 求救语音｜蓝绿紫三色。

合规处理：
「更安全」→ 改客观功能｜「不会摔倒/非常安全」→ 删｜「终身售后」→ 删｜
价格 → 不进稿｜疾病名 → 不用｜「轻轻松松/非常轻松」→ 改「能上」「停得住」
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

BENCH_URL = "https://v.douyin.com/0gaSwZ2JvpE/"
BENCH_KEY = "7680137001514286309"
BENCH_TITLE = "四合一代步车完整版介绍来啦"

FACT_TEXT = (
    "佳康顺P10碳纤维电动轮椅（10AH锂电）：整车净重15.8KG（不含电池，车架约10KG），"
    "航空级真碳纤维+铝合金车架；免弯腰一键折叠，折叠后宽34cm×高80cm；"
    "10股弹簧减震+加厚弹簧坐垫；电磁刹车松手即停、断电自动刹车；"
    "美国PRIDE同款170W×2无刷双电机合计340W，30°陡坡、3cm门槛；"
    "10Ah三元锂电（LG电芯）续航15km，可拆卸充电；"
    "免充气实心防爆轮胎，后轮33cm；最大承重150KG；"
    "万向摇杆控制器，左右手可换，APP手机遥控；SOS求救语音；蓝绿紫三色。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

BATCH = [
    ("SG-20261021-075", "这轮椅能带上飞机吗", [
        "这轮椅能带上飞机吗？",
        "佳康顺P10碳纤维电动轮椅，三个长处占全了。",
        "头一个是轻，碳纤维车架，整车十五点八公斤。",
        "第二个是小，一键折起来三十四公分宽。",
        "第三个是能充，电池整个拎出来，家里插座就行。",
        "我给您看啊，按一下红按钮往上一提就折好了。",
        "后轮是实心胎，落地就着，不用打气。",
        "带去机场之前，您来展厅先试一圈。",
        "我是小冯，昆山做辅具的。",
    ], [
        "单人出镜，站在一台 P10 旁边",
        "讲到折叠真的折一次，电池真的拎出来给镜头看",
        "实心胎那句可以蹲下来拍轮子",
        "结尾邀请到店试车，字幕不写价格",
    ]),
    ("SG-20261021-076", "这轮椅爬坡行不行", [
        "这轮椅爬坡行不行？",
        "佳康顺P10碳纤维电动轮椅，三个长处占全了。",
        "头一个有劲，170瓦电机装两个，340瓦。",
        "30度陡坡能上，三公分门槛也过得去。",
        "第二个停得住，电磁刹车，松开手就停。",
        "坡上站着不往前溜，人也不慌。",
        "第三个不硌，十股弹簧减震，路面颠着不难受。",
        "我给您看啊，坡上松手它就停住了。",
        "家里坡道陡的，您来展厅，我推给您看。",
        "我是小冯，店在昆山张浦。",
    ], [
        "单人出镜，最好带一段坡道实拍",
        "「松开手就停」一定要边推边演示，观众要看见",
        "报参数时说慢一点，170瓦、340瓦、30度这几个数要听得清",
        "结尾停在评论区那句，不写地址不写价格",
    ]),
    ("SG-20261021-077", "这轮椅老人自己会用吗", [
        "这轮椅老人自己会用吗？",
        "佳康顺P10碳纤维电动轮椅，三个长处占全了。",
        "头一个是上手快，一个万向摇杆，往前一推就走。",
        "第二个是顺手，控制器左右手能换。",
        "第三个是能搭把手，APP手机也能遥控。",
        "我给您看啊，摇杆往前一推，车就走了。",
        "摇杆上还有个SOS键，有事按一下。",
        "老人自己上手练两圈，比光听子女讲管用。",
        "我是小冯，有问题评论区问我。",
    ], [
        "单人出镜，坐在车上边说边操作，别站着念",
        "讲摇杆就真的推一下，讲APP就掏手机演示",
        "SOS键给个特写，讲清是求助用的",
        "结尾落在评论区，不写价格不写地址",
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
        target = 60.0
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
                 json.dumps(scan, ensure_ascii=False), "P10碳纤维电动轮椅10AH锂电",
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
                 BENCH_KEY, BENCH_URL, BENCH_TITLE,
                 "P10碳纤维电动轮椅10AH锂电", json.dumps([], ensure_ascii=False),
                 title, json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, target, 1, "型号",
                 "P10 个人号第 2-4 篇（用户要求「再写3个不一样的，稍微简单一点」）："
                 "承接 074，把字数从 244 压到 150-170，句子更短、参数不堆；"
                 "仍用陈大脸「报品类→抛卖点→逐条报数→演示→参数→收尾」骨架。"
                 "三篇角度/收尾各不相同。"))
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
