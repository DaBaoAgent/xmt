# -*- coding: utf-8 -*-
"""个人号 11-06 第 3 篇改稿（v2）：朋友二 · 换方式 —— 报数清单体。

用户指令（2026-11-06）：「你换一个方式啊」。
v1（冬天穿得厚，这车坐得下）是「爷爷奶奶 + 家常口吻 + 参数平铺」的老套路，
与之前几篇同一套写法。v2 整篇换体裁：
  · 钩子从喊人群改成主张句「这车好在哪，我说三个数」，先许愿再交付
  · 结构由散文式改成 1/2/3 报数清单，三个数字＋三句解释，收口一句态度句
  · 口语精确到「公分半」，因为是报数语境，不违和
  · 尾句由「来坐一坐」换成「您来量量看」，与报数呼应，且已查重无重复

角度仍为座宽 / 座深 / 车宽（朋友二 26 篇未写过），规格口径不变：
  座宽 445mm → 四十四公分半；座深 350mm → 三十五公分；展开宽 625mm → 六十二公分半。
不写承重（120kg 与分散受力 100kg 两套口径冲突）；不写价格；不写疾病名；不做医疗宣称。
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
TITLE = "这车好在哪，我说三个数"
MODEL = "朋友二助行器"

LINES = [
    "这车好在哪，我说三个数。",
    "第一个数，座面宽四十四公分半，冬天穿厚裤子还有空。",
    "第二个数，座子深三十五公分，大腿整个搁得住。",
    "第三个数，车宽六十二公分半，屋门都过得去。",
    "就这三个数。",
    "展厅在苏州阳光大厦，您来量量看。",
]

TIPS = [
    "机位固定不动，人直接坐在车上，全程不起身、不出画框",
    "报第一个数时，手掌横着平压座面，从左沿划到右沿，让两边余量留在画面里",
    "报第二个数时，手掌从座面前沿往靠背方向比一段，不用旁白解释够不够",
    "报第三个数时，两臂张开比整车宽，比完就收，别多话",
    "每报一个数手指跟着数一下，数字前顿半拍，节奏比语速重要",
    "说完最后一个字直接停，不寒暄、不挥手、机位不动",
]

FACT_TEXT = (
    "朋友二（NIP-FRIEND 第三代，型号HR101B）带座助行器：铝合金车架；"
    "展开960×625×880mm；折叠440×625×950mm；净重7.8kg；最大负载120kg；"
    "座椅高530mm；座宽445mm/座深350mm；推把880-1005mm；前后轮2×8寸PU胎；"
    "储物袋承重3kg；适用身高140-185cm；精巧反转靠背。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号单人口播（仅小冯出镜，不标说话人）+ 简单档 + 报数清单体（v2 换体裁）。"
    "产品：朋友二助行器（HR101B）。角度：座面宽度 + 座深 + 整车宽度，报三个数。"
    "v1 为家常口吻平铺写法，用户要求换方式，v2 改为主张句钩子 + 一二三报数结构 + 态度句收口。"
    "防撞：朋友二 26 篇已写过一车两用/拐弯/歇脚/单手刹/颜色/储物/下坡/门窄/自己推/推得轻/"
    "菜市场/公园/收纳/一个人带出门/推把高低/反转靠背/拐杖菜篮/座高/三步坐下/上公交，"
    "座宽座深从未单独写；同型号内未用过报数清单体。"
    "不写承重（资料 120kg 与分散受力 100kg 两套口径冲突）；不写价格；不写疾病名；不做防跌倒医疗宣称。"
    "尾句「展厅在苏州阳光大厦，您来量量看。」已全库查重无重复。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（单人口播·报数清单体·固定机位）",
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
        raise SystemExit("不存在 %s，请先跑 make_friend2_personal_20261106_003.py" % CODE)
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
