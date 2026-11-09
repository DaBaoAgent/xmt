# -*- coding: utf-8 -*-
"""个人号 11-06 第 3 篇：朋友二（NIP-FRIEND / HR101B）· 单人口播 · 座面宽度角度。

用户指令（2026-11-06）：「再写1个朋友2」；拍摄仍是「一个人固定机位」。

防角度重复（product_model LIKE 朋友2/朋友二 共 26 篇已查）：
  品牌号 029~034、055~060  一车两用 / 拐弯 / 歇脚 / 单手刹 / 颜色 / 买菜储物 /
                           下坡刹 / 门窄 / 自己推 / 刚出院
  个人号 061~064          推得轻 / 菜市场 / 公园坐 / 收纳占地方
  个人号 093、094         一个人带老人出门 / 推的人高矮不一样（推把调节）
  个人号 001~005          反转靠背 / 拐杖菜篮 / 矮个踩地(座高) / 三步坐下 / 上公交
→ 座面宽度 + 座深（坐得住、穿厚裤子也不挤）从未写过，且固定机位下一个坐姿就能说明，选它。

资料口径（jiaoben/朋友二助行器-紫色_产品信息总结.txt）：
  铝合金车架；展开 960×625×880mm；净重 7.8kg；最大负载 120kg；
  座椅高 530mm；座宽 445mm / 座深 350mm；推把 880-1005mm；
  前后轮 2×8 寸 PU 胎；储物袋承重 3kg；适用身高 140-185cm。
→ 445mm 写「四十多公分宽」、350mm 写「三十多公分深」、展开宽 625mm 写「六十来公分」，
  不做公分以下的精确表述（老人听着不自然）。
  资料对承重有 120kg / 100kg 两套口径（冲突），本篇不写承重。

合规：不写价格；不写疾病名；不做防跌倒等医疗宣称；不出现"最""第一"类绝对化。
尾句「来坐一坐」已全库查重无重复（032「有地方歇」056「能坐会儿」063「坐一下午」均不同）。
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
TITLE = "冬天穿得厚，这车坐得下"
MODEL = "朋友二助行器"

LINES = [
    "爷爷奶奶，冬天穿得厚，坐车就犯愁——屁股搁不住。",
    "这车座面四十多公分宽。",
    "我一屁股坐下，两边还空着。",
    "座子三十多公分深，大腿整个搁得住。",
    "车宽六十来公分，屋门都过得去。",
    "展厅在苏州阳光大厦，来坐一坐。",
]

TIPS = [
    "机位固定不动，人站在车尾侧，先把座面翻给镜头看，全程脚不挪、不出画框",
    "坐下去那一下一镜到底：屁股落座、两手往两边一摊，让画面自己看见余量，别剪",
    "坐稳后把两条腿往前伸平，座深够不够画面里一眼就有，不用旁白解释",
    "说完就坐着收尾，机位不动、人不站起来走开",
    "全程别推车走动——这条只讲坐，走动留到下一条",
]

FACT_TEXT = (
    "朋友二（NIP-FRIEND 第三代，型号HR101B）带座助行器：铝合金车架；"
    "展开960×625×880mm；折叠440×625×950mm；净重7.8kg；最大负载120kg；"
    "座椅高530mm；座宽445mm/座深350mm；推把880-1005mm；前后轮2×8寸PU胎；"
    "储物袋承重3kg；适用身高140-185cm；精巧反转靠背。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号单人口播（仅小冯出镜，不标说话人）+ 简单档 + 口语唠嗑腔。产品：朋友二助行器（HR101B）。"
    "角度：座面宽度 + 座深——冬天穿厚裤子也坐得下，两腿有地方搁；车宽六十来公分屋门过得去。"
    "防撞：朋友二 26 篇已写过一车两用/拐弯/歇脚/单手刹/颜色/储物/下坡/门窄/自己推/推得轻/"
    "菜市场/公园/收纳/一个人带出门/推把高低/反转靠背/拐杖菜篮/座高/三步坐下/上公交，座宽座深从未单独写。"
    "不写承重（资料 120kg 与分散受力 100kg 两套口径冲突）；不写价格；不写疾病名；不做防跌倒医疗宣称。"
    "尾句已全库查重。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（单人口播·座面宽度·固定机位）",
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
