"""口播号 SG-20261020-022：贴对标原句改写（抖音·轮友说用了两三年就散架了）。

对标（160 字 / 29 秒）逐句：
  大家好，我是小美，很多朋友用轮椅最头疼的，就是笨重又不灵活，真是太费劲了。
  今天我就给大家说一说一体式的轮椅好在哪里。
  第一，整车更轻，自己力气小，也可以轻松搬运，毫不费力。
  第二，一体成型，没有焊点，结构更稳定，更稳固，承重也更放心。
  第三，材质防腐耐腐蚀，平时护理擦擦就行，特别省心。
  你们选轮椅时最注意什么呢？评论区告诉我。

**⚠️ 对标踩我们合规线的三处，已改**：
1. 「一体成型没有焊点，结构更稳定更稳固，**承重也更放心**」→
   `safety_guarantee` 禁安全性断言/保证 → 改成客观描述结构特点，
   不下「更放心」这种结论。
2. 「自己力气小，也可以轻松搬运，**毫不费力**」→ 绝对化 → 改「省力不少」。
3. 标题「**用了两三年就散架了**」暗示别家产品容易坏 → `comparison` 禁与其他品牌
   做功效或安全性对比 → 改成中性的「为什么有的车用不久」，不讲别人坏话。

产品口径：**不代入产品**（用户指定）—— 纯科普。

口播号人设：翔哥，十年辅具；直给、短句、口语化；敢说「别急着买」，不贬低友商。
60-90 秒 / 260-400 字。CTA：关注翔哥/评论区聊聊/转给需要的人。

长度贴对标（29 秒），写 ~200 字 / 48 秒左右。
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

TITLE = "有的轮椅用不久，问题常出在车架上"

LINES = [
    "常有轮友问我，为什么有的轮椅用上两三年就松了。",
    "我跟他们讲，先看车架。",
    "拼焊的车架，焊点就是软肋，使久了焊点先松，整车跟着晃。",
    "材质没选对，接缝那儿还容易长锈，越使越糟。",
    "那挑的时候看什么？",
    "看车架是不是一体的，焊点越少越简单，简单的反而不容易坏。",
    "看材质，铝合金的比碳钢的轻，也不容易生锈。",
    "看整车分量，轻一些，自己挪位置省力，儿女搬着也轻松。",
    "这三点看下来，比听十句介绍都管用。",
    "你家的车，用了几年还稳当吗？评论区说说。",
    "我是翔哥，关注我，挑车少走弯路。",
]

TIPS = [
    "开场像在回答轮友提问，语气实在，别像讲课",
    "讲拼焊车架时手指在车架焊点位置点一下，让观众看见焊点在哪",
    "讲材质时拿两块料子对比轻重，让画面说明问题",
    "讲日常打理时做擦车的动作",
    "结尾看镜头邀请评论区互动，语速放慢",
    "字幕可标关键判断点，不写价格",
]

FACT_TEXT = (
    "轮椅选购科普（不代入产品）：车架结构分拼焊式与一体式，"
    "拼焊式焊点是结构薄弱环节，长期使用后焊点易松动；"
    "铝合金车架相较碳钢更轻且不易生锈，日常擦拭即可打理；"
    "整车分量轻则老人自行挪动省力、子女搬运轻松。"
    "选购建议：看车架结构、看材质、看整车分量。"
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

    code = "SG-20261020-022"
    target = 48.0
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
             "7620349965637963584", "https://v.douyin.com/181CSr8Buoo/",
             "轮友说：用了两三年就散架了？#轮椅人生 #轮椅女孩 #残疾人正能量 "
             "#轮椅生活 #残疾人的生活",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "贴对标「轮椅用不久/一体式优点」骨架；**不代入产品**（用户指定）；"
             "对标三处合规问题已改：承重更放心→客观描述（safety_guarantee）、"
             "毫不费力→省力不少（绝对化）、"
             "用了两三年就散架→中性的问题出在哪（comparison）"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 29s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
