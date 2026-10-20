"""抖音视频直链抓取（免 RedFox 积分）+ 落盘。

用法：
  .venv/Scripts/python.exe tools/capture_douyin.py <抖音链接或videoId>

原理：Playwright 打开页面，hook response 拿 douyinvod.com 的 CDN 直链。
⚠️ 必须用 launch_persistent_context（本机 Playwright 版本不支持
   launch(user_data_dir=)），且 profile 用独立目录（Chrome 正在运行会锁原目录）。
"""
import io
import os
import re
import sys
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROFILE = os.path.join(ROOT, "out", "chrome-dy")
DL_DIR = os.path.join(ROOT, "out", "sph_dl")

CDN = ("aweme.snssdk.com", "douyinvod.com", "v3-dy-", "v26-dy-",
       "video.toutiao.com", "bytecdn", "ixigua.com")


def resolve(url):
    """短链 → videoId + 完整页 URL。"""
    import requests
    s = requests.Session()
    s.trust_env = False
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/131.0.0.0 Safari/537.36")})
    r = s.get(url, allow_redirects=True, timeout=30)
    ids = re.findall(r"/video/(\d{15,})", r.url) or \
        re.findall(r"modal_id=(\d{15,})", r.url)
    vid = ids[0] if ids else None
    if not vid:
        m = re.search(r"/sph/([A-Za-z0-9]+)", r.url)
        vid = m.group(1) if m else None
    title = ""
    m = re.search(r"<title>(.*?)</title>", r.text, re.S)
    if m:
        title = " ".join(m.group(1).split())
    return vid, r.url, title


def capture(page_url, wait=10):
    from playwright.sync_api import sync_playwright
    os.makedirs(PROFILE, exist_ok=True)
    hits = []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE, headless=True, channel="chrome",
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled",
                  "--no-sandbox", "--disable-gpu", "--mute-audio"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        def on_resp(r):
            u = r.url
            if any(h in u for h in CDN) and not any(
                    x in u for x in (".jpg", ".jpeg", ".png", ".webp")):
                hits.append(u)
        page.on("response", on_resp)

        try:
            page.goto(page_url, wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print("goto:", str(e)[:90])
        page.wait_for_timeout(3500)
        for _ in range(3):
            page.mouse.wheel(0, 600)
            page.wait_for_timeout(1000)
        for sel in ("video", "[data-e2e='video-player']", ".xgplayer-play"):
            try:
                el = page.query_selector(sel)
                if el:
                    el.click()
                    print("点了:", sel)
                    page.wait_for_timeout(2500)
                    break
            except Exception:
                pass
        page.wait_for_timeout(wait * 1000)
        try:
            for v in page.query_selector_all("video"):
                for attr in ("src", "currentSrc"):
                    try:
                        u = v.evaluate("e => e.%s" % attr)
                        if u and u.startswith("http"):
                            hits.append(u)
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            print("页面标题:", page.title()[:90])
        except Exception:
            pass
        ctx.close()
    return hits


def download(url, path):
    import requests
    s = requests.Session()
    s.trust_env = False
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/131.0.0.0 Safari/537.36"),
        "Referer": "https://www.douyin.com/"})
    r = s.get(url, timeout=180)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(r.content)
    return len(r.content)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "https://v.douyin.com/52CXOjhs8Fs/"
    vid, page_url, title = resolve(src)
    print("videoId:", vid, "| 标题:", title[:60])
    if not vid:
        print("没解析出 videoId")
        return
    if not page_url.startswith("https://www.douyin.com/video/"):
        page_url = "https://www.douyin.com/video/%s" % vid
    hits = capture(page_url)
    print("\n捕获 %d 条 CDN 请求" % len(hits))
    vids = [h for h in hits if "douyinvod" in h or ".mp4" in h]
    if not vids:
        print("没抓到直链")
        return
    best = vids[0]
    print("直链:", best[:170])
    out = os.path.join(DL_DIR, "douyin_%s.mp4" % vid)
    size = download(best, out)
    print("已下载: %s（%.2f MB）" % (out, size / 1048576))


if __name__ == "__main__":
    main()
