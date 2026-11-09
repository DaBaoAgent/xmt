# -*- coding: utf-8 -*-
"""个人号 11-06 第 2 篇：GB-819 折叠带灯拐杖 · 单人口播 · 折叠角度。

用户指令（2026-11-06）：「再写1个拐杖819」；当前拍摄条件「一个人固定机位」。

防角度重复（sg_scripts 里 GB-819 已有 9 篇，全部已归档）：
  040 品牌号 晚上出门黑        → LED 照明
  041 品牌号 这杖还能听收音机  → FM
  042 品牌号 拐杖能调长短吗    → 10 档调节
  043 品牌号 一个人出门咋办    → SOS 报警
  044 品牌号 下雨天能拄吗      → IP43 防溅水
  065 个人号 拐杖有几个脚      → 四脚底座稳
  066 个人号 夜里起夜          → 夜灯 + 续航 12h + 手机线充电
  067 个人号 一个人出门不踏实  → 报警 100 多分贝 + 红光闪光
  068 个人号 照明收音全带了    → 灯 + FM + IP43 + 手机线
→ 折叠从未单独写过，且固定机位下"一折变短、塞进包"是看得见的动作，选它。

资料口径（jiaoben/拐杖_产品信息总结.txt【2】GB-819）：
  折叠带灯拐杖；ABS 手柄 / 6061 铝合金杖身 1.2mm / TPR 脚垫；净重 400g；
  高度 71-93.5cm（人工测量误差 1-2cm）；承重 100kg；1×902030 内置锂电可充；
  LED 照明 / SOS 报警 / FM 76-108MHz / 10 档调节 / 四脚底座。
→ 只用「能折」「比小臂还短」「四百克」「比一瓶矿泉水还轻」，节数资料未写，故不写"三节"。
   安全要点「折叠后勿作支撑使用」→ 稿里只写"不想拄了就收起来"，不暗示折着能拄。

合规：不写价格（含税 52 元为供货口径，不进稿）；不写疾病名；不做防跌倒等医疗宣称。
尾句「来比一比长短」已全库查重无重复（"来折一次""来折一次试试""来亲手折一回"均已被占用）。
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

CODE = "SG-20261106-002"
TITLE = "这拐杖折起来比小臂还短"
MODEL = "GB-819智能收音机拐杖"

LINES = [
    "爷爷奶奶，这根拐杖能折。",
    "走累了拄着，不想拄了，手一收。",
    "往下一折，比小臂还短。",
    "塞进布包，拎着就走。",
    "坐公交、进医院，两只手腾出来。",
    "四百克，比一瓶矿泉水还轻。",
    "展厅在苏州阳光大厦，来比一比长短。",
]

TIPS = [
    "机位固定不动，人站原地：先拄着走两步，再收手折起来，全程脚不挪、不出画框",
    "折的那一下靠身体前倾推到画面正中，别让手跑出镜头，动作一条到底不剪",
    "折完把小臂横过来贴在杖边，长短一比就明白，不用旁白解释",
    "最后把杖塞进随身布包、拎起来抬到镜头前看一眼，人仍站原位",
    "这条只讲折，灯和收音机全程别按，避免观众注意力散",
]

FACT_TEXT = (
    "佳康顺GB-819折叠带灯拐杖：ABS手柄 / 6061铝合金杖身（壁厚1.2mm）/ TPR脚垫；"
    "净重400g；高度71-93.5cm（人工测量误差1-2cm）；承重100kg；"
    "1×902030内置锂电池（可充电）；LED照明 / SOS报警 / FM收音机76-108MHz / "
    "10档调节 / 四脚底座。安全要点：折叠后勿作支撑使用。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

NOTES = (
    "个人号单人口播（仅小冯出镜，不标说话人）+ 简单档 + 口语唠嗑腔。产品：GB-819 折叠带灯拐杖。"
    "角度：折叠——一折比小臂还短、塞进布包、400g 比一瓶矿泉水还轻。"
    "防撞：GB-819 已有 9 篇分别讲过照明、FM、10档、SOS、IP43、四脚底座、续航、充电线，折叠从未单独写；"
    "本条按「一个人固定机位」设计，动作全在原位完成。"
    "不写价格（含税 52 元为供货口径）；不写疾病名；不做防跌倒等医疗宣称；"
    "节数资料未标注故不写；折叠后不作支撑使用，稿里不暗示。尾句已全库查重。"
)


def main():
    body = {"format": "monologue",
            "kind": "短平快·简单档（单人口播·折叠便携·固定机位）",
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
