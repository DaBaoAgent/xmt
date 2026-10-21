"""口播号 SG-20261020-021：贴对标原句改写（抖音·给父母买轮椅别踩坑），**不代入产品**。

对标（250 字 / 55 秒）逐段：
  现象：年轻人给父母选出行工具，看到碳钢轮椅低价促销就心动，觉得能推就行，
        没必要买贵的。但给父母用，轻便和耐用才是关键。
  碳钢的问题①：普遍 12-15 公斤，两个人才能抬进后备箱，没电梯的老楼累得直喘气
  碳钢的问题②：防锈差，下雨推出去一次，车架接缝焊接处都上锈，擦不掉还越挤越多
  碳钢的问题③：用半年就显得破旧不堪
  建议：预算再有限，也优先选铝合金材质，重量能控制在 8-12 公斤
        父母自己扶着也能挪位置，儿女搬运省力，出门旅游方便
  结尾：给父母用就要用好的

**⚠️ 三处按合规调整**：
1. 对标说「碳钢轮椅**低价促销**就心动」→ 涉及 price 规则 → 改成「图便宜」，
   不提价格和促销。
2. 标题「**百分之90%的人都中招**」→ absolute 规则禁绝对化（100%），
   「90%的人都中招」也是绝对化断言 → 改成「不少人栽在这上面」。
3. 讲碳钢上锈/破旧是**材质科普**，不是品牌对比，可以保留；
   但用词别太绝对（不说「都」「一定」），改成「容易」。

产品口径：**不代入产品**（用户指定）——纯科普避坑，不提任何型号/品牌。

口播号人设：翔哥，十年辅具；直给、短句、口语化；敢说「别急着买」，不贬低友商。
60-90 秒 / 260-400 字。CTA：关注翔哥/评论区聊聊/转给需要的人。

长度贴对标（55 秒 / 250 字），写 ~270 字 / 62 秒左右。
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

TITLE = "给父母买轮椅，别栽在材质上"

LINES = [
    "不少年轻人给父母挑轮椅，图便宜就心动，觉得能推就行。",
    "但给父母用，轻便和耐用才是顶要紧的。",
    "先说重量。",
    "碳钢车架普遍十二到十五公斤，搬一趟挺费劲。",
    "塞后备箱常常得两个人搭手，赶上没电梯的老楼，更是喘得不行。",
    "再说防锈。",
    "碳钢车架下雨天推出去一趟，接缝那儿就容易长锈。",
    "锈迹擦不掉，还慢慢往外扩。",
    "用上小半年，车就显得旧了。",
    "所以我常跟来店里的人讲，预算再紧，也优先看铝合金车架。",
    "整车分量能控制在八到十二公斤。",
    "老人自己扶着也能挪个位置，儿女搬着省力，出门带着也方便。",
    "挑的时候你就记住两点。",
    "一问车架什么材质，二问整车多少公斤。",
    "这两样问清楚了，比看十张图片都管用。",
    "你给爸妈买车，问过材质吗？评论区说说。",
    "我是翔哥，关注我，给爸妈挑车少走弯路。",
]

TIPS = [
    "开场像在跟人说事，语气像邻居大哥，别像讲课",
    "讲重量时真去抬一下车，让人看出分量",
    "讲防锈时给车架接缝特写，手指点一下（可用道具示意，别拍生锈竞品）",
    "讲「老人自己扶着挪位置」时演示单手扶车挪动的动作",
    "结尾看镜头，邀请评论区互动，语速放慢",
    "字幕可标 8-12 公斤，不写价格",
]

FACT_TEXT = (
    "轮椅选购材质科普（不代入产品）：碳钢车架整车重量普遍12-15KG，"
    "接缝处遇水容易生锈，锈迹难擦除且会扩散；铝合金车架整车重量通常8-12KG，"
    "更轻便、不易生锈，老人可自行搀扶挪动位置，子女搬运省力，便于携带出门。"
    "选购建议：一问车架材质，二问整车重量。"
)


def main():
    body = {"format": "monologue",
            "lines": [{"speaker": "翔哥", "beat": "口播", "text": t} for t in LINES]}
    body_text = body_plain_text(body)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    disclaimer = util.compliance_config().get("disclaimer") or ""
    scan = compliance.scan_script(body_text, {"disclaimer": disclaimer}, "", FACT_TEXT, [])

    code = "SG-20261020-021"
    target = 60.0
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
            (code, now, now, "待审", "oral", "口播号",
             json.dumps(["翔哥"], ensure_ascii=False), "douyin",
             "7592169055906172169", "https://v.douyin.com/O6ZG7YitUnQ/",
             "给父母买轮椅别踩坑 百分之90的人都中招，听听小高怎么说？"
             "给父母就要最好的，安全出行，人人有责#轮椅 #老人 #踩坑 #科普",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "贴对标「买轮椅别踩坑」骨架；**不代入产品**（用户指定）；"
             "对标的三处合规问题已改：低价促销→图便宜（price）、"
             "90%的人都中招→别栽在材质上（absolute）、"
             "碳钢生锈用「容易」弱化不绝对化"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 55s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
