# -*- coding: utf-8 -*-
"""个人号 061：贴对标「逐项展示」结构改写，代入朋友2（单人口播）。

对标：抖音「#轮椅 #电动轮椅 #老年代步车 #适老化产品 #代步车」144字/26.8秒
结构是**产品实拍 + 逐项讲特点**：轻(8公斤) → 一按就展开 → 两侧扶手可开
方便上下车 → 摇杆轻推往前走/松手停车 → 原地掉头 → 快拆锂电池能上飞机高铁。

**产品错配已处理**：对标是电动代步车（摇杆/松手停车/可拆电池），
朋友2 是**手动四轮带座助行器**（无电机无电池）→ 保留「逐项展示」的
结构和节奏，每一项换成朋友2 真实有的功能，不编电动功能。

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

CODE = "SG-20261020-061"
TITLE = "您看这车推起来多轻"

LINES = [
    "您看这个朋友2，推起来挺轻的。",
    "铝合金的车架，一拉就折，一个人拎得动。",
    "座面一放就能坐，走累了歇一歇。",
    "它还是助行、陪护两用，想走自己扶着走，想歇就坐下。",
    "把手能一档一档调高低，推着顺手。",
    "前轮八寸万向的，原地就能掉头。",
    "刹车是双侧下压的，手一捏就停住。",
    "底下还有网布袋，买菜放东西都方便。",
    "家里正给老人挑车的，评论区说说。",
]

TIPS = [
    "单人出镜，站在一台展开的朋友2旁边，边说边指",
    "每讲一个特点就动一下：折、翻座面、打开扶手、调高度、捏刹车",
    "语速跟日常聊天一样，别念参数，像跟邻居唠嗑",
    "结尾停在评论区那句，不加地址不加价格",
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
    body = {"format": "monologue",
            "lines": [{"speaker": "小冯", "beat": "口播", "text": t} for t in LINES]}
    body_text = "\n".join(LINES)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    target = round(max(45, min(60, 26.8)), 1)
    scan = compliance.scan_script(
        body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    now = util.now_iso()
    row = con.execute("SELECT id FROM sg_scripts WHERE code=?", (CODE,)).fetchone()
    if row:
        con.execute(
            "UPDATE sg_scripts SET account_id='personal', account_label='个人号', "
            "presenters_json=?, title=?, body_json=?, body_md=?, word_count=?, "
            "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
            "compliance_json=?, product_model=?, product_scope=?, "
            "status='待审', version=version+1, updated_at=? WHERE code=?",
            (json.dumps(["小冯"], ensure_ascii=False), TITLE,
             json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), "朋友2", "型号", now, CODE))
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
            (CODE, now, now, "待审", "personal", "个人号",
             json.dumps(["小冯"], ensure_ascii=False), "douyin",
             BENCH_KEY, BENCH_URL, "#轮椅 #电动轮椅 #老年代步车 #适老化产品 #代步车",
             "朋友2", json.dumps([], ensure_ascii=False), TITLE,
             json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "贴对标「产品实拍+逐项讲特点」结构，代入朋友2。"
             "**产品错配已处理**：对标是电动代步车（摇杆/松手停车/快拆电池），"
             "朋友2是手动助行器 → 每项换成朋友2真实功能，不编电动功能。"
             "参数逐字回查知识库（助行器朋友2-参数与卖点）。"))
    con.commit()
    con.close()
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 26.8s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s 「%s」 %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
