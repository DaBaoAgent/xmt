"""口播号 SG-20261020-026：三款助行辅具（小红书对标，朋友2助行器/819拐杖/P10轮椅）。

对标：小红书《爸妈走不远、容易摔倒？三款助行辅具来啦》
（沐品汇创始人刘丹）。**小红书链接跳登录页，正文没抓到** —— 只有标题。
所以这篇是**按标题结构 + 三个产品的知识库资料**写的，不是逐句贴对标。
（跟往常不同，写稿依据我会在交付说明里讲清楚。）

用户指定的三款产品：
  1. 朋友2   —— 知识库纠正：**四轮带座助行器**（不是代步车）
  2. 819拐杖 —— GB-819 智能收音机拐杖
  3. P10轮椅 —— P10 碳纤维电动轮椅

三款产品参数（逐字回查知识库，不编）：

朋友2（四轮带座助行器）
  - 助行 + 陪护推行两用
  - 车架：铝合金「air」轻量可折叠车架
  - 颜色：薄荷绿、绿色、香芋紫
  - 软垫座面（可坐歇）、网布储物袋
  - 双侧下压式线控刹车
  - 多档高度调节
  - 约 8 寸万向前轮

GB-819 智能收音机拐杖
  - LED 手电筒照明（光通量≥180LM、满电照明≥12小时）
  - 高于 100 分贝报警 + 红光闪光警示
  - 76-108MHz FM 调频收音机
  - 可伸缩铝合金杖杆
  - 5V USB 充电
  - IP43 防溅水
  - 超轻带灯可折

P10 碳纤维电动轮椅
  - 碳纤维超轻车架
  - 一键快速折叠
  - 摇杆操控
  - 弹簧减震
  - 可拆卸锂电池
  - 运动风设计
  - （重量/续航/载重等数字参数知识库标注"待补充"→ 不写数字）

⚠️ 合规注意：
- **价格全部不写**（知识库对照表里有 ¥159~259/¥6780~9980，稿子里绝不出现）
- 「容易摔倒」是标题原话，正文**不说"防止摔倒/不会摔"**（safety_guarantee），
  改成讲每款产品解决什么具体问题
- 不说疾病名、不说疗效
- P10 的数字参数知识库待补充 → 不编，只讲结构卖点

口播号人设：翔哥，十年辅具；直给、短句、口语化；敢说「别急着买」，不贬低友商。
60-90 秒 / 260-400 字。CTA：关注翔哥/评论区聊聊/转给需要的人。
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

TITLE = "爸妈走不远，三款辅具怎么挑"

LINES = [
    "常有家属问我，老人走不远，该配个什么辅具。",
    "这事儿得看走到哪一步了，我按三种情况说。",
    "头一种，还能走，就是走不远、站着累。",
    "选带座的四轮助行器。",
    "朋友2 就是这一路，铝合金车架，能折起来。",
    "走累了，座面一放就能坐下歇。",
    "底下有网布袋，买个菜放个东西都方便。",
    "双侧线控刹车，下坡捏一下就走得稳。",
    "第二种，还能走，但晚上出门不踏实。",
    "选带灯的手杖。",
    "819 这根，带 LED 照明，还带 FM 收音机。",
    "还有报警闪光，夜里图个亮眼。",
    "IP43 防溅水，下点小雨也不怕。",
    "USB 充电，跟手机一个线。",
    "第三种，走不太动了，但还想自己出门。",
    "选碳纤维电动轮椅。",
    "P10 这台，碳纤维车架，一键就折。",
    "摇杆操控，不用人推，自己就能走。",
    "电池能拆下来单独充。",
    "三句话记牢。",
    "走得累选助行器，走夜路选手杖，走不动选电动的。",
    "你家里老人走到哪一步了？评论区说说。",
    "我是翔哥，关注我，挑车少走弯路。",
]

TIPS = [
    "开场坐对镜头，语气像在给家属支招",
    "每讲一款就把车推到镜头前，指着对应的部件说",
    "讲朋友2时演示座面放下坐下 + 捏线控刹车",
    "讲 819 时打开手电和收音机，让观众听见声音",
    "讲 P10 时做一键折叠动作 + 摇杆操控",
    "结尾看镜头邀请评论区互动，语速放慢",
    "字幕可标三款名字，不写价格",
]

FACT_TEXT = (
    "佳康顺三款助行辅具："
    "①助行器朋友2：四轮带座助行器，助行与陪护推行两用，铝合金air轻量可折叠车架，"
    "薄荷绿/绿色/香芋紫多色，软垫座面可坐歇，网布储物袋，双侧下压式线控刹车，"
    "多档高度调节，约8寸万向前轮。"
    "②GB-819智能收音机拐杖：LED手电筒照明（光通量≥180LM、满电照明≥12小时），"
    "高于100分贝报警加红光闪光警示，76-108MHz FM调频收音机，"
    "可伸缩铝合金杖杆，5V USB充电，IP43防溅水，超轻带灯可折。"
    "③P10碳纤维电动轮椅：碳纤维超轻车架，一键快速折叠，摇杆操控，弹簧减震，"
    "可拆卸锂电池，运动风设计（整车重量/续航/载重等数字参数待补充）。"
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

    code = "SG-20261020-026"
    target = 85.0
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
             json.dumps(["翔哥"], ensure_ascii=False), "xiaohongshu",
             "69dcbaf000000000210076fb",
             "https://www.xiaohongshu.com/discovery/item/69dcbaf000000000210076fb",
             "爸妈走不远、容易摔倒？三款助行辅具来啦",
             "朋友2/GB-819/P10",
             json.dumps(["jks-product/助行器朋友2-参数与卖点",
                         "jks-product/GB-819智能收音机拐杖-参数与卖点",
                         "jks-product/P10碳纤维电动轮椅-参数与卖点"],
                        ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "小红书对标（链接跳登录页，正文未抓到，按标题结构+三款产品知识库资料写）；"
             "三款：朋友2助行器/GB-819拐杖/P10碳纤维电动轮椅；"
             "价格全不写；不说防摔倒（safety_guarantee），只讲每款解决什么问题；"
             "P10 数字参数知识库待补充，不编"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒 ｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
