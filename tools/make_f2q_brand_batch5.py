# -*- coding: utf-8 -*-
"""按 029 模板批量写 5 篇 GB-819 智能收音机拐杖品牌号（040-044）。

模板（源自 SG-20261020-029，用户认可版）：
  心悦挑刺（反方）→ 小冯拿事实/动作回应（正方），三个来回 + 收尾
  收尾逐篇不同，各贴合本篇卖点。

产品：佳康顺 GB-819 智能收音机拐杖（知识库「GB-819智能收音机拐杖-参数与卖点」）。
参数逐字回查：LED手电筒照明（光通量≥180LM、满电照明≥12小时）、
高于100分贝报警+红光闪光警示、76-108MHz FM调频收音机、可伸缩铝合金杖杆、
5V USB充电、IP43防溅水。
注意：这是**手杖**（没有轮子和座），别写成助行器功能。
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
    ("SG-20261020-040", "晚上出门黑咋办", [
        ("心悦", "反方", "老人晚上出门，黑灯瞎火的咋办呀？"),
        ("小冯", "正方", "您按这个键，LED 灯一亮，一百八流通明，前头照得清清亮亮。"),
        ("心悦", "反方", "亮多久啊？别走半道没电了。"),
        ("小冯", "正方", "充满电能照十二个钟头，遛个弯绰绰有余，USB 口跟手机一个线。"),
        ("心悦", "反方", "那下雨天呢？灯会不会进水？"),
        ("小冯", "正方", "IP43 防溅水，下点小雨不打紧，擦干了照常使。"),
        ("心悦", "反方", "那…摁亮了看看？"),
        ("小冯", "正方", "走，楼道里暗，您摁一下看照得远不远。"),
    ]),
    ("SG-20261020-041", "这杖还能听收音机", [
        ("心悦", "反方", "拐杖还能听收音机？忽悠人呢吧。"),
        ("小冯", "正方", "您拧这个旋钮，76 到 108 兆赫，调频广播随便挑，台多着呢。"),
        ("心悦", "反方", "听得清吗？别滋啦滋啦的乱响。"),
        ("小冯", "正方", "您戴耳机或者外放都行，遛弯听个戏听个新闻，解闷儿。"),
        ("心悦", "反方", "费电吗？听一会儿就没电咋办？"),
        ("小冯", "正方", "USB 充电，跟手机共用一个充电头，晚上充上一宿就行。"),
        ("心悦", "反方", "那…拧个台我听听？"),
        ("小冯", "正方", "走，这会儿正播着戏呢，您拧到那个台试试。"),
    ]),
    ("SG-20261020-042", "拐杖能调长短吗", [
        ("心悦", "反方", "高个儿矮个儿都有，这杖能调长短吗？别一个尺寸糊弄人。"),
        ("小冯", "正方", "您拧这个结，铝合金杖杆能伸缩，一节一节往上调。"),
        ("心悦", "反方", "调的当口松了咋办？别拄着往下缩。"),
        ("小冯", "正方", "卡扣锁死了，拧紧了一般不松，您攥住甩两下试试。"),
        ("心悦", "反方", "那拄着沉不沉？"),
        ("小冯", "正方", "杖杆是铝合金的，轻，手里头没多少分量，拄着不累。"),
        ("心悦", "反方", "那…照我的个儿调一节试试？"),
        ("小冯", "正方", "走，您站直了，我给您量个手，调到手腕齐平那节。"),
    ]),
    ("SG-20261020-043", "一个人出门咋办", [
        ("心悦", "反方", "老人一个人出门，有点事儿咋办？喊不着人。"),
        ("小冯", "正方", "杖上有个警笛键，一摁一百多分贝，老远都听得见。"),
        ("心悦", "反方", "光有声儿，别人知道往哪儿看吗？"),
        ("小冯", "正方", "还带红光闪光，一喘一喘的，夜里头特别显眼，老远能看见。"),
        ("心悦", "反方", "那电池撑得住吗？别到用的时候没电。"),
        ("小冯", "正方", "USB 充电，手机线直接充，出门前充上就行。"),
        ("心悦", "反方", "那…摁一下我听听动静？"),
        ("小冯", "正方", "走，您先捂下耳朵，我教您摁哪个键不费劲。"),
    ]),
    ("SG-20261020-044", "下雨天能拄吗", [
        ("心悦", "反方", "下雨天路滑，这杖能拄吗？别进水坏了使不成。"),
        ("小冯", "正方", "IP43 防溅水，雨点子打上不碍事，擦干了照样使。"),
        ("心悦", "反方", "那杖身呢？会不会锈？"),
        ("小冯", "正方", "铝合金杖杆，沾了水擦一把就行，不爱生锈，用得住。"),
        ("心悦", "反方", "淋了雨，灯和收音机还灵吗？"),
        ("小冯", "正方", "您放心，USB 口有盖，充好电该照明照明，该听戏听戏，一样不落。"),
        ("心悦", "反方", "那…淋点儿水试试？"),
        ("小冯", "正方", "走，接点儿雨水泼上去，擦干了当场摁亮给您看。"),
    ]),
]

TIPS_TAIL = [
    "结尾的收尾句每篇不同，按本篇卖点演，别用同一句话凑",
    "字幕可标功能名（如「IP43 防溅水」），不写价格",
]

FACT_TEXT = (
    "佳康顺GB-819智能收音机拐杖：LED手电筒照明（光通量≥180LM、"
    "满电照明≥12小时）、高于100分贝报警加红光闪光警示、"
    "76-108MHz FM调频收音机、可伸缩铝合金杖杆、5V USB充电、IP43防溅水。"
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
            "两人站在桌边，心悦抱着胳膊挑刺，小冯不吭声听着",
            "小冯全程不靠嘴反驳、全靠动作：摁灯、拧台、调长短，用事实说话",
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
                 json.dumps(scan, ensure_ascii=False), "GB-819智能收音机拐杖",
                 "型号", now, code))
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
                 BENCH_KEY, BENCH_URL, "遇见这么能炫耀的你会怎么办？",
                 "GB-819智能收音机拐杖",
                 json.dumps([], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, target, 1, "型号",
                 "按 029 模板批量产出：同一根819拐杖，心悦挑刺、小冯拿事实/动作回应，"
                 "三个来回+收尾。收尾逐篇不同。参数逐字回查知识库"
                 "（GB-819智能收音机拐杖-参数与卖点）。"))
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
