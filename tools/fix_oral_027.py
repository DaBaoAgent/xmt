"""口播号 SG-20261020-027：贴对标原句改写（抖音·老人刚卧床要知道的事）。

对标（700 字 / 128 秒）结构：
  引子：老人一旦卧床，有几个坎得迟早碰上，提前知道提前预防，
        家属和老人都少受点罪
  ① 长褥疮：24小时躺着，后背/屁股/脚后跟骨头贴着床，血液不流通，
     容易压坏皮肉。对策：勤翻身勤擦洗，每2小时翻一次身左右侧躺；
     有条件用防褥疮垫；皮肤发红别揉搓，翻身悬空保持干燥
  ② 吃饭喝水容易呛：吞咽功能退化快，没咽好呛到肺里引起吸入性肺炎。
     口诀：能坐着吃绝不躺着吃，半躺着背后垫高；吃完饭别立刻平躺，
     靠坐半小时顺气
  ③ 排便困难：不活动肠胃偷懒，几天就出现，憋得难受脾气变大。
     对策：好消化、膳食纤维吃够、饮水跟上；顺时针揉肚子
  ④ 肌肉萎缩快：胳膊腿变细脸颊凹进去。注意营养，补充优质蛋白质
  升华：服侍卧床老人是拼体力和耐心的持久战，家属也要照顾好自己，
        尽心尽力问心无愧就是满分答卷

**⚠️⚠️ 对标踩我们合规线的多处（这篇医学内容最密集），核心转换是
「讲日常照料怎么做，不讲会得什么病」**：
1. 「长**褥疮**」「引起**吸入性肺炎**」→ **疾病名称**，踩 disease_claim
   → 改成「长时间压着同一块皮肤，容易出问题」「躺着吃喝容易呛着」
2. 「**肌肉萎缩**」→ 医学术语 → 改「不怎么动，力气会变小」
3. 「**吞咽功能退化**」「血液不流通」→ 医学表述 → 改「躺着吃喝没那么顺」
4. 「特别常见，也**特别危险**」→ 危险断言 + 焦虑诱导 → 删
5. 「补充**优质蛋白质是首要任务**」→ 营养/健康功效断言 →
   改「吃得跟上，粗细搭配好」
6. 「皮肤发红」→ 症状描述 → 改成「看护时多留意皮肤状态」

产品口径：**不代入产品**（用户指定）—— 纯照料科普。

口播号人设：翔哥，十年辅具；直给、短句、口语化；敢说「别急着买」，不贬低友商。
60-90 秒 / 260-400 字。CTA：关注翔哥/评论区聊聊/转给需要的人。

长度贴对标（128 秒太长），按口播号区间写 ~330 字 / 75 秒。
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

TITLE = "老人行动不便，家属要过的几道坎"

LINES = [
    "家里老人行动不便，一天大部分时间得躺着，有几件事得提前知道。",
    "头一件，皮肤。",
    "长时间躺着，后背屁股脚后跟一直贴着床。",
    "压得久了，皮肤容易出问题。",
    "能做的就是六个字，勤翻身，勤擦洗。",
    "隔上两个钟头翻一回身，左边侧侧，右边侧侧。",
    "看护时多留意皮肤，发现不对先把那位置悬空，保持干爽。",
    "第二件，吃喝。",
    "躺着吃喝没那么顺，一口没咽好就容易呛着。",
    "所以记一句，能坐着吃就别躺着吃。",
    "吃完别马上放平，靠着坐一会儿，顺顺气。",
    "第三件，排便。",
    "天天不活动，肠胃也懒，好几天解不出来是常事。",
    "膳食纤维和水都得跟上。",
    "没事的时候，顺时针在肚子上轻轻揉一揉。",
    "还有一件，长期不怎么动，力气会变小。",
    "所以吃的得跟上，粗细搭配好。",
    "照顾老人是场持久战，拼体力也拼耐心。",
    "尽心尽力，问心无愧，这就够了。",
    "你家是怎么安排翻身的？评论区说说。",
    "我是翔哥，关注我，居家养老少踩坑。",
]

TIPS = [
    "开场坐对镜头，语气像在跟家属交底，别吓唬人",
    "讲皮肤时用手指在后背、屁股、脚后跟几个位置点一下",
    "讲翻身时做侧卧比画的手势，左右各一下",
    "讲吃喝时做背后垫高的动作，手势往上抬",
    "讲揉肚子时在肚子上顺时针画圈",
    "结尾语速放慢，「尽心尽力问心无愧」说慢一点，这句是情绪点",
    "字幕可标三件事，不写价格、不写疾病名",
]

FACT_TEXT = (
    "卧床老人日常照料科普（不代入产品）：长期卧床者同一部位皮肤长时间受压"
    "易出现问题，需勤翻身、勤擦洗，约每两小时翻身一次并左右交替，"
    "留意皮肤状态，发现异常可将该部位悬空保持干爽，有条件可配置防压垫；"
    "进食宜采取坐位或半卧位，背后垫高，避免平躺进食，餐后不宜立即平躺；"
    "卧床活动减少易致排便费劲，饮食宜软和易消化，保证膳食纤维和饮水，"
    "可顺时针轻揉腹部；长期不动会使力气减弱，需保证营养摄入、粗细搭配。"
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

    code = "SG-20261020-027"
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
             "7691102145769142370", "https://v.douyin.com/QYRO-63QLjE/",
             "家里老人刚刚卧床 你需要提前知道的那些事。#居家养老#养老护理#老人护理",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "贴对标「卧床几道坎」骨架；**不代入产品**；"
             "核心转换：讲日常照料怎么做，不讲会得什么病 —— "
             "疾病名（褥疮/吸入性肺炎）、医学术语（肌肉萎缩/吞咽功能退化）、"
             "疾病因果、营养功效断言全部去掉"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 128s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
