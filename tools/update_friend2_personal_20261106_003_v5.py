# -*- coding: utf-8 -*-
"""个人号 11-06 第 3 篇改稿（v5）：朋友二 · 抖音爆款逻辑版。

用户指令（2026-11-06）：「脚本没有吸引力 要带钩子符合抖音的爆款逻辑」。
v1 家常平铺、v2 报数清单，都被判「没吸引力」。v5 按抖音前 3 秒逻辑重做：

  1) 钩子（0-3 秒）：否定共识 + 损失厌恶 ——「买助行器最容易踩的坑，就在屁股底下」
     不喊人群、不提产品名，先给一个有画面感的危险（坑），让人必须听下去。
  2) 痛点（3-8 秒）：冬天穿棉裤坐下夹得慌 —— 具体场景，一句一个信息。
  3) 反转（8-15 秒）：这台四十四公分半、深三十五，一屁股下去两边还空着 —— 用动作证明，不用形容词。
  4) 补刀（15-20 秒）：车宽六十二公分半，屋门照样过得去 —— 顺带打掉「宽了就进不去门」的顾虑。
  5) 行动（收尾）：挤不挤，您来苏州阳光大厦坐下去就知道 —— 挑战式 CTA，与钩子闭环。

角度仍是座宽 / 座深 / 车宽（朋友二 26 篇未写过）；规格口径不变：
  座宽 445mm → 四十四公分半；座深 350mm → 三十五公分；展开宽 625mm → 六十二公分半。
不写承重（120kg 与分散受力 100kg 两套口径冲突）；不写价格；不写疾病名；不做防跌倒等医疗宣称；
不出现「最」字绝对化（钩子里「最容易」已改为「最容易踩的坑」→ 仍含「最」，改掉表述）。
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
TITLE = "坑就在屁股底下"
MODEL = "朋友二助行器"

LINES = [
    "买带座的助行器，坑常常就在屁股底下。",
    "座面窄那么一点，冬天穿棉裤，一坐就夹得慌。",
    "这台宽四十四公分半，深三十五，我一屁股下去两边还空着。",
    "车宽六十二公分半，屋门照样过得去。",
    "挤不挤，您来苏州阳光大厦坐下去就知道。",
]

TIPS = [
    "机位固定不动，人就坐在车上，全程不起身、不出画框",
    "第一句对着镜头说，语速压慢半拍、眼睛别飘，说完停 0.5 秒再接下一句（这句决定完播）",
    "说「夹得慌」时两手往大腿外侧一夹，做出被夹住的姿态，再松开",
    "说「两边还空着」时手掌平压座面、从中间往两边各推一下，让余量出现在画面里",
    "说「屋门照样过得去」时两臂张开比整车宽，比完立刻收",
    "收尾一句语气挑一下、往上扬，说完直接停，不挥手不寒暄",
]

FACT_TEXT = (
    "朋友二（NIP-FRIEND 第三代，型号HR101B）带座助行器：铝合金车架；"
    "展开960×625×880mm；折叠440×625×950mm；净重7.8kg；最大负载120kg；"
    "座椅高530mm；座宽445mm/座深350mm；推把880-1005mm；前后轮2×8寸PU胎；"
    "储物袋承重3kg；适用身高140-185cm；精巧反转靠背。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号单人口播（仅小冯出镜，不标说话人）+ 简单档 + 抖音爆款逻辑版（v5）。"
    "产品：朋友二助行器（HR101B）。角度：座宽 + 座深 + 整车宽。"
    "改稿链：v1 家常平铺 → v2 报数清单体 → v5 按抖音前3秒逻辑重做："
    "否定共识钩子（坑在屁股底下）+ 冬天棉裤夹腿痛点 + 动作证明余量 + 打消门窄顾虑 + 挑战式 CTA 收尾。"
    "防撞：朋友二 26 篇已写过一车两用/拐弯/歇脚/单手刹/颜色/储物/下坡/门窄/自己推/推得轻/"
    "菜市场/公园/收纳/一个人带出门/推把高低/反转靠背/拐杖菜篮/座高/三步坐下/上公交，"
    "座宽座深从未单独写；同型号内未用过否定钩子开场。"
    "不写承重（资料 120kg 与分散受力 100kg 两套口径冲突）；不写价格；不写疾病名；不做防跌倒医疗宣称；"
    "不使用「最」「第一」等绝对化表述（钩子由「最容易踩的坑」改为「坑常常就在屁股底下」）。"
    "尾句「挤不挤，您来苏州阳光大厦坐下去就知道。」已全库查重无重复。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（单人口播·抖音爆款钩子·固定机位）",
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
