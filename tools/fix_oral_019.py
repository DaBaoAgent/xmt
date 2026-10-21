"""口播号 SG-20261020-019：贴对标原句改写（抖音·轮椅定制），代入博爱方特 BA-LZ-2。

对标（542 字 / 90 秒）逐段结构：
  疑问开场：我们都说轮椅需要定制，定制包含哪些内容呢？
  ① 尺寸：坐宽（髋关节最宽处）/坐深（尾骨平面到腿窝减四指）/小腿长/
     靠背高（坐面往上到推把高度）/前坐高、后坐高
  ② 配置：车架颜色、辐条颜色、前叉颜色、小轮颜色、手圈宽窄圆扁、
     靠背软硬、靠背高度弧度、车架管预留长度、重心前后调节
      （技术不好调后面不易后翻 / 技术好调前面滑着轻）
  ③ 效果：坐起来贴合身体、舒服、滑起来轻松
  ④ 颜色按个性喜好选配
  ⑤ 结尾：让刚受伤的伤友少走弯路、多了解辅具知识、少花冤枉钱

产品口径：博爱方特 BA-LZ-2 铝合金焊接车架（成人款）—— 用户指定。
参数逐字回查知识库画册：
  坐宽 六档可选 36/38/40/42/44/46cm（贴合不同体型）
  坐深 36-48 可调节（厘米级）
  前坐高 39-52 可调节（不含坐垫）
  后坐高 37-44 可调节（不含坐垫）
  车架 7003航空铝合金；水平长度 58cm、62cm
  坐垫板 碳纤维板+尼龙绷带；绷带松紧可调
  硬靠背 碳纤维；可快拆，高低及角度可调
  刹车 铝合金；鹰嘴刹车、前推刹车（自选）
  挡腿带 碳纤维；高低、前后、角度可调，可上翻
  前轮 铝合金硬质阳极：黑、钛、金、蓝、红、紫
  后轮 免充气胎 4 寸、5 寸；尺寸自选
  推把 铝合金；高低可调（可选折叠/不折叠）
  包裹 半包裹/浅包裹/浅包裹+摆位=深包裹
  质保 铝合金车架 5 年、其他部件 2 年、内胎 1 年
  售后 收到 3 天内尺寸/重心不合适可线上指导，返厂运费公司承担

口播号人设（config/personas.json 的 oral）：
  翔哥，做了十年养老辅具，常驻苏州阳光大厦展厅；直给、短句、口语化，
  一句话一个信息点；敢说「别急着买」，但不贬低友商。
  60-90 秒 / 260-400 字。CTA：关注翔哥/评论区聊聊/转给需要的人。

⚠️ 合规注意：不能说「治好/疗效」；「全额退款」涉及 price 规则，弱化为
  「不合适能返厂调」；尺寸参数必须与画册一致，不编。
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

TITLE = "轮椅定制到底定制些什么"

LINES = [
    "总有人问我，轮椅定制，定的是些什么？",
    "今天一条讲清楚，看完少花冤枉钱。",
    "第一样，尺寸。",
    "坐宽，就是你屁股两边最宽那块，量准了才不挤。",
    "坐深，尾骨到腿窝，留四指，坐久了不顶。",
    "靠背高低和角度，也是可调的，腰有地方靠。",
    "第二样，配置。",
    "手划圈，宽窄圆扁随你挑。",
    "第三样，重心。",
    "这个最要紧。",
    "技术还不太行的，重心往后调，不容易后翻。",
    "滑得顺的，重心往前调，推起来特别轻。",
    "博爱方特这台，这些都能按你的尺寸和喜好来。",
    "车架是航空铝的，坐宽六档，三十六到四十六公分。",
    "坐深也能调，三十六到四十八。",
    "前坐高三十九到五十二，后坐高三十七到四十四。",
    "靠背碳纤维，能快拆，高低角度都能调。",
    "前轮颜色还有黑、钛、金、蓝、红、紫，按你喜好选。",
    "定完了坐上去贴合身体，滑起来也省劲。",
    "要是拿不准尺寸，来苏州阳光大厦展厅找我。",
    "我帮你量，帮你调。",
    "我是翔哥，做了十年辅具，关注我，少走弯路。",
]

TIPS = [
    "开场坐对镜头，语气像在回答评论区提问，别端着",
    "讲尺寸时手里拿卷尺，边说边在自己身上比画量点",
    "讲重心时两手在车架上做前后推的动作，让观众看懂重心在哪",
    "讲颜色选配时镜头扫过几台不同颜色前轮的车",
    "讲到「帮你量帮你调」时抬手指一下展厅方向",
    "结尾看镜头说关注，语速放慢",
    "字幕可标坐宽坐深的数字区间，不写价格",
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
    "集国内外运动轮椅之所长可调式运动轮椅"
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

    code = "SG-20261020-019"
    target = 90.0
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
             "7270717061381295416", "https://v.douyin.com/P3C38RT6V5Q/",
             "轮椅定制包含哪些内容？#轮椅",
             "博爱方特BA-LZ-2",
             json.dumps(["jks-product/博爱方特画册四-BA-LZ-2铝合金焊接车架(成人款）-20260827.pdf"],
                        ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "型号",
             "贴对标「轮椅定制包含哪些内容」骨架，代入博爱方特 BA-LZ-2 铝合金焊接车架"
             "（成人款）；尺寸参数逐字回查画册，不编"))
        print("已新建", code)
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 90s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
