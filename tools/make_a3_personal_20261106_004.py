# -*- coding: utf-8 -*-
"""个人号 11-06 第 4 篇：A3 镁铝合金大轮手动轮椅（UNQ-A3）· 单人口播 · 后轮快拆角度。

用户指令（2026-11-06）：朋友二 003 连否数版后要求「换个什么破脚本」——换型号 + 换角度。

防角度重复（product_model LIKE A3 共 3 篇已查：待审 006/007/012）：
  已写 轻便(拎得动) / 刹车(停下来的办法有三个) / 折叠(折起来多大)。
→ 后轮快拆（一按就卸、装车省一半地方）从未写过，且一个蹲姿动作就能说清，选它。

资料口径（jiaoben/A3镁铝合金大轮手动轮椅_产品信息总结.txt）：
  镁铝合金车架；展开 1020×660×935mm；净重 10.4kg；最大承重 120kg；
  座宽 450mm / 座深 450mm；四刹车（前置手刹 + 后置手刹 + 驻车卡扣）；
  防翻辅助轮；蜂窝透气坐垫；黄金 8° 靠背；可折叠可拆卸脚踏板带护脚带；
  后置储物袋；免充气实心胎；大轮快拆——按压轮轴快拆按钮并向外抽出后轮。
→ 本篇只讲后轮快拆，不写承重（10.4kg 与主图 8.8kg 存在口径差，且本篇用不上）、
  不写价格、不写疾病名、不做防跌倒医疗宣称、不出现「最」「第一」。

合规：尾句「来亲手拆一回」已全库查重无重复。
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

CODE = "SG-20261106-004"
TITLE = "这车轮子一按就能卸"
MODEL = "A3手动轮椅"

LINES = [
    "爷爷奶奶，这车轮子一按就能卸。",
    "后备箱小，卸了轮子车架薄一半。",
    "往下一压，往上一提，轮子就下来。",
    "一个人装车，不用叫第二个人。",
    "装回去对准一插，听见咔一声。",
    "展厅在苏州阳光大厦，来亲手拆一回。",
]

TIPS = [
    "机位固定不动，人蹲在车尾侧，手就在轮子边上，全程脚不挪、不出画框",
    "拆轮一镜到底：拇指压在轮轴快拆按钮上往下一按、手往外一提，轮子离开车架那一下别剪",
    "装回同样一镜到底：轮轴对准孔一插，让画面里真听见咔一声，不用旁白解释",
    "拆下的轮子就立在脚边，别搬出画框，观众要看见它真卸下来了",
    "全程别起身走动、别推车溜一圈——这条只讲拆装，装车留到下一条",
]

FACT_TEXT = (
    "A3 镁铝合金大轮手动轮椅（UNQ-A3）：镁铝合金车架；展开1020×660×935mm；"
    "净重10.4kg；最大承重120kg；座位宽450mm/座深450mm；靠背高380mm；"
    "四刹车（前置手刹+后置手刹+驻车限位卡扣）；防翻辅助轮；蜂窝透气坐垫；"
    "黄金8°靠背；可折叠可拆卸脚踏板带护脚带；后置储物袋；免充气实心胎；"
    "大轮快拆，按压轮轴快拆按钮并向外抽出后轮，拆后体积更小，便于装车/上楼。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号单人口播（仅小冯出镜，不标说话人）+ 简单档 + 口语唠嗑腔。产品：A3 镁铝合金大轮手动轮椅（UNQ-A3）。"
    "角度：后轮快拆——一按就卸、装车省一半地方、一个人就能装。"
    "防撞：A3 已写轻便/刹车/折叠三篇，快拆从未写；朋友二写过的折叠是整车折叠，本篇是大轮快拆，不同。"
    "不写承重与净重（净重 10.4kg 与主图 8.8kg 口径有差，本篇用不上）；不写价格；不写疾病名；不做防跌倒医疗宣称。"
    "尾句已全库查重。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（单人口播·后轮快拆·固定机位）",
            "lines": [{"speaker": "", "text": t} for t in LINES]}
    body_text = "\n".join(LINES)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    target = 30.0
    scan = compliance.scan_script(body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    if con.execute("SELECT 1 FROM sg_scripts WHERE code=?", (CODE,)).fetchone():
        raise SystemExit("已存在 %s，改稿请走 UPDATE 脚本" % CODE)
    now = util.now_iso()
    con.execute(
        "INSERT INTO sg_scripts (code, created_at, updated_at, status, account_id, "
        "account_label, presenters_json, source_platform, product_model, "
        "product_doc_ids_json, title, body_json, body_md, shooting_tips_json, "
        "compliance_json, facts_json, word_count, estimated_seconds, target_seconds, "
        "version, product_scope, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (CODE, now, now, "待审", "personal", "个人号", json.dumps(["小冯"], ensure_ascii=False),
         "original", MODEL, "[]", TITLE, json.dumps(body, ensure_ascii=False), body_text,
         json.dumps(TIPS, ensure_ascii=False), json.dumps(scan, ensure_ascii=False), "[]",
         wc, sec, target, 1, "型号", NOTES))
    con.commit()
    con.close()

    print("=== %s（%s）===" % (TITLE, CODE))
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
