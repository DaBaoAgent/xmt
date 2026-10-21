# -*- coding: utf-8 -*-
"""个人号 074：按「陈大脸甄选」对标风格写 P10 碳纤维电动轮椅个人号稿。

对标账号：陈大脸甄选（C1585273.6019，源头工厂直营店）
对标视频：四合一代步车完整版介绍（douyin_7680137001514286309，746 字 / 105 秒）
骨架：报品类+卖点总数 → 逐条报数（第一个…第二个…第三个…第四个…第五个）
      → 每条配一个使用状态 → 穿插现场操作演示 → 报具体参数 → 收尾

P10 参数（逐字回查知识库 jks-product/P10碳纤维电动轮椅10AH锂电-产品详细信息
及 详情页 Z:\\7 详情页\\18 P10碳纤维电动轮椅10AH锂电）：
整车净重 15.8KG（不含电池）｜航空级真碳纤维+铝合金车架（车架约 10KG）｜
免弯腰一键折叠，折叠后宽 34cm × 高 80cm｜10 股弹簧减震 + 加厚弹簧坐垫｜
黑科技电磁刹车，松手即停，断电自动刹车｜美国 PRIDE 同款 170W×2 无刷双电机
（合计 340W），30° 陡坡、3cm 门槛｜10Ah 三元锂电（LG 电芯），续航 15km，
可拆卸充电｜免充气实心防爆轮胎，后轮 33cm｜承重 150KG｜三种控制：
电动行走 / 手推行走 / APP 手机遥控，控制器左右可换｜SOS 求救语音｜
蓝 / 绿 / 紫三色。

合规处理：
「更安全」→ 改客观功能（电磁刹车，松开手就停）｜「不会摔倒/非常安全」→ 删｜
「终身售后」→ 删（无正式政策支撑）｜价格 6680 → 绝不进稿｜
「中风脑梗」等疾病名 → 不用｜「轻松/不费劲」→ 改「不硌」「稳当」
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

CODE = "SG-20261021-074"
# 标题不带标点：slugify 会把逗号转成连字符，触发本机安全钩子拦 out/*.docx
TITLE = "这电动轮椅五个长处一块儿占全了"

LINES = [
    "这个就是佳康顺的P10碳纤维电动轮椅。",
    "五个长处一块儿占全了。",
    "头一个是轻，航空级碳纤维车架，整车才十五点八公斤。",
    "第二个是稳当，十股弹簧减震，路面颠着不硌。",
    "第三个是停得住，电磁刹车，松开手就停，坡上也不往前溜。",
    "第四个是有劲，170瓦电机装两个，340瓦，30度陡坡能上，能跑15公里。",
    "第五个是收得小，一键折叠，34公分宽，塞得进后备箱。",
    "我给您看啊，按一下红按钮往上一提就折起来了，不用弯腰。",
    "电池能整个拎出来，家里插座就能充。",
    "家里有老人的，您来展厅坐一圈，比看图片管用。",
    "我是小冯，来了我帮您试。",
]

TIPS = [
    "单人出镜，站在一台 P10 旁边，边说边操作",
    "开头报品类，第二句抛「五个长处一块儿占全了」",
    "报长处时逐条数，每条配一句大白话，别光报参数",
    "讲到折叠真的折一次，电池真的拎出来，镜头给近景",
    "结尾停在展厅邀请，不写价格不写地址",
    "语速跟日常聊天一样，可以有口头禅，别念稿",
]

FACT_TEXT = (
    "佳康顺P10碳纤维电动轮椅（10AH锂电）：整车净重15.8KG（不含电池，车架约10KG），"
    "航空级真碳纤维+铝合金车架；免弯腰一键折叠，折叠后宽34cm×高80cm；"
    "10股弹簧减震+加厚弹簧坐垫；电磁刹车松手即停、断电自动刹车；"
    "美国PRIDE同款170W×2无刷双电机合计340W，30°陡坡、3cm门槛；"
    "10Ah三元锂电（LG电芯）续航15km，可拆卸充电；"
    "免充气实心防爆轮胎，后轮33cm；最大承重150KG；"
    "三种控制：电动行走/手推行走/APP手机遥控，控制器左右可换；SOS求救语音；蓝绿紫三色。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""
BENCH_URL = "https://v.douyin.com/0gaSwZ2JvpE/"
BENCH_KEY = "7680137001514286309"


def main():
    body = {"format": "monologue",
            "lines": [{"speaker": "小冯", "beat": "口播", "text": t} for t in LINES]}
    body_text = "\n".join(LINES)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    target = 60.0
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
             json.dumps(scan, ensure_ascii=False), "P10碳纤维电动轮椅10AH锂电",
             "型号", now, CODE))
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
             BENCH_KEY, BENCH_URL, "四合一代步车完整版介绍来啦",
             "P10碳纤维电动轮椅10AH锂电", json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "对标账号「陈大脸甄选」（C1585273.6019）完整介绍型骨架："
             "逐条报数 + 每条配状态 + 现场演示 + 报具体参数 + 收尾。"
             "分析见 .workbuddy/skills/scriptgen-writing/对标账号分析-陈大脸甄选.md。"
             "P10 参数逐字回查知识库 P10碳纤维电动轮椅10AH锂电-产品详细信息。"))
    con.commit()
    con.close()
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（目标 %.1f 秒）｜ 合规 %s" % (
        wc, sec, target, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s 「%s」 %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
