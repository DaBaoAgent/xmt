"""命令行入口：python -m scriptgen <命令>。"""
import os
import sys
import json
import argparse

from . import util
from . import store
from . import pipeline
from . import personas


ACCOUNT_ALIASES = {
    "口播号": "oral", "口播": "oral", "oral": "oral", "翔哥": "oral",
    "品牌号": "brand", "品牌": "brand", "brand": "brand", "心悦": "brand",
    "个人号": "personal", "个人": "personal", "personal": "personal", "小冯": "personal",
}


def _p(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def _print_add(result):
    est = result.get("estimate") or {}
    if est.get("message"):
        print(est["message"])
    if result.get("status") == "needs_confirmation":
        print("如需继续，加 --yes 重新执行。")
        return
    if result.get("message"):
        print(result["message"])
    items = result.get("items") or []
    if items:
        print("\n处理结果：")
        for it in items:
            bits = [f"{it.get('index', '?')}.", it.get("status") or "—"]
            if it.get("account_label"):
                bits.append(f"账号={it['account_label']}")
            if it.get("product"):
                bits.append(f"产品={it['product']}")
            if it.get("code"):
                bits.append(f"编号={it['code']}")
            if it.get("error"):
                bits.append(f"错误={it['error']}")
            print("  " + " ｜ ".join(str(x) for x in bits))
            if it.get("docx_path"):
                print("     Word：" + it["docx_path"])
            elif it.get("file_path"):
                print("     内部稿：" + it["file_path"])
    pending = result.get("pending") or []
    if pending:
        print("\n待确认（回复编号 + 账号/产品）：")
        for p in pending:
            print(f"  {p.get('index')}. {p.get('title') or p.get('url')}")
            print(f"     候选账号：{'、'.join(p.get('account_candidates') or ['—'])}")
            print(f"     候选产品：{'、'.join(p.get('product_candidates') or ['—'])}")
            print(f"     理由：{p.get('reason') or '—'}")
    if result.get("report_path"):
        print(f"\n批次报告：{result['report_path']}")


def cmd_init(args):
    store.init()
    print("已初始化 scriptgen 数据表与目录。")
    print("数据库：", os.path.join(util.ROOT, "data", "xmt.db"))
    print("知识库：", os.path.join(util.ROOT, "knowledge", "reference"))
    print("脚本：", os.path.join(util.ROOT, "out", "scripts"))
    return 0


def cmd_estimate(args):
    text = "\n".join(args.text)
    est = pipeline.estimate(text, max_calls=args.max_calls)
    if args.json:
        _p(est)
    else:
        print(est.get("message"))
        for i, u in enumerate(est.get("links") or [], 1):
            print(f"  {i}. {u}")
    return 2 if est.get("needs_confirmation") else 0


def cmd_add(args):
    text = "\n".join(args.text)
    result = pipeline.add(
        text,
        account=ACCOUNT_ALIASES.get(args.account, args.account) if args.account else None,
        product=args.product,
        force=args.force,
        yes=args.yes,
        use_llm=not args.no_llm,
        keep_video=args.keep_video,
        max_calls=args.max_calls,
    )
    if args.json:
        _p(result)
    else:
        _print_add(result)
    if result.get("status") in ("no_links",):
        return 1
    if result.get("status") == "needs_confirmation":
        return 2
    return 0


def _parse_choice(s):
    raw = str(s or "").strip().replace("=", ":")
    parts = raw.split(":")
    if not parts or not parts[0].strip().isdigit():
        raise argparse.ArgumentTypeError(f"choice 需要形如 1:brand:F2Q，收到 {s}")
    idx = int(parts[0])
    account = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
    product = parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
    if account:
        account = ACCOUNT_ALIASES.get(account, account)
        if account not in ("oral", "brand", "personal"):
            raise argparse.ArgumentTypeError(f"未知账号 {account}（oral/brand/personal）")
    return {"index": idx, "account": account, "product": product}


def cmd_resolve(args):
    choices = [_parse_choice(x) for x in args.choice]
    result = pipeline.resolve_batch(args.batch, choices, use_llm=not args.no_llm)
    if args.json:
        _p(result)
    else:
        if not result.get("ok"):
            print(result.get("message"))
        else:
            print(f"批次 {result.get('batch_code')}：待确认剩余 {result.get('pending_confirmation')}")
            for x in result.get("resolved") or []:
                if x.get("ok"):
                    print(f"  {x['index']}. 成功 {x.get('code')} ｜ {x.get('docx_path') or x.get('file_path')}")
                else:
                    print(f"  {x['index']}. 失败：{x.get('message')}")
            print(f"批次报告：{result.get('report_path')}")
    return 0 if result.get("ok") else 1


def cmd_approve(args):
    result = pipeline.approve(args.codes, reject=args.reject, note=args.note, by=args.by)
    if args.json:
        _p(result)
    else:
        for x in result.get("items") or []:
            print(f"{x.get('code')}：{'成功' if x.get('ok') else '失败'} ｜ {x.get('status') or x.get('message')} ｜ {x.get('docx_path') or x.get('file_path') or ''}")
    return 0 if all(x.get("ok") for x in (result.get("items") or [])) else 1


def cmd_revise(args):
    result = pipeline.revise(args.code, args.instruction, use_llm=not args.no_llm)
    if args.json:
        _p(result)
    else:
        if result.get("ok"):
            print(f"{args.code} 已改稿到 v{result.get('version')}，状态 {result.get('status')}")
            print("Word：" + str(result.get("docx_path") or result.get("file_path")))
            c = result.get("compliance") or {}
            print(f"合规：{'通过' if c.get('ok') else '需修改'}（高 {c.get('counts', {}).get('high', 0)} / "
                  f"中 {c.get('counts', {}).get('medium', 0)}）")
        else:
            print(result.get("message"))
    return 0 if result.get("ok") else 1


def cmd_sync(args):
    result = pipeline.sync(args.codes, dry_run=args.dry_run)
    if args.json:
        _p(result)
    else:
        for x in result.get("items") or []:
            if x.get("ok"):
                print(f"{x.get('code')}：{'dry-run OK' if x.get('dry_run') else '已同步'} ｜ {x.get('kb_doc_id') or ''}")
                if x.get("dry_run"):
                    print(x.get("content") or "")
            else:
                print(f"{x.get('code')}：失败 ｜ {x.get('message')}")
    return 0 if all(x.get("ok") for x in (result.get("items") or [])) else 1


def cmd_search(args):
    rows = pipeline.search_local(args.query, limit=args.limit)
    if args.json:
        _p(rows)
        return 0
    if not rows:
        print("没有命中。")
        return 0
    for r in rows:
        if r.get("type") == "脚本":
            print(f"[脚本] {r.get('code')} ｜ {r.get('title')} ｜ {r.get('status')} ｜ {r.get('docx_path') or r.get('file_path')}")
        elif r.get("type") == "对标":
            print(f"[对标] {util.platform_label(r.get('platform'))} ｜ {r.get('title')} ｜ {r.get('author')} ｜ {r.get('doc_path')}")
        else:
            print(f"[转写] {util.platform_label(r.get('platform'))} ｜ {r.get('video_key')} ｜ {r.get('snippet')}")
    return 0


def cmd_list(args):
    rows = pipeline.list_scripts(status=args.status, account=args.account,
                                 date=args.date, limit=args.limit)
    if args.json:
        _p(rows)
        return 0
    if not rows:
        print("没有脚本。")
        return 0
    for s in rows:
        print(f"{s.get('code')} ｜ {(s.get('created_at') or '')[:10]} ｜ {s.get('account_label')} ｜ "
              f"{s.get('status')} ｜ v{s.get('version')} ｜ {s.get('title')}")
        print(f"   Word：{s.get('docx_path') or '（未导出）'}")
    return 0


def cmd_show(args):
    s = pipeline.get_script(args.code)
    if not s:
        print("找不到脚本。")
        return 1
    print(f"{s.get('code')} ｜ {s.get('status')} ｜ {s.get('account_label')} ｜ {s.get('title')}")
    print("Word：" + str(s.get("docx_path") or "（未导出）"))
    print("内部稿：" + str(s.get("file_path") or ""))
    if args.full and s.get("file_path") and os.path.exists(s["file_path"]):
        print("\n" + open(s["file_path"], encoding="utf-8").read())
    return 0


def cmd_personas(args):
    if args.derive:
        r = personas.derive(use_llm=not args.no_llm, force=args.force)
        print(("已刷新人设草案。\n" if r.get("ok") else "未刷新：") + str(r.get("reason") or ""))
        if r.get("notes"):
            print("待确认：" + str(r["notes"]))
    print(personas.render_cards())
    return 0


def build_parser():
    ap = argparse.ArgumentParser(prog="python -m scriptgen", description="xmt 拍摄脚本模块")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="初始化数据表与目录")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("estimate", help="只估算链接数量和 RedFox 调用量")
    p.add_argument("text", nargs="+", help="链接/分享文本")
    p.add_argument("--max-calls", type=int, default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_estimate)

    p = sub.add_parser("add", help="提取链接并生成脚本（可批量）")
    p.add_argument("text", nargs="+", help="链接/分享文本，可多行")
    p.add_argument("--account", choices=["oral", "brand", "personal", "口播号", "品牌号", "个人号"],
                   help="强制指定账号；不填则自动判断")
    p.add_argument("--product", help="强制指定产品型号/品类（如 F2Q、小福车、category）")
    p.add_argument("--force", action="store_true", help="忽略缓存，重新提取/生成")
    p.add_argument("--yes", action="store_true", help="超过调用阈值也继续")
    p.add_argument("--no-llm", action="store_true", help="不调用 DeepSeek，走规则兜底")
    p.add_argument("--keep-video", action="store_true", help="保留兜底下载的视频（调试）")
    p.add_argument("--max-calls", type=int, default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("resolve", help="补写批次里待确认的条目")
    p.add_argument("batch", help="批次号")
    p.add_argument("--choice", action="append", required=True,
                   help="形如 1:brand:F2Q、1:oral、2::小福车（可重复）")
    p.add_argument("--no-llm", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("approve", help="人工终审：通过/退回")
    p.add_argument("codes", nargs="+")
    p.add_argument("--reject", action="store_true", help="标记为已退回")
    p.add_argument("--note", help="审核备注")
    p.add_argument("--by", default="老板")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser("revise", help="按指令改稿并保留版本")
    p.add_argument("code")
    p.add_argument("--instruction", required=True)
    p.add_argument("--no-llm", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_revise)

    p = sub.add_parser("sync", help="把已通过脚本同步到公司知识库 marketing")
    p.add_argument("codes", nargs="+")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("search", help="检索本地脚本/对标/转写")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("list", help="列出脚本")
    p.add_argument("--status")
    p.add_argument("--account")
    p.add_argument("--date", help="YYYY-MM-DD")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="查看脚本")
    p.add_argument("code")
    p.add_argument("--full", action="store_true")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("personas", help="查看/提炼三号人设卡")
    p.add_argument("--derive", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--no-llm", action="store_true")
    p.set_defaults(func=cmd_personas)

    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt:
        print("\n已中断。", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"[错误] {type(e).__name__}: {str(e)[:500]}", file=sys.stderr)
        return 1
