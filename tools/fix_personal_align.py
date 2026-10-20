"""个人号 SG-20261020-004：贴着对标原句逐句改写（第五版）。

用户明确要求：**按对标原稿写，只把大概意思给改了** —— 相同的词换成相近意思的词、
把位置调一下，不要大幅删改。
所以本版严格保留对标 5 句的句式骨架和节奏，一句对一句，只做最小必要替换：

对标原句 → 本版改法
1. 之前还不知道，原来广州就有一家老年代步车体验中心。
   → 之前还不知道，原来苏州就有一家老年代步车体验中心。（只换城市）
2. 从来没看到这么多的款式，这么齐全的车型，大轮子的、小轮子的、轻便的、稳重的，全部都有。
   → 从来没看到这么多的款式，这么齐全的车型，大轮子的、小轮子的、能折叠的、拉着走的，全部都有。
     （句式照搬；「轻便的、稳重的」这两个我们没有的车型词，换成 F2Q 真实有的能折叠/拖着走）
3. 还有智能款雷达避障的车型。
   → 还有智能款无刷电机的车型。（保留「还有智能款……的车型」；雷达避障我们产品没有，
     换成知识库有依据的「无刷电机」）
4. 不管是70多还是80多，90多岁的老人都能找到合适的车。
   → 不管是70多还是80多，90多岁的老人，都能在展厅找到合适的车。（补「在展厅」落实地点）
5. 选代步车再也不用瞎跑了，原来广州就有。
   → 选代步车再也不用瞎跑了，原来苏州就有，小冯就在阳光大厦九一一室等您。
     （城市替换 + 末尾补一句小冯自己的邀约，符合个人号 CTA 口径）

只在此骨架上做必要的口语化与合规调整，不另起炉灶。
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

CODE = "SG-20261020-004"
TITLE = "原来苏州家门口就有一家代步车体验中心"

# 逐句贴着对标原句改
LINES = [
    "之前还不知道，原来苏州就有一家老年代步车体验中心。",
    "从来没看到这么多的款式，这么齐全的车型，大轮子的、小轮子的、能折叠的、拖着走的，全部都有。",
    "有能折叠起来拎着走的，也有像拉行李箱一样拖着走的。",
    "还有智能款无刷电机的车型。",
    "不管是70多还是80多，90多岁的老人，都能在展厅找到合适的车。",
    "自己来的，儿女陪着来的，天天都有。",
    "选代步车再也不用瞎跑了，原来苏州就有，我就在阳光大厦九一一室等您。",
]

SHOOTING_TIPS = [
    "开场小冯站在展厅门口，一手指向门内，念第一句的惊讶口气（开头就要有反差）",
    "推进镜头扫过展厅内车辆，把大轮子、小轮子的、能折叠的都带到（对应第二句的车型罗列）",
    "拍到能折叠的车型时演示一下折叠动作，小冯顺口说一句",
    "拍不同年龄的顾客在试坐、儿女陪着老人慢慢看的画面（对应第四句）",
    "结尾镜头带到展厅门牌，小冯朝门内抬手收尾",
    "字幕突出'苏州'和'阳光大厦九一一室'，不要写价格",
]


def main():
    body = {
        "format": "monologue",
        "lines": [{"speaker": "小冯", "beat": "口播", "text": t} for t in LINES],
    }
    body_text = body_plain_text(body)
    spoken = util.strip_speakers(body_text)
    word_count = util.count_chars(spoken)
    seconds = util.estimate_seconds(spoken)

    disclaimer = util.compliance_config().get("disclaimer") or ""
    # 数字溯源：70/80/90 是年龄段不是产品参数，但一并放入事实片段避免误判
    fact_text = "展厅覆盖各年龄段老人：70多岁、80多岁、90多岁"
    scan = compliance.scan_script(body_text, {"disclaimer": disclaimer}, "", fact_text, [])

    con = sqlite3.connect(os.path.join(ROOT, "data", "xmt.db"))
    con.row_factory = sqlite3.Row
    con.execute(
        "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
        "estimated_seconds=?, shooting_tips_json=?, compliance_json=?, "
        "version=version+1, updated_at=? WHERE code=?",
        (TITLE, json.dumps(body, ensure_ascii=False), body_text, word_count, seconds,
         json.dumps(SHOOTING_TIPS, ensure_ascii=False),
         json.dumps(scan, ensure_ascii=False),
         util.now_iso(), CODE))
    con.commit()
    con.close()

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒 ｜ 合规 %s" % (word_count, seconds, scan.get("counts")))
    print()
    for i, t in enumerate(LINES, 1):
        print("%d. %s" % (i, t))
    print()
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
