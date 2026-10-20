"""统一 LLM 调用层：OpenAI 兼容 /chat/completions（只用标准库 + requests）。

key 解析四级回退（任何一级都没有可用 key 时 available() 返回 False，上层自动降级成规则模板版）：
  1. 环境变量 XMT_LLM_API_KEY / DEEPSEEK_API_KEY
  2. 文件 config/llm.local.json（本地私密文件，已被 .gitignore 排除）
     格式 {"provider":"deepseek","base_url":"https://api.deepseek.com/v1","model":"deepseek-chat","api_key":"..."}
  3. Hermes 配置 ~/AppData/Local/hermes/config.yaml 的 api_keys 段（YAML 极简解析，按 provider 名匹配 deepseek）
  4. 环境变量 SILICONFLOW_API_KEY / ZHIPU_API_KEY / SUBLYX_API_KEY（配各自的 base_url）

另有「零密钥」通道：WorkBuddy 云服务 LLM（provider=workbuddy_cloud）。
配置写在 config/llm.local.json 的 cloud 段，走 /.cloud/llm/chat/completions 的 SSE 流式接口，
用 publishableKey 鉴权，用户不需要自己的 API key。优先级：显式 key 通道都不可用时才启用。

安全约定：key 只在内存里流转，绝不写入日志、文件或标准输出；
错误信息里只出现 provider / base_url / model，不出现 key。

调试开关：设置环境变量 XMT_LLM_DISABLED=1 可强制走降级路径（用于验证无 key 时的产出）。
"""

import os
import re
import sys
import json
import time

try:
    import requests
except Exception:  # pragma: no cover - 依赖缺失时整体降级
    requests = None

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # xmt 项目根
LOCAL_JSON = os.path.join(HERE, "config", "llm.local.json")

TIMEOUT = 120          # 单次请求超时（秒）
RETRIES = 2            # 失败重试次数（合计最多 3 次请求）
CLOUD_TIMEOUT = 300    # 云服务 LLM 单次请求超时（长稿出稿较慢）

# 各 provider 的默认 base_url / model（可用环境变量 XMT_LLM_BASE_URL、XMT_LLM_MODEL 覆盖）
DEFAULTS = {
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "siliconflow": {"base_url": "https://api.siliconflow.cn/v1", "model": "Qwen/Qwen2.5-7B-Instruct"},
    "zhipu": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
    "sublyx": {"base_url": "https://api.sublyx.org/v1", "model": "claude-sonnet-4-5-20250929"},
}

# 环境变量名 → provider 名
ENV_PROVIDERS = (
    ("SILICONFLOW_API_KEY", "siliconflow"),
    ("ZHIPU_API_KEY", "zhipu"),
    ("SUBLYX_API_KEY", "sublyx"),
)

# api_keys 段里按 provider 名匹配的候选（按优先级）
API_KEY_NAME_HINTS = ("deepseek", "siliconflow", "zhipu", "sublyx")


def _warn(msg):
    """告警写 stderr，避免污染 CLI 的标准输出（内容里绝不含 key）。"""
    print(f"[llm] {msg}", file=sys.stderr)


def _redact(text, secret):
    """兜底脱敏：供应商回显里万一带上 key，也要在打印前抹掉。"""
    t = str(text)
    if secret:
        t = t.replace(secret, "***")
        if len(secret) > 8:
            t = t.replace(secret[-8:], "***").replace(secret[:8], "***")
    return t


def _clean(v):
    """去掉 YAML/JSON 里值两侧的引号与空白。"""
    if v is None:
        return ""
    s = str(v).strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        s = s[1:-1]
    return s.strip()


def _disabled():
    return _clean(os.environ.get("XMT_LLM_DISABLED")).lower() in ("1", "true", "yes", "on")


def _env(*names):
    for n in names:
        v = _clean(os.environ.get(n))
        if v:
            return v
    return ""


def _override(provider, base_url, model, api_key, source):
    """统一出口：允许 XMT_LLM_BASE_URL / XMT_LLM_MODEL 全局覆盖。"""
    d = DEFAULTS.get(provider, {})
    return {
        "provider": provider,
        "base_url": _env("XMT_LLM_BASE_URL") or base_url or d.get("base_url", ""),
        "model": _env("XMT_LLM_MODEL") or model or d.get("model", ""),
        "api_key": api_key,
        "source": source,
    }


# ---------- 第 2 级：config/llm.local.json ----------

def _from_local_json():
    if not os.path.exists(LOCAL_JSON):
        return None
    try:
        with open(LOCAL_JSON, encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:
        _warn(f"config/llm.local.json 解析失败：{type(e).__name__}")
        return None
    if not isinstance(d, dict):
        return None
    key = _clean(d.get("api_key") or d.get("key") or d.get("XMT_LLM_API_KEY"))
    if not key:
        return None
    provider = _clean(d.get("provider")) or "deepseek"
    return _override(provider, _clean(d.get("base_url")), _clean(d.get("model")), key, "config/llm.local.json")


# ---------- 零密钥通道：WorkBuddy 云服务 LLM ----------

def _cloud_config():
    """读 config/llm.local.json 的 cloud 段（或独立的 cloud.local.json）。

    格式：{"cloud": {"endpoint": "https://xxx.app.workbuddy.host",
                    "publishable_key": "wbpk_xxx",
                    "model": "auto"}}
    """
    paths = [LOCAL_JSON, os.path.join(HERE, "config", "cloud.local.json")]
    for p in paths:
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        c = d.get("cloud") if isinstance(d.get("cloud"), dict) else d
        ep = _clean(c.get("endpoint"))
        pk = _clean(c.get("publishable_key") or c.get("publishableKey"))
        if not ep or not pk:
            continue
        return {
            "provider": "workbuddy_cloud",
            "base_url": ep.rstrip("/"),
            "model": _clean(c.get("model")) or "hunyuan-chat",
            "api_key": pk,
            "source": f"WorkBuddy 云服务（{os.path.basename(p)}）",
        }
    return None


def _cloud_chat(cfg, messages, temperature=0.7, max_tokens=2000):
    """云服务 LLM 调用：SSE 流式，返回拼接后的完整文本。失败返回 None。"""
    if requests is None:
        return None
    url = cfg["base_url"] + "/.cloud/llm/chat/completions"
    headers = {
        "x-wb-webapp-access-key": cfg["api_key"],
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "model": cfg.get("model") or "hunyuan-chat",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    for i in range(RETRIES + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload,
                                 timeout=CLOUD_TIMEOUT, stream=True)
            if resp.status_code != 200:
                _warn(f"第 {i + 1} 次云服务调用失败：HTTP {resp.status_code} "
                      f"{_redact(str(resp.text)[:160], cfg['api_key'])}")
                if i < RETRIES:
                    time.sleep(1.5 * (i + 1))
                continue
            chunks = []
            # 用 bytes 自行解码：requests 的 decode_unicode 会按 latin-1 误判中文
            for raw in resp.iter_lines():
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                body = line[5:].strip()
                if not body or body == "[DONE]":
                    continue
                try:
                    d = json.loads(body)
                except Exception:
                    continue
                for ch in (d.get("choices") or []):
                    delta = ch.get("delta") or {}
                    piece = delta.get("content")
                    if piece:
                        chunks.append(piece)
            text = "".join(chunks).strip()
            if text:
                return text
            _warn(f"第 {i + 1} 次云服务调用返回空内容（provider=workbuddy_cloud，"
                  f"model={cfg.get('model')}）")
        except Exception as e:
            _warn(f"第 {i + 1} 次云服务调用异常：{type(e).__name__}: {e}")
        if i < RETRIES:
            time.sleep(1.5 * (i + 1))
    return None


# ---------- 第 3 级：Hermes 配置的 api_keys 段 ----------

def _hermes_config_path():
    p = _clean(os.environ.get("XMT_HERMES_CONFIG"))
    if p:
        return p
    home = os.path.expanduser("~")
    cands = [
        os.path.join(home, "AppData", "Local", "hermes", "config.yaml"),
        os.path.join(home, ".config", "hermes", "config.yaml"),
        os.path.join(home, ".hermes", "config.yaml"),
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    return cands[0]


def _yaml_simple(path):
    """极简 YAML 解析：只认顶层 `段名:` 与紧随其后的二级 `key: value`。

    够读 api_keys / providers 这两段用，不引入 PyYAML 依赖。
    """
    out = {}
    cur = None
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for raw in f:
                line = raw.rstrip("\n").rstrip("\r")
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                indent = len(line) - len(line.lstrip(" "))
                s = line.strip()
                if indent == 0:
                    cur = s[:-1].strip() if s.endswith(":") else None
                    if cur and cur not in out:
                        out[cur] = {}
                    continue
                if cur and indent >= 2 and ":" in s and not s.startswith("-"):
                    k, _, v = s.partition(":")
                    out[cur][_clean(k)] = _clean(v)
    except Exception as e:
        _warn(f"读取 Hermes 配置失败：{type(e).__name__}")
        return {}
    return out


def _from_hermes_api_keys():
    path = _hermes_config_path()
    if not os.path.exists(path):
        return None
    y = _yaml_simple(path)
    api_keys = y.get("api_keys") or {}
    providers = y.get("providers") or {}
    if not api_keys:
        return None
    low = {str(k).lower(): v for k, v in api_keys.items()}
    for hint in API_KEY_NAME_HINTS:
        # 先精确匹配 provider 名，再模糊匹配（如 deepseek_api_key / deepseek-flash）
        hit = None
        for name, val in low.items():
            if name == hint:
                hit = (name, val)
                break
        if not hit:
            for name, val in low.items():
                if hint in name:
                    hit = (name, val)
                    break
        if hit and hit[1]:
            prov = hint
            base = ""
            for pname, pconf in providers.items():
                if str(pname).lower() == hint and isinstance(pconf, dict):
                    base = _clean(pconf.get("base_url"))
                    break
            if not base and hint == "deepseek":
                model_sec = y.get("model") or {}
                base = _clean(model_sec.get("base_url"))
            return _override(prov, base, "", hit[1], f"Hermes config.yaml api_keys:{hit[0]}")
    return None


# ---------- 总的解析入口 ----------

def resolve():
    """按四级优先级找可用 key；找不到返回 None。返回值里含 api_key，只许内部使用。"""
    if _disabled():
        return None
    if requests is None:
        _warn("requests 未安装，LLM 调用不可用（将走规则降级）")
        return None

    # 1) 环境变量
    k = _env("XMT_LLM_API_KEY", "DEEPSEEK_API_KEY")
    if k:
        return _override("deepseek", "", "", k, "环境变量 XMT_LLM_API_KEY/DEEPSEEK_API_KEY")

    # 2) config/llm.local.json
    cfg = _from_local_json()
    if cfg:
        return cfg

    # 3) Hermes 配置的 api_keys 段（按 provider 名匹配 deepseek 优先）
    cfg = _from_hermes_api_keys()
    if cfg:
        return cfg

    # 4) 其它供应商环境变量
    for env_name, prov in ENV_PROVIDERS:
        v = _clean(os.environ.get(env_name))
        if v:
            d = DEFAULTS[prov]
            return _override(prov, d["base_url"], d["model"], v, f"环境变量 {env_name}")

    # 5) 零密钥兜底：WorkBuddy 云服务 LLM
    cfg = _cloud_config()
    if cfg:
        return cfg

    return None


def available(verbose=False):
    """是否找到可用 key。verbose=True 时在 stderr 说明来源（不含 key）。"""
    cfg = resolve()
    if verbose:
        if cfg:
            _warn(f"可用 LLM：provider={cfg['provider']} model={cfg['model']} base_url={cfg['base_url']} 来源={cfg['source']}")
        else:
            _warn("未找到可用 LLM key，将使用规则模板版（内容仍完整可用）")
    return bool(cfg)


def info():
    """给 CLI 看的状态字典，永远不含 key 本身。"""
    cfg = resolve()
    if not cfg:
        return {"可用": False, "原因": "未找到可用 key（或已通过 XMT_LLM_DISABLED 强制关闭）",
                "查找顺序": ["环境变量 XMT_LLM_API_KEY / DEEPSEEK_API_KEY",
                             f"文件 {LOCAL_JSON}",
                             f"Hermes 配置 {_hermes_config_path()} 的 api_keys 段",
                             "环境变量 SILICONFLOW_API_KEY / ZHIPU_API_KEY / SUBLYX_API_KEY"]}
    return {"可用": True, "provider": cfg["provider"], "model": cfg["model"],
            "base_url": cfg["base_url"], "来源": cfg["source"], "key长度": len(cfg["api_key"])}


def chat(messages, model=None, temperature=0.7, max_tokens=2000):
    """调用 OpenAI 兼容 /chat/completions。

    messages: [{"role":"system"/"user"/"assistant","content":"..."}]
    成功返回文本；失败（无 key / 网络错 / 非 200 / 空内容）一律返回 None，绝不抛异常。
    """
    cfg = resolve()
    if not cfg:
        return None
    if cfg.get("provider") == "workbuddy_cloud":
        return _cloud_chat(cfg, messages, temperature=temperature, max_tokens=max_tokens)
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": model or cfg["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    headers = {"Authorization": "Bearer " + cfg["api_key"], "Content-Type": "application/json"}

    for i in range(RETRIES + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
            if resp.status_code == 200:
                data = resp.json() or {}
                choices = data.get("choices") or []
                text = ""
                if choices:
                    msg = choices[0].get("message") or {}
                    text = msg.get("content") or choices[0].get("text") or ""
                if text and str(text).strip():
                    return str(text).strip()
                _warn(f"第 {i + 1} 次调用返回空内容（provider={cfg['provider']}）")
            else:
                _warn(f"第 {i + 1} 次调用失败：HTTP {resp.status_code} "
                      f"{_redact(str(resp.text)[:160], cfg['api_key'])}（provider={cfg['provider']}）")
        except Exception as e:
            _warn(f"第 {i + 1} 次调用异常：{type(e).__name__}: {e}（provider={cfg['provider']}）")
        if i < RETRIES:
            time.sleep(1.5 * (i + 1))
    return None


def ask(prompt, system=None, **kw):
    """单轮问答便捷封装；失败返回 None。"""
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return chat(msgs, **kw)


# ---------- 文本解析小工具（供 topics / copy / direction 复用） ----------

def extract_json(text, expect="array"):
    """从模型回复里抠出 JSON（容忍 ```json 代码块、前后废话）。失败返回 None。"""
    if not text:
        return None
    s = re.sub(r"```(?:json)?", "", str(text)).strip()
    open_c, close_c = ("[", "]") if expect == "array" else ("{", "}")
    i, j = s.find(open_c), s.rfind(close_c)
    if i < 0 or j <= i:
        return None
    try:
        return json.loads(s[i:j + 1])
    except Exception:
        # 常见小毛病：中文引号、尾随逗号
        frag = s[i:j + 1].replace("“", '"').replace("”", '"').replace("，", ",")
        frag = re.sub(r",\s*([\]}])", r"\1", frag)
        try:
            return json.loads(frag)
        except Exception:
            return None


def strip_fence(text):
    """去掉 markdown 代码块围栏，保留纯文本 / markdown。"""
    if not text:
        return ""
    s = str(text).strip()
    s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


def main():
    import argparse
    ap = argparse.ArgumentParser(description="LLM 连通性检查 / 单轮问答（只读，不写任何文件）")
    ap.add_argument("--check", action="store_true", help="打印当前是否能找到可用 key")
    ap.add_argument("--ask", metavar="提示词", help="发一条单轮请求并打印回复")
    ap.add_argument("--model", help="临时覆盖模型名")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=800)
    args = ap.parse_args()

    st = info()
    for k, v in st.items():
        print(f"{k}: {v}")

    if args.ask:
        if not st.get("可用"):
            print("\n[跳过] 无可用 key，规则降级路径正常工作（用 XMT_LLM_DISABLED=1 可随时复现）")
            return
        print("\n--- 模型回复 ---")
        r = chat([{"role": "user", "content": args.ask}], model=args.model,
                 temperature=args.temperature, max_tokens=args.max_tokens)
        print(r if r else "[调用失败，已按约定返回 None]")


if __name__ == "__main__":
    main()
