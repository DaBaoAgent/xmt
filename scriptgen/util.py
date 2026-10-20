"""通用小工具：路径、配置、URL、计数、文件名。

不在这里做网络请求，也不打印任何密钥。
"""
import os
import re
import json
import math
import hashlib
from datetime import datetime
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(ROOT, "config")


def project_path(rel):
    return rel if os.path.isabs(rel) else os.path.join(ROOT, rel)


def load_json(rel_or_abs, default=None):
    path = project_path(rel_or_abs)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(rel_or_abs, data):
    path = project_path(rel_or_abs)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)
    return path


def config():
    return load_json("config/scriptgen.json", {}) or {}


def redfox_api_key():
    """RedFox 密钥：环境变量优先，其次本地私密文件 config/redfox.local.json。

    密钥不写进 scriptgen.json（那个文件是入库的），也不进日志。
    """
    key = os.environ.get("REDFOX_API_KEY", "").strip()
    if key:
        return key
    local = load_json("config/redfox.local.json", {}) or {}
    return str(local.get("api_key") or "").strip()


def ensure_redfox_env():
    """把本地兜底密钥写回环境变量，供官方 SDK 读取。返回是否可用。"""
    key = redfox_api_key()
    if key:
        os.environ["REDFOX_API_KEY"] = key
    return bool(key)


def personas_config():
    return load_json("config/personas.json", {}) or {}


def compliance_config():
    return load_json("config/compliance.json", {}) or {}


def inventory_config():
    return load_json("config/showroom_inventory.json", {}) or {}


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def now_stamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def ensure_dirs():
    cfg = config()
    paths = cfg.get("paths") or {}
    for key in ("knowledge_dir", "reference_dir", "scripts_dir", "batch_dir", "tmp_dir"):
        rel = paths.get(key)
        if rel:
            os.makedirs(project_path(rel), exist_ok=True)


URL_RE = re.compile(r"https?://[^\s\u4e00-\u9fff，。；！？、）】》」』“”‘’]+", re.I)
TRAILING = ".,;:!?)]}>'\"，。；：！？、）】》」』"


def extract_urls(text):
    """从分享口令/多行文本里提取 URL，去重并保序。"""
    if not text:
        return []
    out, seen = [], set()
    for raw in URL_RE.findall(str(text)):
        url = raw.strip().rstrip(TRAILING)
        if not url or url in seen:
            continue
        if not detect_platform(url):
            continue
        seen.add(url)
        out.append(url)
    return out


def detect_platform(url):
    """返回 douyin / channels / None。"""
    try:
        p = urlparse(url)
    except Exception:
        return None
    host = (p.netloc or "").lower()
    path = (p.path or "").lower()
    if host in ("v.douyin.com", "www.douyin.com", "douyin.com",
                "www.iesdouyin.com", "iesdouyin.com") or host.endswith(".douyin.com"):
        return "douyin"
    if host == "weixin.qq.com" and path.startswith("/sph"):
        return "channels"
    if host in ("channels.weixin.qq.com", "weishi.qq.com") or host.endswith(".weishi.qq.com"):
        return "channels"
    return None


def platform_label(platform):
    return {"douyin": "抖音", "channels": "视频号", "xiaohongshu": "小红书"}.get(platform, platform or "")


def slugify(text, max_len=48):
    """中文可读的文件名片段；不含空格、标点、emoji。"""
    s = str(text or "").strip()
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", s, flags=re.UNICODE)
    s = re.sub(r"-{2,}", "-", s).strip("-_")
    if not s:
        s = "untitled"
    return s[:max_len].rstrip("-_")


def fs_safe(text, max_len=24):
    """纯 ASCII 的文件系统安全片段（目录名用）。

    中文目录名会被本机安全钩子拦（PermissionError WinError 5），
    这里把非 ASCII 字符换成短哈希，保证路径可用且可读。
    """
    s = str(text or "").strip()
    ascii_part = re.sub(r"[^A-Za-z0-9-]+", "-", s, flags=re.UNICODE)
    ascii_part = re.sub(r"-{2,}", "-", ascii_part).strip("-_")
    if not ascii_part:
        return "ref-" + short_hash(s or "ref")
    return ascii_part[:max_len].rstrip("-_")


def short_hash(text, n=8):
    return hashlib.sha1(str(text or "").encode("utf-8")).hexdigest()[:n]


def count_chars(text):
    """统计非空白字符数（中文按字算，英文按字符算）。"""
    return len(re.sub(r"\s+", "", str(text or "")))


def estimate_seconds(text, chars_per_sec=4.2):
    n = count_chars(text)
    return round(n / float(chars_per_sec or 4.2), 1) if n else 0.0


def format_seconds(sec):
    try:
        sec = float(sec)
    except Exception:
        return "—"
    if sec < 60:
        return f"{sec:.1f} 秒"
    m, s = divmod(int(round(sec)), 60)
    return f"{m} 分 {s} 秒"


def parse_count(v):
    """'1.4万' / '10+' / '2,823' / 1641 -> int 或 None。"""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip().replace(",", "").replace("+", "")
    if not s:
        return None
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(万|w|W)?$", s)
    if not m:
        return None
    n = float(m.group(1))
    if m.group(2):
        n *= 10000
    return int(n)


def normalize_hashtag(tag):
    t = str(tag or "").strip()
    if not t:
        return ""
    return t if t.startswith("#") else "#" + t


def normalize_tags(tags, limit=5, brand_tag="#佳康顺"):
    out, seen = [], set()
    for t in tags or []:
        t = normalize_hashtag(t)
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    if brand_tag:
        bt = normalize_hashtag(brand_tag)
        out = [t for t in out if t != bt]
        if len(out) >= limit:
            out = out[:limit - 1]
        out.append(bt)
    return out[:limit]


def split_sentences(text):
    """粗分句，保留标点，供拆解/统计使用。"""
    t = str(text or "").strip()
    if not t:
        return []
    parts = re.split(r"(?<=[。！？!?；;])\s*|\n+", t)
    return [p.strip() for p in parts if p.strip()]


def ngrams(text, n=8):
    """去掉空白/标点后的字符 n-gram 集合，用于原创度粗检。"""
    t = re.sub(r"[\s\W_]+", "", str(text or ""), flags=re.UNICODE)
    if len(t) < n:
        return set()
    return {t[i:i + n] for i in range(len(t) - n + 1)}


def overlap_ratio(new_text, ref_text, n=8):
    a, b = ngrams(new_text, n), ngrams(ref_text, n)
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a))


def longest_common_substring_len(a, b):
    a, b = str(a or ""), str(b or "")
    if not a or not b:
        return 0
    # 滚动一维 DP，避免长文本开大矩阵
    prev = [0] * (len(b) + 1)
    best = 0
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            if ai == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


def md_escape_cell(s):
    return str(s or "").replace("|", "\\|").replace("\n", " ").strip()


def redact_secret(text, secret):
    t = str(text or "")
    if secret:
        t = t.replace(str(secret), "***")
    return t


def env_bool(name, default=False):
    v = os.environ.get(name)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def parse_bool(v, default=False):
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def clamp(n, lo, hi):
    try:
        n = float(n)
    except Exception:
        n = lo
    return max(lo, min(hi, n))


def is_empty(v):
    return v is None or (isinstance(v, str) and not v.strip())
