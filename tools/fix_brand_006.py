"""品牌号 第 2 篇（SG-20261020-006）：贴对标原句改写。

对标（抖音·爱优护电动代步车，15.6s / 78 字）逐句：
  没想到，他的上班坐驾这么特别，竟然是一台电动代步车，
  车身一拉就能快速展开，从侧面上车更加轻松省力，
  操作简单，坐上就能直接开走，
  日常短途出行也不用总麻烦家人。

品牌号人设（config/personas.json 的 brand）：
  心悦主讲提问 / 小冯实操回答；「每条只讲一个客户真问题，不堆功能点」
  30-45 秒 / 150-240 字；CTA 到店试车
  structure_pref：真实客户疑问开场 → 心悦提问小冯演示 → 第二问加细节
                → 心悦收束成判断 → CTA

本篇只讲**一个**客户真问题：这车能折叠、好收纳、坐着就能走（对标的核心）。
不叠减震、不叠刹车、不叠坡道 —— 那是 003 已经讲过的。

改法（骨架照搬，只换近义词 + 换地点 + 替产品口径）：
  没想到 → 真没想到
  上班坐驾这么特别 → 这车还挺讲究
  竟然是一台电动代步车 → 竟然是台能折叠的
  车身一拉就能快速展开 → 往边上一拉就开了
  从侧面上车更加轻松省力 → 侧身坐上去也省劲
  操作简单 → 开着简单
  坐上就能直接开走 → 坐好就走
  日常短途出行也不用总麻烦家人 → 平常出门也不用老麻烦人
"""
import os
import io
import sys
import json
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from scriptgen import util  # noqa: E402
from scriptgen.writer import body_plain_text  # noqa: E402
from scriptgen import compliance  # noqa: E402

DB = os.path.join(ROOT, "data", "xmt.db")

TITLE = "这车能折叠，收起来不占地儿"

PAIRS = [
    ("心悦", "提问", "真没想到，这车还挺讲究，竟然是台能折叠的。"),
    ("小冯", "演示", "来，您看，往边上一拉就开了，三秒的事。"),
    ("心悦", "追问", "收起来能塞哪儿去？"),
    ("小冯", "演示", "折好跟个行李箱差不多，竖着靠墙放就成。"),
    ("心悦", "再追问", "那骑着呢，复杂不复杂？"),
    ("小冯", "演示", "简单，坐好就走，不用学。"),
    ("心悦", "判断", "所以选这种能折的，重点看收放和上手难不难。"),
    ("小冯", "回应", "平常出门买菜接娃，都不用老麻烦家里人。"),
    ("心悦", "CTA", "您来苏州阳光大厦展厅坐一圈，试过就知道合不合适。"),
]

TIPS = [
    "开场两人在展厅同框，心悦先开口提问，镜头给到那台展开的车",
    "小冯演示折叠时给中景：拉开 → 展开一气呵成，不要剪断",
    "折好之后拍车身收窄的特写，再拍竖着靠墙放的全景",
    "心悦问「骑着复杂不复杂」时，小冯直接跨坐上去，一拧就走",
    "两人对话节奏要快，一问一答，别让一方说长段",
    "结尾两人一起看镜头，CTA 由心悦说",
    "字幕突出「苏州阳光大厦九一一室」，不写价格",
]

FACT_TEXT = (
    "F2Q轻便折叠旅游代步车：折叠尺寸 高度98CM 宽度44CM 净重19KG "
    "展开尺寸105×54×90CM 最大载重125KG 电机240W高效无刷电机 电池10AH锂电 "
    "一键折叠/一拉即折叠（专利设计 按钮往外一拉一压完成折叠 专利号ZL2020 2 092755.4）"
    "可拖行 可放汽车后备箱 环形把手"
)


def main():
    body = {"format": "dialogue",
            "lines": [{"speaker": s, "beat": b, "text": t} for s, b, t in PAIRS]}
    body_text = body_plain_text(body)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    disclaimer = util.compliance_config().get("disclaimer") or ""
    scan = compliance.scan_script(body_text, {"disclaimer": disclaimer}, "", FACT_TEXT, [])

    code = "SG-20261020-006"
    target = max(30 * 0.8, min(45 * 1.2, 15.6 * 1.2))
    now = util.now_iso()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    exists = con.execute("SELECT id FROM sg_scripts WHERE code=?", (code,)).fetchone()
    if exists:
        con.execute(
            "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
            "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
            "compliance_json=?, version=version+1, updated_at=? WHERE code=?",
            (TITLE, json.dumps(body, ensure_ascii=False), body_text, wc, sec,
             round(target, 1), json.dumps(TIPS, ensure_ascii=False),
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
            (code, now, now, "待审", "brand", "品牌号",
             json.dumps(["心悦", "小冯"], ensure_ascii=False), "douyin",
             "7670093302795980066", "https://v.douyin.com/14bsXXYzpZk",
             "你见过这么高级的座驾吗？#爱优护电动轮椅 #电动轮椅 #关爱老人",
             None, json.dumps([], ensure_ascii=False), TITLE,
             json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, round(target, 1), 1, "品类",
             "同一对标（抖音爱优护）改写为品牌号版本：心悦提问小冯实操，"
             "只讲「能折叠好收纳上手就能走」一个客户真问题，不叠其他卖点"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（目标 %.1fs）｜ 合规 %s" % (
        wc, sec, target, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
