"""口播号 SG-20261020-024：贴对标原句改写（抖音·电动轮椅能否上路）。

对标（1607 字 / 232 秒）核心结构：
  引子：不少人说电动轮椅禁止上路、交警会查扣、必须上牌
  ① 定性：电动轮椅是医疗器械，不是法定车辆
  ② 室内场景：小区、公园、商场、医院、室内都能用；地铁、电梯、高铁、
     部分飞机上也能用（上飞机要满足航司规定）
  ③ 室外场景：有人行道走人行道 → 没人行道借自行车道靠右 → 两者都没有
     走马路最右侧靠边
  ④ 误区：只有残疾人才能用？不是。真正用的是腿脚不便的人，正常人不会想用
  ⑤ 误区：没有残疾人证就不是残疾人？—— **法律认定问题**
  结尾：腿脚不便的老人或残疾人都能合法使用

**⚠️⚠️ 这篇对标有四类高风险内容，全部去掉**：
1. **引用具体法律条款**（《残疾人保障法》《无障碍环境建设条例》
   《道路交通安全法》）→ **不能替法律解释或转述条款**，说错是法律责任
   → 只讲「电动轮椅属于医疗器械，不是机动车」这一条常识性定性
2. **「这都是合法合规的，不要有任何的担心」** → 法律结论性断言，
   不能替法律下结论 → 改成「具体规定各地有差异，拿不准问当地交管部门」
3. **「没有残疾人证，你也属于残疾人」** → 法律认定问题，不该由我们解释
   → 整段删掉
4. **「脑梗」等疾病名 + 残疾人证/补贴政策** → 踩 disease_claim 且涉政策敏感
   → 整段删掉
5. 对标的电动轮椅速度数据（6-7 公里/小时）→ 产品参数，我们不带入产品，
   不该报具体数字 → 删掉

产品口径：**不代入产品**（用户指定）—— 纯科普答疑。

口播号人设：翔哥，十年辅具；直给、短句、口语化；敢说「别急着买」，不贬低友商。
60-90 秒 / 260-400 字。CTA：关注翔哥/评论区聊聊/转给需要的人。

长度：对标 232 秒太长，按口播号区间写 ~330 字 / 75 秒。
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

TITLE = "电动轮椅能上路吗，要不要上牌"

LINES = [
    "总有人问我，电动轮椅能不能上路，要不要上牌。",
    "先说结论：电动轮椅属于医疗器械，不是机动车。",
    "所以它不存在上牌这回事，也没有牌照这一说。",
    "那能在哪些地方用？",
    "小区、公园、商场、医院、屋里头，这些地方都能正常用。",
    "地铁、电梯、高铁，大部分也都能进。",
    "坐飞机的话，得提前问航司，按人家的规定来。",
    "室外呢？",
    "有人行道就走人行道。",
    "没有人行道，就借自行车道，尽量靠右。",
    "两边都没有，就贴着马路最右边慢慢走。",
    "总的一条，靠右、慢行、别往机动车道中间去。",
    "还有人问，家里老人没证能不能用。",
    "我的看法是，按实际需要来，谁需要谁用。",
    "但具体到每个地方的管理尺度不太一样。",
    "拿不准的，问一下当地交管部门最稳妥。",
    "别自己瞎猜，也别信评论区那些吓人的话。",
    "你家那边管得严不严？评论区说说。",
    "我是翔哥，关注我，挑车少走弯路。",
]

TIPS = [
    "开场坐对镜头，语气像在回答评论区提问",
    "讲使用场景时镜头切换：小区→公园→商场，或直接在展厅里边说边指",
    "讲室外靠右行走时用手比画从人行道到自行车道再到马路边",
    "讲到「问当地交管部门」时语气认真，这是给观众兜底的话",
    "结尾看镜头邀请评论区互动，语速放慢",
    "字幕可标三条场景，不写价格、不引法条",
]

FACT_TEXT = (
    "电动轮椅使用常识科普（不代入产品）：电动轮椅属于医疗器械而非机动车，"
    "不存在上牌和牌照要求；可在小区、公园、商场、医院及室内等场所正常使用，"
    "地铁、电梯、高铁大部分可进入，乘坐飞机需提前咨询航空公司并按其规定执行；"
    "室外行驶应有人行道走人行道，无人行道借自行车道靠右行驶，"
    "两者皆无则紧贴马路最右侧边缘慢行；各地管理尺度存在差异，"
    "建议拿不准时咨询当地交管部门。"
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

    code = "SG-20261020-024"
    target = 75.0
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
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), now, code))
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
             "7631942094403900518", "https://v.douyin.com/jyAiONaQbYw/",
             "电动轮椅能否上路？电动轮椅能在什么地方行驶？电动轮椅需要上牌吗？"
             "#电动轮椅 #能否上路 #和美德电动轮椅 #宗谋大叔 #答疑解惑",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "贴对标「能否上路/在哪行驶/要不要上牌」三问骨架；**不代入产品**；"
             "对标的高风险内容全部去掉：法律条款引用、法律结论断言、"
             "残疾人证法律认定、疾病名与补贴政策、产品速度参数"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 232s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
