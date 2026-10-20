"""公司知识库 MCP 客户端（streamable HTTP，最小实现）。

只用标准库 + requests：
  - initialize / notifications/initialized
  - tools/call: kb_search / kb_read / kb_write / kb_list

约定：token 只从环境变量 COMPANY_KB_TOKEN 读，任何日志都不打印 token。
"""
import os
import json
import requests

from . import util


class CompanyKBError(RuntimeError):
    pass


class CompanyKB:
    def __init__(self, url=None, token=None, timeout=None):
        cfg = (util.config().get("company_kb") or {})
        self.url = (url or os.environ.get("COMPANY_KB_URL")
                    or cfg.get("url") or "http://192.168.1.79:8788/mcp")
        self.token = token if token is not None else os.environ.get("COMPANY_KB_TOKEN", "")
        self.timeout = int(timeout or cfg.get("timeout_sec") or 30)
        self.session = requests.Session()
        # 内网地址绕过全局代理；与 README 的 NO_PROXY 约定一致
        self.session.trust_env = False
        self._id = 0
        self._initialized = False
        self._mcp_session_id = None
        self._instructions = ""

    # ---------- 基础 ----------

    def available(self):
        return bool(self.token)

    def _headers(self):
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.token:
            h["Authorization"] = "Bearer " + self.token
        if self._mcp_session_id:
            h["mcp-session-id"] = self._mcp_session_id
        return h

    def _next_id(self):
        self._id += 1
        return self._id

    @staticmethod
    def _parse_messages(resp):
        raw = resp.content.decode("utf-8", errors="replace")
        ctype = (resp.headers.get("content-type") or "").lower()
        if "text/event-stream" in ctype or raw.lstrip().startswith(("event:", "data:")):
            out = []
            for block in raw.split("\n\n"):
                data_lines = []
                for line in block.splitlines():
                    if line.startswith("data:"):
                        data_lines.append(line[5:].lstrip())
                if not data_lines:
                    continue
                try:
                    out.append(json.loads("\n".join(data_lines)))
                except Exception:
                    continue
            return out
        try:
            return [resp.json()]
        except Exception:
            return []

    def _post(self, payload, count=True):
        if not self.token:
            raise CompanyKBError("未配置 COMPANY_KB_TOKEN，无法访问公司知识库")
        try:
            resp = self.session.post(self.url, headers=self._headers(),
                                     json=payload, timeout=self.timeout)
        except requests.RequestException as e:
            raise CompanyKBError(f"公司知识库连接失败：{type(e).__name__}（{self.url}）") from e
        sid = resp.headers.get("mcp-session-id")
        if sid:
            self._mcp_session_id = sid
        if resp.status_code >= 400:
            raise CompanyKBError(f"公司知识库 HTTP {resp.status_code}：{resp.text[:300]}")
        msgs = self._parse_messages(resp)
        err = next((m.get("error") for m in msgs if m.get("error")), None)
        if err:
            raise CompanyKBError(f"公司知识库 JSON-RPC 错误：{str(err)[:300]}")
        return msgs

    def _initialize(self):
        if self._initialized:
            return
        msgs = self._post({
            "jsonrpc": "2.0", "id": self._next_id(), "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "xmt-scriptgen", "version": "0.1.0"},
            },
        }, count=False)
        for m in msgs:
            if m.get("id") and isinstance(m.get("result"), dict):
                self._instructions = m["result"].get("instructions") or ""
                break
        # notification，无 id；服务端可能返回 202/空 body
        try:
            self.session.post(
                self.url, headers=self._headers(),
                json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                timeout=self.timeout)
        except requests.RequestException:
            pass
        self._initialized = True

    def _call(self, name, arguments):
        self._initialize()
        rid = self._next_id()
        msgs = self._post({
            "jsonrpc": "2.0", "id": rid, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }, count=True)
        result = None
        for m in msgs:
            if m.get("id") == rid:
                result = m.get("result")
                break
        if result is None:
            raise CompanyKBError(f"公司知识库未返回 {name} 的结果")
        if isinstance(result, dict) and result.get("isError"):
            text = self._content_text(result)
            raise CompanyKBError(f"公司知识库 {name} 执行失败：{text[:500]}")
        return result

    @staticmethod
    def _content_text(result):
        parts = []
        for c in (result or {}).get("content") or []:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text") or "")
        return "\n".join(parts)

    # ---------- 工具封装 ----------

    def search(self, query, kbs=None, top_k=8, mode="keyword"):
        args = {"query": str(query or "").strip(), "top_k": int(top_k), "mode": mode}
        if kbs:
            args["kb"] = list(kbs) if isinstance(kbs, (list, tuple)) else [kbs]
        result = self._call("kb_search", args)
        text = self._content_text(result)
        try:
            data = json.loads(text)
        except Exception:
            return []
        hits = data.get("hits") if isinstance(data, dict) else None
        return hits or []

    def read(self, doc_id, offset=0, max_chars=6000):
        result = self._call("kb_read", {
            "doc_id": str(doc_id), "offset": int(offset), "max_chars": int(max_chars)})
        text = self._content_text(result)
        try:
            data = json.loads(text)
        except Exception:
            return {"doc_id": doc_id, "content": text}
        if isinstance(data, dict):
            data.setdefault("doc_id", doc_id)
            return data
        return {"doc_id": doc_id, "content": text}

    def read_text(self, doc_id, max_chars=6000):
        data = self.read(doc_id, max_chars=max_chars)
        return (data.get("content") or data.get("text") or "") if isinstance(data, dict) else str(data)

    def write(self, kb, title, content, doc_id=None, tags=None, expected_version=None):
        args = {"kb": kb, "title": title, "content": content}
        if doc_id:
            args["doc_id"] = doc_id
        if tags:
            args["tags"] = list(tags)
        if expected_version is not None:
            args["expected_version"] = int(expected_version)
        result = self._call("kb_write", args)
        text = self._content_text(result)
        try:
            return json.loads(text)
        except Exception:
            return {"raw": text}

    def list_docs(self, kb=None, prefix=None, limit=50, updated_after=None):
        args = {"limit": int(limit)}
        if kb:
            args["kb"] = kb
        if prefix:
            args["prefix"] = prefix
        if updated_after:
            args["updated_after"] = updated_after
        result = self._call("kb_list", args)
        text = self._content_text(result)
        try:
            data = json.loads(text)
            return data.get("docs") or data.get("items") or data.get("list") or []
        except Exception:
            return []

    def close(self):
        try:
            self.session.close()
        except Exception:
            pass
