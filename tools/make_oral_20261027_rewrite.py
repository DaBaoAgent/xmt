# -*- coding: utf-8 -*-
r"""口播号 015/016/017 重做：三篇各拆一条对标视频的不同逻辑，选题与句式互不复用。

015 对标《短视频开头第一句全教学》方向一「替观众说出他的处境」
    骨架：具体到细节的处境 → 说出观众心里那句抱怨 → 反转真正原因 → 量三个数 → 当场验证
    选题：门槛 / 门宽 / 电梯过不去（通行），不碰尺寸适配母题
016 对标《短视频爆款结构 两大模型》PREP（观点-理由-案例-重申）
    选题：一天要搬几次（重量与搬动）
017 对标《教会你无限复制爆款》无限游戏逻辑
    骨架：反常识断言 → 经验自证 → 多数人怎么做 → 错在把长期事当一次消费 → 代价 → 养护动作
    选题：用久了松、响（整备与养护）

用法：.venv/Scripts/python.exe tools/make_oral_20261027_rewrite.py
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
    # ---------- 015 ----------
    dict(
        code="SG-20261027-001",
        title="老人不愿意出门问题常在那三厘米的门槛",
        target=82.0,
        lines=[
            "推到自家门口那道门槛，前轮一顶，车往后弹一下，人跟着晃一下。",
            "儿女当场就来一句，这车怎么这么难推。",
            "真不一定是难推。",
            "门净宽八十，车宽七十四，两边各剩三厘米，手一歪就蹭门框。",
            "老人缩着肩膀过门，一次两次还行，天天这样，他就不想出门了。",
            "我见过太多这样的车，买回去只在客厅里转圈。",
            "挑车之前先量三个数：家门净宽、卫生间门宽、电梯门宽。",
            "三个数里挑最小的，减掉四厘米，就是车能顺顺当当过去的宽度。",
            "再蹲下来看一眼前轮，轮子大一点，过门槛才不容易顶住。",
            "别在店里光看外面。推着车到门口顶一次门槛，当场就知道行不行。",
            "车能不能出这个门，比车好不好看要紧得多。",
            TAIL,
        ],
        tips=[
            "第一句不要平着念，「一顶」「弹一下」「晃一下」三个动作连着做，手上要有动作",
            "「儿女当场就来一句」换成家里人的口气，别念成旁白",
            "「真不一定是难推」重读「不一定」，停半拍再解释，这是反转点",
            "说门宽车宽时两只手比出两边各剩多少，比数字更有画面",
            "「缩着肩膀过门」自己先缩一下肩，观众立刻懂",
            "「只在客厅里转圈」用手指在身前画个小圈，别多说",
            "量三个数时伸三根手指，一个数点一下，节奏要稳",
            "结尾「顶一次门槛」可以招手，像是带人过去试",
        ],
        notes="对标《短视频开头第一句全教学》方向一替观众说出处境：门槛卡住的具体细节开场；"
              "选题为通行（门宽/门槛/电梯），与尺寸适配母题完全分开；软版不写型号价格",
    ),
    # ---------- 016 ----------
    dict(
        code="SG-20261027-002",
        title="轮椅搬不动再结实也没人愿意用",
        target=85.0,
        lines=[
            "挑轮椅，先算一件事，一天要搬几回。",
            "老人自己上下车要搬，儿女装后备箱要搬，没电梯的楼，一天上上下下就是三四回。",
            "车重两公斤，前面听着不算什么，搬起来就是多喘两口气，多歇一回。",
            "我们这行有句话，买的时候看结不结实，用的时候看轻不轻。",
            "前年有个客户，住六楼没电梯，家里挑了台特别敦实的，二十多公斤。",
            "第一次下楼，两个人抬，抬到三楼歇一次。",
            "第二次就不愿意抬了，那车从此搁在楼道拐角。",
            "后来换了台轻的，老人一只手拎得起来，天天下楼晒太阳。",
            "轻不等于不结实。车架用什么料、焊点扎不扎实，跟轻重是两码事。",
            "挑的时候别只听人说结实，你自己提着车架的一头离地试试。",
            "拎得动，才谈得上天天用。",
            TAIL,
        ],
        tips=[
            "第一句「一天要搬几回」问出来，顿一下，让观众自己心里数",
            "「装后备箱」时两手做抬举动作，动作要脆",
            "「多喘两口气」可以说得像真喘了一下，别修饰",
            "「看结不结实」和「看轻不轻」两句对着说，一前一后两个手势",
            "案例段放平语气，像在讲邻居家的事，「二十多公斤」可以比个抱的动作",
            "「抬到三楼歇一次」停一拍，这是全片的转折",
            "「搁在楼道拐角」往旁边一眼，别多解释",
            "结尾「拎得动」时一只手真的提一下，动作就是论点",
        ],
        notes="对标《短视频爆款结构 两大模型》PREP：观点（一天搬几回）→ 理由 → 六楼客户案例 → 重申；"
              "选题为重量与搬动，不写坐宽坐深、不写型号价格",
    ),
    # ---------- 017 ----------
    dict(
        code="SG-20261027-003",
        title="轮椅不是买回来的东西是养出来的",
        target=86.0,
        lines=[
            "轮椅不是买回家就完事的，它是往后几年要一直养着的东西。",
            "我干辅具这行十年，看过太多车，头一年好推，第二年就开始响。",
            "多数人买车只问一件事，牢不牢。",
            "没人问这车往后谁给它紧螺丝。",
            "一台车天天承重、天天颠，螺丝会松，轮子会偏，脚踏垫会磨平。",
            "松了没人管，偏了没人调，越晃越厉害，最后老人一句这车不行，其实只是没整备过。",
            "家里能做的其实不多，就几件小事。",
            "三个月摸一遍螺丝，扶手和靠背晃不晃，晃就紧。",
            "脚踏垫磨得发亮了，换一块，脚底才不打滑。",
            "轮子推起来跑偏，别硬推，找个师傅把轴调正。",
            "布面塌了就该换，塌下去的布面人坐不住。",
            "车养得住，人才愿意天天坐。",
            TAIL,
        ],
        tips=[
            "第一句「不是买回家就完事的」语气要笃定，别商量",
            "「第二年就开始响」可以学一声咯吱，别演过头",
            "「多少钱，结不结实」两句问得快，这是多数人的真实状态",
            "「谁给它紧螺丝」放慢，这句是全片的钩子",
            "讲螺丝、轮子、脚踏垫三样时手依次点三下，节奏跟上",
            "「老人一句这车不行」换成家属转述的口气，别评判",
            "养护四件事一件一件说，每件说完停半拍，方便人记",
            "结尾「车养得住」看镜头，语气收住，再进固定尾句",
        ],
        notes="对标《教会你无限复制爆款》无限游戏逻辑：别把长期的事当成一次消费；"
              "选题为整备与养护，不碰尺寸、不碰价格与服务承诺",
    ),
]


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    disclaimer = util.compliance_config().get("disclaimer") or ""
    fact = ("辅具使用与维护常识（不代入型号与参数）：轮椅长期承重使用后，紧固件松动、"
            "轮轴偏移、脚踏垫磨损、座布下塌均会影响推行与坐姿稳定，定期检查与更换易损件"
            "可维持正常使用状态；选购时还应核对家门、卫生间门与电梯门的通行净宽。")

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
        print()
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
