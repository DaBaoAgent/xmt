# -*- coding: utf-8 -*-
"""个人号 073：按「陈大脸甄选」对标风格写 F2Q 个人号稿（样稿）。

对标账号：陈大脸甄选（C1585273.6019，源头工厂直营店，279作品）
风格要点（见 skills/scriptgen-writing/对标账号分析-陈大脸甄选.md）：
- 人称「咱们/您」，口头禅「就是…呢…啊…然后呢」
- **逐条报数**：第一个…第二个…第三个…第四个
- 每条配一个使用场景（谁在什么状态下用）
- 演示感：「我给您看啊」「您看」
- 报具体参数（19KG/240W/10AH/六重保护）
- 收尾：邀请到店 + 自报身份

F2Q 参数（逐字回查知识库「F2Q轻便折叠旅游代步车10AH锂电-产品详细信息」）：
四大优势=更安全（智能电磁刹车，松开即刹，坡停不溜车，六重电池保护）/
更轻便（航空铝合金车架，仅19KG，专利折叠设计，一拖即走）/
更舒适（双重弹簧减震，皮革高回弹坐垫，减震弹簧座椅）/
更强劲（美国PRIDE同款240W无刷电机，轻松爬大坡，10AH锂电续航持久）；
底部购物篮、可调节车头、前置高亮大灯、防倾倒后轮、高靠背、宽大脚踏板；
品牌理念「孩子孝·爸妈笑」，18年专注医疗器械生产研发。

合规处理（对标原文踩线处）：
「中风脑梗恢复期」→ 删（疾病名）｜「不会摔倒/非常安全」→ 改客观功能描述｜
「非常轻松/轻轻松松」→ 改「不费劲/稳当」｜「腿部肌肉得不到锻炼」→ 删（功效断言）
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

CODE = "SG-20261020-073"
TITLE = "这代步车四个功能一块儿占了"

LINES = [
    "这个就是佳康顺的F2Q轻便折叠代步车。",
    "您别看它小，四个功能一块儿都占了。",
    "第一个是安全，智能电磁刹车，松开手就停，坡上停住也不溜车。",
    "第二个是轻，航空铝合金的车架，整车才十九公斤，一拖就走。",
    "第三个是坐着稳当，双重弹簧减震，皮革高回弹的坐垫。",
    "第四个是有劲，240瓦无刷电机，爬个大坡不费劲，十安时的锂电，还有六重保护。",
    "我给您看啊，这前面的大红灯，夜里照路看得清。",
    "您再看底下这个购物篮，买菜装一兜子也不沉。",
    "家里有爸妈要出行的，您来展厅坐一圈，比看图片管用。",
    "我是小冯，来了我帮您试。",
]

TIPS = [
    "单人出镜，站在一台F2Q旁边，边说边操作",
    "开头报品类，第二句抛「四个功能一块儿都占了」",
    "报四个功能时逐条数，最后一条是「有劲」",
    "讲到哪就动哪：按遥控演示刹车、拍大灯、提购物篮",
    "语速跟日常聊天一样，可以有口头禅，别念稿",
    "结尾邀请到店，字幕不写价格",
]

FACT_TEXT = (
    "佳康顺F2Q轻便折叠旅游代步车（10AH锂电）：更安全（智能电磁刹车，松开即刹，"
    "坡停不溜车，六重电池保护）；更轻便（航空铝合金车架，仅19KG，专利折叠设计，"
    "一拖即走）；更舒适（双重弹簧减震，皮革高回弹坐垫，减震弹簧座椅）；"
    "更强劲（美国PRIDE同款240W无刷电机，轻松爬大坡，10AH锂电续航持久）；"
    "底部购物篮、可调节车头、前置高亮大灯、防倾倒后轮、高靠背、宽大脚踏板；"
    "18年专注医疗器械生产研发，品牌理念「孩子孝·爸妈笑」。"
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
    target = round(max(45, min(60, 60.0)), 1)
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
             json.dumps(scan, ensure_ascii=False), "F2Q轻便折叠旅游代步车10AH锂电",
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
             "F2Q轻便折叠旅游代步车10AH锂电", json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "对标账号「陈大脸甄选」（C1585273.6019）风格样稿：逐条报数+每条配场景"
             "+现场演示+报具体参数+邀请到店。分析见 "
             ".workbuddy/skills/scriptgen-writing/对标账号分析-陈大脸甄选.md。"
             "F2Q 的「四大优势」正好对应他的逐条报数结构。"))
    con.commit()
    con.close()
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒 ｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s 「%s」 %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
