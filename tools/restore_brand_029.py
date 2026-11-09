"""恢复品牌号 SG-20261020-029 原记录（带座助行器，一个说行一个嫌）。

原因：口播稿误用了同一 code，UPDATE 覆盖了该记录。原稿正文/拍摄提示仍在
out/scripts/2026-10-21/brand/SG-20261020-029_带座助行器-一个说行一个嫌.md。
本脚本从该 md 还原 body_json / tips / 字数，并重新跑合规扫描。
"""
import io
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from scriptgen import util  # noqa: E402
from scriptgen.writer import body_plain_text  # noqa: E402
from scriptgen import compliance  # noqa: E402

DB = os.path.join(ROOT, "data", "xmt.db")
MD = os.path.join(ROOT, "out", "scripts", "2026-10-21", "brand",
                  "SG-20261020-029_带座助行器-一个说行一个嫌.md")
CODE = "SG-20261020-029"
TITLE = "带座助行器，一个说行一个嫌"

md = io.open(MD, encoding="utf-8").read()

lines = []
for m in re.finditer(r"\*\*(心悦|小冯)（[^）]*）\*\*：［(反方|正方)］(.+)", md):
    lines.append({"speaker": m.group(1), "beat": m.group(2), "text": m.group(3).strip()})
assert len(lines) == 8, len(lines)

tips = []
sec = md.split("## 三、拍摄提示")[1].split("## 四、")[0]
for raw in sec.strip().splitlines():
    t = re.sub(r"^\d+\.\s*", "", raw.strip())
    if t:
        tips.append(t)

body = {"format": "dialogue", "lines": lines}
body_text = body_plain_text(body)
spoken = util.strip_speakers(body_text)
wc = util.count_chars(spoken)
est = util.estimate_seconds(spoken)
disclaimer = util.compliance_config().get("disclaimer") or ""
scan = compliance.scan_script(body_text, {"disclaimer": disclaimer}, "", "", [])

now = util.now_iso()
con = sqlite3.connect(DB)
con.execute(
    "UPDATE sg_scripts SET title=?, account_id='brand', account_label='品牌号', "
    "presenters_json=?, product_model=?, benchmark_url=?, benchmark_title=?, "
    "body_json=?, body_md=?, shooting_tips_json=?, publish_json=?, compliance_json=?, "
    "word_count=?, estimated_seconds=?, target_seconds=?, product_scope='型号', "
    "status='待审', notes=?, updated_at=?, version=14 WHERE code=?",
    (TITLE, json.dumps(["心悦", "小冯"], ensure_ascii=False), "朋友2",
     "https://v.douyin.com/h3AJIsVteww/",
     "遇见这么能炫耀的你会怎么办？#皮皮熊老年代步车 #老年代步车 #适老化产品 #电动四轮车 #老人出行神器",
     json.dumps(body, ensure_ascii=False), body_text,
     json.dumps(tips, ensure_ascii=False),
     json.dumps({"disclaimer": disclaimer}, ensure_ascii=False),
     json.dumps(scan, ensure_ascii=False), wc, est, 30.0,
     "品牌号问答体：心悦挑刺、小冯拿动作回应；卖点回查知识库（助行器朋友2-参数与卖点）",
     now, CODE))
con.commit()
con.close()

print("已恢复", CODE, TITLE)
print("%d 字 / %.1f 秒 ｜ 合规 %s ｜ 拍摄提示 %d 条" % (wc, est, scan.get("counts"), len(tips)))
for f in scan.get("findings") or []:
    print("  [%s] %s「%s」" % (f.get("severity"), f.get("rule_id"), f.get("match")))
