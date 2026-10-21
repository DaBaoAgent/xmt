# -*- coding: utf-8 -*-
"""按 029 模板写 5 篇朋友2 品牌号（055-059），单人口播、长度贴对标。

对标：抖音「姐妹，电动轮椅真的很适合你好嘛」59字/11秒
结构「一句真麻烦 → 几条怎么挑/怎么用」，一条一条说清楚。
形式：单人口播（小冯），不对话；不写 CTA、不写地址。

产品：佳康顺助行器朋友2（四轮带座助行器），参数逐字回查知识库：
助行与陪护推行两用、铝合金air轻量可折叠车架、薄荷绿/绿色/香芋紫多色可选、
软垫座面可坐歇、网布储物袋（买菜可放蔬菜瓜果）、双侧下压式线控刹车、
多档高度调节、约8寸万向前轮。
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
    ("SG-20261020-055", "买菜回来东西放哪儿", [
        "买完菜东西放哪儿？",
        "朋友2底下有个网布袋，菜和水果塞里头。",
        "手还能搭在扶手上，不用拎着。",
        "车架是铝合金的，能折起来，拎回去也不沉。",
    ]),
    ("SG-20261020-056", "推累了能坐会儿吗", [
        "推着推着累了，能坐会儿吗？",
        "朋友2有座面，软垫的，坐上去歇一歇。",
        "座面和把手都能调高低，按您的个儿来。",
        "走累了往下一坐，歇够了自己就能起来。",
    ]),
    ("SG-20261020-057", "这车下坡刹得住吗", [
        "下坡的时候刹得住吗？",
        "朋友2是双侧下压式线控，手一捏就停住。",
        "前轮八寸万向的，拐弯也跟得上。",
        "车架铝合金的，推起来稳当，不晃。",
    ]),
    ("SG-20261020-058", "楼道口窄推得过去吗", [
        "楼道口窄，推得过去吗？",
        "朋友2前轮是八寸万向的，原地就能调头。",
        "想收起来一拉就折，靠墙一放不占地方。",
        "把手还能调八个档，您推着顺手。",
    ]),
    ("SG-20261020-059", "自个儿能推着走吗", [
        "老人能自个儿推着走吗？",
        "能。朋友2是助行、陪护两用。",
        "想走自个儿扶着走，想歇就翻下来坐。",
        "两个把手，中间有刹车，走多远都心里有底。",
    ]),
]

TIPS_TAIL = [
    "结尾就停在最后一句，不加 CTA、不加地址",
    "字幕可标功能名（如「双侧线控刹车」），不写价格",
]

FACT_TEXT = (
    "佳康顺助行器朋友2（四轮带座助行器）：助行与陪护推行两用，"
    "铝合金air轻量可折叠车架，薄荷绿/绿色/香芋紫多色可选，"
    "软垫座面可坐歇，网布储物袋（买菜可放蔬菜瓜果），"
    "双侧下压式线控刹车，多档高度调节，约8寸万向前轮。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""
BENCH_URL = "https://v.douyin.com/Uuxh3-unN7w/"
BENCH_KEY = "7426274092665359666"


def build_body(lines):
    body = {"format": "monologue",
            "lines": [{"speaker": "小冯", "beat": "口播", "text": t} for t in lines]}
    return body, "\n".join(lines)


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    for code, title, lines in BATCH:
        body, body_text = build_body(lines)
        spoken = util.strip_speakers(body_text)
        wc = util.count_chars(spoken)
        sec = util.estimate_seconds(spoken)
        target = round(max(30, min(45, 11.0)), 1)
        scan = compliance.scan_script(
            body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])
        tips = [
            "单人出镜，对着镜头说，语速跟日常聊天一样",
            "开头一句是观众的真麻烦，语气带点犯难",
            "中间讲这车怎么用，一条一条说清楚，别赶",
            "结尾就停在最后一句，不加 CTA 不加地址",
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
                (json.dumps(["小冯"], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), "朋友2", "型号",
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
                 json.dumps(["小冯"], ensure_ascii=False), "douyin",
                 BENCH_KEY, BENCH_URL, "姐妹，电动轮椅真的很适合你好嘛", "朋友2",
                 json.dumps([], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, target, 1, "型号",
                 "单人口播（用户指定不要对话版），长度贴对标（59字/11秒量级）。"
                 "代入朋友2助行器，参数逐字回查知识库"
                 "（助行器朋友2-参数与卖点）。"))
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
