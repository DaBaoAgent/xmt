"""每日编排 v2（cron 入口）：采集 → 分析 → 洞察 → 看板。

阶段：
  1. 自有账号采集（抖音免登录 / 小红书带 cookie）
  2. 对标账号主页采集（config/rivals.json 里填了 url / xhs_id 的号）
  3. 关键词搜索（监控词 → search_hits，找对标 + 找选题素材）
  4. 平台热搜（抖音 / 微博 / 百度）
  5. 分析层（analytics：增长 / 爆款 / 对标差距）+ 周报
  6. 洞察层（insight：选题池 + 下一步拍摄方向）
  7. 看板 HTML

用法：
    python snapshot.py                 # 全量
    python snapshot.py --quick         # 跳过对标采集与洞察生成（只更新自有账号数据与看板）
    python snapshot.py --no-insight    # 采集全做，不做 LLM 生成
环境变量：
    XMT_TARGET=30     每账号抓取作品条数
    XMT_TOPICS=10     每次生成选题数
"""
import os
import sys
import time
import argparse
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import db  # noqa: E402

TARGET = int(os.environ.get("XMT_TARGET", "30"))
TOPICS = int(os.environ.get("XMT_TOPICS", "10"))


def _step(name, fn, results):
    t0 = time.time()
    try:
        out = fn()
        results[name] = f"{out}"
        print(f"  [ok] {name}: {out}  ({time.time()-t0:.0f}s)")
    except Exception as e:
        results[name] = f"error: {type(e).__name__}: {e}"
        print(f"  [fail] {name}: {type(e).__name__}: {e}")
        traceback.print_exc()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="跳过对标采集与洞察生成")
    ap.add_argument("--no-insight", action="store_true", help="跳过 LLM 生成")
    ap.add_argument("--headed", action="store_true", help="显示浏览器窗口（排错用）")
    args = ap.parse_args()

    t0 = time.time()
    n = db.init()
    results = {"db_accounts": n}
    print(f"db init 完成，accounts={n}")

    # 1. 自有账号
    def own():
        import collect_douyin
        import collect_xhs
        a = collect_douyin.run(target=TARGET, headed=args.headed)
        b = collect_xhs.run(target=TARGET, headed=args.headed) if collect_xhs.available() else (0, 0)
        return f"抖音 {a[0]}/{a[1]}，小红书 {b[0]}/{b[1]}"
    _step("自有账号采集", own, results)

    # 2-4. 对标 / 关键词 / 热搜（耗时，quick 模式跳过）
    if not args.quick:
        def rivals():
            from collectors import rival
            ok, total = rival.run_rivals(target=TARGET, headed=args.headed)
            return f"{ok}/{total}"
        _step("对标账号采集", rivals, results)

        def search():
            from collectors import rival
            s = rival.run_search(limit=TARGET, headed=args.headed)
            return f"{len(s)} 个关键词"
        _step("关键词搜索", search, results)

        def hot():
            from collectors import hot
            return hot.run(headed=args.headed)
        _step("平台热搜", hot, results)

    # 5. 分析层
    def analyze():
        try:
            from analytics import growth
        except ImportError as e:
            return f"analytics 未就绪（{e}）"
        ranking = growth.growth_ranking(days=7)
        return f"涨粉排行 {len(ranking)} 个号"
    _step("增长分析", analyze, results)

    def weekly():
        try:
            import report as rep
        except ImportError as e:
            return f"report 未就绪（{e}）"
        return rep.build_weekly_report(days=7)
    _step("周报生成", weekly, results)

    def discover():
        try:
            from analytics import discover as D
        except ImportError as e:
            return f"discover 未就绪（{e}）"
        cands = D.discover(top=10, days=30)
        gap = D.content_gap(days=30)
        return (f"对标候选 {len(cands)} 个；题材差距：外部样本 {gap['rival_count']} / "
                f"自有样本 {gap['own_count']}")
    _step("对标候选与题材差距", discover, results)

    # 6. 洞察层
    if not args.quick and not args.no_insight:
        def topics():
            from insight import topics as T
            rows = T.generate_topics(n=TOPICS)
            return f"{len(rows)} 条选题"
        _step("选题池", topics, results)

        def direction():
            from insight import direction as D
            out = D.next_direction(days=7)
            return (out or "")[:80]
        _step("拍摄方向", direction, results)
    else:
        results["选题池"] = "skipped"
        results["拍摄方向"] = "skipped"

    # 7. 销售/租赁报表 → 董事长汇报材料（放在看板前，看板才能展示销售数据）
    def sales_step():
        try:
            from sales import parse as sp
            from sales import speech
        except ImportError as e:
            return f"sales 未就绪（{e}）"
        try:
            recs, spath = sp.load()
        except FileNotFoundError:
            return "无销售报表文件，跳过"
        out, cur = speech.build(records=recs, export_docx=True)
        return (f"{cur['label']} {cur['count']} 单 {cur['total']} 元 → "
                f"{os.path.basename(out)}")
    _step("销售汇报材料", sales_step, results)

    # 8. 看板（最后生成，包含以上所有数据）
    def dash():
        import dashboard
        return dashboard.build()
    _step("看板生成", dash, results)

    print("=" * 60)
    print("快照完成，用时 %.1fs" % (time.time() - t0))
    for k, v in results.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
