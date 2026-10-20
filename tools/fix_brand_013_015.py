"""F2Q 品牌号 013/014/015 换稿（用户反馈 5/6/7 不行）。

被换掉的三篇：
  013 原来夜路出行有灯照着   → 改为「车头能调，个子矮也能开」
  014 原来买菜不用人帮着拎   → 改为「陡坡不往后仰」
  015 原来坐久了也能坐得住   → 改为「电池能拎出来充」

理由：原来那三个场景（夜路/买菜/久坐）偏泛，观众代入感弱；换成
**F2Q 独有、别人答不上来的具体功能**，更能体现产品差异。

结构沿用 012 的「新旧对比」模板：
  心悦抗拒钩子 → 小冯「不，试试才知道」→ 演示
  → 三轮质疑打脸 → 「原来…」→「只有试试才知道」

所有参数逐字回查公司知识库，不编。
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

# ---------------------------------------------------------------- #
# 013 → 可调节车头（适合不同身高）
# ---------------------------------------------------------------- #
T013 = "原来矮个子也能开"
P013 = [
    ("心悦", "钩子", "我这么矮，够得着这车吗？"),
    ("小冯", "回应", "不，试试才知道。"),
    ("小冯", "演示", "您看，这个车头能上下调。"),
    ("心悦", "提问", "能调多少？"),
    ("小冯", "回应", "按您身量调，调好了手正好搭得上。"),
    ("心悦", "再问", "调完了坐着硌不硌？"),
    ("小冯", "回应", "座椅有减震弹簧，靠背也撑得住腰。"),
    ("心悦", "质疑", "那调完还能不能折？"),
    ("小冯", "回应", "照折不误，一拉就折好。"),
    ("心悦", "收尾", "原来矮个子也能开。"),
    ("小冯", "回应", "只有试试才知道。"),
]

# ---------------------------------------------------------------- #
# 014 → 防倾倒后轮（爬坡不后仰）
# ---------------------------------------------------------------- #
T014 = "原来陡坡不往后仰"
P014 = [
    ("心悦", "钩子", "以前那车一上陡坡就往后仰，吓得我不敢上。"),
    ("小冯", "回应", "不，试试才知道。"),
    ("小冯", "演示", "您看这后轮，往后翘着一块。"),
    ("心悦", "提问", "翘着干嘛用的？"),
    ("小冯", "回应", "防倾倒后轮，坡太陡能撑住，不往后翻。"),
    ("心悦", "再问", "那坡上停了溜不溜？"),
    ("小冯", "回应", "电磁刹车，松手就停住。"),
    ("心悦", "质疑", "上坡动力够吗？"),
    ("小冯", "回应", "二百四的无刷电机，摇杆一推就上去了。"),
    ("心悦", "收尾", "原来陡坡不往后仰。"),
    ("小冯", "回应", "只有试试才知道。"),
]

# ---------------------------------------------------------------- #
# 015 → 安规电池 + 六重保护 + 可提取充电
# ---------------------------------------------------------------- #
T015 = "原来电池能拎出来充"
P015 = [
    ("心悦", "钩子", "电池还得整台推去充，太麻烦了。"),
    ("小冯", "回应", "不，试试才知道。"),
    ("小冯", "演示", "您看，电池一抠就下来了。"),
    ("心悦", "提问", "拎去哪儿充？"),
    ("小冯", "回应", "拎回家插上就行，车上也能直接充。"),
    ("心悦", "再问", "这电池安全吗？"),
    ("小冯", "回应", "安规锂电，六重保护，过充过压过流都管着。"),
    ("心悦", "质疑", "能充多久啊？"),
    ("小冯", "回应", "十安时的锂电，一天买菜转公园够了。"),
    ("心悦", "收尾", "原来电池能拎出来充。"),
    ("小冯", "回应", "只有试试才知道。"),
]

SCRIPTS = [
    ("SG-20261020-013", T013, P013, "车头可调节（不同身高）",
     ["可调节车头适合不同身高", "减震弹簧座椅+高靠背", "一拉即折叠不受影响"]),
    ("SG-20261020-014", T014, P014, "陡坡防后仰",
     ["防倾倒后轮防止爬坡后倾", "智能电磁刹车", "240W无刷电机爬坡"]),
    ("SG-20261020-015", T015, P015, "电池可提取",
     ["电池一键提取单独充电/车上直充", "安规锂电六重保护", "10AH锂电续航"]),
]

FACT_TEXT = (
    "F2Q轻便折叠旅游代步车10AH锂电："
    "展开尺寸105×54×90CM 折叠尺寸高度98CM宽度44CM 净重19KG 最大载重125KG "
    "座位高49.5CM 宽37.5CM 深36CM 前轮18CM后轮21.5CM(9寸大轮) "
    "电机240W高效无刷电机(美国PRIDE同款) 电池10AH安规锂电池 "
    "智能电磁刹车(松开即刹 断电也能刹 坡上不溜车) 陡坡自动匀速 轻松爬坡 轻松过弯 "
    "环形把手控制面板(移动拨杆/电源开关/速度旋钮/电量显示/喇叭) "
    "拨杆向上手动可推行 拨杆向下电动自动行驶 一拖即走 "
    "一拉即折叠(专利 按钮往外一拉一压完成折叠 专利号ZL2020 2 092755.4) "
    "底部购物篮 可调节车头(适合不同身高人群 随需求调节高度) "
    "前置高亮大灯 防倾倒后轮(防止车子爬坡时因角度过大后倾导致的摔倒) "
    "舒适扶手皮革包裹 高靠背设计(支撑腰背 久坐不累) 宽大脚踏板(防滑) "
    "高回弹防水皮革坐垫 减震弹簧座椅(缓解腰部疲劳) 航空铝合金车架 "
    "安规电池六重安全保护(过压/过充/过流/过温/过放/短路) "
    "电池一键提取(可直接提取电池单独充电 也可车上免弯腰直冲) 佳康顺18年"
)


def build_tips(feature):
    return [
        "开场讲%s的顾虑，态度要像真在犯愁" % feature,
        "小冯边说边演示，三次演示配三个不同机位，动作要连贯",
        "讲到关键数字时给特写（车头/后轮/电池/折叠动作）",
        "两人对话节奏要快，一问一答，别让一方说长段",
        "结尾两人对视一下，不加 CTA，不加地址",
        "字幕可标 19 公斤、10 安时这类关键数字，不写价格",
    ]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    disclaimer = util.compliance_config().get("disclaimer") or ""
    now = util.now_iso()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    results = []

    for code, title, pairs, feature, points in SCRIPTS:
        body = {"format": "dialogue",
                "lines": [{"speaker": s, "beat": b, "text": t} for s, b, t in pairs]}
        body_text = body_plain_text(body)
        spoken = util.strip_speakers(body_text)
        wc = util.count_chars(spoken)
        sec = util.estimate_seconds(spoken)
        scan = compliance.scan_script(body_text, {"disclaimer": disclaimer},
                                     "", FACT_TEXT, [])
        tips = build_tips(feature)
        con.execute(
            "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
            "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
            "compliance_json=?, version=version+1, updated_at=?, "
            "notes=? WHERE code=?",
            (title, json.dumps(body, ensure_ascii=False), body_text, wc, sec, 30.0,
             json.dumps(tips, ensure_ascii=False), json.dumps(scan, ensure_ascii=False),
             now,
             "沿用 012 新旧对比结构：%s；打脸点=%s；参数逐字回查知识库"
             % (feature, "、".join(points)), code))
        results.append((code, title, wc, sec, scan))
    con.commit()
    con.close()

    for code, title, wc, sec, scan in results:
        print("=" * 60)
        print("%s ｜ %s" % (code, title))
        print("%d 字 / %.1f 秒 ｜ 合规 %s" % (wc, sec, scan.get("counts")))
        print("-" * 60)
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        r = dict(con.execute("SELECT body_md FROM sg_scripts WHERE code=?", (code,)).fetchone())
        con.close()
        print(r["body_md"])
        for f in scan.get("findings") or []:
            print("  [%s] %s ｜「%s」｜ %s" % (
                f.get("severity"), f.get("rule_id"), f.get("match"),
                f.get("suggest") or ""))
        print()


if __name__ == "__main__":
    main()
