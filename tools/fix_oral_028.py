"""口播号 SG-20261020-028：贴对标原句改写（抖音·越垫厚棉被越容易起压疮）。

对标（726 字 / 141 秒）结构：
  钩子：垫得越软越容易长压疮。家属怕老人搁骨头，垫厚棉被/两三层软垫
  现实：睡厚棉被的老人，不出半个月，尾椎骨或脚后跟就会破皮甚至溃烂
  真相：压疮不仅是压出来的，更是捂出来的。厚棉被极度吸水且不透气。
        体弱出虚汗 + 排泄物挥发 → 高温高湿大蒸笼，皮肤被捂久像泡澡泡发，
        变脆弱，翻身或轻擦就破
  对策①：第一步不是加厚，是**做减法**。科学抗压底座是防压疮气垫床，
         上面别塞厚，只铺一层轻薄透气的护理床单。床铺够薄，
         气垫床波浪起伏才能传到身上；材料透气，空气才能流通带走汗液湿气
  对策②：隔尿垫别叠加。很多家属在床单下铺三四个一次性隔尿垫，
         底层是防漏塑料膜，铺得越多后背越像密不透风的雨衣。
         正确做法：买一片大尺寸高吸收量的隔尿垫，填在臀部下方，一层就够
  升华：真正的舒服不是在长辈身上堆积柔软，而是给脆弱的皮肤留出呼吸空间。
        保持干爽透气，才是最顶级的皮肤护理
  CTA：点赞订阅转发打赏

**⚠️ 对标踩我们合规线的多处，核心转换「讲床铺怎么弄，不讲会得什么病」**：
1. 「**压疮/褥疮**」出现 N 次 → disease_claim 禁用词表里有「褥疮」，
   ASR 识别的「压窗」就是它 → 全部改成「皮肤出问题」「压坏了」
2. 「破皮甚至**溃烂**」→ 症状描述 → 改成「容易受损」
3. 「**角质层像泡澡泡发**」「高温高湿」→ 医学/生理机制 → 删，讲结果不讲机制
4. 「**防压疮气垫床**」→ 具体产品 + 功能宣称，用户指定不带入产品 →
   改成原则（床铺要薄、要透气），不点名产品
5. 「排泄物挥发」→ 不雅且医学 → 删
6. 「**最顶级的**皮肤护理」→ 绝对化 → 删

产品口径：**不代入产品**（用户指定）—— 纯照护科普。

口播号人设：翔哥，十年辅具；直给、短句、口语化；敢说「别急着买」，不贬低友商。
60-90 秒 / 260-400 字。CTA：关注翔哥/评论区聊聊/转给需要的人。

长度贴对标（141 秒太长），按口播号区间写 ~340 字 / 80 秒。
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

TITLE = "床铺不是越软越好"

LINES = [
    "很多家属怕老人骨头搁着，给铺厚厚的棉被，一层不够还铺两层。",
    "觉得越软越舒服，其实不是这么回事。",
    "老人长时间压着同一个地方，皮肤本来就容易出问题。",
    "再垫上厚棉被，软是软了，可它吸水又不透气。",
    "老人躺着容易出汗，棉被很快就潮。",
    "皮肤一直闷在潮湿里，时间长了反而更脆弱。",
    "这时候翻个身擦一下，都可能把皮肤弄伤。",
    "所以第一步不是加厚，是做减法。",
    "床铺薄一点，透气一点，比多铺一层棉被管用。",
    "底下垫的东西要能让空气走动，把潮气带走。",
    "再说隔尿垫。",
    "不少家属怕漏尿洗床单，在床单底下一次性铺三四个。",
    "隔尿垫底下那层是防漏的，铺得越多越闷。",
    "铺三四个，跟在老人后背裹层塑料布差不多。",
    "正确做法是，买一片大点的、吸得住的，垫在身子底下，一层就够了。",
    "照顾老人，舒服不是靠堆软乎劲儿。",
    "是让皮肤能喘上气，干干爽爽的，比什么都强。",
    "你家床铺铺了几层？评论区说说。",
    "我是翔哥，关注我，居家养老少踩坑。",
]

TIPS = [
    "开场坐对镜头，语气像在纠正一个常见误区，别训人",
    "讲厚棉被时用手比画往上铺的动作，铺两层时手势重复一次",
    "讲「裹层塑料布」时做个把塑料布蒙在背上的手势，反差要明显",
    "讲隔尿垫时拿一片做示范，从一片铺到三四片再收回来",
    "结尾看镜头邀请评论区互动，语速放慢",
    "字幕可标「一层就够」，不写价格、不写疾病名",
]

FACT_TEXT = (
    "卧床老人床铺照护科普（不代入产品）：厚棉被虽软但吸水性强、透气性差，"
    "老人卧床时皮肤长时间受压且易出汗，若床铺过厚过闷则皮肤更易受损；"
    "照护上应减少铺垫层数，保持床铺轻薄透气，让潮气能够散去；"
    "一次性隔尿垫底层为防漏材质，多层叠加会影响透气，"
    "建议选用一片大尺寸高吸收量的隔尿垫垫于身下一层即可。"
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

    code = "SG-20261020-028"
    target = 80.0
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
             "7684124217972956239", "https://v.douyin.com/ME01VqwyrGQ/",
             "越给老人垫厚棉被，越容易起压疮！#居家养老#养老护理",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "贴对标「厚棉被误区」骨架；**不代入产品**（用户指定）；"
             "对标多处医学内容已改：压疮/褥疮→皮肤出问题、溃烂→受损、"
             "角质层泡发等生理机制→删、防压疮气垫床→讲薄且透气的原则不点名产品"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 141s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
