# -*- coding: utf-8 -*-
"""口播号（老大号）定改制轮椅稿：对标《硬广变软广的阳谋短视频开头》。

对标：https://v.douyin.com/3PgSTLQ5x3e/ → douyin_7673385070476906865（528字/约75秒）
对标讲的「阳谋三句开头」：
  ① 理解难处——不是他不想，而是真的没有条件（"找不到对象，不是不想找，而是没时间"）
  ② 激发欲望——谁都想……也想……（把向往的画面说给观众听）
  ③ 替他说话——但现在行业太乱/被坑了，不是你的错
  ④ 给方法——今天我给你几个方法，让你……
本稿只借这个骨架，正文不出现「阳谋」「公式」「套路」等元叙事。

定改制轮椅：品类通用，不报型号、不报价格、不报数字；手动款，不写电动词。
口播号人设：翔哥，单人独播 60-90 秒 / 260-400 字，尾句统一 FIXED_TAIL。
同批已有 001 下坡刹车、002 上下床转移、003 闷颠难擦、004 门槛、005 重量、006 养护，
本稿走「老人不愿出门=车不合身」，与 004 门槛母题区分（那是通行，这是合身）。
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

BENCH_URL = "https://v.douyin.com/3PgSTLQ5x3e/"
BENCH_KEY = "7673385070476906865"
BENCH_TITLE = "硬广变软广的阳谋短视频开头 #编导 #代运营 #短视频干货分享"

FACT_TEXT = (
    "定改制轮椅：按使用者身高、腿长、坐宽、坐深实测，结合由谁推、路上的坡坎情况，"
    "调整坐高、坐深、脚踏高低、扶手位置，属于手动轮椅的尺寸与结构定改制，"
    "坐上去不合适可继续微调。品类通用口径，不涉及具体型号参数。"
)

CODE = "SG-20261027-006"
TITLE = "老人坐上轮椅就不爱出门，多半不是他不想动"

LINES = [
    "很多老人坐上轮椅以后，就不爱出门了。",
    "不是他不想动，是这车不合他的身。",
    "我在店里看了十年车，这种事见得最多。",
    "坐垫高了一指，脚就悬着，坐一会儿腿就不舒服。",
    "坐深不对，人往前出溜，得一直拿胳膊撑着。",
    "靠背直挺挺的，腰后头空着，坐久了整个人往下滑。",
    "谁都想推着老人出门的时候，他能自己坐直了，看看街上。",
    "谁都想他自己扶着扶手能挪一挪，不用整天靠在床上。",
    "但现在卖的车，尺寸是照大多数人做的，不是照着您家老人。",
    "卖车的人也少问一句，老人多高，平时是谁推。",
    "定改制这事说白了不复杂，就是把车照着人重新对一遍。",
    "先量，身高、腿长、坐多宽、坐多深，一样一样来。",
    "再问，他自己推还是儿女推，路上有没有坡。",
    "然后调，坐高、坐深、脚踏、扶手，对着他的身架一样一样试。",
    "调完让他自己坐上去，哪儿差一点，再动一动。",
    "车合身了，人坐得住，才愿意出门。",
]

TIPS = [
    "翔哥单人出镜，坐着或站在一台轮椅旁边说，别背稿",
    "说到坐垫、脚踏、扶手时手要指到对应位置，观众才知道你在说哪儿",
    "「量身高、腿长、坐多宽、坐深」这段配卷尺实拍空镜，插在口播中间",
    "全程不报型号、不报价格、不写字幕地址",
]


def main():
    con = sqlite3.connect(DB)
    body_text = body_plain_text("\n".join(LINES + [TAIL]))
    spoken = util.strip_speakers(body_text)
    wc = util.count_chars(spoken)
    sec = util.estimate_seconds(spoken)
    body = {"format": "monologue", "lines": [{"text": t} for t in LINES]}
    publish = {"disclaimer": util.compliance_config().get("disclaimer") or ""}
    scan = compliance.scan_script(body_text, publish, "", FACT_TEXT, [])
    now = util.now_iso()
    row = con.execute("SELECT id FROM sg_scripts WHERE code=?", (CODE,)).fetchone()
    if row:
        con.execute(
            "UPDATE sg_scripts SET account_id='oral', account_label='口播号', "
            "presenters_json=?, title=?, body_json=?, body_md=?, word_count=?, "
            "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
            "compliance_json=?, product_model=?, product_scope=?, status='待审', "
            "version=version+1, updated_at=? WHERE code=?",
            (json.dumps(["翔哥"], ensure_ascii=False), TITLE,
             json.dumps(body, ensure_ascii=False), body_text, wc, sec, 82.0,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), "定改制轮椅", "品类", now, CODE))
    else:
        con.execute(
            "INSERT INTO sg_scripts (code, created_at, updated_at, status, "
            "account_id, account_label, presenters_json, source_platform, "
            "video_key, benchmark_url, benchmark_title, product_model, "
            "product_doc_ids_json, title, body_json, body_md, "
            "shooting_tips_json, publish_json, compliance_json, facts_json, "
            "word_count, estimated_seconds, target_seconds, version, "
            "product_scope, notes) VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (CODE, now, now, "待审", "oral", "口播号",
             json.dumps(["翔哥"], ensure_ascii=False), "douyin", BENCH_KEY,
             BENCH_URL, BENCH_TITLE, "定改制轮椅",
             json.dumps([], ensure_ascii=False), TITLE,
             json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False),
             json.dumps(publish, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, 82.0, 1, "品类",
             "对标《硬广变软广的阳谋短视频开头》的阳谋三句骨架：理解难处→激发欲望→"
             "替他说话→给方法；正文不提阳谋/公式；定改制品类通用，不写型号价格；"
             "与 004 门槛稿区分（本稿讲合身，不讲通行）。"))
    print("%s %s ｜ %d 字 / %.1f 秒 ｜ 合规 %s" % (
        CODE, TITLE, wc, sec, scan.get("counts")))
    for f in scan.get("findings") or []:
        print("  [%s] %s 「%s」 %s" % (f.get("severity"), f.get("rule_id"),
                                       f.get("match"), f.get("suggest") or ""))
    con.commit()
    con.close()


if __name__ == "__main__":
    main()
