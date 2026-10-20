"""F2Q 品牌号 5 篇（编号 007-011）：一问一答，各讲一个客户真问题。

素材来源：config/personas.json 的 brand 人设 + 公司知识库
  jks-product/F2Q轻便折叠旅游代步车10AH锂电-产品详细信息-9a454f.txt
所有产品参数与动作描述**逐字回查知识库**，不编。

品牌号人设：
  心悦：亲和、专业、会接话，负责提出疑问和总结判断
  小冯：朴实、动手能力强，负责实操、演示和补关键体验
  一问一答；「每条只讲一个客户真问题，不堆功能点」
  30-45 秒 / 150-240 字；CTA 到店试车
  品牌号也可单人出镜（用户确认过），这 5 篇统一用双人问答 —— 品牌号
  天然适合「客户提问 + 店员演示」，且便于实拍动作。

长度：参照现有品牌号稿 003（对标 25.4s → 成稿 25s / 105字），
      这 5 篇按 30-45 秒区间控制在 130-190 字。

分号原则：**一条只讲一个问题**，不叠加别的卖点。
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
# 007 折叠收纳
# ---------------------------------------------------------------- #
T007 = "这车折起来，能塞进后备箱吗"
P007 = [
    ("心悦", "提问", "很多叔叔阿姨第一句话就问，这车折起来放得下吗？"),
    ("小冯", "演示", "来，您看，按钮往外一拉，一压就折好了。"),
    ("心悦", "追问", "折完多重？"),
    ("小冯", "回应", "十九公斤，跟个行李箱差不多。"),
    ("心悦", "追问", "塞得进后备箱不？"),
    ("小冯", "回应", "高度九十八，宽四十四，放后备箱绰绰有余。"),
    ("心悦", "判断", "所以这种能折的，关键看折完多大、多沉。"),
    ("小冯", "回应", "拎不动也没事，不能开的时候拖着走就行。"),
]

# ---------------------------------------------------------------- #
# 008 上下坡
# ---------------------------------------------------------------- #
T008 = "上下坡这车，稳得住吗"
P008 = [
    ("心悦", "提问", "上下坡这车，稳得住吗？"),
    ("小冯", "演示", "下坡您松手就停住了，不往前冲。"),
    ("心悦", "追问", "坡上停会不会溜？"),
    ("小冯", "回应", "电磁刹车，断电也能刹住。"),
    ("心悦", "再追问", "上坡呢，动力够吗？"),
    ("小冯", "回应", "二百四的无刷电机，爬坡不吃力。"),
    ("心悦", "判断", "所以坡道多的地方，得看刹车和动力两样。"),
    ("小冯", "回应", "下坡还有个自动匀速，系统会帮着控速。"),
]

# ---------------------------------------------------------------- #
# 009 续航
# ---------------------------------------------------------------- #
T009 = "这车能跑多远，电够不够"
P009 = [
    ("心悦", "提问", "这车能跑多远，电够不够？"),
    ("小冯", "演示", "十安时的锂电，一天出门买菜转公园够了。"),
    ("心悦", "追问", "电还剩多少，怎么知道？"),
    ("小冯", "回应", "把手上有个电量表，低到满一眼就看出来。"),
    ("心悦", "再追问", "没电了能充不？"),
    ("小冯", "回应", "电池能整个提出来，拎回去充。"),
    ("心悦", "判断", "所以买这种车，续航和充电池方不方便，都得问。"),
    ("小冯", "回应", "电池有六重保护，充电也放心。"),
]

# ---------------------------------------------------------------- #
# 010 路面颠簸
# ---------------------------------------------------------------- #
T010 = "路面不平，颠不颠人"
P010 = [
    ("心悦", "提问", "路面不平的地方，颠不颠人？"),
    ("小冯", "演示", "您感受一下，前头是双弹簧减震。"),
    ("心悦", "追问", "石子路上呢？"),
    ("小冯", "回应", "车头跟着地面起伏走，轮子一直贴着地。"),
    ("心悦", "再追问", "轮子扎胎怎么办？"),
    ("小冯", "回应", "实心大轮，不扎胎，九寸的过坎也稳。"),
    ("心悦", "判断", "所以小区石子路、减速带多的话，看减震和轮胎。"),
    ("小冯", "回应", "坐垫也是高回弹的，屁股没那么硌。"),
]

# ---------------------------------------------------------------- #
# 011 上手操作
# ---------------------------------------------------------------- #
T011 = "不会骑车，也能上手开吗"
P011 = [
    ("心悦", "提问", "不会骑车的人，也能上手开吗？"),
    ("小冯", "演示", "来您看，这个环形把手，往前一推就走。"),
    ("心悦", "追问", "这个开关呢？"),
    ("小冯", "回应", "开关一按就开机，旋钮调快慢，喇叭在这儿。"),
    ("心悦", "再追问", "手能握得住吗？"),
    ("小冯", "回应", "扶手是皮革包的，握着不硌手。"),
    ("心悦", "判断", "所以挑车的时候，得让老人自己上手试一回。"),
    ("小冯", "回应", "坐上来开两圈，什么感觉当场就知道。"),
]

SCRIPTS = [
    ("SG-20261020-007", T007, P007),
    ("SG-20261020-008", T008, P008),
    ("SG-20261020-009", T009, P009),
    ("SG-20261020-010", T010, P010),
    ("SG-20261020-011", T011, P011),
]

FACT_TEXT = (
    "F2Q轻便折叠旅游代步车10AH锂电："
    "展开尺寸105×54×90CM 折叠尺寸高度98CM宽度44CM 净重19KG(不含电池扶手坐垫) "
    "最大载重125KG 座位高49.5CM 宽37.5CM 深36CM 前轮18CM后轮21.5CM(9寸大轮) "
    "电机240W高效无刷电机(美国PRIDE同款) 电池10AH安规锂电池 "
    "一拉即折叠(专利设计 按钮往外一拉一压完成折叠 专利号ZL2020 2 092755.4) "
    "一拖即走 智能电磁刹车(松开即刹断电也能刹) 陡坡自动匀速AI控速 "
    "双重弹簧减震+悬浮减震 升级免维护实心大轮(防爆防扎) 环形把手控制面板 "
    "(移动拨杆/电源开关OFF-ON/速度调节旋钮/电量显示E到F/喇叭按钮) "
    "电池一键提取可单独充电 六重电池保护(过压过充过流过温过放短路) "
    "高回弹防水皮革坐垫 减震弹簧座椅 航空铝合金车架 可调节车头 "
    "高靠背 宽大脚踏板 底部购物篮 前置高亮大灯 防倾倒后轮 "
    "佳康顺18年医疗器械 孩子孝爸妈笑"
)

TIPS_TMPL = [
    "开场心悦先提问，镜头给到那台{FEATURE}的车",
    "小冯回答时必须配实拍动作，不能只说",
    "讲到关键数字时给特写（车架/把手/车轮/折叠动作）",
    "两人对话节奏要快，一问一答，别让一方说长段",
    "结尾两人一起看镜头，不用加 CTA",
    "字幕可标关键数字，不写价格",
]


def build_tips(feature):
    return [t.replace("{FEATURE}", feature) for t in TIPS_TMPL]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    disclaimer = util.compliance_config().get("disclaimer") or ""
    now = util.now_iso()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    results = []

    for code, title, pairs in SCRIPTS:
        body = {"format": "dialogue",
                "lines": [{"speaker": s, "beat": b, "text": t} for s, b, t in pairs]}
        body_text = body_plain_text(body)
        spoken = util.strip_speakers(body_text)
        wc = util.count_chars(spoken)
        sec = util.estimate_seconds(spoken)
        scan = compliance.scan_script(body_text, {"disclaimer": disclaimer},
                                     "", FACT_TEXT, [])
        tips = build_tips(title)
        exists = con.execute("SELECT id FROM sg_scripts WHERE code=?", (code,)).fetchone()
        if exists:
            con.execute(
                "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
                "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
                "compliance_json=?, version=version+1, updated_at=? WHERE code=?",
                (title, json.dumps(body, ensure_ascii=False), body_text, wc, sec,
                 40.0, json.dumps(tips, ensure_ascii=False),
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
                 "F2Q", "", "F2Q轻便折叠旅游代步车10AH锂电",
                 "F2Q", json.dumps(["jks-product/F2Q轻便折叠旅游代步车10AH锂电-产品详细信息-9a454f.txt"],
                                   ensure_ascii=False),
                 title, json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(tips, ensure_ascii=False),
                 json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, 40.0, 1, "型号",
                 "F2Q 品牌号系列，一条只讲一个客户真问题：%s；"
                 "所有参数与动作逐字回查公司知识库" % title))
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
