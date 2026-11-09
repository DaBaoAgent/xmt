# -*- coding: utf-8 -*-
"""个人号 11-06 第 3 篇改稿（v7）：朋友二 · 换风格 —— 幽默自嘲叙事。

用户指令（2026-11-06）：「再换一个风格」。
话题沿用 v6 的「老人不肯用」，但表达风格整篇换掉：v6 是温情扎心旁观式，
v7 改成第一人称自嘲讲自家糗事，用荒诞画面开场 + 母子抬杠对话 + 换用法破局。

  钩子：这车买回去，我妈先拿它当晾衣架，挂了半个月 —— 荒诞画面，2 秒抓住人
  对话：我说妈这是推着走的 / 她说我这腿还用不着 —— 一问一答，节奏像相声，带笑点
  破局：我没劝，把椅背翻过来往门口一摆 —— 不硬推产品，换个用法解决心理门槛
  结果：第三天她自己推着去买菜 —— 具体时间点，可信度高于任何形容词
  行动：带他也推一圈 —— 顺着「怎么让他自己用」收口

口径：朋友二 HR101B，铝合金车架、四轮可推可坐、精巧反转靠背、多色可选。
不写价格；不写疾病名；不做防跌倒等医疗宣称；不使用「最」「第一」绝对化。
尾句「展厅在苏州阳光大厦，让他自己试一把。」已全库查重无重复。
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
TITLE = "我妈把它当晾衣架用了半个月"
MODEL = "朋友二助行器"

LINES = [
    "这车买回去，我妈先拿它当晾衣架，挂了半个月。",
    "我说妈，这是推着走的。",
    "她说我这腿还用不着。",
    "我没劝，把椅背翻过来往门口一摆，进门就能坐。",
    "第三天她自己推着去买菜了。",
    "展厅在苏州阳光大厦，让他自己试一把。",
]

TIPS = [
    "机位固定不动，人就站在车边，全程不挪脚、不出画框",
    "第一句用唠家常的语气说，别咨询、别卖货，说到「晾衣架」时手往椅背上一搭、抬一下眉毛",
    "「我说妈」「她说」两句自己换声：前半句正常，后半句压低、拖一点，像学长辈的腔",
    "说「椅背翻过来」时当场把靠背翻一次，动作要慢、要完整，让镜头看清就是一个动作",
    "说「第三天她自己推着去买菜了」时笑一下再开口，别念台词",
    "收尾语气放松、不催，说完直接停",
]

FACT_TEXT = (
    "朋友二（NIP-FRIEND 第三代，型号HR101B）带座助行器：铝合金车架；"
    "展开960×625×880mm；折叠440×625×950mm；净重7.8kg；最大负载120kg；"
    "座椅高530mm；座宽445mm/座深350mm；推把880-1005mm；前后轮2×8寸PU胎；"
    "储物袋承重3kg；适用身高140-185cm；精巧反转靠背。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号单人口播（仅小冯出镜，不标说话人）+ 简单档 + 幽默自嘲叙事（v7 换风格）。"
    "产品：朋友二助行器（HR101B）。话题沿用 v6『老人不肯用』，风格由旁观扎心改为第一人称讲自家糗事。"
    "改稿链：v1 座宽家常 → v2 报数清单 → v5 抖音钩子 → v6 心理抗拒旁观式 → "
    "用户『再换一个风格』→ v7 荒诞画面开场（当晾衣架）+ 母子抬杠对话 + 翻椅背换用法破局 + 具体时间点结果。"
    "防撞：朋友二 27 篇已写过一车两用/拐弯/歇脚/颜色/拎得动/储物/下坡刹/门窄/自己推/推得轻/"
    "菜市场/公园/收纳/一个人带出门/推把高低/刚出院/反转靠背/拐杖菜篮/座高/三步坐下/上公交/实心胎/心理抗拒，"
    "『当晾衣架』式的自嘲叙事从未用过。"
    "不写价格；不写疾病名；不做防跌倒医疗宣称；不出现『最』『第一』绝对化。"
    "尾句「展厅在苏州阳光大厦，让他自己试一把。」已全库查重无重复。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（单人口播·幽默自嘲叙事·固定机位）",
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
