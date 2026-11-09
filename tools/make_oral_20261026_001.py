"""口播号 SG-20261026-001：对标《爆款文案第四期 加钩子》写定改制轮椅（软版·弱广告）。

对标结构（102 秒 / 689 字）：
  主张：爆款文案不是口才好，是会加转折点、加钩子；每 30 秒最好有一个钩子
  四种钩子公式：
    ① 直接讲数据——「我做了 200 场直播才发现……」
    ② 设置反转——「但我那时候不知道啊，这恰恰才是最坑的」
    ③ 留悬念——「三个月后，我突然接到了一个电话」
    ④ 反常识——「你以为粉丝越多越好，错了」
  中段：开篇钩子之后讲方法/观点，用论据撑住
  结尾：引导评论区互动，或直接收住

本篇取 ④反常识开篇 + ③留悬念中段 + 结尾互动：
  反常识钩子：买轮椅先问「能坐多重、能折多小」，这两句都问错了
  悬念钩子：用了三个月，人瘦了八斤，查一圈没毛病
  落点：不是人变了才要定改制，是人一定会变，车得留改的余地
  软版口径：不点名型号、不列参数、不写价格、不承诺疗效，结尾劝退式

口播号人设：翔哥，十年辅具；直给、短句、口语化；敢说「别急着买」。
60-90 秒 / 260-400 字。
"""
import io
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from scriptgen import util  # noqa: E402
from scriptgen.writer import body_plain_text  # noqa: E402
from scriptgen import compliance  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DB = os.path.join(ROOT, "data", "xmt.db")

TITLE = "买轮椅先问能坐多重，其实问错了"

LINES = [
    "买轮椅，很多人第一句先问：能坐多重，能折多小。",
    "这两句，问错了。",
    "我干这行十年，见过最难受的客户，是车没坏，人坐不住。",
    "去年有个客户，半年前买了台现成车。",
    "用了三个月，人瘦了八斤。",
    "后来他女儿推他来，一坐下我就看出来了。",
    "他整个人往下滑，膝盖比大腿根还高，坐十来分钟就得往上挪一次。",
    "挪一次，身子就得重新找位置。",
    "坐一天下来，人是累的。",
    "累着累着，饭就吃不下了。",
    "问题不在人，在车。",
    "他瘦了，坐宽坐深都空出来，人是撑着劲儿坐的。",
    "现成车按标准身形做，尺寸定死，改不动。",
    "定改制不是让你多花钱买台高级的。",
    "是车架留了余地，坐宽、坐深、靠背、脚踏，人变了还能跟着调。",
    "这十年见得最多的，不是轮子坏了，是人变了车没变。",
    "所以买之前，别急着问能坐多重，让人拿尺子量他今天坐下去的样子。",
    "今天对得上，明年胖了瘦了，也得有地方能改。",
    "家里老人坐轮椅总往下滑的，评论区说一句。",
    "我是翔哥，十年辅具，只说真话。",
]

TIPS = [
    "开场连问两句「能坐多重、能折多小」，第二句停顿半拍再说「问错了」，钩子才扎得住",
    "讲「人瘦了八斤」时语气放平，不要煽，像在说一件常见事",
    "讲往下滑时用身体演一遍：身子往下一沉、膝盖抬起来、再往上挪一次",
    "讲「尺寸定死，想改也改不动」时手掌往桌上压一下，做个按死的手势",
    "结尾邀请互动前停一秒，看镜头，语速放慢",
    "字幕只标「人变了，车没变」，不写价格、不写型号、不写疾病名",
]

FACT_TEXT = (
    "轮椅适配常识（不代入型号与参数）：现成轮椅按通用身形规格生产，"
    "座位宽度、深度、靠背与脚踏高度出厂后基本固定；使用者体重与体形变化后，"
    "原尺寸可能不再贴合，容易出现身体下滑、需反复调整坐姿的情况；"
    "定改制轮椅的车架预留了调整空间，可按使用者当前身形调校坐宽、坐深、"
    "靠背角度与脚踏高度，以适应体形变化。选购前应以使用者实际坐姿量取尺寸。"
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

    code = "SG-20261026-001"
    target = 82.0
    now = util.now_iso()
    publish = {"disclaimer": disclaimer,
               "douyin": {"title": TITLE,
                          "tags": "#轮椅 #养老辅具 #居家照护",
                          "cover_top": "问错的两句话",
                          "cover_bottom": "人变了，车没变"},
               "channels": {"title": "人瘦了八斤，车还是那台车",
                            "tags": "#轮椅 #居家养老"}}

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    exists = con.execute("SELECT id FROM sg_scripts WHERE code=?", (code,)).fetchone()
    if exists:
        con.execute(
            "UPDATE sg_scripts SET title=?, body_json=?, body_md=?, word_count=?, "
            "estimated_seconds=?, target_seconds=?, shooting_tips_json=?, "
            "publish_json=?, compliance_json=?, version=version+1, updated_at=? WHERE code=?",
            (TITLE, json.dumps(body, ensure_ascii=False), body_text, wc, sec, target,
             json.dumps(TIPS, ensure_ascii=False), json.dumps(publish, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), now, code))
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
             "7620009104841937050", "https://v.douyin.com/KbUxrfo8aok/",
             "爆款文案第四期 加钩子 #爆款 #文案 #爆款视频 #实体 #短视频",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False), json.dumps(publish, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "对标「爆款文案第四期 加钩子」：反常识开篇（能坐多重/能折多小问错了）"
             "+ 留悬念中段（用了三个月人瘦八斤）+ 评论区互动收尾；"
             "软版弱广告，不点名型号、不列参数、不写价格"))
        print("已新建", code)
    con.commit()
    con.close()

    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 102s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
