# -*- coding: utf-8 -*-
"""个人号 11-06 第 3 篇改稿（v6）：朋友二 · 换话题 —— 老人不肯用（心理抗拒）。

用户指令（2026-11-06）：「不喜欢这个话题」→ 选「还是朋友二，换个话题：老人嫌像病人车，不肯用」。
v1 家常平铺（座宽座深）、v2 报数清单、v5 抖音钩子（坑在屁股底下），话题都是「尺寸参数」，
用户明确不喜欢。v6 整篇换话题：从「车的尺寸」换到「人的心理」——

  钩子：给老人买助行器，卡住的多半不是钱，是他一句「我不用」——否定「贵才是障碍」的共识
  痛点：拿回家搁门口，一个月不碰（画面具体、有刺痛感）
  真相：不是走不动，是怕邻居问一句「你咋了」——把说不出口的那层挑明，这是转发点
  反转：这车看着不像医院里的东西，四轮带椅背，展开就是把椅子——给出「他肯用」的理由
  行动：带他来推一圈（把 CTA 从「来买」换成「带他来试」，顺着心理题收）

口径：朋友二 HR101B，铝合金车架、四轮可推可坐、精巧反转靠背、多色可选。
不写价格；不写疾病名；不做防跌倒等医疗宣称；不说「不像医疗器械」（合规风险）→ 改「不像医院里的东西」。
尾句「展厅在苏州阳光大厦，带他来推一圈。」已全库查重无重复。
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

CODE = "SG-20261106-003"
TITLE = "买回去一个月，他一次没碰"
MODEL = "朋友二助行器"

LINES = [
    "给老人买助行器，卡住的多半不是钱，是他一句「我不用」。",
    "拿回家搁门口，他能一个月不碰。",
    "不是走不动，是怕邻居问一句：你咋了。",
    "这车看着不像医院里的东西，四个轮子带个椅背，展开就是把椅子。",
    "展厅在苏州阳光大厦，带他来推一圈。",
]

TIPS = [
    "机位固定不动，人就站在车边，全程不挪脚、不出画框",
    "第一句对着镜头说，语气像在说自家的事，别喊、别推销，说完停半秒",
    "说「搁门口一个月不碰」时手往侧后方一摆，指一下门口方向，身体不动",
    "说「你咋了」时压低嗓子、学邻居那半句，短促、带点试探，这一下最容易让人共情",
    "说「带个椅背」时手掌拍两下椅背，再说「展开就是把椅子」时顺势往座面上一按",
    "收尾不劝不催，语气放平，说完直接停",
]

FACT_TEXT = (
    "朋友二（NIP-FRIEND 第三代，型号HR101B）带座助行器：铝合金车架；"
    "展开960×625×880mm；折叠440×625×950mm；净重7.8kg；最大负载120kg；"
    "座椅高530mm；座宽445mm/座深350mm；推把880-1005mm；前后轮2×8寸PU胎；"
    "储物袋承重3kg；适用身高140-185cm；精巧反转靠背。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号单人口播（仅小冯出镜，不标说话人）+ 简单档 + 心理抗拒话题（v6）。"
    "产品：朋友二助行器（HR101B）。话题：老人嫌像病人车、不肯用，先解决『肯不肯用』而不是『好不好用』。"
    "改稿链：v1 座宽家常版 → v2 报数清单 → v5 抖音钩子(坑在屁股底下) → 用户『不喜欢这个话题』→ "
    "v6 整篇换话题到人的心理：否定『钱是障碍』共识 + 搁门口不碰画面 + 怕邻居问的真相 + "
    "『不像医院里的东西』给台阶 + 带他来试的 CTA。"
    "防撞：朋友二 27 篇已写过一车两用/拐弯/歇脚/颜色/拎得动/储物/下坡刹/门窄/自己推/推得轻/"
    "菜市场/公园/收纳/一个人带出门/推把高低/刚出院/反转靠背/拐杖菜篮/座高/三步坐下/上公交/实心胎，"
    "『老人心理不接受』从未写过。"
    "不写价格；不写疾病名；不做防跌倒医疗宣称；不出现『最』『第一』绝对化；"
    "合规风险词『医疗器械』改为口语『医院里的东西』。"
    "尾句「展厅在苏州阳光大厦，带他来推一圈。」已全库查重无重复。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（单人口播·心理抗拒话题·固定机位）",
            "lines": [{"speaker": "", "text": t} for t in LINES]}
    body_text = "\n".join(LINES)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    target = 30.0
    scan = compliance.scan_script(body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT version FROM sg_scripts WHERE code=?", (CODE,)).fetchone()
    if not row:
        raise SystemExit("不存在 %s" % CODE)
    now = util.now_iso()
    con.execute(
        "UPDATE sg_scripts SET updated_at=?, title=?, body_json=?, body_md=?, "
        "shooting_tips_json=?, compliance_json=?, word_count=?, estimated_seconds=?, "
        "target_seconds=?, version=?, notes=? WHERE code=?",
        (now, TITLE, json.dumps(body, ensure_ascii=False), body_text,
         json.dumps(TIPS, ensure_ascii=False), json.dumps(scan, ensure_ascii=False),
         wc, sec, target, (row["version"] or 1) + 1, NOTES, CODE))
    con.commit()
    con.close()

    print("=== %s（%s，v%d）===" % (TITLE, CODE, (row["version"] or 1) + 1))
    print("%d 字 / %.1f 秒（目标 %.1f 秒）｜ 合规 %s" % (wc, sec, target, scan.get("counts")))
    print()
    print(body_text)
    findings = scan.get("findings") or []
    if findings:
        for f in findings:
            print("  [%s] %s 「%s」 %s" % (f.get("severity"), f.get("rule_id"),
                                           f.get("match"), f.get("suggest") or ""))
    else:
        print("  （无合规命中）")


if __name__ == "__main__":
    main()
