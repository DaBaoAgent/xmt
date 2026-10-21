# -*- coding: utf-8 -*-
"""品牌号 069-072：小飞燕护理手推车，4 个完全不同的场景（单人口播·小冯）。

形式：单人口播（用户已明确「我不要对话的」），约 95-110 字/篇，
结尾落评论区互动，不加地址不写价格。

小飞燕 = 佳康顺**护理手推车**（全家可用轮椅，手动推行，无电机）。
参数逐字回查本地详情页 Z:\\7 详情页\\35  小飞燕（主图 + 25 张详情图）：
1 全家都能用 护理手推车 WHEELCHAIR
2 免安装、打开即用更省心
3 轻巧便携、折叠不占空间
4 防后倾小轮：爬坡时自动触地支撑、防止后翻
5 靠背双档可调：95°端坐 / 145°仰躺，前后提拉精准分档稳固锁定
6 加大底座加宽轴距：平稳出行、无惧颠簸
7 360°万向前轮：顺滑不卡顿
8 稳固弹性实心轮：耐磨防滑、推行顺畅
9 加厚碳钢合金：管壁加厚、耐磨抗锈、不易变形、承重更高
10 老人代步 / 孕妈代步 / 儿童代步 全家可用
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

BATCH = [
    ("SG-20261020-069", "吃饭的时候怎么坐", [
        "小飞燕？吃饭的时候让人坐哪儿合适？",
        "靠背能提拉调两档，九十五度坐直了吃饭正好。",
        "往后一拉，一百四十五度，往后靠着歇会儿也成。",
        "底座加大加宽，坐上去不晃。",
        "买回去不用装，打开就能用，省心。",
        "家里有吃饭要人推的，评论区说说。",
    ]),
    ("SG-20261020-070", "带娃出来遛弯坐得稳吗", [
        "带娃出来遛弯，这车坐着稳不稳？",
        "前轮是三百六十度万向的，原地就能调头。",
        "轮子是弹性实心轮，耐磨防滑，推行也顺当。",
        "底座加宽轴距，过小坎儿不飘。",
        "孩子坐累了，靠背还能放倒躺一会儿。",
        "带娃出门的，评论区说说。",
    ]),
    ("SG-20261020-071", "带去看医生好不好搬", [
        "带老人去医院，车好不好搬？",
        "小飞燕轻巧便携，折叠起来不占地方，后备箱里塞得下。",
        "免安装，打开即用，不用费劲组装，也不用找人装。",
        "车架是加厚碳钢合金，壁厚耐磨抗锈，用久了不塌。",
        "折叠了拎着走，也不沉。",
        "常跑医院的，评论区说说。",
    ]),
    ("SG-20261020-072", "推一上午手累不累", [
        "推着人走一上午，推的人手累不累？",
        "万向前轮顺滑不卡顿，转弯不用使劲拧。",
        "实心轮推行顺畅，轮子不吃地面。",
        "底座加大加宽轴距，走起来不东倒西歪。",
        "车架加厚碳钢，推着心里踏实。",
        "家里谁天天推人遛弯的，评论区说说。",
    ]),
]

TIPS = [
    "单人出镜，站在一台小飞燕旁边，边说边做动作",
    "讲靠背两档时真的提拉一下，让观众看见档位",
    "讲折叠就当场折一下，别只说",
    "结尾停在评论区那句，不加地址不写价格",
    "字幕可标功能名（如「防后倾小轮」），不写价格",
]

FACT_TEXT = (
    "佳康顺小飞燕护理手推车（全家可用轮椅，手动推行无电机）："
    "免安装打开即用、轻巧便携折叠不占空间、"
    "防后倾小轮（爬坡时自动触地支撑防止后翻）、"
    "靠背双档可调（95°端坐/145°仰躺，前后提拉精准分档稳固锁定）、"
    "加大底座加宽轴距（平稳出行无惧颠簸）、360°万向前轮（顺滑不卡顿）、"
    "稳固弹性实心轮（耐磨防滑推行顺畅）、"
    "加厚碳钢合金（管壁加厚、耐磨抗锈、不易变形、承重更高）、"
    "适用老人代步/孕妈代步/儿童代步。"
)

DISCLAIMER = util.compliance_config().get("disclaimer") or ""
BENCH_URL = "https://v.douyin.com/h3AJIsVteww/"
BENCH_KEY = "7674149769651997988"


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    for code, title, lines in BATCH:
        body = {"format": "monologue",
                "lines": [{"speaker": "小冯", "beat": "口播", "text": t}
                          for t in lines]}
        body_text = "\n".join(lines)
        spoken = util.strip_speakers(body_text)
        wc = util.count_chars(spoken)
        sec = util.estimate_seconds(spoken)
        target = round(max(30, min(45, 21.1)), 1)
        scan = compliance.scan_script(
            body_text, {"disclaimer": DISCLAIMER}, "", FACT_TEXT, [])
        now = util.now_iso()
        row = con.execute("SELECT id FROM sg_scripts WHERE code=?",
                          (code,)).fetchone()
        if row:
            con.execute(
                "UPDATE sg_scripts SET account_id='brand', account_label='品牌号', "
                "presenters_json=?, title=?, body_json=?, body_md=?, word_count=?, "
                "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
                "compliance_json=?, product_model=?, product_scope=?, "
                "status='待审', version=version+1, updated_at=? WHERE code=?",
                (json.dumps(["小冯"], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
                 json.dumps(TIPS, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), "小飞燕护理手推车", "型号",
                 now, code))
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
                (code, now, now, "待审", "brand", "品牌号",
                 json.dumps(["小冯"], ensure_ascii=False), "douyin",
                 BENCH_KEY, BENCH_URL, "遇见这么能炫耀的你会怎么办？",
                 "小飞燕护理手推车", json.dumps([], ensure_ascii=False), title,
                 json.dumps(body, ensure_ascii=False), body_text,
                 json.dumps(TIPS, ensure_ascii=False),
                 json.dumps({"disclaimer": DISCLAIMER}, ensure_ascii=False),
                 json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
                 wc, sec, target, 1, "型号",
                 "小飞燕护理手推车，单人口播（用户明确不要对话版），"
                 "四个完全不同的场景：吃饭/带娃/看病/长时间推行。"
                 "参数逐字回查本地详情页 Z:\\7 详情页\\35  小飞燕。"
                 "**是手推车，无电机无摇杆无刹车，稿里不写**。"))
        print("%s %s ｜ %d 字 / %.1f 秒 ｜ 合规 %s" % (
            code, title, wc, sec, scan.get("counts")))
        for f in scan.get("findings") or []:
            print("  [%s] %s 「%s」 %s" % (
                f.get("severity"), f.get("rule_id"), f.get("match"),
                f.get("suggest") or ""))
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
