"""品牌号 SG-20261020-012：贴对标原句改写（抖音·皮皮熊电动轮椅）。

对标（皮皮熊医疗器械旗舰店，27 秒 / 130 字）逐句：
  电动的太难学，我才不要呢。          ← 女儿/儿子的抗拒
  不！
  新车下坡松手就停，旧车两把手都杀不住。   ← 新旧对比①：刹车
  我一个人咋上都去坡？                ← 疑问
  新车摇杆一推就能上，旧车手搓肿了都上不去，还容易摔。  ← 新旧对比②：动力
  这么窄的路指定重车。                ← 质疑
  新车推摇杆就能转弯，很轻松。          ← 新旧对比③：操控
  旧车得使劲掰轮子，胳膊都酸啦。
  原来学电动轮椅这么简单呢？           ← 认知反转
  只有试试才知道。                     ← 结尾（无 CTA 无地址）

改法：保留「新旧对比」结构和「只有试试才知道」的结尾，替换成 F2Q 的真实卖点：
  刹车 → 智能电磁刹车（松开即刹，断电也能刹）
  上坡 → 240W 无刷电机（美国 PRIDE 同款），轻松爬坡
  转弯 → 环形把手 + 移动拨杆，反应灵敏
  窄路 → 9 寸大轮 + 折叠 44cm 宽
所有参数逐字回查知识库，不编。

品牌号人设：心悦提问、小冯实操；一条只讲一个客户真问题。
但本篇对标本身是「新旧对比」结构，就按对标走（贴原句优先）。
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

TITLE = "原来学电动代步车这么简单"

PAIRS = [
    ("心悦", "钩子", "电动的太难学，我可不要。"),
    ("小冯", "回应", "不，试试才知道。"),
    ("小冯", "演示", "您看，下坡我一松手就停住了。"),
    ("心悦", "提问", "电磁刹车？断电也能刹住？"),
    ("小冯", "回应", "断电也能刹住。"),
    ("心悦", "再问", "那您一个人能上坡不？"),
    ("小冯", "回应", "二百四的无刷电机，摇杆一推就上去了，不用人推。"),
    ("心悦", "质疑", "这么窄的路，您这车过得去不？"),
    ("小冯", "回应", "折起来才四十四公分宽，推摇杆转弯也灵活。"),
    ("心悦", "收尾", "原来学电动代步车这么简单呢？"),
    ("小冯", "回应", "只有试试才知道。"),
]

TIPS = [
    "开场心悦一脸嫌弃地说「太难学」，反差感要足",
    "小冯边说边演示：松手停住、摇杆上坡、推把手转弯，动作要连贯",
    "讲刹车时给车头特写，松开手柄停住的瞬间要拍清",
    "讲上坡时用坡道实拍，摇杆一推车就上去了",
    "讲窄路时拍车从门缝/窄道通过的镜头",
    "结尾两人对视一下，不加 CTA",
    "字幕可标 44 公分这类关键数字，不写价格",
]

FACT_TEXT = (
    "F2Q轻便折叠旅游代步车10AH锂电："
    "展开尺寸105×54×90CM 折叠尺寸高度98CM宽度44CM 净重19KG 最大载重125KG "
    "电机240W高效无刷电机(美国PRIDE同款) 电池10AH安规锂电池 "
    "智能电磁刹车(松开即刹 断电也能刹 坡上不溜车) 陡坡自动匀速AI控速 "
    "轻松爬坡 轻松过弯 反应灵敏精准反应操作 直角都能灵活过 "
    "环形把手控制面板(移动拨杆控制前进/电源开关OFF-ON/速度调节旋钮/电量显示/喇叭) "
    "拨杆向上手动模式可推行 拨杆向下电动模式自动行驶 "
    "双重弹簧减震+悬浮减震 升级免维护实心大轮9寸(防爆防扎 轻松越坎) "
    "一拉即折叠(专利设计 按钮往外一拉一压完成折叠 专利号ZL2020 2 092755.4) "
    "高靠背 宽大脚踏板 底部购物篮 前置高亮大灯 防倾倒后轮 佳康顺18年"
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

    code = "SG-20261020-012"
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
             json.dumps(["小冯", "心悦"], ensure_ascii=False), "douyin",
             "7684168037901094150", "https://v.douyin.com/52CXOjhs8Fs/",
             "这么好学的电动轮椅，爸妈一学就会#皮皮熊电动轮椅 #电动轮椅 #老人 #轮椅 #轮椅出行",
             "F2Q",
             json.dumps(["jks-product/F2Q轻便折叠旅游代步车10AH锂电-产品详细信息-9a454f.txt"],
                        ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "贴对标「新旧对比」结构改写：刹车/上坡/转弯三项换成 F2Q 真实卖点，"
             "结尾保留「只有试试才知道」；参数逐字回查知识库"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 27s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
