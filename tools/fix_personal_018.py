"""个人号 SG-20261020-018：贴对标原句改写（抖音·小美说轮椅）。

对标（小美说轮椅，26 秒 / 130 字）逐句：
  同样是轮椅，为什么越来越多人选择运动轮椅呢？   ← 疑问式开场
  很多人以为它只能赛场用，实际上日常散步也很香。 ← 打破误解
  车身轻巧灵活，自己独自出门的话，转向操控也很顺手。
  加速加大手推圈，推行更省力。
  加宽坐垫，久坐更舒适。
  长时间出门逛街，手臂也不容易发酸。
  你现在用什么轮椅呢？评论区聊一聊吧。        ← 结尾（评论区互动，无地址）

产品口径：A3 镁铝合金轻便手动轮椅（用户确认）
  仅重10.4KG / 承重120KG 双X交叉结构 防翻轮设计
  黄金8°靠背 蜂窝透气坐垫 透气蜂窝坐垫(加厚亚麻布)
  弧形哑光铝合金扶手 万向轮灵活转向 大轮手推圈
  自行刹车(前置手刹) + 刹车把手(后置手刹) 脚踏板可折叠可拆卸
  适用：小区/公园散步、购物买菜、外出旅行(可折叠放后备箱)、就医出行

改法：贴原句骨架，逐句换近义词 + 换成 A3 的真实卖点：
  同样是轮椅 → 都是轮椅
  为什么越来越多人选择运动轮椅呢 → 为什么越来越多的人挑轻便的呢
  很多人以为它只能赛场用 → 很多人以为这车只能推着走
  实际上日常散步也很香 → 其实日常出门最合适
  车身轻巧灵活 → 车身轻，镁铝合金的
  转向操控也很顺手 → 万向轮前头，转弯跟得上
  加速加大手推圈，推行更省力 → 大轮手推圈，一推就动
  加宽坐垫，久坐更舒适 → 蜂窝透气坐垫，久坐不闷
  长时间出门逛街，手臂也不容易发酸 → 出门逛半天，手臂也不容易发酸
  你现在用什么轮椅呢？评论区聊一聊吧 → 你家现在用啥？评论区说说

个人号人设：小冯，工厂店经营者，第一人称朴实、真实场景开场、CTA 落展厅地址。
长度贴对标（26 秒 / 130 字），不补多余话术。
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

TITLE = "都是轮椅，怎么越来越多的人挑轻便的"

LINES = [
    "都是轮椅，怎么越来越多的人挑轻便的？",
    "很多人以为这车只能推着走，其实日常出门挺合适。",
    "车身轻，镁铝合金的，二十来斤。",
    "自己一个人出门，前头小轮子转得动，好拐弯。",
    "大轮子边上那圈手一推就走，不用使劲。",
    "坐垫是蜂窝透气的，坐久了不闷。",
    "出门逛半天，手臂也不酸。",
    "你家现在用啥？评论区说说。",
]

TIPS = [
    "开场站在一台轻便轮椅旁，镜头给全景，带点疑问的口气",
    "讲「才十斤多」时把车抬起来一下，让人看到真的轻",
    "讲万向轮转向时给前轮特写，镜头跟着轮子转",
    "讲手推圈时手放在圈上推一下，动作要自然",
    "讲坐垫时给特写，按一下坐垫",
    "结尾自然看镜头 inviting 互动，不念地址",
    "字幕可标 10.4 公斤这类数字，不写价格",
]

FACT_TEXT = (
    "A3镁铝合金大轮手动轮椅："
    "仅重10.4KG 承重120KG 双X交叉结构 防翻轮设计 "
    "黄金8°靠背 蜂窝透气坐垫(加厚亚麻布) 人体工学设计 "
    "弧形哑光铝合金扶手 透气蜂窝坐垫 大轮手推圈 万向轮灵活转向 "
    "自行刹车(前置手刹 老人操作) 刹车把手(后置手刹 护理员操作) "
    "腿带(护脚带) 脚踏板(PU塑料 可折叠可拆卸) "
    "镁铝合金材质 出口日本精工标准 承重120KG "
    "适用场景：居家室内/小区公园散步/购物买菜(后置储物袋)/外出旅行(可折叠放后备箱)/就医出行 "
    "适用人群：老年人日常出行代步/腿脚不便/术后康复 "
    "佳康顺16年医疗器械 源头工厂 美国FDA注册 欧盟CE认证"
)


def main():
    body = {"format": "monologue",
            "lines": [{"speaker": "小冯", "beat": "口播", "text": t} for t in LINES]}
    body_text = body_plain_text(body)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    disclaimer = util.compliance_config().get("disclaimer") or ""
    scan = compliance.scan_script(body_text, {"disclaimer": disclaimer}, "", FACT_TEXT, [])

    code = "SG-20261020-018"
    target = 30.0
    now = util.now_iso()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    exists = con.execute("SELECT id FROM sg_scripts WHERE code=?", (code,)).fetchone()
    if exists:
        con.execute(
            "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
            "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
            "compliance_json=?, version=version+1, updated_at=? WHERE code=?",
            (TITLE, json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
             json.dumps(TIPS, ensure_ascii=False), json.dumps(scan, ensure_ascii=False),
             now, code))
        print("已更新", code)
    else:
        con.execute(
            "INSERT INTO sg_scripts (code, created_at, updated_at, status, account_id, "
            "account_label, presenters_json, source_platform, video_key, benchmark_url, "
            "benchmark_title, product_model, product_doc_ids_json, title, body_json, body_md, "
            "shooting_tips_json, publish_json, compliance_json, facts_json, word_count, "
            "estimated_seconds, target_seconds, version, product_scope, notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (code, now, now, "待审", "personal", "个人号",
             json.dumps(["小冯"], ensure_ascii=False), "douyin",
             "7668513357422431494", "https://v.douyin.com/Wb9LzMizAKI/",
             "同样是轮椅，为什么越来越多人选择运动轮椅呢？ #轮椅 #为什么 #运动轮椅 #中进智行客",
             "A3",
             json.dumps(["jks-product/A3镁铝合金大轮手动轮椅-产品详细信息"], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "贴对标「打破误解 + 列优点 + 评论区互动」结构，代入 A3 镁铝合金轻便手动轮椅"
             "（用户确认口径）；参数逐字回查知识库；结尾保留评论区互动，不加地址"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 26s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
