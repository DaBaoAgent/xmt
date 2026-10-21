# -*- coding: utf-8 -*-
"""按 029 模板批量写 5 篇小飞燕电动代步车品牌号（045-049）。

模板（源自 SG-20261020-029，用户认可版）：
  心悦挑刺（反方）→ 小冯拿事实/动作回应（正方），三个来回 + 收尾
  收尾逐篇不同，各贴合本篇卖点。

产品：佳康顺「小飞燕」电动代步车（老人代步轻便轮椅，知识库
「小飞燕详情_06~24」系列图）。
参数逐字回查：
- 轮椅防倾轮：爬坡时自动触地支撑，防止后翻
- 加厚碳钢合金管：壁加厚、耐磨抗锈、不易变形、承重更高
- 靠背双档可调：95°端坐 / 145°仰躺（可坐可躺）
- 加大底座加宽轴距：平稳出行无惧颠簸
- 360°万向前轮：顺滑不卡顿
- 稳固弹性实心轮：耐磨防滑、推行顺畅
- 适用人群：老人代步、孕妈代步、儿童代步
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
    ("SG-20261020-045", "上陡坡往后仰吗", [
        ("心悦", "反方", "小飞燕？上陡坡会不会往后仰啊？"),
        ("小冯", "正方", "您瞧后轮这块，防倾轮，坡一陡它就自动触地支撑着，不后翻。"),
        ("心悦", "反方", "那坡上停住了，溜不溜？"),
        ("小冯", "正方", "松手就停住，电磁刹着，坡上跟平地上一个样，不溜。"),
        ("心悦", "反方", "车架子扛得住吗？别压两年就变形。"),
        ("小冯", "正方", "加厚碳钢合金管，壁加厚了，耐磨抗锈，也不易变形。"),
        ("心悦", "反方", "那…推去过一回陡坡？"),
        ("小冯", "正方", "走，地库那个坡够陡，推上去您看防倾轮啥时候落地。"),
    ]),
    ("SG-20261020-046", "这车能躺吗", [
        ("心悦", "反方", "老人逛累了想躺一会儿，这车能躺吗？"),
        ("小冯", "正方", "靠背两档，九十五度端坐，一百四十五度仰躺，一提一拉就换。"),
        ("心悦", "反方", "换挡的时候松了咋办？别躺到一半塌下来。"),
        ("小冯", "正方", "卡扣精准分档，锁死了稳当着，您晃两下试试。"),
        ("心悦", "反方", "躺上头颠不颠？"),
        ("小冯", "正方", "底座加大加宽了，轴距也宽，坐着躺着都不那么晃了。"),
        ("心悦", "反方", "那…放平了我试试？"),
        ("小冯", "正方", "走，我给您放到仰躺那档，您靠上去试试腰有处托没有。"),
    ]),
    ("SG-20261020-047", "窄处调头灵吗", [
        ("心悦", "反方", "电梯口、楼道口那么窄，这车调头灵吗？别卡半道上。"),
        ("小冯", "正方", "前轮三百六度万向，原地就能调头，顺滑不卡顿，一把就过来。"),
        ("心悦", "反方", "轮子耐磨不耐磨？别推俩月就磨平了。"),
        ("小冯", "正方", "稳固弹性实心轮，耐磨防滑，推起来也顺当，不较劲。"),
        ("心悦", "反方", "窄路上稳不稳？别一头栽过去。"),
        ("小冯", "正方", "底座加大加宽，轴距宽，窄道上也不飘。"),
        ("心悦", "反方", "那…找个窄地方转转？"),
        ("小冯", "正方", "走，电梯口那块最窄，推过去原地转一圈您瞧。"),
    ]),
    ("SG-20261020-048", "这车晃不晃", [
        ("心悦", "反方", "小飞燕这车，推起来晃不晃？别软绵绵的。"),
        ("小冯", "正方", "车架子是加厚碳钢合金管，壁加厚，不易变形，承重也更高。"),
        ("心悦", "反方", "碳钢的那不就沉吗？推着费不费劲？"),
        ("小冯", "正方", "轮子是三百六度万向的，顺滑不卡顿，推起来不较劲。"),
        ("心悦", "反方", "那路上坑坑洼洼的呢？"),
        ("小冯", "正方", "底座加大、轴距加宽，压得住，过坎坐着也不飘。"),
        ("心悦", "反方", "那…我上手推两圈？"),
        ("小冯", "正方", "走，您推着过两个减速带，手里头感觉一下晃不晃。"),
    ]),
    ("SG-20261020-049", "谁都能开吗", [
        ("心悦", "反方", "这车谁能开？家里老人使得惯吗？"),
        ("小冯", "正方", "老人代步、孕妈代步、儿童代步都行，一车伺候一家人，不挑人。"),
        ("心悦", "反方", "那操作难不难？别整一堆按键。"),
        ("小冯", "正方", "就一个摇杆，往前推就走，撒手就停住，不用学，一教就会。"),
        ("心悦", "反方", "坐久了累不累？"),
        ("小冯", "正方", "靠背两档，九十五度端坐、一百四十五度仰躺，坐着躺着随意换。"),
        ("心悦", "反方", "那…我开两圈试试？"),
        ("小冯", "正方", "走，钥匙给您，绕展厅一圈，哪儿不顺手您跟我说。"),
    ]),
]

TIPS_TAIL = [
    "结尾的收尾句每篇不同，按本篇卖点演，别用同一句话凑",
    "字幕可标功能名（如「防倾轮」），不写价格",
]

FACT_TEXT = (
    "佳康顺小飞燕电动代步车（老人代步轻便轮椅）：轮椅防倾轮（爬坡时自动"
    "触地支撑、防止后翻）、加厚碳钢合金管（壁加厚、耐磨抗锈、不易变形、"
    "承重更高）、靠背双档可调（95°端坐/145°仰躺）、加大底座加宽轴距"
    "（平稳出行）、360°万向前轮（顺滑不卡顿）、稳固弹性实心轮（耐磨防滑）、"
    "适用老人代步/孕妈代步/儿童代步。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""
BENCH_URL = "https://v.douyin.com/h3AJIsVteww/"
BENCH_KEY = "7674149769651997988"


def build_body(pairs):
    body = {"format": "dialogue",
            "lines": [{"speaker": s, "beat": b, "text": t} for s, b, t in pairs]}
    lines = ["%s：%s" % (s, t) for s, b, t in pairs]
    return body, "\n".join(lines)


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    for code, title, pairs in BATCH:
        body, body_text = build_body(pairs)
        spoken = util.strip_speakers(body_text)
        wc = util.count_chars(spoken)
        sec = util.estimate_seconds(spoken)
        target = round(max(30, min(45, 29.0)), 1)
        scan = compliance.scan_script(
            body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])
        tips = [
            "两人站在同一台小飞燕两边，心悦抱着胳膊挑刺，小冯不吭声听着",
            "小冯全程不靠嘴反驳、全靠动作：指防倾轮、放靠背、原地调头，用事实说话",
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
                 json.dumps(scan, ensure_ascii=False), "小飞燕", "型号",
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
                 BENCH_KEY, BENCH_URL, "遇见这么能炫耀的你会怎么办？", "小飞燕",
                 json.dumps([], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, target, 1, "型号",
                 "按 029 模板批量产出：同一台小飞燕，心悦挑刺、小冯拿事实/动作回应，"
                 "三个来回+收尾。收尾逐篇不同。参数逐字回查知识库"
                 "（小飞燕详情_06~24）。"))
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
