"""口播号 SG-20261020-025：贴对标原句改写（抖音·半失能老人三大件）。

对标（746 字 / 135 秒）结构：
  引子：长辈腿脚开始不好，第一件事是买电动轮椅还是护理床？都不是。
        先别急着花冤枉钱。对还能自己翻身、能借力站起来的半失能长辈来说，
        买太高级的会直接替代他们所有的发力动作，反而会加速肌肉萎缩。
        核心策略应该是协助而不是替代。
  ① 床头移动坐便椅（带扶手）：夜间起夜去卫生间是跌倒高发路段。
     放床边，坐床沿转身就能上厕所。几十上百块，把夜间跌倒风险降到极低。
  ② 床垫下床边助力扶手（免打孔）：早晨起床腹部核心没力量，
     总要家属声拉应拽，家属腰受不了，长辈有负罪感。塞床垫下固定，
     自己用手拉栏杆借手臂力量坐起来。减轻照护者负担，
     鼓励长辈锻炼上肢力量，保护残存机能。
  ③ 专业防滑洗澡椅：别坐塑料小板凳洗澡，地面湿滑、没靠背没扶手，
     重心不稳后果不堪设想。专业洗澡椅有漏水孔、宽大吸盘脚垫、高度可调，
     洗澡不耗费太多体力，家属擦洗也踏实。
  升华：好辅具不是比拼价格，价值是为长辈搭建安全支点，
        借助支点继续保有生活自理的尊严。花小钱办对事。
  CTA：关注 + 下期见

**⚠️ 对标踩我们合规线的六处，已改**：
1. 「几百块钱」「几十上百块」→ price 规则禁具体价格 → 全部删掉
2. 「半失能」「**肌肉萎缩**」「残存机能」→ 医学术语/疾病描述、功效断言
   → 改成「腿脚弱一些」「力气」「自己能做的事让他自己做」
3. 「风险**非常高**」「**后果不堪设想**」→ 安全断言 + 焦虑诱导 →
   改成「容易出意外」
4. 「把风险降到了**极低**」→ 安全断言 → 改成「稳妥不少」
5. 「买电动轮椅还是护理床？**都不是**」→ 我们是卖辅具的，
   且涉及产品对比 → 改成「先看眼下最要紧解决什么」
6. 「花小钱办对事」→ 涉钱 → 改成「花在刀刃上」

产品口径：**不代入产品**（用户指定）—— 纯科普。

口播号人设：翔哥，十年辅具；直给、短句、口语化；敢说「别急着买」，不贬低友商。
60-90 秒 / 260-400 字。CTA：关注翔哥/评论区聊聊/转给需要的人。

长度贴对标（135 秒太长），按口播号区间写 ~330 字 / 75 秒。
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

TITLE = "老人腿脚弱了，先添这三样"

LINES = [
    "家里长辈腿脚开始不利索了，先别急着添大件。",
    "先看眼下最要紧解决什么。",
    "今天说三样。",
    "头一样，床头放把带扶手的移动坐便椅。",
    "很多老人出意外，是在夜里起夜去卫生间的路上。",
    "头一阵晕，腿又没劲。",
    "坐便椅搁在床边，坐床沿转个身就能用，不用摸黑走远路。",
    "第二样，床垫底下塞个床边助力扶手。",
    "免打孔，塞进去就固定住了。",
    "早上醒来，老人自己拉着栏杆，借手臂的力气就能坐起来。",
    "家里人也不用弯腰去拽，腰能松口气。",
    "自己能做的事让他自己做，这点挺要紧。",
    "第三样，换掉卫生间里那个塑料小板凳。",
    "地面湿滑，板凳没靠背也没扶手，坐着不踏实。",
    "专业的洗澡椅带靠背和扶手，底部有吸盘脚垫，坐着稳当。",
    "椅面带漏水孔，高度能调，洗澡不那么累。",
    "这三样都不起眼，但都踩在老人日常真用得上的点上。",
    "好辅具不是比谁贵，是看有没有踩在点上。",
    "花在刀刃上，家里也省心。",
    "你家给老人添了什么？评论区说说。",
    "我是翔哥，关注我，居家养老少踩坑。",
]

TIPS = [
    "开场坐对镜头，语气像在跟邻居支招，别像讲课",
    "讲坐便椅时镜头带到床头位置，用手比画坐床沿转身的动作",
    "讲床边扶手时做塞床垫的动作，再演示拉栏杆坐起",
    "讲洗澡椅时指着椅面漏水孔和底部脚垫，给特写",
    "结尾看镜头邀请评论区互动，语速放慢",
    "字幕可标三样东西的名字，不写价格、不写医疗术语",
]

FACT_TEXT = (
    "居家养老辅具科普（不代入产品）：带扶手的移动坐便椅可置于床边，"
    "减少老人夜间起夜行走距离；床边助力扶手免打孔，塞于床垫下即可固定，"
    "老人可借手臂力量自行坐起，减轻照护者弯腰负担；"
    "专业防滑洗澡椅带靠背与扶手，底部有吸盘脚垫，椅面带漏水孔，"
    "高度可调节。三样均属于居家日常照护中常用的基础辅具。"
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

    code = "SG-20261020-025"
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
             "7670490099574595764", "https://v.douyin.com/b-RKM_0BWj0/",
             "半失能老人必备的“高性价比三大件”。 #养老护理#居家护理#养老产品",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "贴对标「居家三大件」骨架；**不代入产品**（用户指定）；"
             "对标六处合规问题已改：具体价格→删、"
             "半失能/肌肉萎缩/残存机能→腿脚弱一些/力气/自己做、"
             "风险极高/后果不堪设想/降到极低→容易出意外/稳妥不少、"
             "「买电动轮椅还是护理床都不是」→先看眼下最要紧的、"
             "花小钱→花在刀刃上"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 135s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
