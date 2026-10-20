"""F2Q 品牌号 5 篇（013-017）：沿用 012 的「新旧对比」结构。

012 的结构模板（贴对标皮皮熊）：
  心悦抗拒钩子 → 小冯「不，试试才知道」→ 小冯演示
  → 心悦提问 / 小冯回应（×3 轮质疑打脸）
  → 心悦「原来这么简单呢」→ 小冯「只有试试才知道」

这 5 篇换 5 个不同场景，每篇打脸 3 个点：
  013 夜路出行   —— 大灯 / 座高 / 视野
  014 买菜拎货   —— 购物篮 / 踏板 / 载重
  015 久坐腰酸   —— 高靠背 / 减震弹簧座椅 / 皮革坐垫
  016 手动电动   —— 拨杆上下切换 / 拖行 / 折叠
  017 一个人搬   —— 19KG / 折叠尺寸 / 后备箱

所有参数逐字回查公司知识库（F2Q 详细资料），不编。
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
T013 = "原来夜路出行有灯照着"
P013 = [
    ("心悦", "钩子", "晚上出门黑灯瞎火的，我可不敢。"),
    ("小冯", "回应", "不，试试才知道。"),
    ("小冯", "演示", "您看，这车前面有个大亮灯。"),
    ("心悦", "提问", "这灯亮不亮？"),
    ("小冯", "回应", "前置高亮大灯，路面照得清清亮亮。"),
    ("心悦", "再问", "那坐高了，是不是看得更远？"),
    ("小冯", "回应", "座高四十九公分，坐直了前面看得清楚。"),
    ("心悦", "质疑", "晚上走黑路，脚下看不清咋办？"),
    ("小冯", "回应", "前头高亮大灯照着，脚底下不黑。"),
    ("心悦", "收尾", "原来夜路出行有灯照着，心里踏实多了。"),
    ("小冯", "回应", "只有试试才知道。"),
]

# ---------------------------------------------------------------- #
T014 = "原来买菜不用人帮着拎"
P014 = [
    ("心悦", "钩子", "买完菜还得人拎，我可不干。"),
    ("小冯", "回应", "不，试试才知道。"),
    ("小冯", "演示", "您看，这车底下有个篮子。"),
    ("心悦", "提问", "能装多少？"),
    ("小冯", "回应", "菜啊瓜果搁里头正好，不用提在手上。"),
    ("心悦", "再问", "脚搁哪儿？"),
    ("小冯", "回应", "宽大脚踏板，两只脚放着稳当，还防滑。"),
    ("心悦", "质疑", "东西多了压得住吗？"),
    ("小冯", "回应", "最大载重一百二十五公斤，放心坐。"),
    ("心悦", "收尾", "原来买菜不用人帮着拎了。"),
    ("小冯", "回应", "只有试试才知道。"),
]

# ---------------------------------------------------------------- #
T015 = "原来坐久了也能坐得住"
P015 = [
    ("心悦", "钩子", "坐久了腰酸得要命，我受不了。"),
    ("小冯", "回应", "不，试试才知道。"),
    ("小冯", "演示", "您往椅背上一靠，试试这感觉。"),
    ("心悦", "提问", "靠背挺得住不？"),
    ("小冯", "回应", "高靠背设计，撑住腰背，不往前塌。"),
    ("心悦", "再问", "坐垫硬不硬？"),
    ("小冯", "回应", "皮革高回弹的，防水好擦，也不硌人。"),
    ("心悦", "质疑", "路上颠久了呢？"),
    ("小冯", "回应", "座椅带减震弹簧，久坐也不那么累。"),
    ("心悦", "收尾", "原来坐久了也能坐得住。"),
    ("小冯", "回应", "只有试试才知道。"),
]

# ---------------------------------------------------------------- #
T016 = "原来电的能推、手动能开"
P016 = [
    ("心悦", "钩子", "万一没电了，那不趴窝了？"),
    ("小冯", "回应", "不，试试才知道。"),
    ("小冯", "演示", "您看这个拨杆，往上一推。"),
    ("心悦", "提问", "往上是怎么了？"),
    ("小冯", "回应", "手动模式，推着就能走。"),
    ("心悦", "再问", "往下呢？"),
    ("小冯", "回应", "往下就是电动，一推就走。"),
    ("心悦", "质疑", "不能开的地方怎么办？"),
    ("小冯", "回应", "折起来拖着走，抬也抬得动。"),
    ("心悦", "收尾", "原来电的手动的都能用。"),
    ("小冯", "回应", "只有试试才知道。"),
]

# ---------------------------------------------------------------- #
T017 = "原来一个人也能搬上车"
P017 = [
    ("心悦", "钩子", "这么沉，我一个人搬得动吗？"),
    ("小冯", "回应", "不，试试才知道。"),
    ("小冯", "演示", "您看，一拉就折起来了。"),
    ("心悦", "提问", "折完多重？"),
    ("小冯", "回应", "十九公斤，跟个行李箱差不多。"),
    ("心悦", "再问", "塞得进后备箱不？"),
    ("小冯", "回应", "高度九十八，宽四十四，搁后备箱正好。"),
    ("心悦", "质疑", "天天拎来拎去的，累不累？"),
    ("小冯", "回应", "折叠不占地，扔后备箱里就成。"),
    ("心悦", "收尾", "原来一个人也能搬上车。"),
    ("小冯", "回应", "只有试试才知道。"),
]

SCRIPTS = [
    ("SG-20261020-013", T013, P013, "夜路出行",
     ["前置高亮大灯", "座位高度49.5CM", "视野"]),
    ("SG-20261020-014", T014, P014, "买菜拎货",
     ["底部购物篮", "宽大脚踏板防滑", "最大载重125KG"]),
    ("SG-20261020-015", T015, P015, "久坐腰酸",
     ["高靠背支撑腰背", "皮革高回弹防水坐垫", "减震弹簧座椅"]),
    ("SG-20261020-016", T016, P016, "手动电动切换",
     ["拨杆向上手动可推行", "拨杆向下电动自动行驶", "一拖即走/折叠不占地"]),
    ("SG-20261020-017", T017, P017, "一个人搬上车",
     ["一拉即折叠", "净重19KG", "折叠尺寸98×44CM/放后备箱"]),
]

FACT_TEXT = (
    "F2Q轻便折叠旅游代步车10AH锂电："
    "展开尺寸105×54×90CM 折叠尺寸高度98CM宽度44CM 净重19KG(不含电池扶手坐垫) "
    "最大载重125KG 座位高49.5CM 宽37.5CM 深36CM 前轮18CM后轮21.5CM(9寸大轮) "
    "电机240W高效无刷电机(美国PRIDE同款) 电池10AH安规锂电池 "
    "智能电磁刹车(松开即刹 断电也能刹) 陡坡自动匀速AI控速 轻松爬坡 轻松过弯 "
    "环形把手控制面板(移动拨杆控制前进/电源开关OFF-ON/速度调节旋钮/电量显示/喇叭) "
    "拨杆向上手动模式可推行 拨杆向下电动模式自动行驶 一拖即走 "
    "一拉即折叠(专利设计 按钮往外一拉一压完成折叠 专利号ZL2020 2 092755.4) "
    "折叠收纳不占地 轻松放入汽车后备箱 不能行驶的区域可拖行 "
    "双重弹簧减震+悬浮减震 升级免维护实心大轮9寸(防爆防扎) "
    "底部购物篮(外出携带物品 购物可放蔬菜瓜果) 可调节车头 "
    "前置高亮大灯(夜晚出行看清路面) 防倾倒后轮 舒适扶手皮革包裹 "
    "高靠背设计(支撑腰背 久坐不累) 宽大脚踏板(双脚放置舒适 防滑设计) "
    "高回弹防水皮革坐垫 减震弹簧座椅(老年人腰部易酸痛 加入减震弹簧缓解疲劳) "
    "航空铝合金车架 佳康顺18年 孩子孝爸妈笑"
)


def build_tips(feature):
    return [
        "开场%s由心悦带着情绪说「太…我可不要」，反差要足" % feature,
        "小冯边说边演示，三次演示分别配三个不同机位",
        "讲到关键数字时给特写（车头/底部/靠背/拨杆/折叠动作）",
        "两人对话节奏要快，一问一答，别让一方说长段",
        "结尾两人对视一下，不加 CTA，不加地址",
        "字幕可标 19 公斤、44 公分这类关键数字，不写价格",
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
        exists = con.execute("SELECT id FROM sg_scripts WHERE code=?", (code,)).fetchone()
        if exists:
            con.execute(
                "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
                "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
                "compliance_json=?, version=version+1, updated_at=? WHERE code=?",
                (title, json.dumps(body, ensure_ascii=False), body_text, wc, sec,
                 30.0, json.dumps(tips, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), now, code))
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
                 "7684168037901094150", "https://v.douyin.com/52CXOjhs8Fs/",
                 "这么好学的电动轮椅，爸妈一学就会#皮皮熊电动轮椅 #电动轮椅 #老人 #轮椅 #轮椅出行",
                 "F2Q",
                 json.dumps(["jks-product/F2Q轻便折叠旅游代步车10AH锂电-产品详细信息-9a454f.txt"],
                            ensure_ascii=False),
                 title, json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, 30.0, 1, "型号",
                 "沿用 012 的「新旧对比」结构：%s；打脸点=%s；参数逐字回查知识库"
                 % (feature, "、".join(points))))
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
