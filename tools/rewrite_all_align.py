"""三篇旧稿按「贴对标原句改写」重做。

用户方法论：**贴对标原句改，不要另起炉灶** ——
保留对标每句的句式骨架、语序、节奏，一句对一句，只做最小必要替换：
  ① 换同义词/近义词 ② 调位置 ③ 替换我们没有或不能说的内容

对标原句见各段的 SOURCE 注释。本文件一次性重做三篇。
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

# ============================================================
# 001 个人号 · 小冯 · 品类通用
# 对标 SOURCE（顾店长·派斯莱德，17 句，45.3s）：
#   买代步车不要再当小白了，进店不管他怎么说，你就淡定的问他几个问题。
#   第一，什么车架？／车架决定了整车的重量…优选铝合金车架，不要碳钢车架。
#   第二，什么电机多少瓦？／动力决定了爬坡能力，优选有刷电机不低于500瓦…
#   第三，什么电池？／铅酸还是锂电？／预算充足选锂电，比轻…
#   第四，什么刹车？／电磁还是电子？／首选电磁刹车，断电不溜坡。
#   第五，轮胎是实心还是充气？／省心就选实心。
#   把这些问题记在手机里照着问一遍，能避开90%的坑。
#   只卖对的，不卖贵的。／关注顾店长，智能代步更放心。
# 改法：保留「五问」骨架和「第一…第五…」序数；删掉所有瓦数（知识库无来源）、
#       删掉「只卖对的不卖贵的」（价格暗示）；CTA 换成小冯的展厅邀约。
LINES_001 = [
    "买代步车别再当小白了，进店不管他怎么说，淡定点问他几个问题。",
    "第一，什么车架？车架决定整车重量，优选铝合金的，别选碳钢的。",
    "第二，什么电机？看动力够不够爬坡，别光听人家说智能。",
    "第三，什么电池？铅酸还是锂电？预算够就选锂电，使用频率高选容量大的。",
    "第四，什么刹车？电磁还是电子？选电磁的，松手就刹，坡上不溜车。",
    "第五，轮胎实心还是充气？老人天天出门就选实心的，省心。",
    "这几条记手机里，到店里照着问一遍，能避开大部分坑。",
    "我是小冯，在苏州阳光大厦九一一室，来了我陪您试一圈。",
]

TIPS_001 = [
    "开场手持手机做记录状，念第一句时语气认真，制造「别当小白」的紧迫感",
    "每说一个「第一…第五」，镜头给对应部件特写（车架、电机、电池、刹车、轮胎）",
    "念「第五」的时候蹲下拍轮胎，指一下是实心的",
    "念最后一句时抬头看镜头，指一下展厅方向",
    "字幕把「第一到第五」做成序号，逐条跟画面切",
]

# ============================================================
# 002 翔哥号 · 品类通用
# 对标 SOURCE（轮椅哥明月，27 句，115.8s）：
#   超过500块钱的轮椅都是智商税。／这轮椅你说有啥？／四个轮子加一个车架…
#   这都是我在评论区看到的。／我相信说这些话的人第一他不是残障人士…
#   大家可以上网搜一下这个轮组多少钱…／这个轮组是用在自行车上的，大几百大几千一对。
#   那么这种东西放在轮椅上，怎么就成了暴利了呢？
#   咱们这款轮椅做的非常扎实，大家看一下总宽度。／多少？／36的座宽，总宽度53厘米。
#   通过狭小的卫生间，甚至去高铁，都能畅通无阻。
#   还有一点，仅重9.5公斤。／大家可以在网上找一下…
#   然后咱们这款又非常结实，看看好不好用。／大家看一下啊／嘿！看到了吧，就这么灵活。
#   而且非常坚固，你听这个声音…／操纵起来看一下我撞那个地方…说停就停，说走就走。
# 改法：保留「评论区质疑 → 逐条反驳 → 现场演示 → 收尾」骨架和那句反问；
#       删掉所有价格和具体数字（9.5kg/53cm/36座宽/500元），改成定性描述；
#       保留「说停就停，说走就走」这种收尾口播。
LINES_002 = [
    "评论区老有人说，轮椅不就是几个轮子加个车架，不值什么钱。",
    "这都是我在评论区看到的。说句实话，说这话的人多半没用过轮椅。",
    "轮椅值不值钱，不在轮子，在坐得舒不舒服、推得省不省力。",
    "就拿坐高来说，太低了推起来费胳膊，这个很多轮椅都调不对。",
    "还有宽度，整车多宽就决定了能不能进窄门、进卫生间。",
    "轻便也重要，轻的子女单手能拎起来，带着出门方便。",
    "结实不结实、晃不晃，上手推两把就知道。",
    "所以轮椅好不好，别听人瞎说，自己上手试。",
    "我是翔哥，在苏州阳光大厦展厅，你来了我带你推一圈。",
]

TIPS_002 = [
    "开场正对镜头，表情认真，直接复述质疑，不铺垫",
    "讲到坐高时站在轮椅后方，手扶把手演示高度调节",
    "讲到宽度时拍整车过门的镜头（拍窄门通过），让画面说明问题",
    "讲到轻便时演示单手拎起或提起车架的动作",
    "讲推起来晃不晃时给轮子特写，用手拨一下听异响",
    "结尾语气转平，指向展厅邀请试车",
]

# ============================================================
# 003 品牌号 · 心悦+小冯 · F2Q
# 对标 SOURCE（皮皮熊，9 句，25.4s，抬杠对话）：
#   谁让你坐我新车的？／我自己也有，你这车下陡坡可别摔了。
#   我这车下坡会智能控速，才不会摔呢。
#   陡坡你上不去了吧？／我两手一搭，推我妈上陡坡很轻松，你儿子推不动吧？
#   你这车开得过窄门吗？／我这车啊，电机灵敏，轻松过。
#   你磕磕绊绊老撞门吧？／你还是换个好点的车吧！
# 改法：保留「A质疑→B回应→再质疑→再回应」的抬杠骨架和互不服气的口气；
#       把三个质疑点换成 F2Q 真实有的（坡道控速、爬坡动力、窄门通过）；
#       保留「你这车…吧？」这种挑衅句式。
PAIRS_003 = [
    ("心悦", "钩子", "你这车，下陡坡不溜车啊？"),
    ("小冯", "回应", "我这车，下坡自动匀速，不往前冲。"),
    ("心悦", "再质疑", "陡坡你上不去吧？"),
    ("小冯", "回应", "动力足，你儿子推不动，我来推您试试。"),
    ("心悦", "再质疑", "你这车，窄门过得去吗？"),
    ("小冯", "回应", "折叠后宽四十四公分，窄门轻松过。"),
    ("心悦", "再质疑", "坡上要停，溜车怎么办？"),
    ("小冯", "回应", "电磁刹车，松手就刹住。"),
    ("心悦", "收尾", "行，算你这车还行。"),
    ("心悦", "CTA", "来苏州阳光大厦展厅，坐一圈、试一圈。"),
]

TITLE_003 = "你这车下陡坡不溜车啊"


def render(lines, fmt="monologue"):
    if fmt == "dialogue":
        body = {"format": "dialogue",
                "lines": [{"speaker": s, "beat": b, "text": t} for s, b, t in lines]}
    else:
        body = {"format": "monologue",
                "lines": [{"speaker": "小冯", "beat": "口播", "text": t} for t in lines]}
    return body, body_plain_text(body)


def save(code, title, body, tips, fact_text=""):
    body_text = body_plain_text(body)
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    disclaimer = util.compliance_config().get("disclaimer") or ""
    scan = compliance.scan_script(body_text, {"disclaimer": disclaimer}, "", fact_text, [])
    con = sqlite3.connect(DB)
    con.execute(
        "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
        "estimated_seconds=?, shooting_tips_json=?, compliance_json=?, "
        "version=version+1, updated_at=? WHERE code=?",
        (title, json.dumps(body, ensure_ascii=False), body_text, wc, sec,
         json.dumps(tips, ensure_ascii=False),
         json.dumps(scan, ensure_ascii=False), util.now_iso(), code))
    con.commit()
    con.close()
    return body_text, wc, sec, scan


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    jobs = [
        ("SG-20261020-001", "买代步车先问这几个问题",
         LINES_001, TIPS_001, "monologue", ""),
        ("SG-20261020-002", "轮椅真不是几个轮子加个车架",
         LINES_002, TIPS_002, "monologue", ""),
        ("SG-20261020-003", TITLE_003, PAIRS_003, None, "dialogue",
         "折叠尺寸：高度98CM，宽度44CM 电机240W 无刷 陡坡自动匀速 智能电磁刹车"),
    ]
    for code, title, lines, tips, fmt, facts in jobs:
        body, _ = render(lines, fmt)
        t = tips if tips is not None else [
            "两人在展厅同框对坐或并肩站立，心悦先开口，语气带点挑衅",
            "小冯回应时配合演示动作：坡道匀速、爬坡、过门、刹车",
            "讲折叠后宽度时给折叠动作特写，镜头看到车身收窄",
            "两人对话节奏要快，一问一答不留空",
            "结尾两人一起看镜头，CTA 由心悦说，语气自然",
        ]
        body_text, wc, sec, scan = save(code, title, body, t, facts)
        print("=" * 62)
        print("%s ｜ %s" % (code, title))
        print("%d 字 / %.1f 秒 ｜ 合规 %s" % (wc, sec, scan.get("counts")))
        print("-" * 62)
        print(body_text)
        for f in scan.get("findings") or []:
            print("  [%s] %s ｜「%s」｜ %s" % (
                f.get("severity"), f.get("rule_id"), f.get("match"),
                f.get("suggest") or ""))
        print()


if __name__ == "__main__":
    main()
