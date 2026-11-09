# -*- coding: utf-8 -*-
r"""口播号 012/013/014 重做：与 015/016/017 一起构成六篇互不同构的口播稿。

012 对标《爆款文案第四期 加钩子》——反常识 + 留悬念
    选题：刹车停不住（安全）
013 对标《20年前的广告现在还能用？》——现象 → 危害 → 原因 → 解决方案
    选题：上下床/上车那一下的转移（照护场景）
014 对标《爆款开头公式》第五条痛点罗列——嫌弃…的人一定要试试
    选题：闷、颠、不好清理（日常体感与清洁）

六篇互补：012 刹车 / 013 转移 / 014 闷颠脏 / 015 门槛通行 / 016 重量搬动 / 017 养护。
用法：.venv/Scripts/python.exe tools/make_oral_20261026_rewrite.py
"""
import io
import json
import os
import sqlite3
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scriptgen import util, compliance  # noqa: E402
from scriptgen.writer import body_plain_text  # noqa: E402

DB = os.path.join(ROOT, "data", "xmt.db")
TAIL = "关注翔哥，了解更多辅具知识。"

ORDERS = [
    # ---------- 012 刹车 ----------
    dict(
        code="SG-20261026-001",
        title="推老人下坡你敢不敢松手一秒钟",
        target=84.0,
        lines=[
            "推老人下坡那段路，你敢不敢松手一秒钟？",
            "很多车，一松手，车自己就往下跑。",
            "我在店里看了十年车，坡上出过事的不止一回。",
            "出事往往不是车难推，是停不住。",
            "刹车不是越紧越好，是你要停的地方，它得停得住。",
            "有的车按下去手一松就弹回来，平地上够用，坡上人得一直捏着。",
            "有的车按下去能卡住，手放开了还锁着，等红灯、等电梯的时候才敢松手。",
            "还有一种是锁轮圈的，力道更实，路不平也不容易溜。",
            "有的车两边轮子各一个刹，得两个都按下去才算停住，只按一边，车会打转。",
            "最怕的是车停住了还一点点往下溜。人不注意，一松劲，身子就往后仰。",
            "坐公交更明显。司机一脚刹车，车往前冲，老人手抓不住，全靠后面的人顶。",
            "试车别在平地上。找个缓坡，把车停住，松手，看它跑不跑。",
            "再问一句，他自己按得动吗，手掌有没有劲。",
            "车推得再顺，停不住就是麻烦。",
            TAIL,
        ],
        tips=[
            "第一句是问句，问完停一拍，让观众自己在心里回答",
            "「一松手，车自己就往下跑」手真的松开一下，动作比话狠",
            "「坡上出过事的不止一回」语气压下来，不要渲染细节",
            "三种刹车一种一句，手上各做一个动作：弹回、卡住、锁轮圈",
            "「找个缓坡」这句可以招手，像叫上人现在就去试",
            "「手掌有没有劲」这句是替家属想的，说慢一点",
            "结尾「停不住就是麻烦」收住，不解释，接固定尾句",
        ],
        notes="对标《爆款文案第四期 加钩子》反常识+留悬念：开场问句抛悬念（敢不敢松手），"
              "中段反转真正原因是停不住；选题为刹车安全，不碰尺寸适配母题；软版不写型号与价格",
    ),
    # ---------- 013 转移 ----------
    dict(
        code="SG-20261026-002",
        title="从轮椅挪到床上那一下最怕的是这几种",
        target=86.0,
        lines=[
            "从轮椅挪到床上那一下，两个人都屏着气。",
            "一个在背后抱，一个在旁边扶，稍微歪一点就得重来。",
            "家里一天要进进出出好几趟，趟趟这么挪，越挪越怕。",
            "摔过一回的，他自己就不敢动了，往后一步都等人来抱。",
            "挪不顺，问题常常不在人没劲，是车停的位置不对。",
            "车得能贴着床沿停，中间别隔着一截，人跨不过去就只能抬。",
            "脚踏挡路的，腿伸不直；能翻起来、能整个卸下来的，挪的时候腿才有地方放。",
            "车停稳之前先锁刹，别让人用身子顶着车。",
            "床也有关系。床高一点，人是往下去，稳当；床矮，人得往上抬，容易后仰。",
            "床靠墙的，车只能斜着停，更难挪，这时候宁可在床边加一块板过渡。",
            "家里人手少的，一个人挪最吃力。别让老人搂脖子，两个人一起倒更危险。",
            "真要挪，先把老人挪到床边坐稳，脚落地，再起身，一步一步来。",
            "买之前，让老人自己试着挪一次，家属站边上，先别急着抱。",
            "他自己能挪，往后才不用天天等人。",
            TAIL,
        ],
        tips=[
            "第一句「两个人都屏着气」说出来时也屏一下，别一笑就过去",
            "「一个抱，一个扶」用手比两个人的位置，画面立刻出来",
            "「越挪越怕」放慢，这句是情绪转折",
            "「摔过一回的」不要演摔倒，只说后果，说重一点就够",
            "「不是人没劲，是车停的位置不对」重读「位置」，这是反转点",
            "讲脚踏时真的抬一下腿，翻起来和拆下来两个动作分开做",
            "「先锁刹」手上按一下，动作要干脆",
            "结尾「不用天天等人」语气软下来，别喊，接固定尾句",
        ],
        notes="对标《20年前的广告现在还能用？》现象-危害-原因-解决方案四段式："
              "落脚在上下床/上车的转移安全；选题与尺寸、通行、重量都不重叠；软版不写型号价格与售后条款",
    ),
    # ---------- 014 闷、颠、不好清理 ----------
    dict(
        code="SG-20261026-003",
        title="又闷又颠还不好擦的轮椅最让人坐不住",
        target=85.0,
        lines=[
            "又闷、又颠、还不好擦的轮椅，家里有老人天天坐的最清楚。",
            "这三种毛病，我一个月听二十回。",
            "先说闷。后背和屁股捂一天，起身衣服是潮的。",
            "布面不透气，夏天更明显，坐一阵子人就想起身。",
            "再说颠。路上砖缝、石子，一路颠上去，老人的腰跟着一晃一晃。",
            "硬轮子省事，路况差的时候，颠得人不敢久坐。",
            "轮子大的过砖缝顺，小的灵活，可路面差就吃亏，得看家里外头是什么路。",
            "第三是难清理。汤洒了、水洒了，布面吸进去，抹一遍还是那股味。",
            "能拆下来洗的布面、能直接擦的坐板，日常就省一半事。",
            "洗也得有第二套换，不然拆下来那天老人没处坐。",
            "这三样，宣传页上一般不写。",
            "不用急着定。让老人上去坐坐，摸摸布面，问他闷不闷。",
            "再推着车走十米砖路，颠不颠，自己心里就有数。",
            "天天用的东西，坐着舒服不舒服，藏不住。",
            TAIL,
        ],
        tips=[
            "开场三连「又闷、又颠、又不好擦」一句一顿，节奏压住",
            "「我一个月听二十回」轻点头，是经验背书，别说成数据",
            "讲闷时手在背后扇一下，别描述太多",
            "讲颠时手在身前上下抖两下，幅度小一点",
            "「抹一遍还是那股味」皱一下鼻子，生活感就有了",
            "「宣传页上一般不写」压低声音，像说内行话",
            "「走十米砖路」可以抬脚示意，给一个能立刻照做的动作",
            "结尾「藏不住」看镜头，停半拍再接固定尾句",
        ],
        notes="对标《爆款开头公式》第五条痛点罗列结构：三种嫌法并列，逐条给判断动作；"
              "选题为体感与清洁（闷/颠/难擦），与 012 刹车、013 转移、015 门槛、016 重量、017 养护全不重叠",
    ),
]


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    disclaimer = util.compliance_config().get("disclaimer") or ""
    fact = ("辅具使用常识（不代入型号与参数）：轮椅制动装置分为按压回弹式与可锁定式，"
            "坡道、公交停靠等场景需确认制动后车轮不位移；转移时应使轮椅贴近床沿或座椅、"
            "移开或上翻脚踏并锁止车轮；透气坐垫、可拆洗布面与轮径、路况匹配程度会影响"
            "久坐体感与日常清洁难度。")

    for o in ORDERS:
        body = {"format": "monologue",
                "lines": [{"speaker": "", "beat": "口播", "text": t} for t in o["lines"]]}
        body_text = body_plain_text(body)
        spoken = util.strip_speakers(body_text)
        wc = util.count_chars(spoken)
        sec = util.estimate_seconds(spoken)
        scan = compliance.scan_script(body_text, {"disclaimer": disclaimer}, "", fact, [])
        now = util.now_iso()
        old = con.execute("SELECT publish_json FROM sg_scripts WHERE code=?", (o["code"],)).fetchone()
        publish = json.loads(old["publish_json"]) if old and old["publish_json"] else {}
        publish.setdefault("disclaimer", disclaimer)
        publish["douyin"] = dict(publish.get("douyin") or {})
        publish["douyin"]["title"] = o["title"]
        con.execute(
            "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
            "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, publish_json=?, "
            "compliance_json=?, facts_json=?, notes=?, version=version+1, updated_at=? "
            "WHERE code=?",
            (o["title"], json.dumps(body, ensure_ascii=False), body_text, wc, sec,
             o["target"], json.dumps(o["tips"], ensure_ascii=False),
             json.dumps(publish, ensure_ascii=False), json.dumps(scan, ensure_ascii=False),
             json.dumps([], ensure_ascii=False), o["notes"], now, o["code"]))
        print("=== %s %s ===" % (o["code"], o["title"]))
        print("%d 字 / %.1f 秒 ｜ 合规 %s" % (wc, sec, scan.get("counts")))
        print(body_text)
        for f in scan.get("findings") or []:
            print("  [%s] %s ｜「%s」｜ %s" % (f.get("severity"), f.get("rule_id"),
                                              f.get("match"), f.get("suggest") or ""))
        print()
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
