"""把「对标账号.txt」里的手动清单导入 config/rivals.json。

清单格式（宽松，写起来不用管结构）——账号名与链接交替出现即可：

    护卫神官方旗舰店
    https://v.douyin.com/RhAJChj6BOk/

    皮皮熊电动车旗舰店

    https://v.douyin.com/AmHkW8UqCtc/

也支持小红书号写法：`小红书号：95480619590` 或直接一串数字账号。

平台自动判断：含 douyin 的链接 → 抖音；含 xiaohongshu 的链接或「小红书号」→ 小红书。
导入时会清掉 rivals.json 里的示例占位条目，并按「账号名 + 平台」去重（重复导入不会产生副本）。

用法：
    python import_rivals.py              # 解析并写回 config/rivals.json
    python import_rivals.py --dry-run    # 只打印解析结果，不写文件
    python import_rivals.py --src 其他.txt
"""
import os
import re
import json
import hashlib
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "对标账号.txt")
DST = os.path.join(HERE, "config", "rivals.json")

_URL_RE = re.compile(r"https?://\S+")
_XHS_ID_RE = re.compile(r"小红书号[:：]?\s*([0-9A-Za-z_\-]{5,32})")


def _platform_of(url=None, line=None):
    if url:
        if "douyin" in url:
            return "douyin"
        if "xiaohongshu" in url or "xhslink" in url:
            return "xiaohongshu"
    if line and "小红书" in line:
        return "xiaohongshu"
    return "douyin"


def parse(path=SRC):
    """解析清单文件 -> [{name, platform, url?, xhs_id?}]。文件不存在或为空返回 []。"""
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip().strip("\u3000").strip()
            if not line:
                continue

            url_m = _URL_RE.search(line)
            if url_m:
                url = url_m.group(0).rstrip("/")
                # 归属到最近一条还没填地址的条目
                e = out[-1] if out else None
                if e is None or e.get("url") or e.get("xhs_id"):
                    e = {"name": "", "platform": "", "url": ""}
                    out.append(e)
                e["url"] = url
                e["platform"] = _platform_of(url, line)
                continue

            id_m = _XHS_ID_RE.search(line)
            if id_m:
                e = out[-1] if out else None
                if e is None or e.get("url") or e.get("xhs_id") or e.get("xhs_id_set"):
                    e = {"name": "", "platform": "xiaohongshu", "url": ""}
                    out.append(e)
                e["xhs_id"] = id_m.group(1)
                e["platform"] = "xiaohongshu"
                continue

            # 其余一律当账号名
            out.append({"name": line, "platform": "", "url": ""})

    if out and not out[-1].get("url") and not out[-1].get("xhs_id") and not out[-1].get("name"):
        out.pop()
    return [x for x in out if x.get("name") or x.get("url") or x.get("xhs_id")]


def _rid(entry):
    plat = (entry.get("platform") or "douyin")[:3]
    seed = entry.get("name") or entry.get("xhs_id") or entry.get("url") or ""
    # 用 md5 而不是内置 hash()：hash() 每个进程都带随机种子，会导致 id 每次导入都变
    h = hashlib.md5(str(seed).encode("utf-8")).hexdigest()[:5]
    return f"rival_{plat}_{h}"


def to_rival_entry(entry):
    plat = entry.get("platform") or _platform_of(entry.get("url"))
    e = {
        "id": _rid(entry),
        "owner": "待补",
        "name": entry.get("name") or entry.get("xhs_id") or entry.get("url", "")[:24],
        "platform": plat,
        "role": "同类目对标",
        "note": "由 对标账号.txt 导入",
    }
    if plat == "xiaohongshu":
        e["xhs_id"] = entry.get("xhs_id", "")
        if entry.get("url"):
            e["url"] = entry["url"]
    else:
        e["url"] = entry.get("url", "")
    return e


def merge(entries, dst=DST, dry=False):
    if os.path.exists(dst):
        with open(dst, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"_comment": "对标账号 + 监控关键词", "rivals": [], "keywords": {}}
    data.setdefault("_comment",
                    "对标账号 + 监控关键词。抖音填主页分享链接 url；小红书填 xhs_id（小红书号）。"
                    "kind=rival，与自有账号同库同表，看板按 kind 分区展示。")
    data.setdefault("keywords", {
        "douyin": ["电动轮椅", "轮椅老人", "护理床", "代步车"],
        "xiaohongshu": ["电动轮椅", "老人代步车", "适老化改造", "康复辅具"],
    })

    # 清掉示例占位条目
    data["rivals"] = [r for r in (data.get("rivals") or [])
                      if "示例" not in (r.get("name") or "")
                      and "example" not in (r.get("id") or "")]

    existing = {(r.get("name"), r.get("platform")) for r in data["rivals"]}
    added, updated = [], []
    for e in entries:
        r = to_rival_entry(e)
        key = (r["name"], r["platform"])
        if key in existing:
            # 已存在则补全缺失的地址
            for old in data["rivals"]:
                if (old.get("name"), old.get("platform")) == key:
                    if r.get("url") and not old.get("url"):
                        old["url"] = r["url"]
                        updated.append(r["name"])
                    if r.get("xhs_id") and not old.get("xhs_id"):
                        old["xhs_id"] = r["xhs_id"]
                        updated.append(r["name"])
            continue
        data["rivals"].append(r)
        existing.add(key)
        added.append(r["name"])

    if not dry:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return added, updated, data["rivals"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--dst", default=DST)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    entries = parse(args.src)
    if not entries:
        print(f"「{os.path.basename(args.src)}」里没解析到账号（文件为空或格式无法识别）。")
        return
    print(f"解析到 {len(entries)} 个账号：")
    for e in entries:
        loc = e.get("url") or (f"小红书号 {e.get('xhs_id')}" if e.get("xhs_id") else "（缺地址，不会采集）")
        print(f"  · {e.get('name') or '（未命名）'}  [{e.get('platform') or '未判定'}]  {loc}")

    added, updated, all_rivals = merge(entries, dst=args.dst, dry=args.dry_run)
    verb = "将写入" if args.dry_run else "已写入"
    print(f"\n{verb} {args.dst}")
    print(f"  新增 {len(added)} 个：{'、'.join(added) if added else '无'}")
    print(f"  补全地址 {len(updated)} 个：{'、'.join(sorted(set(updated))) if updated else '无'}")
    print(f"  当前对标账号共 {len(all_rivals)} 个")
    if not args.dry_run:
        print("\n下一步：.venv/Scripts/python.exe -m collectors.rival     # 采集对标主页")


if __name__ == "__main__":
    main()
