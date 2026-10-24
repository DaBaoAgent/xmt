# -*- coding: utf-8 -*-
r"""出稿一键收尾：渲染 md → ORDER 自动插入 → 刷 TXT/HTML → 质量检查。

用法：
  # 一键收尾（写稿脚本落库后跑，code 可一次传多个）
  .venv/Scripts/python.exe tools/finish_script.py SG-20261024-086 [SG-20261024-087 ...]

  # 只跑全库质量检查（尾句查重 + target 区间校验），不渲染
  .venv/Scripts/python.exe tools/finish_script.py --check

  # 查某个型号已被写过哪些稿、什么角度（出稿前防角度重复）
  .venv/Scripts/python.exe tools/finish_script.py --angles F2Q

  # 清理历史 Word 提词版（项目已停出 Word：output.docx_enabled=false）
  .venv/Scripts/python.exe tools/finish_script.py --purge-docx

本脚本把原 SOP 第 7-9 步的人工操作全部自动化：
  1. 渲染源 md（pipeline._render_script；Word 已停用）
  2. 新 code 自动插进 config/export_order.json 的同账号组末尾
     （不再需要手改 export_standalone.py 的 ORDER——已数据化）
  3. subprocess 刷 稿子/ 单篇 TXT 与 对照表/ HTML
  4. 质量检查：合规高危/中危必须 0；target_seconds 落在人设区间；
     全账号尾句去重（重复只警告，不阻断——历史遗留稿由用户定夺）
幂等：重复跑同一个 code 不会重复插 ORDER。

产出三件套（2026-10-24 起不再出 Word）：
  源 md  |  稿子/{账号}/NNN_标题.txt  |  对照表/对标对照表-{账号}.html
"""
import io
import json
import os
import sqlite3
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from scriptgen import store  # noqa: E402
from scriptgen import pipeline  # noqa: E402

DB = os.path.join(ROOT, "data", "xmt.db")
OUT_DIR = os.path.join(ROOT, "out")
ORDER_FILE = os.path.join(ROOT, "config", "export_order.json")
PERSONAS_FILE = os.path.join(ROOT, "config", "personas.json")


def load_order():
    with io.open(ORDER_FILE, encoding="utf-8") as f:
        return json.load(f)["order"]


def save_order(order):
    with io.open(ORDER_FILE, "w", encoding="utf-8") as f:
        json.dump({"order": order}, f, ensure_ascii=False, indent=1)


def insert_order(codes):
    """把新 code 插到 config/export_order.json 里同账号最后一个 code 之后。"""
    order = load_order()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    by = {r["code"]: dict(r) for r in con.execute("SELECT code, account_label FROM sg_scripts")}
    con.close()
    added = []
    for code in codes:
        if code in order:
            continue
        label = (by.get(code) or {}).get("account_label") or "个人号"
        idxs = [i for i, c in enumerate(order)
                if (by.get(c) or {}).get("account_label") == label]
        pos = (idxs[-1] + 1) if idxs else len(order)
        order.insert(pos, code)
        added.append((code, label, pos))
    if added:
        save_order(order)
        for code, label, pos in added:
            print("  [ORDER] %s 已插入 %s 组（位置 %d）" % (code, label, pos))
    return added


def quality_check(codes):
    """合规 / 人设区间 / 全账号尾句查重。返回是否有硬问题。"""
    hard = False
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = {r["code"]: dict(r) for r in con.execute("SELECT * FROM sg_scripts")}

    # 1. 本次 code 的合规与区间
    personas = {}
    if os.path.exists(PERSONAS_FILE):
        with io.open(PERSONAS_FILE, encoding="utf-8") as f:
            personas = {p["id"]: p for p in json.load(f)["personas"]}
    label2pid = {"口播号": "oral", "品牌号": "brand", "个人号": "personal"}
    for code in codes:
        r = rows.get(code)
        if not r:
            print("  [检查] %s 不在库，跳过" % code)
            continue
        cj = json.loads(r["compliance_json"] or "{}")
        counts = cj.get("counts") or {}
        hi, mid = counts.get("high", 0), counts.get("medium", 0)
        flag = "OK" if (hi == 0 and mid == 0) else "★不合格"
        if hi or mid:
            hard = True
        print("  [合规] %s 高危=%d 中危=%d %s" % (code, hi, mid, flag))
        p = personas.get(label2pid.get(r["account_label"], ""), {})
        dur = p.get("duration") or {}
        lo, hi_s = dur.get("min"), dur.get("max")
        tgt = r["target_seconds"]
        if lo and hi_s and tgt and not (lo <= tgt <= hi_s):
            print("  [区间] %s target=%.0fs 不在 %s 人设区间 %s-%ss（用户「简单一点」批次除外，确认是否有意）"
                  % (code, tgt, r["account_label"], lo, hi_s))

    # 2. 全账号尾句查重（跳过已归档：用户用过并移进 1 已用 的稿不再占位置）
    lasts = {}
    for r in con.execute(
            "SELECT code, title, account_label, body_md FROM sg_scripts "
            "WHERE (status IS NULL OR status <> '已归档') ORDER BY id"):
        lines = [x for x in (r["body_md"] or "").split("\n") if x.strip()]
        if not lines:
            continue
        lasts.setdefault((r["account_label"], lines[-1]), []).append(r["title"])
    dups = {k: v for k, v in lasts.items() if len(v) > 1}
    if dups:
        print("  [尾句] 发现 %d 组重复（规则：批量稿最后一句必须不同）：" % len(dups))
        for (label, line), titles in sorted(dups.items()):
            print("    %s 「%s」→ %d 篇：%s" % (label, line, len(titles), "、".join(titles)))
    else:
        print("  [尾句] 三账号共 %d 组收尾，无重复" % len(lasts))
    con.close()
    return hard


def check_angles(model):
    """列出某个型号已写的稿：标题 + 首句 + 尾句，出稿前防角度重复。
    已归档（用过并移进 1 已用）的稿不计入——那些不会再用。"""
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT code, account_label, title, body_md FROM sg_scripts "
        "WHERE product_model LIKE ? AND (status IS NULL OR status <> '已归档') "
        "ORDER BY id", ("%" + model + "%",)).fetchall()
    con.close()
    if not rows:
        print("没有找到 %s 的稿" % model)
        return
    print("%s 已有 %d 篇：" % (model, len(rows)))
    for r in rows:
        lines = [x for x in (r["body_md"] or "").split("\n") if x.strip()]
        print("  [%s] %s" % (r["account_label"], r["title"]))
        if lines:
            print("    首句：%s" % lines[0][:50])
            print("    尾句：%s" % lines[-1][:50])


def purge_docx(codes=None, limit=30):
    """清理 Word 提词版。

    2026-10-24 起项目不再出 Word（config/scriptgen.json 的 output.docx_enabled=false），
    产出三件套：源 md + 稿子/ 单篇 txt + 对照表/ HTML。
    这里把已生成的 docx 文件删掉，并把库里的 docx_path 字段清空。

    注意：本机安全钩子限制单次删除数量（bulk 阈值 50），所以默认一次最多删 30 个，
    剩下的重复跑本命令即可清空（脚本会报剩余数）。"""
    import glob as _glob
    con = sqlite3.connect(DB)
    files = []
    if codes:
        for code in codes:
            s = store.get_script(con, code)
            p = s.get("docx_path") if s else None
            if p:
                files.append(os.path.join(ROOT, p) if not os.path.isabs(p) else p)
    else:
        files = _glob.glob(os.path.join(OUT_DIR, "*.docx"))
    removed = 0
    failed = []
    for p in files:
        if removed >= limit:
            break
        if os.path.exists(p):
            try:
                os.remove(p)
                removed += 1
            except Exception as e:
                # 本机删除走回收站，个别文件可能失败（如被占用/钩子拒绝），跳过继续
                failed.append(os.path.basename(p))
                print("  [跳过] %s：%s" % (os.path.basename(p), str(e)[:60]))
    con.execute("UPDATE sg_scripts SET docx_path=NULL")
    con.commit()
    con.close()
    left = len(_glob.glob(os.path.join(OUT_DIR, "*.docx")))
    print("  [清理] 本次删除 %d 个 Word，库内 docx_path 已清空；out/ 还剩 %d 个"
          % (removed, left))
    if left:
        print("  （安全钩子限制单次删除数量，再跑一次本命令继续清理）")
    return removed


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    if args[0] == "--check":
        quality_check([])
        return
    if args[0] == "--angles":
        check_angles(args[1] if len(args) > 1 else "")
        return
    if args[0] == "--purge-docx":
        purge_docx()
        return

    codes = args
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    missing = [c for c in codes if not store.get_script(con, c)]
    if missing:
        print("库里没有这些 code：%s（先跑写稿脚本落库）" % "、".join(missing))
        con.close()
        return

    # 1. 渲染 md（Word 已停用：output.docx_enabled=false）
    print("== 1. 渲染（只出 md）==")
    for code in codes:
        s = store.get_script(con, code)
        store.update_script(con, code, file_path=store.script_path(s))
        con.commit()
        pipeline._render_script(con, code)
        print("  [渲染] %s %s" % (code, s.get("title")))
    con.close()

    # 2. ORDER 自动插入
    print("== 2. ORDER 插入 ==")
    if not insert_order(codes):
        print("  （ORDER 里都已有，跳过）")

    # 4. 刷 TXT + HTML
    print("== 3. 刷产出 ==")
    for tool in ("export_standalone.py", "archive_scripts.py"):
        p = subprocess.run(
            [sys.executable, os.path.join(HERE, tool)],
            capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
        tail = (p.stdout or "").strip().split("\n")[-3:]
        print("  [%s] %s" % (tool, " / ".join(t.strip() for t in tail if t.strip())))

    # 5. 质量检查
    print("== 4. 质量检查 ==")
    hard = quality_check(codes)
    if hard:
        print("\n★ 有硬问题（合规高危/中危），修完再归档")
        sys.exit(2)
    print("\n收尾完成。归档提醒：git add 时把 稿子/ 和 对照表/ 一起带上"
          "（它们不在 .gitignore，但历来漏提交）。")


if __name__ == "__main__":
    main()
