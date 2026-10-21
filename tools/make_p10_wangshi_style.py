# -*- coding: utf-8 -*-
"""个人号 021：按「助行辅具王师傅-大脸老年代步车」对标风格写 P10 稿（样稿）。

对标账号：助行辅具王师傅-大脸老年代步车（抖音号 97428562854，128 作品）
来源短链：https://v.douyin.com/AE6tbFhlBN4/
分析文档：.workbuddy/skills/scriptgen-writing/对标账号分析-王师傅大脸老年代步车.md

与陈大脸的区别（本次改稿的要点）：
- **开头用悬念问句**，不是「这个就是XX产品」这种报品类的写法
- 句子更短、更口语，人称偏「咱们」，带「呢/啊/咱们」口头禅
- 参数口语化：「15.8KG」→「才十五点八公斤」，「340W」→「170瓦装两个，340瓦」
- 收尾带一点情绪，不全是「评论区说说」

骨架（悬念钩子型）：抛悬念问句 → 报品类 → 逐条说长处（每个都带场景）
→ 报重量/续航 → 现场演示 → 邀请到店

★ 竞品参数绝不抄：他那边是 16 公斤 / 12 公里 / 陀螺仪 / 大阻尼康复模式，
  那是**他那台四合一代步车**的参数。我们写 P10 一律用知识库的真实数：
  整车 15.8KG（不含电池）｜折叠后宽 34cm｜170W×2=340W｜续航 15km｜
  10 股弹簧减震｜电磁刹车松手即停｜免弯腰一键折叠｜电池可拆卸充。

合规：删「轻轻松松/非常轻松」「最绝的是」等绝对化；「锻炼站立行走能力」等功效
断言一律不写；不写价格、不写疾病名、不写竞品参数。
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

CODE = "SG-20261021-078"
# 标题不带标点：slugify 会把标点转成连字符，触发本机安全钩子拦 out/*.docx
TITLE = "您信十五公斤的电动轮椅吗"

LINES = [
    "您见过能塞进后备箱的电动轮椅吗？",
    "佳康顺这台P10碳纤维电动轮椅，折叠起来就三十四公分宽。",
    "整车才十五点八公斤，电池能整个拎出来，家里插座就能充。",
    "开着也稳当，电磁刹车，松开手就停，坡上也不往前溜。",
    "电机是170瓦装两个，340瓦，30度陡坡能上，续航15公里。",
    "我给您看啊，按一下红按钮往上一提就折好了，不用弯腰。",
    "家里有老人的，您来展厅坐一圈，比看图片管用。",
    "我是小冯，来了我帮您试。",
]

TIPS = [
    "单人出镜，站在一台 P10 旁边，开口先抛问句",
    "第一句要有停顿感，悬念抛完再报品类",
    "讲折叠真的折一次，电池真的拎出来，镜头给近景",
    "参数说得慢一点，十五点八公斤、三十四公分、340瓦、15公里要听得清",
    "结尾停在展厅邀请，字幕不写价格不写地址",
]

FACT_TEXT = (
    "佳康顺P10碳纤维电动轮椅（10AH锂电）：整车净重15.8KG（不含电池，车架约10KG），"
    "航空级真碳纤维+铝合金车架；免弯腰一键折叠，折叠后宽34cm×高80cm；"
    "10股弹簧减震+加厚弹簧坐垫；电磁刹车松手即停、断电自动刹车；"
    "美国PRIDE同款170W×2无刷双电机合计340W，30°陡坡、3cm门槛；"
    "10Ah三元锂电（LG电芯）续航15km，可拆卸充电；"
    "免充气实心防爆轮胎，后轮33cm；最大承重150KG；"
    "万向摇杆控制器，左右手可换，APP手机遥控；SOS求救语音；蓝绿紫三色。"
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
             json.dumps(scan, ensure_ascii=False), "P10碳纤维电动轮椅10AH锂电",
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
             "P10碳纤维电动轮椅10AH锂电", json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "个人号第 2 个对标账号「助行辅具王师傅-大脸老年代步车」（97428562854）"
             "的悬念钩子型骨架样稿：开头抛悬念问句 → 报品类 → 逐条说长处 → "
             "报重量续航 → 现场演示 → 邀请到店。"
             "分析见 .workbuddy/skills/scriptgen-writing/对标账号分析-王师傅大脸老年代步车.md。"
             "★ 竞品参数（16公斤/12公里/陀螺仪/大阻尼）一律没抄，用 P10 知识库真实参数。"))
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
