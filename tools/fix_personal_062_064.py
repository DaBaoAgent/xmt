# -*- coding: utf-8 -*-
"""个人号 062-064：沿用 061 的「逐项展示」结构，代入朋友2，各篇场景/卖点/收尾不同。

对标（061 的那条）：抖音「#轮椅 #电动轮椅 #老年代步车 #适老化产品 #代步车」
144字/26.8秒，结构是**产品实拍 + 逐项讲特点**。
本批沿用该结构与长度量级（130-150字），但换场景、换卖点组合、换收尾句。

**产品错配原则照旧**：对标是电动代步车（摇杆/松手停车/快拆电池），
朋友2 是手动四轮带座助行器 → 只写朋友2 真实有的功能，不编电动功能。

朋友2 参数（逐字回查知识库「助行器朋友2-参数与卖点」）：
助行与陪护推行两用、铝合金air轻量可折叠车架、薄荷绿/绿色/香芋紫多色可选、
软垫座面可坐歇、网布储物袋、双侧下压式线控刹车、多档高度调节、约8寸万向前轮。
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
    ("SG-20261020-062", "推去菜市场的车", [
        "推着老人去菜市场，得有辆顺手的车，买了菜还得能拿得动。",
        "朋友2底下有个网布袋，菜和水果塞里头，手还能搭扶手上。",
        "前轮八寸万向的，菜市场里人来人往，拐弯也跟得上，不别扭。",
        "走一圈累了，座面一放就能坐会儿。",
        "买完往回推，双侧下压的刹车，手一捏就停住。",
        "家里正给老人挑车的，评论区说说。",
    ]),
    ("SG-20261020-063", "推去公园坐一下午", [
        "推老人去公园，能坐一下午才舒服，累了还能歇脚。",
        "朋友2的座面是软垫的，屁股有地方托，腰也能靠着。",
        "铝合金车架，轻便，一个人推着不费劲，推半天也不累。",
        "前轮万向的，沙土路上也顺滑，不较劲，小坎儿过得去。",
        "双侧线控刹车，坡上停住就锁死，人也踏实。",
        "想让老人多出门遛遛的，评论区说说，我给您参谋。",
    ]),
    ("SG-20261020-064", "这车收起来占地方吗", [
        "买回去搁家里，占不占地方？家里地方小就麻烦了。",
        "朋友2一拉就折，竖着靠墙一放，跟个行李箱差不多。",
        "车架是铝合金的，拎着不沉，一只手就提得动。",
        "把手八个档、座面七档，按推的人和坐的人分别调。",
        "薄荷绿、香芋紫，好几个色，按喜好挑，老人看着也高兴。",
        "拿不准收起来多大，去展厅量量就知道。",
    ]),
]

TIPS = [
    "单人出镜，站在一台展开的朋友2旁边，边说边指",
    "每讲一个特点就动一下：折、翻座面、打开扶手、调高度、捏刹车",
    "语速跟日常聊天一样，别念参数，像跟邻居唠嗑",
    "结尾停在最后一句，不加价格",
    "字幕可标功能名（如「双侧下压式线控」），不写价格",
]

FACT_TEXT = (
    "佳康顺助行器朋友2（四轮带座助行器）：助行与陪护推行两用，"
    "铝合金air轻量可折叠车架，薄荷绿/绿色/香芋紫多色可选，"
    "软垫座面可坐歇，网布储物袋（买菜可放蔬菜瓜果），"
    "双侧下压式线控刹车，多档高度调节，约8寸万向前轮。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""
BENCH_URL = "https://v.douyin.com/1HemwSJOe8M/"
BENCH_KEY = "7626208190128612602"


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    for code, title, lines in BATCH:
        body = {"format": "monologue",
                "lines": [{"speaker": "小冯", "beat": "口播", "text": t}
                          for t in lines]}
        body_text = "\n".join(lines)
        spoken = util.strip_speakers(body_text)
        wc = util.count_chars(spoken)
        sec = util.estimate_seconds(spoken)
        target = round(max(45, min(60, 26.8)), 1)
        scan = compliance.scan_script(
            body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])
        now = util.now_iso()
        row = con.execute("SELECT id FROM sg_scripts WHERE code=?",
                          (code,)).fetchone()
        if row:
            con.execute(
                "UPDATE sg_scripts SET account_id='personal', account_label='个人号', "
                "presenters_json=?, title=?, body_json=?, body_md=?, word_count=?, "
                "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
                "compliance_json=?, product_model=?, product_scope=?, "
                "status='待审', version=version+1, updated_at=? WHERE code=?",
                (json.dumps(["小冯"], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
                 json.dumps(TIPS, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), "朋友2", "型号", now, code))
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
                (code, now, now, "待审", "personal", "个人号",
                 json.dumps(["小冯"], ensure_ascii=False), "douyin",
                 BENCH_KEY, BENCH_URL,
                 "#轮椅 #电动轮椅 #老年代步车 #适老化产品 #代步车",
                 "朋友2", json.dumps([], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(TIPS, ensure_ascii=False),
                 json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, target, 1, "型号",
                 "沿用 061 的「产品实拍+逐项讲特点」结构，代入朋友2，"
                 "换场景/卖点组合/收尾。对标是电动代步车（摇杆/松手停车/快拆电池），"
                 "朋友2是手动助行器 → 只写朋友2真实功能，不编电动功能。"))
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
