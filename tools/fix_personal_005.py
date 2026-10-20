"""品牌号 第 2 篇（编号 005）：贴对标原句改写（抖音·爱优护电动轮椅）。

账号：品牌号（单人口播 · 小冯）—— 品牌号也支持一个人拍，不必双人对话。

对标（爱优护电动代步车，15.6s / 78 字）：
  没想到，他的上班坐驾这么特别，竟然是一台电动代步车，
  车身一拉就能快速展开，从侧面上车更加轻松省力，
  操作简单，坐上就能直接开走，
  日常短途出行也不用总麻烦家人。
作者：爱优护电动代步车 ｜ 品类：电动轮椅/代步车

改法（逐句贴骨架，只换近义词 + 换地点 + 替品类）：
  没想到 → 真没想到
  他的上班坐驾这么特别 → 街坊的通勤车这么讲究
  竟然是一台电动代步车 → 竟然是台电动轮椅
  车身一拉就能快速展开 → 车往那儿一架就拉开了
  从侧面上车更加轻松省力 → 侧面坐上去省劲多了
  操作简单 → 开起来简单
  坐上就能直接开走 → 坐好就走
  日常短途出行也不用总麻烦家人 → 平常出门买菜接娃，不用再麻烦家里人

账号口径：
  品牌号，单人出镜（小冯）。30-45 秒 / 150-240 字。
  CTA 落展厅地址（合规 contact 规则禁「加微信」）。
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

TITLE = "真没想到，街坊的通勤车这么讲究"

LINES = [
    "真没想到，街坊的通勤车这么讲究，竟然是台电动轮椅。",
    "车往那儿一架就拉开了，不用蹲着收，也不用撂倒。",
    "侧面坐上去省劲多了，腿不用使劲蹬。",
    "开起来简单，摇一摇就走，不用学。",
    "坐好就走，平常出门买菜接娃，都不用再麻烦家里人。",
    "有位阿姨跟我说，早先出门得麻烦人，现在自己就能出去转转了。",
    "您要是也想要一台，别光看照片，来展厅坐一坐、试一圈最实在。",
    "我是小冯，在苏州阳光大厦九一一室，来了我帮您试。",
]

TIPS = [
    "开场站在一台展开的轮椅旁边，一手指向它，带点惊讶的口气",
    "讲「一拉就开」时给完整动作特写：拉开 → 展开，一气呵成",
    "讲侧面坐上去时拍侧面角度的动作，别只说",
    "讲「不用麻烦家里人」时语气转柔，可以配子女陪行的画面",
    "中间提到阿姨的话时，可切一镜顾客试坐的实拍（要本人同意出镜）",
    "结尾镜头带到展厅门牌，小冯抬手示意",
    "字幕突出「苏州阳光大厦九一一室」，不写价格",
]

FACT_TEXT = (
    "F2Q轻便折叠旅游代步车：折叠尺寸 高度98CM 宽度44CM 净重19KG "
    "电机240W高效无刷电机 电池10AH锂电 最大载重125KG "
    "一键折叠/一拉即折叠（专利设计 按钮往外一拉一压完成折叠 专利号ZL2020 2 092755.4）"
    "可调节车头 防倾倒后轮 高靠背 宽大脚踏板 底部购物篮"
)


def main():
    body = {"format": "monologue",
            "lines": [{"speaker": "小冯", "beat": "口播", "text": t} for t in LINES]}
    body_text = body_plain_text(body)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    disclaimer = util.compliance_config().get("disclaimer") or ""
    scan = compliance.scan_script(body_text, {"disclaimer": disclaimer}, "", FACT_TEXT, [])

    code = "SG-20261020-005"
    # 品牌号人设 30-45 秒；对标 15.6 秒低于下限 → 目标取人设下限 30 秒
    target = 30.0
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
             json.dumps(["小冯"], ensure_ascii=False), "douyin",
             "7670093302795980066", "https://v.douyin.com/14bsXXYzpZk",
             "你见过这么高级的座驾吗？#爱优护电动轮椅 #电动轮椅 #关爱老人",
             None, json.dumps([], ensure_ascii=False), TITLE,
             json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "品牌号小冯单人口播（品牌号也支持单人拍），贴对标「通勤车讲究」骨架逐句改写；"
             "真实场景+展厅细节+朴实邀请，产品品类通用不绑型号"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 15.6s，真目标 %.1fs）｜ 合规 %s" % (
        wc, sec, target, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
