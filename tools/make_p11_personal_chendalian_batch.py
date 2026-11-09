# -*- coding: utf-8 -*-
"""个人号 080-084：按「陈大脸甄选」对标风格写 F2Q 折叠代步车 5 篇。

对标：陈大脸甄选（抖音号 C1585273.6019，店铺账号 / 老板出镜 / 工厂直供+避坑人设）
分析：.workbuddy/skills/scriptgen-writing/对标账号分析-陈大脸甄选.md
骨架：①完整介绍型（逐条报数）②实测答疑型（观众质疑开场+反问收尾）
      ③科普折叠型 ④送礼情感型 ⑤避坑科普型（账号主线）

★ 参数全部来自 docs/产品参数档案.md「F2Q」：19KG / 240W / 10AH六重保护 /
  折完宽44cm高98cm / 载重125KG / 前轮18后轮21.5(9寸实心) / 座高49.5宽37.5深36 /
  无具体续航km（不写公里数）
★ 竞品参数（16公斤/12公里/陀螺仪/大阻尼/四合一）一个都不抄
★ 合规：不写「安全/不会摔/轻轻松松/锻炼肌肉」等断言
"""
import io
import json
import os
import sqlite3
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scriptgen import util  # noqa: E402
from scriptgen import compliance  # noqa: E402

DB = os.path.join(ROOT, "data", "xmt.db")

FACT_TEXT = (
    "佳康顺F2Q轻便折叠旅游代步车（10AH锂电）：展开105×54×90CM，折叠高98CM宽44CM；"
    "净重19KG（不含电池扶手坐垫），最大载重125KG；座高49.5CM宽37.5CM深36CM；"
    "前轮18CM、后轮21.5CM（9寸大轮）；240W高效无刷电机（美国PRIDE同款）；"
    "10AH安规锂电池，六重保护；一拉即折叠（按钮往外一拉一压，专利号ZL2020 2 092755.4）、"
    "一拖即走；智能电磁刹车松开即刹、断电也能刹；陡坡自动匀速AI控速；"
    "拨杆向上手动推行/向下电动；双重弹簧减震+悬浮减震；免维护实心9寸大轮防爆防扎；"
    "环形把手控制面板、底部购物篮、可调节车头、前置大灯、防倾倒后轮、"
    "高回弹防水皮革坐垫、高靠背、宽大脚踏板；佳康顺18年医疗器械。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""

SCRIPTS = [
    {
        "code": "SG-20261023-080",
        "title": "这台折叠代步车能干四件事",
        "bench": ("https://www.douyin.com/video/7680137001514286309",
                  "7680137001514286309",
                  "四合一代步车完整版介绍来啦，感兴趣的朋友快来围观"),
        "lines": [
            "这台折叠代步车，能干四件事。",
            "第一件，能折。按钮一拉一压，折完四十四公分宽，后备箱搁得下。",
            "第二件，能拖。拉杆一拽，跟行李箱一样拖着走，坐高铁方便。",
            "第三件，能推。拨杆往上，子女推着老人逛公园。",
            "第四件，能开。拨杆往下是电动，240瓦，买菜逛公园够用。",
            "刹车松手就停，断电也刹得住。",
            "轮子是九寸实心轮，不用打气；整车十九公斤，一个人搬得上车。",
        ],
        "tips": [
            "单人出镜，站在一台展开的F2Q旁边，开口先报品类",
            "报「四件事」时用手势数，一到四，观众跟得上",
            "折叠真的折一次：拉按钮、往下一压，镜头给近景",
            "讲「一拖即走」时把车拖着走两步，别只站着说",
            "参数说慢一点：四十四公分、十九公斤、一百二十五公斤",
            "结尾停在展厅邀请，字幕不写价格不写门牌",
        ],
        "note": "陈大脸「完整介绍型」骨架：报品类+功能数 → 逐条报数 → 每条配场景 → 报参数 → 收尾安抚。",
    },
    {
        "code": "SG-20261023-081",
        "title": "轮子这么小过坎行不行",
        "bench": ("https://www.douyin.com/video/7690439597482903921",
                  "7690439597482903921",
                  "四合一老年代步车爬坡安全吗？请看户外实测"),
        "lines": [
            "好多叔叔阿姨问我：轮子这么小，过坎行不行？",
            "今天推出来，试给您看。",
            "开机先解锁，不解锁它不走，怕您没坐稳车就动了。",
            "前面这道坎三公分，一档直接开过去。",
            "上这个小坡用二档，240瓦电机，不用您使劲。",
            "刹车我松手了，您看，停了，没往前溜。",
            "下坡也松手就停，控制器自己压着速度。",
            "九寸实心轮，扎不破，不用打气。",
            "这么试完，您心里有数了吗？",
        ],
        "tips": [
            "户外实拍，找一道三公分左右的门槛和一个缓坡",
            "开场用观众质疑的原话起头，不要先夸产品",
            "每一个动作都要拍到位：解锁键、过坎、上坡、松手刹停",
            "下坡演示前说一句「我松手了啊」，制造现场感",
            "结尾反问，停顿两秒再接字幕",
        ],
        "note": "陈大脸「实测答疑型」骨架：观众质疑开场 → 说明测试条件 → 解锁/过坎/上坡/刹车/下坡逐项演示 → 反问收尾。",
    },
    {
        "code": "SG-20261023-082",
        "title": "折叠代步车到底怎么折怎么展开",
        "bench": ("https://www.douyin.com/video/7681975200456669818",
                  "7681975200456669818",
                  "一个视频告诉您，到底什么是三合一代步车？"),
        "lines": [
            "折叠代步车怎么折怎么展开，我演一遍。",
            "展开就一下，按钮一拉一压，撑开一台车，不用弯腰。",
            "把手高度能调，个子高往上提一点。",
            "拨杆往上推是手推，往下是电动，一车当两车用。",
            "坐垫靠背防水，脏了湿布一擦。",
            "座位高四十九点五，宽三十七点五，老人坐着正合适。",
            "折起来高九十八、宽四十四，后备箱、墙角都能搁。",
        ],
        "tips": [
            "桌面/空地演示，动作连贯，一镜到底最好",
            "展开和折叠各演示一次，中间不要剪断",
            "讲到尺寸时用手比一下四十四公分",
            "拨杆上下切换要拍到，观众才明白一车两用",
            "字幕只写尺寸，不写价格",
        ],
        "note": "陈大脸「科普介绍型」骨架：报产品 → 折叠/展开演示 → 逐项讲结构 → 报尺寸/座位 → 收尾陈述。",
    },
    {
        "code": "SG-20261023-083",
        "title": "送爸妈代步车别只问要不要",
        "bench": ("https://www.douyin.com/video/7692673275927004345",
                  "7692673275927004345",
                  "叔叔收到女儿送的四合一代步车，老幸福了"),
        "lines": [
            "问十句「要不要」，不如说一句「我给您买了」。",
            "常有子女来挑代步车，最后都落到这台折叠款。",
            "理由是能折能拖，回老家塞后备箱就行。",
            "老人自己拨杆就开，去村口坐坐不用人陪。",
            "刹车松手就停，反应慢半拍也没事。",
            "十九公斤，家里人一个人搬得动。",
            "座位宽三十七点五，坐垫防水，脏了擦一下。",
            "送长辈，他敢自己用才要紧。",
        ],
        "tips": [
            "可单人出镜，语气放软，别喊麦",
            "前两句对着镜头说，像唠家常",
            "讲「不用人陪」时给一个老人自己拨杆的示意动作",
            "结尾停在陈述句，不硬喊下单",
        ],
        "note": "陈大脸「送礼情感型」骨架：一句金句开场 → 子女挑车的真实场景 → 逐条说为什么选它 → 情感落点陈述收尾。",
    },
    {
        "code": "SG-20261023-084",
        "title": "买折叠代步车先避开这三个坑",
        "bench": ("https://www.douyin.com/video/7680916374746634939",
                  "7680916374746634939",
                  "网友直夸：这款四合一代步车真不赖"),
        "lines": [
            "买折叠代步车，先说三个坑。",
            "一，光图轻。车架薄了坐着晃，这台十九公斤，车架厚实。",
            "二，只看能折，不看折完多宽。这台折完四十四。",
            "三，电池不问保护。这台10AH，六重保护，能拆下来充。",
            "轮子也要问，充气轮扎了就趴窝，这台九寸实心轮。",
            "刹车当场试，松手看停不停得住，这台松手就刹。",
            "我不劝您买贵的，劝您买对的。",
        ],
        "tips": [
            "单人出镜，语气像熟人提醒，不像卖货",
            "三个坑用手指数，一条一条说，说完一条停顿一下",
            "讲电池时把电池拎出来给镜头看",
            "结尾那句「买对的」放慢，别配促销字幕",
        ],
        "note": "陈大脸账号主线「不踩坑、不花冤枉钱」的避坑骨架：先立三个坑 → 每条给判断方法 → 落到自家参数 → 收尾价值主张。",
    },
]


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    now = util.now_iso()
    for item in SCRIPTS:
        lines = item["lines"]
        body = {"format": "monologue",
                "lines": [{"speaker": "小冯", "beat": "口播", "text": t} for t in lines]}
        body_text = "\n".join(lines)
        spoken = util.strip_speakers(body_text)
        wc = util.count_chars(spoken)
        sec = util.estimate_seconds(spoken)
        target = 40.0
        scan = compliance.scan_script(
            body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])
        url, key, btitle = item["bench"]
        row = con.execute("SELECT id FROM sg_scripts WHERE code=?", (item["code"],)).fetchone()
        if row:
            con.execute(
                "UPDATE sg_scripts SET account_id='personal', account_label='个人号', "
                "presenters_json=?, title=?, body_json=?, body_md=?, word_count=?, "
                "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
                "compliance_json=?, facts_json=?, product_model=?, product_scope=?, "
                "benchmark_url=?, video_key=?, benchmark_title=?, notes=?, "
                "status='待审', version=version+1, updated_at=? WHERE code=?",
                (json.dumps(["小冯"], ensure_ascii=False), item["title"],
                 json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
                 json.dumps(item["tips"], ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False),
                 json.dumps([FACT_TEXT], ensure_ascii=False),
                 "F2Q轻便折叠旅游代步车10AH锂电", "型号",
                 url, key, btitle, item["note"], now, item["code"]))
        else:
            con.execute(
                "INSERT INTO sg_scripts (code, created_at, updated_at, status, "
                "account_id, account_label, presenters_json, source_platform, "
                "video_key, benchmark_url, benchmark_title, product_model, "
                "product_doc_ids_json, title, body_json, body_md, "
                "shooting_tips_json, publish_json, compliance_json, facts_json, "
                "word_count, estimated_seconds, target_seconds, version, "
                "product_scope, notes) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (item["code"], now, now, "待审", "personal", "个人号",
                 json.dumps(["小冯"], ensure_ascii=False), "douyin",
                 key, url, btitle,
                 "F2Q轻便折叠旅游代步车10AH锂电", json.dumps([], ensure_ascii=False),
                 item["title"], json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(item["tips"], ensure_ascii=False),
                 json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False),
                 json.dumps([FACT_TEXT], ensure_ascii=False),
                 wc, sec, target, 1, "型号", item["note"]))
        print("=== %s %s ===" % (item["code"], item["title"]))
        print("%d 字 / %.1f 秒（目标 %.0f）｜合规 %s" % (wc, sec, target, scan.get("counts")))
        for f in scan.get("findings") or []:
            print("  [%s] %s 「%s」 %s" % (f.get("severity"), f.get("rule_id"),
                                           f.get("match"), f.get("suggest") or ""))
        print()
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
