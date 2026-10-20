"""品牌号 F2Q 定稿：按知识库原词手动成稿并入库。

背景：LLM 改稿在这条上反复跑偏（砍掉质疑点、对话断掉、超时），
改成人工定稿 —— 参数全部取自知识库 F2Q 文档原词，避免模型自由发挥。

事实来源：jks-product/F2Q轻便折叠旅游代步车10AH锂电-产品详细信息-9a454f.txt
  - 折叠方式：一拉一按，3 秒折叠（按钮往外一拉，一压完成折叠）
    专利证书号 ZL2020 2 092755.4
  - 折叠尺寸：高度98CM，宽度44CM ｜ 净重19KG ｜ 240W 高效无刷电机 ｜ 10AH 锂电池
  - 折叠后可拖行（不能行驶的区域可拖行）、可放汽车后备箱
  - 智能无刷控制器：陡坡自动匀速、轻松过弯
  - 智能电磁刹车：松开即刹，坡上不溜坡
  - 双重减震：双弹簧减震 + 悬浮减震
  - 升级免维护实心大轮：9寸大轮轻松越坎，可过小区路/减速带/石头路/台阶
  - 防倾倒后轮：防止爬坡时角度过大后倾
  - 手/电动自由切换：拨杆向上手动推行，向下电动行驶
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

CODE = "SG-20261020-003"

TITLE = "你家这车能上我们那坡吗"

# 稿中用到的数字/参数，其知识库依据（用于合规扫描的数字溯源）
FACT_TEXT = (
    "产品型号：F2Q 电池规格：10AH 锂电池 电机功率：240W "
    "展开尺寸：105 × 54 × 90 CM 折叠尺寸：高度98CM，宽度44CM "
    "产品净重：19 KG（不含电池、扶手、坐垫） 最大载重：125 KG "
    "轮胎尺寸：前轮直径18CM / 后轮直径21.5CM（9寸大轮） "
    "一拉一按 3秒折叠 专利号：ZL2020 2 092755.4 "
    "陡坡自动匀速 智能电磁刹车 松开即刹 坡上不溜坡 "
    "双弹簧减震 悬浮减震 防倾倒后轮 9寸大轮轻松越坎 航空铝合金车架"
)

# 逐句：说话人 / 节奏点 / 台词
LINES = [
    ("心悦", "钩子", "不少叔叔阿姨问，这车收起来占地不？"),
    ("小冯", "演示", "按钮往外一拉，一压就折好，三秒的事。"),
    ("心悦", "追问", "折完能拖着走不？"),
    ("小冯", "演示", "能，19 公斤，跟拉行李箱似的拖着走。"),
    ("心悦", "质疑", "老小区的路坑坑洼洼，颠得人难受咋办？"),
    ("小冯", "演示", "前头双弹簧减震，后头防倾倒轮，跟着路面摆。"),
    ("心悦", "再质疑", "上坡会不会突然往前冲？"),
    ("小冯", "演示", "智能无刷控制器，上陡坡自动匀速，不往前冲。"),
    ("心悦", "再质疑", "坡上要停，会不会溜车？"),
    ("小冯", "演示", "智能电磁刹车，一松手就刹住，坡上不溜车。"),
    ("心悦", "判断&CTA", "选代步车，您来苏州阳光大厦展厅试一圈。"),
]

SHOOTING_TIPS = [
    "开场两人在展厅同框，心悦先开口提问，不要看镜头",
    "讲折叠时小冯单手演示：按钮往外一拉、一压，3 秒折完，给中景看到完整动作",
    "折完顺手演示拖着走，像拉行李箱，让画面说明「能拖行」",
    "讲减震时镜头给前轮弹簧与后轮特写，小冯边推边讲路面起伏",
    "讲陡坡控速时如果展厅有坡道就实拍一次，没有就用手指比划坡度",
    "讲电磁刹车时给控制器松手动作的特写，配合一句「一松手就停」",
    "结尾两人一起看镜头，CTA 由心悦说，语气像邀邻居来坐坐",
]


def main():
    body = {
        "format": "dialogue",
        "lines": [{"speaker": s, "beat": b, "text": t} for s, b, t in LINES],
    }
    body_text = body_plain_text(body)
    spoken = util.strip_speakers(body_text)
    word_count = util.count_chars(spoken)
    seconds = util.estimate_seconds(spoken)

    # 合规扫描（发布包必须带免责声明；数字要能在事实片段里溯源）
    disclaimer = util.compliance_config().get("disclaimer") or ""
    scan = compliance.scan_script(body_text, {"disclaimer": disclaimer}, "", FACT_TEXT, [])

    con = sqlite3.connect(os.path.join(ROOT, "data", "xmt.db"))
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM sg_scripts WHERE code=?", (CODE,)).fetchone()
    if not row:
        print("找不到 %s" % CODE)
        return
    d = dict(row)
    con.execute(
        "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
        "estimated_seconds=?, shooting_tips_json=?, compliance_json=?, "
        "presenters_json=?, publish_json=?, version=version+1, updated_at=? WHERE code=?",
        (TITLE, json.dumps(body, ensure_ascii=False), body_text, word_count, seconds,
         json.dumps(SHOOTING_TIPS, ensure_ascii=False),
         json.dumps(scan, ensure_ascii=False),
         json.dumps(["心悦", "小冯"], ensure_ascii=False),
         json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
         util.now_iso(), CODE))
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒 ｜ 合规 %s" % (
        word_count, seconds, scan.get("counts")))
    print()
    print(body_text)
    print()
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」" % (f.get("severity"), f.get("rule_id"), f.get("match")))


if __name__ == "__main__":
    main()
