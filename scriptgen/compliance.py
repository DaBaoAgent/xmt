"""医疗辅具口播合规扫描。

依据《广告法》第十六条 + 《医疗器械广告审查办法》的保守口径：
  - 不做功效/安全断言，不提治愈率/有效率
  - 不与别家对比，不用患者/专家/医生作推荐证明
  - 不使用绝对化/最高级用语
  - 不写价格（本模块自己的策略）
  - 数字类事实必须有知识库来源
只做文本扫描，不替代法务/广告审查。
"""
import re

from . import util


class Scanner:
    def __init__(self, cfg=None):
        self.cfg = cfg or util.compliance_config()
        self.rules = self.cfg.get("rules") or []
        self.disclaimer = self.cfg.get("disclaimer") or ""
        self.review_note = self.cfg.get("medical_review_note") or ""
        self.publish_checks = self.cfg.get("publish_checks") or []
        self.safe_context = self.cfg.get("safe_context_patterns") or []
        quality = util.config().get("quality") or {}
        self.numeric_check = self.cfg.get("numeric_claim_check",
                                          quality.get("flag_numeric_claims", True))
        self.numeric_units = (self.cfg.get("numeric_claim_allow_units")
                              or quality.get("numeric_claim_allow_units") or [])

    def _safe(self, text, start, end):
        ctx = text[max(0, start - 8):min(len(text), end + 8)]
        for s in self.safe_context:
            if s and s in ctx:
                return True
        return False

    def scan_text(self, text, location="口播", fact_text="", facts=None):
        text = str(text or "")
        findings = []
        seen = set()
        for rule in self.rules:
            pat = rule.get("pattern")
            if not pat:
                continue
            try:
                matches = list(re.finditer(pat, text, flags=re.I))
            except re.error:
                continue
            for m in matches:
                matched = m.group(0)
                if not matched.strip():
                    continue
                if self._safe(text, m.start(), m.end()):
                    continue
                key = (rule.get("id"), matched, self._ctx(text, m.start(), m.end()))
                if key in seen:
                    continue
                seen.add(key)
                findings.append({
                    "rule_id": rule.get("id"),
                    "severity": rule.get("severity") or "medium",
                    "match": matched[:80],
                    "context": self._ctx(text, m.start(), m.end()),
                    "message": rule.get("message") or "",
                    "suggest": rule.get("suggest") or "",
                    "location": location,
                })
        # 数字类事实必须能在知识库事实里找到
        if self.numeric_check:
            findings.extend(self._numeric(text, location, fact_text, facts))
        return findings

    @staticmethod
    def _ctx(text, start, end):
        return text[max(0, start - 12):min(len(text), end + 12)].replace("\n", " ").strip()

    def _numeric(self, text, location, fact_text, facts):
        units = self.numeric_units or []
        if not units:
            return []
        pat = r"(\d+(?:\.\d+)?)\s*(" + "|".join(re.escape(u) for u in units) + r")\b"
        source = str(fact_text or "")
        for f in facts or []:
            if isinstance(f, dict):
                source += "\n" + str(f.get("claim") or "")
        out = []
        for m in re.finditer(pat, text, flags=re.I):
            raw = m.group(0)
            num = m.group(1)
            # 事实文本里出现同一个数字+单位，或同一个数字，就视为有来源
            if re.search(re.escape(num) + r"\s*" + re.escape(m.group(2)), source, flags=re.I):
                continue
            if re.search(r"(?<![\d.])" + re.escape(num) + r"(?![\d.])", source):
                continue
            out.append({
                "rule_id": "numeric_unverified",
                "severity": "medium",
                "match": raw,
                "context": self._ctx(text, m.start(), m.end()),
                "message": "数字类事实在知识库事实片段里找不到来源。",
                "suggest": "补充知识库来源，或删掉具体数字，改成定性描述。",
                "location": location,
            })
        return out

    def scan_script(self, body_text, publish=None, transcript_text="", fact_text="", facts=None):
        findings = []
        findings.extend(self.scan_text(body_text, "口播", fact_text, facts))
        publish = publish or {}
        for key, label in (("douyin", "抖音发布"), ("channels", "视频号发布"),
                           ("xiaohongshu", "小红书发布")):
            p = publish.get(key) or {}
            parts = []
            parts.extend(p.get("titles") or ([p.get("title")] if p.get("title") else []))
            parts.extend(p.get("tags") or [])
            if p.get("body_opening"):
                parts.append(p["body_opening"])
            cover = p.get("cover") or {}
            if isinstance(cover, dict):
                parts.extend([cover.get("top") or "", cover.get("bottom") or ""])
            if parts:
                findings.extend(self.scan_text("\n".join(parts), label, fact_text, facts))
        if not publish.get("disclaimer"):
            findings.append({
                "rule_id": "missing_disclaimer",
                "severity": "high",
                "match": "发布包缺少免责声明",
                "context": "",
                "message": "发布文案必须固定附医疗器械个人使用提示。",
                "suggest": "在 publish.disclaimer 写入配置里的免责声明。",
                "location": "发布",
            })
        # 与对标原文的重合度 / 最长公共子串
        if transcript_text:
            q = util.config().get("quality") or {}
            n = int(q.get("overlap_ngram") or 8)
            max_ratio = float(q.get("max_overlap_ratio") or 0.12)
            ratio = util.overlap_ratio(body_text, transcript_text, n)
            lcs = _longest_common_substring(body_text, transcript_text)
            if ratio > max_ratio or len(lcs) >= 20:
                findings.append({
                    "rule_id": "overlap_high",
                    "severity": "high",
                    "match": (lcs[:40] + "…") if len(lcs) > 40 else lcs,
                    "context": f"{n}-gram 重合率 {ratio:.2%}；最长公共子串 {len(lcs)} 字",
                    "message": "与对标口播原句重合度过高，可能被判搬运。",
                    "suggest": "保留结构，逐句重写；删掉与对标相同的长句和独特措辞。",
                    "location": "口播",
                })
        # 去重
        dedup, seen = [], set()
        for f in findings:
            key = (f.get("rule_id"), f.get("match"), f.get("location"))
            if key in seen:
                continue
            seen.add(key)
            dedup.append(f)
        counts = {"high": sum(1 for f in dedup if f.get("severity") == "high"),
                  "medium": sum(1 for f in dedup if f.get("severity") == "medium"),
                  "low": sum(1 for f in dedup if f.get("severity") == "low")}
        return {
            "ok": counts["high"] == 0,
            "needs_review": bool(dedup),
            "counts": counts,
            "findings": dedup,
            "disclaimer": self.disclaimer,
            "medical_review_note": self.review_note,
            "publish_checks": self.publish_checks,
        }


def scan_script(body_text, publish=None, transcript_text="", fact_text="", facts=None):
    return Scanner().scan_script(body_text, publish, transcript_text, fact_text, facts)


def _longest_common_substring(a, b):
    a, b = str(a or ""), str(b or "")
    if not a or not b:
        return ""
    # 只保留文字/数字，降低标点造成的假重合
    a2 = re.sub(r"[\s\W_]+", "", a, flags=re.UNICODE)
    b2 = re.sub(r"[\s\W_]+", "", b, flags=re.UNICODE)
    if not a2 or not b2:
        return ""
    # 控制规模：取前 1500 字，足够抓搬运
    a2, b2 = a2[:1500], b2[:1500]
    prev = [0] * (len(b2) + 1)
    best_len = best_end = 0
    for i in range(1, len(a2) + 1):
        cur = [0] * (len(b2) + 1)
        ai = a2[i - 1]
        for j in range(1, len(b2) + 1):
            if ai == b2[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best_len:
                    best_len = cur[j]
                    best_end = i
        prev = cur
    return a2[best_end - best_len:best_end] if best_len else ""
