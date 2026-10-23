# -*- coding: utf-8 -*-
"""个人号 023：F2Q 折叠代步车稿（王师傅「悬念钩子型」风格）。

对标账号：助行辅具王师傅-大脸老年代步车（抖音号 97428562854，priority 1）
来源：https://v.douyin.com/AE6tbFhlBN4/ → 视频 7680916374746634939
分析文档：.workbuddy/skills/scriptgen-writing/对标账号分析-王师傅大脸老年代步车.md

骨架（悬念钩子型）：开头抛悬念问句 → 报一个具体的人/场景 → 现场演示 →
逐条说长处（每条带动作）→ 情绪收尾 → 一句展厅邀请。

★ 角度避重：080-084 已写过 F2Q 的四功能/小轮过坎/折叠操作/送爸妈/避坑，
  本篇专写「断电/没电也刹得住 + 拨杆切手动推行」，是 080-084 没碰的角度。

F2Q 参数（来源：docs/产品参数档案.md + 知识库
jks-product/F2Q轻便折叠旅游代步车10AH锂电-产品详细信息-9a454f.txt）：
- 智能电磁刹车：松开即刹、断电也能刹
- 拨杆向上手动推行 / 向下电动（没电也能推着走）
- 双重弹簧减震 + 悬浮减震
- 免维护实心 9 寸大轮（前 18CM / 后 21.5CM），防爆防扎
- 底部购物篮、环形把手控制面板、前置高亮大灯、防倾倒后轮
- 240W 无刷电机、10AH 安规锂电六重保护、净重 19KG、载重 125KG

★ 禁写：没有具体续航公里数（别编「能跑 XX 公里」）；
  「两段一压一扣」是编的，折叠是「按钮往外一拉，一压」（专利 ZL2020 2 092755.4）；
  不写价格、不写绝对化词。
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

CODE = "SG-20261023-085"
# 标题不带标点：slugify 会把标点转成连字符，触发本机安全钩子拦 out/*.docx
TITLE = "代步车没电了刹得住吗"

LINES = [
    "代步车没电了，坡上停得住吗？",
    "前阵子展厅来位老先生，进门就问我这个。",
    "我把他领到车跟前，说您把手松开。",
    "这车是电磁刹车，手一松就刹，断了电也刹得住，不会哧溜往下滑。",
    "他还不放心，我把电门关了，再松手，车纹丝不动。",
    "真要没电了也不怕，拨杆往上一掰，电动变手动，推着照样回家。",
    "双重弹簧加悬浮减震，过个坎不颠。",
    "底部还有个大购物篮，买个菜逛个公园都够用。",
    "老人自己敢开车出门，靠的就是这份踏实。",
    "您来阳光大厦展厅，我给您试一遍。",
]

TIPS = [
    "单人出镜，站在 F2Q 旁边，开口先抛问句，抛完停顿一下",
    "「松手就刹」真的松一次手柄，镜头给前轮特写",
    "关电门再演示一次断电刹停，让观众看见断了电也停得住",
    "拨杆切换真的掰一下：往上手动推行、往下电动",
    "减震和购物篮各给一个近景，别只用嘴说",
    "结尾情绪句放慢，不配促销字幕，不写地址门牌",
]

FACT_TEXT = (
    "佳康顺F2Q轻便折叠旅游代步车（10AH锂电）：展开105×54×90CM，"
    "折叠高98CM宽44CM；净重19KG（不含电池扶手坐垫），最大载重125KG；"
    "座高49.5CM宽37.5CM深36CM；前轮18CM、后轮21.5CM（9寸大轮）；"
    "240W高效无刷电机（美国PRIDE同款）；10AH安规锂电池，六重保护；"
    "一拉即折叠（按钮往外一拉一压，专利号ZL2020 2 092755.4）、一拖即走；"
    "智能电磁刹车松开即刹、断电也能刹；陡坡自动匀速AI控速；"
    "拨杆向上手动推行/向下电动；双重弹簧减震+悬浮减震；"
    "免维护实心9寸大轮防爆防扎；环形把手控制面板、底部购物篮、可调节车头、"
    "前置大灯、防倾倒后轮、高回弹防水皮革坐垫、高靠背、宽大脚踏板；"
    "佳康顺18年医疗器械。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""
BENCH_URL = "https://www.douyin.com/video/7680916374746634939"
BENCH_KEY = "7680916374746634939"
BENCH_TITLE = "网友直夸：这款四合一代步车真不赖"


def main():
    body = {"format": "monologue",
            "lines": [{"speaker": "小冯", "beat": "口播", "text": t} for t in LINES]}
    body_text = "\n".join(LINES)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    target = 40.0
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
             json.dumps(scan, ensure_ascii=False), "F2Q轻便折叠旅游代步车10AH锂电",
             "型号", now, CODE))
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
             BENCH_KEY, BENCH_URL, BENCH_TITLE,
             "F2Q轻便折叠旅游代步车10AH锂电", json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False),
             json.dumps([FACT_TEXT], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "F2Q 个人号第 6 篇（080-084 之后第 6 个角度），"
             "按王师傅悬念钩子型骨架写：开头抛悬念问句 → 一位老先生的场景 → "
             "两次现场演示（松手即刹 / 断电刹停）→ 拨杆切手动 → 情绪收尾 → "
             "展厅邀请。★ 专写断电刹车+手动推行，避开 080-084 已用角度"
             "（四功能/小轮过坎/折叠操作/送爸妈/避坑）。"
             "参数全部贴档案：电磁刹车松开即刹断电也能刹、拨杆向上手动/向下电动、"
             "双重弹簧+悬浮减震、9寸实心轮、购物篮；无续航公里数（别编）、"
             "无价格。"))
    con.commit()
    con.close()
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（目标 %.1f 秒）｜ 合规 %s" % (
        wc, sec, target, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s 「%s」 %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
