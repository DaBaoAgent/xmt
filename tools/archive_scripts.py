"""刷新 HTML 对照表（TXT 归档已由 export_standalone.py 接管，按账号分目录单独输出）。

用法：
  python tools/archive_scripts.py            # 刷 HTML 对照表
  python tools/archive_scripts.py --html     # 同上

产物：
  对照表/index.html                 入口页，点卡片进各号文档
  对照表/对标对照表-{号}.html        左右分栏：左对标，右改稿

> 一篇一个的单独 txt 由 tools/export_standalone.py 生成到「稿子/{账号}/」，
> 按账号分三个子目录，不再生成合并版 txt（口播稿/ 目录已废弃删除）。

规则：
  - 只收 status in (待审, 已通过) 且有逐字稿的记录；失败/未定的不出稿不入档
  - 每次运行都重建文件，不会重复堆叠
"""
import os
import sys
import json
import sqlite3
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "xmt.db")

# 账号 id → (文件名, 标题, 出镜人标注)
ACCOUNTS = {
    "oral":   ("口播稿-翔哥号.txt", "翔哥号 ｜ 单人口播", "翔哥"),
    "brand":  ("口播稿-品牌号.txt", "品牌号 ｜ 双人问答", "心悦 + 小冯"),
    "personal": ("口播稿-个人号.txt", "个人号 ｜ 单人口播", "小冯"),
}

HEADER = """{title}
出镜：{presenters}
拍摄地：苏州阳光大厦展厅（姑苏区西环路717号运智路阳光大厦911室）
说明：本文档由 scriptgen 自动归档，按出稿顺序排列。改稿后重新运行 tools/archive_scripts.py 即可刷新。
不写价格、不承诺疗效、只讲结构与场景（合规口径）。

======================================================================

"""

SEP = "\n\n" + "-" * 70 + "\n\n"


def load_rows():
    if not os.path.exists(DB):
        print("找不到数据库：%s（先跑 python -m scriptgen init）" % DB)
        return []
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        "SELECT * FROM sg_scripts ORDER BY created_at, id")]
    con.close()
    # 同 code 只留最新版本
    latest = {}
    for r in rows:
        latest[r["code"]] = r
    return [latest[c] for c in sorted(latest, key=lambda c: (latest[c].get("created_at") or "", c))]


def render(r, idx):
    body = (r.get("body_md") or "").strip()
    if not body:
        return None
    presenters = r.get("presenters_json") or "[]"
    try:
        pres = json.loads(presenters) if isinstance(presenters, str) else presenters
    except Exception:
        pres = []
    tips = r.get("shooting_tips_json") or "[]"
    try:
        tips = json.loads(tips) if isinstance(tips, str) else tips
    except Exception:
        tips = []

    lines = []
    lines.append("【%02d】%s" % (idx, r.get("title") or "(无标题)"))
    lines.append("编号：%s ｜ 版本：v%s ｜ 状态：%s" % (
        r.get("code"), r.get("version"), r.get("status")))
    lines.append("账号：%s ｜ 出镜：%s" % (r.get("account_label"), "、".join(pres) or "—"))
    lines.append("时长：约 %.1f 秒 ｜ 字数：%s" % (
        float(r.get("estimated_seconds") or 0), r.get("word_count") or "—"))
    bench = (r.get("benchmark_title") or "").strip()
    if bench:
        # 对标标题常带换行，压成一行再显示，避免撑乱归档格式
        bench = " ".join(x.strip() for x in bench.splitlines() if x.strip())
        lines.append("对标：%s（%s）" % (bench[:70], r.get("source_platform") or ""))
        lines.append("      %s" % (r.get("benchmark_url") or ""))
    prod = (r.get("product_model") or "").strip()
    if prod:
        prod_line = prod
    else:
        scope = (r.get("product_scope") or "").strip()
        prod_line = {"不代入": "不代入产品（不绑定具体型号）",
                     "型号": "具体型号"}.get(scope, "品类通用（不写具体型号）")
    lines.append("产品：%s" % prod_line)
    lines.append("")
    lines.append("—— 逐字稿 ——")
    lines.append("")
    for seg in body.split("\n"):
        lines.append("　　" + seg.strip() if seg.strip() else "")
    if tips:
        lines.append("")
        lines.append("—— 拍摄提示 ——")
        lines.append("")
        for i, t in enumerate(tips, 1):
            lines.append("　%d. %s" % (i, str(t).strip()))
    return "\n".join(lines)


def main():
    """只刷 HTML 对照表（TXT 已由 export_standalone.py 接管）。"""
    sync_html()


def sync_html():
    """顺带刷新三个 HTML 对照表（同一套数据源，保证 TXT 与网页一致）。

    输出到项目根的「对照表」目录（跟「稿子」并排，方便直接找）。
    ⚠️ write_html() 的 rows 必须是 build_tencent_table.build() 返回的处理后数据
    （中文键名：标题/对标链接/对标结构拆解…），不能直接传数据库行。
    """
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_btt", os.path.join(ROOT, "tools", "build_tencent_table.py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        rows = m.build()
        by_acc = {}
        for r in rows:
            by_acc.setdefault(r.get("_account_id") or "oral", []).append(r)
        out_dir = os.path.join(ROOT, "对照表")
        made = m.write_html(by_acc, out_dir=out_dir)
        print()
        print("HTML 对照表 ->  对照表\\")
        for fn, n in made:
            print("  %-30s %s" % (fn, ("%d 条" % n) if n >= 0 else "（入口页）"))
    except Exception as e:
        print("（HTML 对照表刷新失败：%s: %s）" % (type(e).__name__, str(e)[:120]))


if __name__ == "__main__":
    args = set(sys.argv[1:])
    sync_html()
