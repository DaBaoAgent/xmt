# -*- coding: utf-8 -*-
"""按 029 模板批量写 5 篇朋友2 品牌号（030-034）。

模板（源自 SG-20261020-029，用户认可版）：
  心悦挑刺（反方）→ 小冯拿事实/动作回应（正方），三个来回 + 收尾
  收尾固定：心悦松口约试「那…推出去试试？」→ 小冯「走，是骡子是马，
  推下去转一圈就知道。」

五个脚本各换三个卖点，全部逐字回查知识库
（助行器朋友2-参数与卖点：助行+陪护推行两用 / 铝合金air轻量可折叠车架 /
薄荷绿绿色香芋紫多色 / 软垫座面坐歇 / 网布储物袋 / 双侧下压式线控刹车 /
多档高度调节 / 约8寸万向前轮）。
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

# 每篇 = (code, 标题, [(说话人, 节拍, 台词), ...])
BATCH = [
    ("SG-20261020-030", "一车两种用法", [
        ("心悦", "反方", "朋友2？看着就跟普通助行车差不多。"),
        ("小冯", "正方", "它有两种用法。您扶着往前推，它是助行车；翻下来，它就是陪护车，我在后头推您。"),
        ("心悦", "反方", "那推的人使力不使力？"),
        ("小冯", "正方", "推把多档能调，我个儿高您个儿矮，都能找个顺手的位置。"),
        ("心悦", "反方", "推着出门，东西往哪儿放？"),
        ("小冯", "正方", "底下网布袋，菜啊水果塞里头，手还能搭扶手上。"),
        ("心悦", "反方", "哟，一车两用。推出去试试？"),
        ("小冯", "正方", "走，是骡子是马，推下去转一圈就知道。"),
    ]),
    ("SG-20261020-031", "四轮车拐弯笨不笨", [
        ("心悦", "反方", "四轮车最怕笨，拐个弯得使老大劲，老人推不动。"),
        ("小冯", "正方", "您瞧前头这轮，八寸万向的，窄地方原地就能调头，不用挪第二下，您试试。"),
        ("心悦", "反方", "那下坡呢，往下出溜怎么办？"),
        ("小冯", "正方", "双侧线控刹车，手一捏就停住，下坡不往前冲。"),
        ("心悦", "反方", "搬上楼沉不沉？"),
        ("小冯", "正方", "铝合金车架，轻，您一只手就拎得动，搬上楼不费劲。"),
        ("心悦", "反方", "那…推出去试试手？"),
        ("小冯", "正方", "走，是骡子是马，推下去转一圈就知道好坏。"),
    ]),
    ("SG-20261020-032", "逛累了有地方歇", [
        ("心悦", "反方", "老人出门逛着逛着累了，路边有地方坐吗？"),
        ("小冯", "正方", "您看这座面，软垫的，走累了翻下来就能歇，屁股不硌。"),
        ("心悦", "反方", "歇完接着走，收起来麻烦吗？"),
        ("小冯", "正方", "一拉就折，折起来个头不大，塞后备箱正合适，出门带着不占地方。"),
        ("心悦", "反方", "那座儿高低，合不合适呀？"),
        ("小冯", "正方", "多档能调，按身高调，坐着不憋屈，站起来也不费劲。"),
        ("心悦", "反方", "那…推出去遛一圈？"),
        ("小冯", "正方", "走，是骡子是马，推下去转一圈就知道。"),
    ]),
    ("SG-20261020-033", "一只手拎得动吗", [
        ("心悦", "反方", "老人手没劲，一只手捏得住刹车吗？别光看着行。"),
        ("小冯", "正方", "双侧下压式线控，往下轻轻一压就刹住，不用使大劲，老人也捏得动。"),
        ("心悦", "反方", "那推把呢，找个顺手的位置难不难？"),
        ("小冯", "正方", "推把多档能调，高个儿矮个儿都有合适的位置，搭着手不别扭。"),
        ("心悦", "反方", "搬上搬下沉不沉？"),
        ("小冯", "正方", "铝合金车架，轻，拎着不费劲，搬上搬下都行。"),
        ("心悦", "反方", "那推出去试试手？"),
        ("小冯", "正方", "走，是骡子是马，推下去转一圈就知道。"),
    ]),
    ("SG-20261020-034", "这车都有什么色儿", [
        ("心悦", "反方", "这车咋还有粉的？老人用不着吧，花里胡哨的不实用。"),
        ("小冯", "正方", "薄荷绿、香芋紫，好几个色，老人按喜好挑，推出去也不难看。"),
        ("心悦", "反方", "光好看不顶用，刹得住吗？"),
        ("小冯", "正方", "双侧线控刹车，下坡捏一下就停住，不往前蹿。"),
        ("心悦", "反方", "那出门买菜，东西咋办？"),
        ("小冯", "正方", "网布袋在底下，菜和水果都搁得下，手上还能搭在扶手上歇着。"),
        ("心悦", "反方", "那…推一台试试手？"),
        ("小冯", "正方", "走，是骡子是马，推下去转一圈就知道。"),
    ]),
]

TIPS_TAIL = [
    "结尾心悦先松口约试，小冯接「是骡子是马」，抬手指向展厅外",
    "字幕可标功能名（如「双侧线控刹车」），不写价格",
]

FACT_TEXT = (
    "佳康顺助行器朋友2（四轮带座助行器）：助行与陪护推行两用，"
    "铝合金air轻量可折叠车架，薄荷绿/绿色/香芋紫多色可选，"
    "软垫座面可坐歇，网布储物袋（买菜可放蔬菜瓜果），"
    "双侧下压式线控刹车，多档高度调节，约8寸万向前轮。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""
BENCH_URL = "https://v.douyin.com/h3AJIsVteww/"
BENCH_KEY = "7674149769651997988"


def build_body(pairs):
    body = {"format": "dialogue",
            "lines": [{"speaker": s, "beat": b, "text": t} for s, b, t in pairs]}
    lines = []
    for s, b, t in pairs:
        lines.append("%s：%s" % (s, t))
    return body, "\n".join(lines)


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    for code, title, pairs in BATCH:
        body, body_text = build_body(pairs)
        spoken = util.strip_speakers(body_text)
        wc = util.count_chars(spoken)
        sec = util.estimate_seconds(spoken)
        target = round(max(30, min(45, 29.0)), 1)   # 品牌号 30-45s，对标 29s → 取下限
        scan = compliance.scan_script(
            body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])
        tips = [
            "两人站在同一台朋友2两边，心悦抱着胳膊挑刺，小冯不吭声听着",
            "小冯全程不靠嘴反驳、全靠动作：折车、捏刹车、调高度，用事实说话",
            "心悦语气有弧线：不屑 → 咦？ → 认可，最后一句眼睛亮了",
        ] + TIPS_TAIL
        now = util.now_iso()
        row = con.execute("SELECT id FROM sg_scripts WHERE code=?",
                          (code,)).fetchone()
        if row:
            con.execute(
                "UPDATE sg_scripts SET account_id='brand', account_label='品牌号', "
                "presenters_json=?, title=?, body_json=?, body_md=?, word_count=?, "
                "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
                "compliance_json=?, product_model=?, product_scope=?, "
                "status='待审', version=version+1, updated_at=? WHERE code=?",
                (json.dumps(["心悦", "小冯"], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), "朋友2", "型号",
                 now, code))
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
                (code, now, now, "待审", "brand", "品牌号",
                 json.dumps(["心悦", "小冯"], ensure_ascii=False), "douyin",
                 BENCH_KEY, BENCH_URL, "遇见这么能炫耀的你会怎么办？", "朋友2",
                 json.dumps([], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, target, 1, "型号",
                 "按 029 模板批量产出：同一台朋友2，心悦挑刺、小冯拿事实/动作回应，"
                 "三个来回+收尾。卖点逐字回查知识库（助行器朋友2-参数与卖点）。"))
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
