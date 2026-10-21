"""品牌号 SG-20261020-029：贴对标原句改写（抖音·遇见这么能炫耀的），朋友2。

对标（115 字 / 29 秒）双人抬杠结构：
  A：你怎么知道我买了新车啊？
  B：谁问你了？
  A：你不会才知道我这车是AI自驾吧？
  B：AI什么AI？我只知道下坡要自动减速才最重要。拔掉电池都不会溜坡哦。
  A：你不会才知道我这车很轻便吗？
  B：是吗？我只知道能一秒折叠起来，轻松搬进后面箱才叫轻便。
  B：车不行就别来炫了。

**⚠️ 产品错配问题（本篇关键）**：
对标讲的是**电动代步车**（AI自驾、拔掉电池不溜坡、一秒折叠进后备箱），
而 **朋友2 是四轮带座助行器**（无电机、无电池）。
硬套会编造产品功能（绝对禁止）→ 保留抬杠结构和节奏，
把卖点换成朋友2**真实有的**（逐字回查知识库）：
  对标「下坡自动减速/拔电池不溜坡」→ 朋友2 **双侧下压式线控刹车**
  对标「一秒折叠搬进后备箱」   → 朋友2 **铝合金 air 轻量可折叠车架**
  另加一轮朋友2 的**网布储物袋**（买菜放瓜果）

**⚠️ 合规注意**：
- 对标收尾「**车不行就别来炫了**」→ 踩别的产品，comparison 规则禁与其他品牌
  做功效或安全性对比 → 改成小冯推车邀请试的中性收尾
- 不说"防摔/不会翻"（safety_guarantee），只讲刹车怎么用
- 不讲价格

朋友2 参数（知识库：助行器朋友2-参数与卖点）：
  四轮带座助行器；助行 + 陪护推行两用
  铝合金 air 轻量可折叠车架；薄荷绿/绿色/香芋紫
  软垫座面（可坐歇）；网布储物袋；双侧下压式线控刹车
  多档高度调节；约 8 寸万向前轮

品牌号人设：心悦主讲、小冯实操。本篇把「炫耀 vs 怼」改成
「新买了车的高兴顾客 vs 懂行店员」，既保留抬杠节奏又符合人设。
30-45 秒 / 150-240 字。CTA 落展厅地址。

长度贴对标（29 秒），按品牌号区间写 ~165 字 / 38 秒。
"""
import os
import io
import sys
import json
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from scriptgen import util  # noqa: E402
from scriptgen.writer import body_plain_text  # noqa: E402
from scriptgen import compliance  # noqa: E402

DB = os.path.join(ROOT, "data", "xmt.db")

TITLE = "带座算什么，能捏住刹车才要紧"

PAIRS = [
    ("心悦", "钩子", "你看我新买的这台，带座的，走累了能坐。"),
    ("小冯", "回应", "带座算什么？下坡能捏住刹车才要紧。"),
    ("心悦", "再炫耀", "那它轻啊，拎着就走。"),
    ("小冯", "回应", "轻算什么？能折起来、拎着不费劲才叫方便。"),
    ("心悦", "再炫耀", "它底下还能放东西呢。"),
    ("小冯", "回应", "网布袋买菜放瓜果正好，这个实在。"),
    ("心悦", "收尾", "那你倒是说说，它到底哪儿好啊？"),
    ("小冯", "回应", "铝合金车架能折，双侧线控刹车，多档高度能调。"),
    ("小冯", "CTA", "走，推出去转一圈。好不好使，你试过就知道了。"),
]

TIPS = [
    "开场心悦推着新买的助行器进场，语气带点小得意",
    "小冯每次泼冷水时语速快一点、语气平淡，反差出喜剧效果",
    "讲刹车时真的捏一下双侧线控刹车，让观众看见动作",
    "讲折叠时当场把车折起来，一气呵成",
    "讲网布袋时从袋里掏出一把菜做示范",
    "结尾小冯抬手指向展厅外，邀请试推",
    "字幕可标「双侧线控刹车」「可折叠」，不写价格",
]

FACT_TEXT = (
    "佳康顺助行器朋友2（四轮带座助行器）："
    "助行与陪护推行两用，铝合金air轻量可折叠车架，"
    "薄荷绿/绿色/香芋紫多色可选，软垫座面可坐歇，"
    "网布储物袋（买菜可放蔬菜瓜果），双侧下压式线控刹车，"
    "多档高度调节，约8寸万向前轮。"
)


def main():
    body = {"format": "dialogue",
            "lines": [{"speaker": s, "beat": b, "text": t} for s, b, t in PAIRS]}
    body_text = body_plain_text(body)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    disclaimer = util.compliance_config().get("disclaimer") or ""
    scan = compliance.scan_script(body_text, {"disclaimer": disclaimer}, "", FACT_TEXT, [])

    code = "SG-20261020-029"
    target = 38.0
    now = util.now_iso()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    exists = con.execute("SELECT id FROM sg_scripts WHERE code=?", (code,)).fetchone()
    if exists:
        con.execute(
            "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
            "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
            "compliance_json=?, version=version+1, updated_at=? WHERE code=?",
            (TITLE, json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
             json.dumps(TIPS, ensure_ascii=False), json.dumps(scan, ensure_ascii=False),
             now, code))
        print("已更新", code)
    else:
        con.execute(
            "INSERT INTO sg_scripts (code, created_at, updated_at, status, account_id, "
            "account_label, presenters_json, source_platform, video_key, benchmark_url, "
            "benchmark_title, product_model, product_doc_ids_json, title, body_json, body_md, "
            "shooting_tips_json, publish_json, compliance_json, facts_json, word_count, "
            "estimated_seconds, target_seconds, version, product_scope, notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (code, now, now, "待审", "brand", "品牌号",
             json.dumps(["心悦", "小冯"], ensure_ascii=False), "douyin",
             "7674149769651997988", "https://v.douyin.com/h3AJIsVteww/",
             "遇见这么能炫耀的你会怎么办？#皮皮熊老年代步车 #老年代步车 "
             "#适老化产品 #电动四轮车 #老人出行神器",
             "朋友2",
             json.dumps(["jks-product/助行器朋友2-参数与卖点"], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "贴对标「双人抬杠」结构；**产品错配已处理**：对标是电动代步车"
             "（AI自驾/拔电池/一秒折叠进后备箱），朋友2是四轮带座助行器"
             "（无电机无电池）→ 不编功能，换成朋友2真实卖点"
             "（双侧线控刹车/铝合金可折车架/网布储物袋）；"
             "对标收尾「车不行就别来炫了」踩 comparison → 改中性收尾"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 29s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
