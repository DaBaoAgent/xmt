"""每日编排：跑各平台采集 -> 写快照 -> 生成看板。cron 入口。"""
import os
import sys
import time
import traceback

import db
import dashboard

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = int(os.environ.get("XMT_TARGET", "30"))


def main():
    t0 = time.time()
    db.init()
    results = {}

    # 抖音（前台免登录）
    try:
        import collect_douyin
        ok, total = collect_douyin.run(target=TARGET)
        results["douyin"] = f"{ok}/{total}"
    except Exception as e:
        results["douyin"] = f"error: {type(e).__name__}: {e}"
        traceback.print_exc()

    # 小红书（需登录 cookie，未配置则跳过）
    try:
        import collect_xhs
        if collect_xhs.available():
            r = collect_xhs.run(target=TARGET)
            results["xiaohongshu"] = str(r)
        else:
            results["xiaohongshu"] = "skipped(未配置cookie)"
    except Exception as e:
        results["xiaohongshu"] = f"error: {type(e).__name__}: {e}"

    try:
        out = dashboard.build()
        results["dashboard"] = out
    except Exception as e:
        results["dashboard"] = f"error: {e}"
        traceback.print_exc()

    print("=" * 60)
    print("快照完成，用时 %.1fs" % (time.time() - t0))
    for k, v in results.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
