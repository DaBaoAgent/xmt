"""个人号 SG-20261020-004 简化定稿：句子更短，去书面词。

用户反馈「稍微简单一点」——原稿 229 字/54.5 秒偏长，且有「我每次进去都得转一圈
才认全」「每个人都透着认真」这类偏书面的表达。改成更口语的短句。

要点保持不变：个人号小冯第一人称、展厅惊讶式种草的钩子、不代入任何产品。
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
TITLE = "苏州街坊有福了，家门口就能试代步车"

LINES = [
    "您知道吗，苏州阳光大厦展厅里代步车特别多。",
    "大轮子小轮子，轻便的笨重的，都有。",
    "我常驻昆山，又天天往展厅跑，车型多得自己都转不过来。",
    "昨天刚帮忙搬了几辆新车进来。",
    "有些车能折叠，拎得动；有些拖着走，跟拉箱子一样。",
    "来挑车的人挺多，自己来的，儿女陪着来的都有。",
    "在展厅里摸摸座椅，试试把手，慢慢看，不着急。",
    "有位阿姨来的时候说，看广告看花了眼了，不知道该买哪种。",
    "在这儿坐一圈、试一圈，她就明白自己该要哪一款了。",
    "您要是给家里长辈找代步车，拿不准买哪种，就来展厅坐坐试一圈。",
    "心里就有数了。",
]

SHOOTING_TIPS = [
    "开场镜头从展厅门口推进，展示满墙的代步车，小冯边走边介绍",
    "中景拍摄小冯搬动一辆代步车入库的动作，背景有不同款式车辆",
    "特写镜头捕捉几位不同年龄的顾客在试坐、触摸车辆细节",
    "结尾镜头小冯站在展厅中央，做出邀请手势指向周围车辆",
    "字幕突出'苏州阳光大厦911室'地址信息和'来试坐再决定'的提示",
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
    scan = compliance.scan_script(body_text, {"disclaimer": disclaimer}, "", "", [])

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
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」" % (f.get("severity"), f.get("rule_id"), f.get("match")))


if __name__ == "__main__":
    main()
