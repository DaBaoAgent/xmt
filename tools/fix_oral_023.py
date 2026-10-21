"""口播号 SG-20261020-023：贴对标原句改写（抖音·买手动的还是电动的）。

对标（363 字 / 68 秒）结构：
  引子：买轮椅手动还是电动，取决于使用者的年龄、身体状况、使用场景
  ① 年龄：年龄偏大身体功能和大脑反应能力都会下降，为了个人安全考虑，
     建议头脑清醒、手部功能正常的人用低速电动轮椅；
     身体状况差一些的在家人陪同下用手动轮椅
  ② 身体状况：上肢功能正常建议手动轮椅；手臂功能好，能用手掌和手臂发力，
     也可以用手动轮椅；经常活动才能维持身体健康，千万不要对电动轮椅产生依赖
  ③ 使用场景：室内两种都行；室外电动轮椅时速慢、续航短、巨航段受限；
     长距离出行要坐交通工具的，可以选手动轮椅加车头（坐高铁能骑着上），
     这种组合时速快、续航远都灵活
  结尾：还不知道怎么选，评论区留言

**⚠️ 对标踩我们合规线的四处，已改**：
1. 「年龄偏大，**身体功能和大脑反应能力都会下降**」→ 对老年人的能力贬损，
   且是健康断言 → 改成「年纪大了，选择上更要求稳当、好操作」，
   不做能力贬损。
2. 「**经常活动才能维持身体的健康**」→ 健康功效断言（efficacy 类）→
   改成「多活动活动，人也舒坦些」，不承诺健康效果。
3. 「**千万不要对电动轮椅产生依赖**」→ 负面/诱导性表述 →
   改成中性的「按自己的力气和习惯来选」。
4. 「**为了您的个人安全考虑**」+ 分级建议 → 安全断言 →
   改成客观的功能对比，不下安全结论。

产品口径：**不代入产品**（用户指定）—— 纯科普。

口播号人设：翔哥，十年辅具；直给、短句、口语化；敢说「别急着买」，不贬低友商。
60-90 秒 / 260-400 字。CTA：关注翔哥/评论区聊聊/转给需要的人。

长度贴对标（68 秒 / 363 字），写 ~370 字 / 78 秒左右。
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

TITLE = "买轮椅，手动的还是电动的"

LINES = [
    "买轮椅，手动的还是电动的？",
    "这个没有标准答案，看三样东西。",
    "头一样，年纪和力气。",
    "年纪大一些的，选车上操作简单、坐上去就稳当的，比什么都要紧。",
    "手上有劲的，手动轮椅推着走，反倒更自在。",
    "第二样，胳膊使不使得上劲。",
    "手动轮椅靠手掌和手臂发力，长期用，臂力得跟上。",
    "要是胳膊没劲，硬推久了手腕肩膀都吃不消。",
    "这种情况，电动的能省不少力。",
    "多活动活动人也舒坦些，按自己力气和习惯选就好。",
    "第三样，使用场景。",
    "屋里头用，两种都合适。",
    "出门去公园、菜场，电动轮椅劲儿大，速度也能自己调。",
    "但它重，搬上搬下没那么方便，续航也得留个余量。",
    "要是经常要出远门、坐高铁，手动轮椅配个车头更合适。",
    "到了地方拆开车头，折叠起来能带着走。",
    "这种组合走得远也灵活。",
    "所以别一上来就问哪个好。",
    "先想想谁用、在哪儿用、怎么用。",
    "这三样想清楚，答案自然就出来了。",
    "你家买的是哪种？评论区说说。",
    "我是翔哥，关注我，挑车少走弯路。",
]

TIPS = [
    "开场坐对镜头，语气像在跟人商量，别像下结论",
    "讲胳膊发力时用手比画推轮圈的动作",
    "讲电动省力时指一下车上的控制器",
    "讲高铁场景时做折叠动作，然后拎一下示意能带走",
    "结尾看镜头邀请评论区互动，语速放慢",
    "字幕可标三个判断维度，不写价格",
]

FACT_TEXT = (
    "轮椅选购科普（不代入产品）：手动轮椅依靠手掌和手臂推动轮圈发力，"
    "长期使用需要臂力；电动轮椅由电机驱动，操作相对省力，速度可调节，"
    "但整车分量更重、搬抬不便，续航需留余量；手动轮椅可加装车头组合使用，"
    "折叠后便于携带、适合乘坐高铁等长途出行场景。"
    "选购建议：一看使用者和年纪力气，二看胳膊使不使得上劲，三看使用场景。"
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

    code = "SG-20261020-023"
    target = 78.0
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
             "7240281678927646009", "https://v.douyin.com/MCdn5XKBsEU/",
             "买轮椅不知道是该买手动的还是电动的？#轮椅#残疾人辅具#老年人",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "贴对标「手动 vs 电动」三维度骨架；**不代入产品**（用户指定）；"
             "对标四处合规问题已改：能力贬损→求稳当好操作、"
             "才能维持健康→人也舒坦些、不要产生依赖→按自己力气和习惯、"
             "为了个人安全→客观功能对比"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 68s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
