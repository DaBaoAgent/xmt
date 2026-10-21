# -*- coding: utf-8 -*-
"""按 029 模板写 5 篇品牌号（050-054），不代入产品。

对标：抖音「姐妹，电动轮椅真的很适合你好嘛」59字/11秒，
结构「问题（轮椅遇到台阶下不去）→ 一秒折叠 → 提起下楼 → 一按展开 → 摇杆一推就走」。

模板（源自 SG-20261020-029）：心悦挑刺（反方）→ 小冯演示/解答（正方），
三个来回 + 收尾，收尾逐篇不同。

**本批不代入产品**（用户指定）：不写任何型号名，只讲「怎么挑」的
选购常识 + 场景应对，不给具体产品做功能宣称。
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
    ("SG-20261020-050", "轮椅下台阶咋弄", [
        ("心悦", "反方", "老人坐轮椅碰上台阶，下不去咋弄？难不成两个人抬下去？"),
        ("小冯", "正方", "挑能快折的，几下一折，拎着就下去了，不用抬。"),
        ("心悦", "反方", "折完会不会散？拎到一半散架了咋办。"),
        ("小冯", "正方", "折完有卡扣锁着，拎着不散，到平地一按就展开，省事。"),
        ("心悦", "反方", "那拎着沉不沉？"),
        ("小冯", "正方", "挑的时候问清整车多重，轻一些的一个人拎得动，不费劲。"),
        ("心悦", "反方", "那…折一下我看看？"),
        ("小冯", "正方", "走，我折一遍您给计着时，几秒的事儿。"),
    ]),
    ("SG-20261020-051", "想带出门塞不下咋办", [
        ("心悦", "反方", "想带老人出门玩，轮椅塞不进后备箱，这事儿咋办？"),
        ("小冯", "正方", "挑能折的，折起来立着放，占地小，一般的后备箱都塞得进。"),
        ("心悦", "反方", "折完多重？我一个人抬得动不？"),
        ("小冯", "正方", "问清公斤数，轻的自己能抬，重的得俩人搭手。"),
        ("心悦", "反方", "到地方展开麻烦吗？别拧半天螺丝。"),
        ("小冯", "正方", "一按就开，几秒的事儿，不用拧螺丝，也不用找人帮忙。"),
        ("心悦", "反方", "那…折起来我看看尺寸？"),
        ("小冯", "正方", "走，折好了您比划一下，跟后备箱比比量。"),
    ]),
    ("SG-20261020-052", "家门口窄进不去", [
        ("心悦", "反方", "家门口窄，轮椅推进去费劲，这事儿咋办？"),
        ("小冯", "正方", "挑车前先量门框多宽，再对照车多宽，别买完了卡门口进不去。"),
        ("心悦", "反方", "车宽去哪儿看？参数一大堆看不懂。"),
        ("小冯", "正方", "问清最宽处多少公分，别只看座位多宽，扶手外沿也算。"),
        ("心悦", "反方", "进门之后呢？掉头难不难？"),
        ("小冯", "正方", "前轮能万向转的，原地掉头，不用提起来挪第二下。"),
        ("心悦", "反方", "那…量一下我这家门？"),
        ("小冯", "正方", "走，拿尺子量门框，我给您对几款合适的宽度。"),
    ]),
    ("SG-20261020-053", "没电了扔半道咋办", [
        ("心悦", "反方", "电动轮椅没电了，扔半道上回不了家，这事儿咋办？"),
        ("小冯", "正方", "多数电车都有手推模式，拨一下就能推着走，不耽误回家。"),
        ("心悦", "反方", "推着费劲不？别推两步就喘。"),
        ("小冯", "正方", "挑的时候问清空车多重，轻一些的推着不累。"),
        ("心悦", "反方", "那咋知道还剩多少电？别等趴窝了才知道。"),
        ("小冯", "正方", "看电量显示，剩一两格就该充了，出门前充满。"),
        ("心悦", "反方", "那…推一把我试试？"),
        ("小冯", "正方", "走，切到手推那档，您上手感觉一下轻重，试试推着累不累。"),
    ]),
    ("SG-20261020-054", "地库坡陡不敢下", [
        ("心悦", "反方", "小区地库坡陡，坐电动轮椅下坡心里发慌，这事儿咋办？"),
        ("小冯", "正方", "下坡用低速档，慢慢蹭着走，别直着冲下去。"),
        ("心悦", "反方", "坡上停了，会不会往后溜啊？"),
        ("小冯", "正方", "挑带驻车刹车的，停住就锁死，不后溜，人也踏实。"),
        ("心悦", "反方", "咋知道这坡，咱到底下得下不下？"),
        ("小冯", "正方", "先推着走一趟试试，心里有数了再让老人自己下。"),
        ("心悦", "反方", "那…推下去一趟？"),
        ("小冯", "正方", "走，我推着走一遍，您在旁边看咋控速度，哪儿不合适您说。"),
    ]),
]

TIPS_TAIL = [
    "结尾的收尾句每篇不同，按本篇场景演，别用同一句话凑",
    "本批不代入产品，台词里不出现任何型号名",
    "字幕不写价格",
]

FACT_TEXT = (
    "电动轮椅/轮椅选购常识（不代入具体产品）：挑能快折的（折完有卡扣锁着、"
    "一按展开）；问清整车公斤数（轻的一个人拎得动/推着不累）；"
    "量门框再对照车宽（问最宽处多少公分）；前轮万向可原地掉头；"
    "电动轮椅多带手推模式（没电可推着走）、看电量显示、剩一两格就充；"
    "下坡用低速档、挑带驻车刹车的（停住锁死不后溜）。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""
BENCH_URL = "https://v.douyin.com/Uuxh3-unN7w/"
BENCH_KEY = "7426274092665359666"


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
        target = round(max(30, min(45, 11.0)), 1)
        scan = compliance.scan_script(
            body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])
        tips = [
            "两人站在展厅里，心悦抱着胳膊挑刺提问，小冯拿动作/事实回应",
            "心悦语气有弧线：犯难 → 咦？ → 认可，最后一句眼睛亮了",
        ] + TIPS_TAIL
        now = util.now_iso()
        row = con.execute("SELECT id FROM sg_scripts WHERE code=?",
                          (code,)).fetchone()
        if row:
            con.execute(
                "UPDATE sg_scripts SET account_id='brand', account_label='品牌号', "
                "presenters_json=?, title=?, body_json=?, body_md=?, word_count=?, "
                "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
                "compliance_json=?, product_model=NULL, product_scope=?, "
                "status='待审', version=version+1, updated_at=? WHERE code=?",
                (json.dumps(["心悦", "小冯"], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), "品类",
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
                 BENCH_KEY, BENCH_URL, "姐妹，电动轮椅真的很适合你好嘛",
                 None, json.dumps([], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, target, 1, "品类",
                 "按 029 模板批量产出：心悦挑刺、小冯拿动作/事实回应，三个来回+收尾，"
                 "收尾逐篇不同。**不代入产品**（用户指定）：不写型号名，只讲选购常识"
                 "与场景应对。对标：抖音「姐妹，电动轮椅真的很适合你好嘛」"
                 "（59字/11秒，台阶下不去→一秒折叠→提起下楼→一按展开）。"))
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
