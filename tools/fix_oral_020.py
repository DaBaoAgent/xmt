"""口播号 SG-20261020-020：贴对标原句改写（抖音·警惕低价杂牌仿运动轮椅）。

对标（中进智行客，187 字 / 33 秒）逐句：
  警惕低价杂牌仿运动轮椅
  市面上便宜的号称运动轮椅，基本都是缩水材质、劣质配件、无调节结构，
  使用一年左右车架就会松动和异响。
  那么我给大家一个合理的参考价位：入门靠谱款 2500-4500，中端可调款 4500-8000，
  碳纤维等材料要到万元以上，毕竟一分价钱一分货。
  很多特别便宜的，在你有可能看不见的地方去苛刻。
  评论区告诉我，你的轮椅是花多少钱买的呢？记得点赞关注哦！

**⚠️ 两处必须改**：
1. 对标给了具体价格区间（2500-4500 / 4500-8000 / 万元以上）→
   我们的 `price` 合规规则禁「具体价格、多少钱、报价、优惠」→ 全部去掉，
   改成定性判断（「便宜的在看不见的地方缩水」）。
2. 「警惕低价杂牌」隐含贬低其他品牌 → `comparison` 规则禁与其他品牌做功效或
   安全性对比 → 改成讲「怎么挑」的正面判断标准，不说别人坏话。

产品口径：博爱方特 BA-LZ-2 铝合金焊接车架（成人款）—— 用户指定。
上一篇 019 已查好的参数继续用：7003 航空铝合金车架、坐宽六档 36-46cm、
坐深 36-48 可调、前坐高 39-52、后坐高 37-44、靠背碳纤维可快拆高低角度可调、
质保车架 5 年/其他部件 2 年、收到 3 天内尺寸重心不合适可线上指导返厂运费公司承担。

口播号人设：翔哥，十年辅具；直给、短句、口语化；敢说「别急着买」，不贬低友商。
60-90 秒 / 260-400 字。CTA：关注翔哥/评论区聊聊/转给需要的人。

长度贴对标（33 秒），写 ~200 字 / 45 秒左右，不往人设下限凑。
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

TITLE = "便宜的仿运动轮椅，差在哪儿"

LINES = [
    "市面上不少便宜车，号称是运动轮椅。",
    "问题基本都在一样的地方。",
    "材质缩水，车架管子薄，用上一两年就晃。",
    "没有调节结构，坐宽坐深都是死的，人合不上车。",
    "靠背也不能调高低，坐久了腰没处靠。",
    "所以挑这种车，别光看价格。",
    "你看它车架是什么料，坐宽能不能一档档调，靠背能不能调高低。",
    "博爱方特这台，坐宽六档，三十六到四十六公分，坐深前后坐高都能调。",
    "靠背是碳纤维的，能快拆，高低角度随便调。",
    "车架质保五年。",
    "你家的车，坐宽是死的还是能调的？评论区说说。",
    "我是翔哥，关注我，挑车少走弯路。",
]

TIPS = [
    "开场站对镜头，语气像在劝人，别像在骂人（不说竞品坏话）",
    "讲材质缩水时拿两根管子对比粗细，让画面说明问题",
    "讲调节结构时演示坐宽档位切换 + 靠背高低调节，动作要连贯",
    "讲质保时语气放平稳，像在给底气，别喊促销",
    "结尾看镜头邀请评论区互动，语速放慢",
    "字幕可标坐宽档位和质保年限，不写价格",
]

FACT_TEXT = (
    "博爱方特 BA-LZ-2 铝合金焊接车架（成人款）定制轮椅："
    "坐宽六档可选36/38/40/42/44/46cm贴合不同体型 "
    "坐深36-48可调节(厘米级) 前坐高39-52可调节(不含坐垫) 后坐高37-44可调节(不含坐垫) "
    "车架7003航空铝合金水平长度58cm、62cm "
    "坐垫板碳纤维板+尼龙绷带绷带松紧可调 侧板7075铝合金 "
    "硬靠背碳纤维可快拆高低及角度可调 "
    "刹车铝合金鹰嘴刹车/前推刹车自选 "
    "挡腿带碳纤维高低前后角度可调可上翻 脚踏板铝合金高低可调 "
    "前轮铝合金硬质阳极黑钛金蓝红紫 后轮免充气胎4寸5寸尺寸自选 "
    "推把铝合金高低可调可选折叠不可折叠 零配件多种颜色可选 "
    "包裹方式半包裹/浅包裹/浅包裹加摆位等于深包裹 "
    "质保铝合金车架5年其他部件2年内胎1年 "
    "收到后3天内尺寸及重心不合适可线上指导需返厂调节运费由公司承担 "
    "可调式运动轮椅 集国内外运动轮椅之所长"
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

    code = "SG-20261020-020"
    target = 45.0
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
             "7673411619103296794", "https://v.douyin.com/T64zlGw73is/",
             "警惕低价杂牌“仿运动轮椅” #中进智行客 #轮椅 #运动轮椅 #杂牌 #科普",
             "博爱方特BA-LZ-2",
             json.dumps(["jks-product/博爱方特画册四-BA-LZ-2铝合金焊接车架(成人款）-20260827.pdf"],
                        ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "贴对标「警惕低价仿运动轮椅」骨架；**删掉对标所有价格区间**（price 规则），"
             "改成定性判断；不说竞品坏话（comparison 规则），改为讲怎么挑。"
             "产品参数逐字回查博爱方特画册"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 33s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
