# -*- coding: utf-8 -*-
"""按 029 模板批量写 5 篇减震款助行器品牌号（035-039）。

模板（源自 SG-20261020-029，用户认可版）：
  心悦挑刺（反方）→ 小冯拿事实/动作回应（正方），三个来回 + 收尾
  收尾逐篇不同，各贴合本篇卖点。

产品：佳康顺助行器「减震款」（知识库文档「主图-减震款」，无型号名）。
参数逐字回查：减震款+储物袋、把手8档调节、坐椅7档调节、高强碳素钢、
重量8.9KG、展开83.5*41*76-96CM、折叠83.5*41*40CM、汽车级弹簧减震、
大容量储物袋、双凹云感坐垫、可折叠放后备箱。
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
    ("SG-20261020-035", "这车过减速带颠不颠", [
        ("心悦", "反方", "小区减速带多，这车推过去颠不颠呀？"),
        ("小冯", "正方", "您瞧这根弹簧，汽车级减震，过坎不蹿，推的人手也不麻。"),
        ("心悦", "反方", "那坐着硌不硌？"),
        ("小冯", "正方", "双凹云感坐垫，中间凹两边托，坐久了不压屁股，起身也不打滑。"),
        ("心悦", "反方", "逛完收起来麻烦吗？"),
        ("小冯", "正方", "一拉就折，折起来个头不大，塞后备箱正合适，出门带着不占地方。"),
        ("心悦", "反方", "那…推去过一回减速带？"),
        ("小冯", "正方", "走，楼下就有减速带，推过去蹍一下就知道灵不灵。"),
    ]),
    ("SG-20261020-036", "把手能调到合适高度吗", [
        ("心悦", "反方", "高个儿矮个儿都有，这把手咋调？"),
        ("小冯", "正方", "把手八档，一寸一寸往上提，高个儿矮个儿总有一档顺手。"),
        ("心悦", "反方", "那座儿高低呢？"),
        ("小冯", "正方", "坐椅七档，按身高调，坐着不憋屈，站起来也不费劲，老人使着正合适。"),
        ("心悦", "反方", "钢的架子，压得住吗？别中看不中用。"),
        ("小冯", "正方", "高强碳素钢车架，您整个身子压上去都不带晃，稳当着呢。"),
        ("心悦", "反方", "那…照我这身量调一档？"),
        ("小冯", "正方", "走，我先量个手，给您调到最顺手的位置再试。"),
    ]),
    ("SG-20261020-037", "出门买菜放哪儿", [
        ("心悦", "反方", "出门买的那点儿东西，放哪儿啊？"),
        ("小冯", "正方", "您看这袋，大容量储物袋，菜啊水果塞里头，手还能搭在把手上歇着。"),
        ("心悦", "反方", "装满了拎着沉不沉？"),
        ("小冯", "正方", "八公斤九，一只手拎得动，搬上楼搬后备箱都不费劲。"),
        ("心悦", "反方", "搁家里头占地方吗？"),
        ("小冯", "正方", "一拉就折，折起来靠墙角，跟个行李箱差不多，不碍事。"),
        ("心悦", "反方", "那…装满一袋，推出去推推看？"),
        ("小冯", "正方", "走，菜市场遛一圈，袋子装满再回来，您拎着算我输。"),
    ]),
    ("SG-20261020-038", "坐上去得劲儿吗", [
        ("心悦", "反方", "这坐垫坐着得劲儿吗？别硬邦邦的硌屁股。"),
        ("小冯", "正方", "双凹云感的，您坐上来试试，屁股有地方托，腰也能靠着。"),
        ("心悦", "反方", "座儿能调高低吗？"),
        ("小冯", "正方", "坐椅七档，腿长的腿短的都能找到合适的位置，不高不低正合适。"),
        ("心悦", "反方", "石子路上颠得慌怎么办？"),
        ("小冯", "正方", "汽车级弹簧减震，车头跟着地面起伏走，石子路上也不硬蹿。"),
        ("心悦", "反方", "那…我坐上去歇会儿，您推着我走走？"),
        ("小冯", "正方", "走，您坐着别动，我推您走两圈试试。"),
    ]),
    ("SG-20261020-039", "这车看着单薄结实吗", [
        ("心悦", "反方", "看着挺单薄的，结实吗？别坐两天就晃荡。"),
        ("小冯", "正方", "高强碳素钢车架，焊点密，您使劲压压听声儿都是实的。"),
        ("心悦", "反方", "钢的那不就沉吗？老人使得动？"),
        ("小冯", "正方", "八公斤九，比您手里那袋米还轻，拎着就能走，一点儿不逞强。"),
        ("心悦", "反方", "那路上颠得慌咋办？"),
        ("小冯", "正方", "汽车级弹簧减震，过坎不蹿，推的人手也不麻，坐着也不怎么颠。"),
        ("心悦", "反方", "那…我使劲压压这架子？"),
        ("小冯", "正方", "走，您上手使劲压，晃一下算我的。"),
    ]),
]

TIPS_TAIL = [
    "结尾的收尾句每篇不同，按本篇卖点演，别用同一句话凑",
    "字幕可标功能名（如「汽车级弹簧减震」），不写价格",
]

FACT_TEXT = (
    "佳康顺助行器减震款（四轮带座助行器）：减震款+储物袋，把手8档调节，"
    "坐椅7档调节，高强碳素钢，重量8.9KG，展开83.5*41*76-96CM，"
    "折叠83.5*41*40CM，汽车级弹簧减震，大容量储物袋，双凹云感坐垫，"
    "可折叠放后备箱。"
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
            "两人站在同一台减震款旁边，心悦抱着胳膊挑刺，小冯不吭声听着",
            "小冯全程不靠嘴反驳、全靠动作：压弹簧、调档位、折车，用事实说话",
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
                 json.dumps(scan, ensure_ascii=False), "减震款助行器", "型号",
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
                 BENCH_KEY, BENCH_URL, "遇见这么能炫耀的你会怎么办？",
                 "减震款助行器",
                 json.dumps([], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, target, 1, "型号",
                 "按 029 模板批量产出：同一台减震款助行器，心悦挑刺、小冯拿事实/动作"
                 "回应，三个来回+收尾。收尾逐篇不同。参数逐字回查知识库"
                 "（主图-减震款）。"))
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
