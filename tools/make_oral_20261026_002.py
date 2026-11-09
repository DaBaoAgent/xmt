"""口播号 SG-20261026-002：对标《20年前的广告现在还能用？》写定改制轮椅（软版）。

对标结构（64.5 秒 / 455 字）：
  钩子：一条 20 年前的广告，改一次跑出 10 万播放（结果前置 + 悬念）
  公式：现象 + 危害 + 原因 + 解决方案
        「孩子咳嗽老不好（现象）→ 多半是肺热（危害）→ 肺部感染（原因）
         → 用某某口服液（解决方案）」
  主张：这套结构每句话都在把人往前推，比直接说「我们多专业」有说服力
  结尾：评论区留下行业，现场套公式

本篇用法：保留「现象→危害→原因→办法」四段骨架，落定改制轮椅；
  钩子改成翔哥口吻（朋友讲这套老套路今天还管用，我拿轮椅说一遍），
  不写播放量、不写型号、不写参数、不写价格。

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

TITLE = "推老人出门，一趟要停七八回"

LINES = [
    "推老人出门，走不了多远，他就说停一下，我往上挪挪。",
    "一趟出去，停七八回。",
    "后来他不太愿意出门了，说太麻烦人。",
    "家里人以为是他懒得动。",
    "不是。",
    "是坐得不合身，人一直在拿胳膊撑着、拿脚蹬着坐。",
    "一天下来，肩膀发酸，屁股也磨得慌。",
    "坐都坐不住，哪还有心思看外头。",
    "问题不在人，在这台车。",
    "座位深了一截，后背贴不到靠背。",
    "脚踏低了一点，腿吊着，人自然往下出溜。",
    "现成的车按标准身形做，出厂什么样就什么样。",
    "能改的，叫定改制。",
    "办法就一条，把车按人量一遍。",
    "坐宽多少、坐深多少、脚踏多高、靠背什么角度，一样一样对。",
    "这几处能调，才叫人坐车，不是车坐人。",
    "调不了的，别硬塞给人。",
    "挑的时候，别在店里坐两分钟就定。",
    "让他坐满十分钟，看还往前蹭不蹭，腿麻不麻。",
    "坐得住，再谈别的。",
    "家里老人坐轮椅，一趟要停几回的，评论区说个数。",
    "我是翔哥，辅具这行十年，将就的话我不说。",
]

TIPS = [
    "开场第一句就把「停一下，我往上挪挪」演出来，手上做一次往上提的动作",
    "说「一趟出去，停七八回」时语速放慢，重音落在「七八回」",
    "讲危害时肩膀往上一耸、手在屁股上按一下，把「撑着劲儿坐」演出来",
    "讲原因时把脚往前一伸、脚尖点地，演示「腿吊着」，再说「往下出溜」",
    "讲量尺寸时用手依次点四个位置：两侧、身后、脚下、背后，节奏一下一下来",
    "结尾看镜头放慢语速，字幕只标「坐满十分钟再定」，不写价格、不写型号",
]

FACT_TEXT = (
    "轮椅适配常识（不代入型号与参数）：现成轮椅按通用身形规格生产，"
    "座位宽度、深度、靠背与脚踏高度出厂后基本固定；若使用者身形与之不匹配，"
    "易出现身体前滑、需反复调整坐姿、靠背贴合不足等情况，久坐会明显疲劳；"
    "定改制轮椅可按使用者实际坐姿调整坐宽、坐深、靠背角度与脚踏高度；"
    "选购试坐应持续足够时间，观察是否出现下滑或不适。"
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

    code = "SG-20261026-002"
    target = 85.0
    now = util.now_iso()
    publish = {"disclaimer": disclaimer,
               "douyin": {"title": TITLE,
                          "tags": "#轮椅 #养老辅具 #居家照护",
                          "cover_top": "一趟停七八回",
                          "cover_bottom": "不是他坐不住，是车不合身"},
               "channels": {"title": "老人不愿出门，可能不是腿的事",
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
             "7640075440225719033", "https://v.douyin.com/uVu6tVvH50I/",
             "20年前的广告现在还能用？#短视频干货#自媒体#代运营",
             None, json.dumps([], ensure_ascii=False),
             TITLE, json.dumps(body, ensure_ascii=False), body_text,
             json.dumps(TIPS, ensure_ascii=False), json.dumps(publish, ensure_ascii=False),
             json.dumps(scan, ensure_ascii=False), json.dumps([], ensure_ascii=False),
             wc, sec, target, 1, "品类",
             "对标「20年前的广告现在还能用？」：套现象+危害+原因+办法四段式，"
             "落定改制轮椅「车不合身」；软版弱广告，不点名型号、不列参数、不写价格"))
        print("已新建", code)
    con.commit()
    con.close()

    print("=== %s ===" % TITLE)
    print("%d 字 / %.1f 秒（对标 64.5s）｜ 合规 %s" % (wc, sec, scan.get("counts")))
    print()
    print(body_text)
    for f in scan.get("findings") or []:
        print("  [%s] %s ｜「%s」｜ %s" % (
            f.get("severity"), f.get("rule_id"), f.get("match"),
            f.get("suggest") or ""))


if __name__ == "__main__":
    main()
