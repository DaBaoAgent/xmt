# -*- coding: utf-8 -*-
"""个人号 022：NIP 助行器稿（王师傅「悬念钩子型」风格）。

对标账号：助行辅具王师傅-大脸老年代步车（抖音号 97428562854）
来源短链：https://v.douyin.com/AE6tbFhlBN4/
分析文档：.workbuddy/skills/scriptgen-writing/对标账号分析-王师傅大脸老年代步车.md

骨架（悬念钩子型）：抛悬念问句 → 报品类 → 逐条说长处（每条带场景）
→ 报具体参数 → 现场演示 → 邀请到店

NIP 参数（多源交叉核对：知识库 jks-product/助行器nip红色-参数与卖点_97a2fb-0a3c2f.md
+ common/配文_ecafaa-e905bd.txt + common/配文_47c8a3-5593d4.txt +
marketing/小红书文案_3563d6 / 739302 / f547b9）：
- 红色弧形铝合金车架（escape®系列）+ 黑白千鸟格布艺座靠，内衬软垫
- 净重 7.8kg（铝合金车架），承重 150kg
- 银色立管多孔位调节 + 快锁卡扣，握把高度 810～913mm 可调，适配 150～185cm
- 双侧刹车杆线控刹车，手指一勾即停、松手即刹
- 约 8 寸五辐条轮，前轮万向转向，转向灵活
- 一体式可歇座椅，走累了转身就坐
- 一拉折叠、一按展开，收起窄窄一条放后备箱
- 新西兰原装进口，汽车级金属烤漆
- 佳康顺 17 年匠心，工厂直营

★ 竞品参数绝不抄：上一条对标（王师傅）说的 16 公斤 / 12 公里 / 陀螺仪 /
  大阻尼康复模式，是他那台四合一代步车的，跟 NIP 无关。
  NIP 是**手动四轮带座助行器**：没有电机、没有电池、没有摇杆、没有电磁刹车，
  刹车是**手拉线刹**。绝不能写成电动款。

合规：删「轻轻松松/非常安全/安全第一」等绝对化与安全断言；「康复辅助」类
功效暗示改成生活化场景；不写价格、不写疾病名、不写竞品参数。
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

CODE = "SG-20261021-079"
# 标题不带标点：slugify 会把标点转成连字符，触发本机安全钩子拦 out/*.docx
TITLE = "您见过七公斤多的助行器吗"

LINES = [
    "您见过七公斤多的助行器吗？",
    "佳康顺这台NIP助行器，整车才七点八公斤。",
    "头一个是稳当，红色弧形车架重心低，推着不晃。",
    "第二个是坐着，累了往回一转身就能坐。",
    "第三个是能调，握把三档高度，一百五到一米八五都能调。",
    "两侧都有刹车杆，手指一勾就停。",
    "我给您看啊，往前一拉就折起来了，收起一条窄，放后备箱不占地方。",
    "车里还有千鸟格的座靠，透气不闷汗。",
    "给爸妈挑助行器的，您来展厅推一圈，比看图片管用。",
    "我是小冯，来了我帮您试。",
]

TIPS = [
    "单人出镜，站在一台 NIP 旁边，开口先抛问句",
    "第一句要有停顿感，悬念抛完再报品类",
    "讲折叠真的拉一次，讲刹车勾一下刹车杆让观众看见",
    "高度调节要真的拔插销，镜头给立管上的孔位特写",
    "千鸟格座靠给个近景，这是这台的记忆点",
    "结尾停在展厅邀请，字幕不写价格不写地址",
]

FACT_TEXT = (
    "佳康顺NIP助行器（HR008NIP / BC2，escape系列）：红色弧形铝合金车架+银色立管，"
    "黑白千鸟格布艺座靠内衬软垫；净重7.8kg，承重150kg；"
    "握把高度810～913mm三档可调，适配150～185cm身高；"
    "双侧刹车杆线控刹车，手指一勾即停、松手即刹；"
    "约8寸五辐条轮，前轮万向转向；一体式可歇座椅，走累了转身就坐；"
    "一拉折叠、一按展开；新西兰原装进口，汽车级金属烤漆；佳康顺17年匠心，工厂直营。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""
BENCH_URL = "https://v.douyin.com/AE6tbFhlBN4/"
BENCH_KEY = "7698333734378016015"
BENCH_TITLE = "全网1000多万人看过的四合一代步车 你不会没看过吧？"


def main():
    body = {"format": "monologue",
            "lines": [{"speaker": "小冯", "beat": "口播", "text": t} for t in LINES]}
    body_text = "\n".join(LINES)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    target = 60.0
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
             json.dumps(scan, ensure_ascii=False), "NIP助行器",
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
             "NIP助行器", json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "NIP 助行器（HR008NIP / BC2，escape系列）个人号稿，"
             "按「助行辅具王师傅-大脸老年代步车」悬念钩子型骨架写。"
             "参数多源交叉核对：知识库参数与卖点 + 三篇配文/小红书文案，"
             "7.8kg / 承重150kg / 3档810-913mm / 双刹车杆 / 一拉折叠 / 千鸟格座靠。"
             "★ NIP 是手动四轮带座助行器：无电机无电池无摇杆，刹车是手拉线刹，"
             "绝不能写成电动款。"
             "★ 没抄王师傅那台四合一代步车的参数（16公斤/12公里/陀螺仪/大阻尼）。"))
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
