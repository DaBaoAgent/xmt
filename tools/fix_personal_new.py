"""个人号 SG-20261020-004 全新定稿（第四版）。

用户要求：不要提「昆山苏州两头跑」，按原来那版的大意重写一篇全新的稿子。
这一版重新构思，不在上一版上打补丁：
  - 只在小冯自己待的展厅里讲，不提工厂、不提两地跑
  - 保留对标视频「原来家门口就有、车型多、不用瞎跑」的核心手法
  - 口语化短句，不代入任何产品
  - CTA 只落展厅地址（合规 contact 规则禁「加微信」这类）
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
TITLE = "原来苏州家门口就有这么个地方"

LINES = [
    "跟您说个事儿，您可能不信。",
    "苏州阳光大厦九一一室，那儿有个展厅，专门看代步车。",
    "我是天天在里头待着的。",
    "一进门您就知道，大轮子的、小轮子的、能折叠的，都有。",
    "七八十岁的老人来，儿女陪着来的，都有。",
    "上周有个阿姨，进门就说：早知道这么近，我跑什么商场啊。",
    "她在展厅里坐了一圈、试了一圈，出来跟我讲，心里有底了。",
    "选车这事，光看照片真看不明白。",
    "坐下来、推两把，那个合不合手，一试就出来了。",
    "您在苏州的街坊，需要给家里长辈挑代步车，就来阳光大厦九一一室看看。",
    "跑一趟，比您在网上翻半天强。",
]

SHOOTING_TIPS = [
    "开场小冯站在展厅门口，一手指向门内，一边说开场白，语气像跟街坊拉家常",
    "推进镜头展示展厅内车辆分布，扫到大轮子、小轮子、可折叠的车型",
    "拍小冯跟顾客打招呼、陪同试坐的真实场景，不要摆拍",
    "特写顾客坐上车、伸手摸把手、试着推两下的动作",
    "结尾镜头带到展厅门牌（九一一室），小冯朝门内抬手示意",
    "字幕突出'苏州阳光大厦九一一室'，别写价格",
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
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
