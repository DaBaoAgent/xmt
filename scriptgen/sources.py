"""对标视频提取：抖音 / 视频号。

主通道：RedFox 提文案（transcript_submit/result）+ 作品元数据。
兜底：RedFox 去水印下载 → ffmpeg 抽音频 → 本地 faster-whisper。

只在这里接触平台/RedFox；不写数据库、不生成脚本。
"""
import os
import re
import sys
import time
import json
import shutil
import subprocess
import requests

from . import util
from . import asr

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")


class ExtractionError(RuntimeError):
    pass


class CallCounter:
    """一次批次内的调用计数；poll 不计费，但单独记录。"""

    def __init__(self):
        self.events = []

    def add(self, platform, operation, billable=True, note=""):
        self.events.append({
            "platform": platform,
            "operation": operation,
            "billable": bool(billable),
            "note": note,
        })

    @property
    def billable(self):
        return sum(1 for e in self.events if e["billable"])

    @property
    def polls(self):
        return sum(1 for e in self.events if not e["billable"])

    def snapshot(self):
        return {
            "billable": self.billable,
            "polls": self.polls,
            "events": list(self.events),
        }


class RedFoxExtractor:
    def __init__(self, cfg=None, counter=None, keep_video=False, logger=None):
        self.cfg = cfg or util.config()
        self.redfox_cfg = self.cfg.get("redfox") or {}
        self.asr_cfg = self.cfg.get("asr") or {}
        self.counter = counter or CallCounter()
        self.keep_video = keep_video or bool(self.asr_cfg.get("keep_video"))
        self.logger = logger or (lambda msg: print(msg, file=sys.stderr, flush=True))
        self._client = None
        self.poll_interval = int(self.redfox_cfg.get("poll_interval_sec") or 3)
        self.timeout = int(self.redfox_cfg.get("transcript_timeout_sec") or 180)

    # ---------- 基础 ----------

    def client(self):
        if self._client is None:
            from redfox import RedFoxClient
            self._client = RedFoxClient()
        return self._client

    def _record(self, platform, operation, billable=True, note=""):
        self.counter.add(platform, operation, billable=billable, note=note)

    @staticmethod
    def _err(e):
        resp = getattr(e, "response", None)
        extra = ""
        if resp:
            try:
                extra = " | " + json.dumps(resp, ensure_ascii=False)[:260]
            except Exception:
                extra = " | " + str(resp)[:260]
        return f"{type(e).__name__}: {str(e)[:300]}{extra}"

    # ---------- 入口 ----------

    def extract(self, url, platform=None):
        platform = platform or util.detect_platform(url)
        if platform == "douyin":
            return self.extract_douyin(url)
        if platform == "channels":
            return self.extract_channels(url)
        return self._error_result(platform, url, "不支持的链接平台（只支持抖音/视频号）")

    def _error_result(self, platform, url, message, warnings=None, meta=None):
        out = self._base_result(platform, url)
        out["error"] = message
        out["warnings"] = list(warnings or [])
        if meta:
            out.update({k: v for k, v in meta.items() if v is not None})
        return out

    def _base_result(self, platform, url):
        return {
            "platform": platform,
            "url": url,
            "resolved_url": url,
            "video_id": None,
            "author": None,
            "author_id": None,
            "title": None,
            "description": None,
            "duration_sec": None,
            "stats": {"like": None, "comment": None, "share": None, "collect": None, "play": None},
            "publish_time": None,
            "tags": [],
            "cover_url": None,
            "metadata_source": None,
            "transcript": None,
            "warnings": [],
            "error": None,
            "api_calls": self.counter.snapshot(),
        }

    # ---------- 抖音 ----------

    def extract_douyin(self, url):
        out = self._base_result("douyin", url)
        client = self.client()
        warnings = []
        resolved_url, video_id = self.resolve_douyin(url)
        out["resolved_url"] = resolved_url or url
        out["video_id"] = video_id

        meta = {}
        # 1) 广域库：有 video_id 时最稳
        if video_id:
            try:
                self._record("douyin", "get_work_wide")
                raw = client.douyin.get_work_wide(video_id=video_id)
                meta = self._norm_douyin_wide(raw)
                out["metadata_source"] = "redfox_wide"
            except Exception as e:
                warnings.append("广域库元数据失败：" + self._err(e))
        # 2) 优质库按链接
        if not meta.get("title") and not meta.get("author"):
            try:
                self._record("douyin", "get_work")
                raw = client.douyin.get_work(work_url=url)
                meta = self._merge_meta(meta, self._norm_douyin_quality(raw))
                if meta:
                    out["metadata_source"] = "redfox_quality"
            except Exception as e:
                warnings.append("优质库元数据失败：" + self._err(e))
        # 3) 下载接口补元数据（同时给本地 ASR 备用）
        download_payload = None
        if not meta.get("title"):
            try:
                self._record("douyin", "download_douyin")
                download_payload = client.tools.download_douyin(url)
                meta = self._merge_meta(meta, self._norm_download(download_payload, "douyin"))
                if meta:
                    out["metadata_source"] = "redfox_download"
            except Exception as e:
                warnings.append("下载接口元数据失败：" + self._err(e))

        if meta:
            self._apply_meta(out, meta)
        if not out["video_id"] and meta.get("video_id"):
            out["video_id"] = meta["video_id"]

        # 提文案
        transcript = None
        try:
            self._record("douyin", "transcript_submit")
            task = client.douyin.transcript_submit(url)
            task_id = (task or {}).get("taskId") or (task or {}).get("task_id")
            if not task_id:
                raise ExtractionError("提文案提交未返回 taskId")
            transcript = self._poll_transcript("douyin", task_id)
            transcript["task_id"] = task_id
        except Exception as e:
            warnings.append("RedFox 提文案失败：" + self._err(e))

        if not transcript or not transcript.get("text"):
            warnings.append("转本地 Whisper 兜底")
            local = self._local_asr_from_download(
                "douyin", url, download_payload, client, warnings)
            if local and local.get("text"):
                transcript = local
            elif local:
                warnings.extend(local.get("warnings") or [])
                out["error"] = local.get("error") or "本地兜底失败"

        if transcript and transcript.get("text"):
            out["transcript"] = transcript
            out["error"] = None
            if not out.get("duration_sec") and transcript.get("segments"):
                out["duration_sec"] = transcript["segments"][-1].get("end")
        elif not out.get("error"):
            out["error"] = "未取到口播文案"
        out["warnings"] = warnings
        out["api_calls"] = self.counter.snapshot()
        return out

    def resolve_douyin(self, url):
        """短链 → video_id + 最终 URL。失败时保留原 URL。"""
        if not url:
            return url, None
        m = re.search(r"douyin\.com/(?:video|note)/(\d{10,})", url)
        if m:
            return url, m.group(1)
        m = re.search(r"[?&]modal_id=(\d{10,})", url)
        if m:
            return url, m.group(1)
        try:
            r = requests.get(url, headers={"User-Agent": UA}, allow_redirects=True, timeout=15)
            final = str(r.url)
            for pat in (r"douyin\.com/(?:video|note)/(\d{10,})",
                        r"[?&]modal_id=(\d{10,})"):
                m = re.search(pat, final)
                if m:
                    return final, m.group(1)
            text = r.text or ""
            m = re.search(r"https?://www\.douyin\.com/video/(\d{10,})", text)
            if m:
                return m.group(0), m.group(1)
            m = re.search(r'"aweme_id"\s*:\s*"(\d{10,})"', text)
            if m:
                return final, m.group(1)
            return final, None
        except Exception as e:
            self.logger(f"[douyin] 短链解析失败：{type(e).__name__}: {str(e)[:120]}")
            return url, None

    def _norm_douyin_wide(self, d):
        if not isinstance(d, dict):
            return {}
        content = d.get("content") or ""
        tags = [t.get("tagName") for t in (d.get("tagList") or []) if t.get("tagName")]
        return {
            "video_id": str(d.get("videoId") or "") or None,
            "author": d.get("authorName"),
            "author_id": d.get("authorUniqueId") or d.get("authorUid"),
            "title": content.strip(),
            "description": content.strip(),
            "duration_sec": self._duration_sec(d.get("duration")),
            "stats": {
                "like": util.parse_count(d.get("likeCount")),
                "comment": util.parse_count(d.get("commentCount")),
                "share": util.parse_count(d.get("shareCount")),
                "collect": util.parse_count(d.get("collectCount")),
                "play": None,
            },
            "publish_time": d.get("publishTime"),
            "tags": tags,
            "cover_url": d.get("coverUrl"),
        }

    def _norm_douyin_quality(self, d):
        if not isinstance(d, dict):
            return {}
        item = d.get("aweme_detail") or d.get("aweme") or d.get("data") or d
        if not isinstance(item, dict):
            return {}
        author = item.get("author") or {}
        stats = item.get("statistics") or {}
        desc = item.get("desc") or item.get("title") or ""
        video = item.get("video") if isinstance(item.get("video"), dict) else {}
        cover_obj = video.get("cover") if isinstance(video.get("cover"), dict) else {}
        cover_urls = cover_obj.get("url_list") or []
        cover = cover_urls[0] if cover_urls else None
        return {
            "video_id": str(item.get("aweme_id") or item.get("video_id") or "") or None,
            "author": author.get("nickname") or item.get("author_name"),
            "author_id": author.get("unique_id") or author.get("uid"),
            "title": desc.strip(),
            "description": desc.strip(),
            "duration_sec": self._duration_sec(item.get("duration")),
            "stats": {
                "like": util.parse_count(stats.get("digg_count") or item.get("like_count")),
                "comment": util.parse_count(stats.get("comment_count") or item.get("comment_count")),
                "share": util.parse_count(stats.get("share_count") or item.get("share_count")),
                "collect": util.parse_count(stats.get("collect_count") or item.get("collect_count")),
                "play": util.parse_count(stats.get("play_count") or item.get("play_count")),
            },
            "publish_time": item.get("create_time") or item.get("publish_time"),
            "tags": self._tags_from_text(desc),
            "cover_url": cover,
        }

    def _norm_download(self, d, platform):
        if not isinstance(d, dict):
            return {}
        resources = d.get("resources") or d.get("resource") or []
        r0 = resources[0] if resources and isinstance(resources[0], dict) else {}
        desc = d.get("desc") or d.get("title") or d.get("description") or ""
        duration = d.get("durationSeconds") or d.get("duration") or r0.get("durationSeconds")
        return {
            "video_id": str(d.get("videoId") or d.get("video_id") or "") or None,
            "author": d.get("nickname") or d.get("authorName") or d.get("author_name"),
            "author_id": d.get("authorId") or d.get("author_id"),
            "title": desc.strip(),
            "description": desc.strip(),
            "duration_sec": self._duration_sec(duration),
            "stats": {
                "like": util.parse_count(d.get("likeNum") or d.get("likeCount")),
                "comment": util.parse_count(d.get("commentNum") or d.get("commentCount")),
                "share": util.parse_count(d.get("shareNum") or d.get("shareCount") or d.get("forwardCount")),
                "collect": util.parse_count(d.get("collectNum") or d.get("favoriteNum")),
                "play": util.parse_count(d.get("playCount")),
            },
            "publish_time": d.get("publishTime"),
            "tags": self._tags_from_text(desc),
            "cover_url": d.get("cover") or r0.get("coverUrl"),
        }

    # ---------- 视频号 ----------

    def extract_channels(self, url):
        out = self._base_result("channels", url)
        client = self.client()
        warnings = []
        meta = {}
        try:
            self._record("channels", "get_work_by_link")
            raw = client.wechat_channels.get_work_by_link(url)
            meta = self._norm_channels(raw)
            out["metadata_source"] = "redfox_channels_link"
        except Exception as e:
            warnings.append("视频号详情失败：" + self._err(e))
        if meta:
            self._apply_meta(out, meta)

        transcript = None
        try:
            self._record("channels", "transcript_submit")
            task = client.wechat_channels.transcript_submit(url)
            task_id = (task or {}).get("taskId") or (task or {}).get("task_id")
            if not task_id:
                raise ExtractionError("提文案提交未返回 taskId")
            transcript = self._poll_transcript("channels", task_id)
            transcript["task_id"] = task_id
        except Exception as e:
            warnings.append("RedFox 提文案失败：" + self._err(e))

        if not transcript or not transcript.get("text"):
            warnings.append("转本地 Whisper 兜底")
            local = self._local_asr_from_download("channels", url, None, client, warnings)
            if local and local.get("text"):
                transcript = local
            elif local:
                warnings.extend(local.get("warnings") or [])
                out["error"] = local.get("error") or "本地兜底失败"

        if transcript and transcript.get("text"):
            out["transcript"] = transcript
            out["error"] = None
            if not out.get("duration_sec") and transcript.get("segments"):
                out["duration_sec"] = transcript["segments"][-1].get("end")
        elif not out.get("error"):
            out["error"] = "未取到口播文案"
        out["warnings"] = warnings
        out["api_calls"] = self.counter.snapshot()
        return out

    def _norm_channels(self, d):
        if not isinstance(d, dict):
            return {}
        title = (d.get("title") or d.get("description") or "").strip()
        desc = (d.get("description") or title).strip()
        return {
            "video_id": str(d.get("exportId") or d.get("videoId") or d.get("id") or "") or None,
            "author": d.get("nickname"),
            "author_id": d.get("exportId") or d.get("userId"),
            "title": title,
            "description": desc,
            "duration_sec": self._duration_sec(d.get("duration") or d.get("durationSeconds")),
            "stats": {
                "like": util.parse_count(d.get("likeNum") or d.get("likeCount")),
                "comment": util.parse_count(d.get("commentNum") or d.get("commentCount")),
                "share": util.parse_count(d.get("shareNum") or d.get("shareCount") or d.get("forwardCount")),
                "collect": util.parse_count(d.get("collectNum") or d.get("favoriteNum")),
                "play": util.parse_count(d.get("playCount")),
            },
            "publish_time": d.get("publishTime"),
            "tags": self._tags_from_text(desc),
            "cover_url": d.get("cover"),
        }

    # ---------- 提文案轮询 ----------

    def _poll_transcript(self, platform, task_id):
        client = self.client()
        fn = (client.douyin.transcript_result if platform == "douyin"
              else client.wechat_channels.transcript_result)
        deadline = time.time() + self.timeout
        last_status = None
        while time.time() < deadline:
            self._record(platform, "transcript_result", billable=False, note=str(task_id))
            try:
                r = fn(task_id)
            except Exception as e:
                raise ExtractionError("查询提文案结果失败：" + self._err(e))
            if not isinstance(r, dict):
                raise ExtractionError("提文案结果结构异常")
            status = str(r.get("status") or "").lower()
            last_status = status
            if status in ("succeeded", "success", "completed", "done", "finished"):
                text = (r.get("text") or "").strip()
                if not text:
                    raise ExtractionError("提文案任务成功但文本为空")
                return self._normalize_transcript(r)
            if status in ("failed", "fail", "error", "cancelled", "canceled"):
                raise ExtractionError(f"提文案失败：{r.get('failReason') or status}")
            if r.get("failReason"):
                raise ExtractionError(f"提文案失败：{r.get('failReason')}")
            time.sleep(self.poll_interval)
        raise ExtractionError(f"提文案超时（{self.timeout} 秒），最后状态 {last_status or 'unknown'}")

    @staticmethod
    def _normalize_transcript(r):
        text = (r.get("text") or "").strip()
        segs = []
        for s in (r.get("stampSents") or r.get("segments") or []):
            if not isinstance(s, dict):
                continue
            txt = (s.get("textSeg") or s.get("text") or "").strip()
            if not txt:
                continue
            start = s.get("start") if s.get("start") is not None else s.get("start_time")
            end = s.get("end") if s.get("end") is not None else s.get("end_time")
            segs.append({
                "start": RedFoxExtractor._time_sec(start),
                "end": RedFoxExtractor._time_sec(end),
                "text": txt,
            })
        return {
            "text": text,
            "segments": segs,
            "source": "redfox",
            "language": "zh",
            "task_id": r.get("taskId"),
            "error": None,
        }

    # ---------- 本地兜底 ----------

    def _local_asr_from_download(self, platform, url, download_payload, client, warnings):
        local = {"text": "", "segments": [], "source": "local_whisper", "error": None,
                 "warnings": []}
        video_path = audio_path = None
        try:
            if download_payload is None:
                try:
                    self._record(platform, f"download_{platform}")
                    download_payload = (client.tools.download_douyin(url) if platform == "douyin"
                                        else client.tools.download_wechat_channels(url))
                except Exception as e:
                    local["error"] = "下载视频失败：" + self._err(e)
                    return local
            video_url = self._find_video_url(download_payload)
            if not video_url:
                local["error"] = "下载接口未返回视频地址"
                return local
            video_path = self._download_video(video_url, platform)
            audio_path = self._extract_audio(video_path)
            result = asr.transcribe(
                audio_path,
                model_name=self.asr_cfg.get("model") or "medium",
                device=self.asr_cfg.get("device") or "auto",
                compute_type=self.asr_cfg.get("compute_type") or "int8",
                language=self.asr_cfg.get("language") or "zh",
            )
            local.update({
                "text": result.get("text") or "",
                "segments": result.get("segments") or [],
                "source": "local_whisper",
                "model": result.get("model"),
                "device": result.get("device"),
                "language": result.get("language") or "zh",
                "error": result.get("error"),
            })
        except Exception as e:
            local["error"] = "本地兜底失败：" + self._err(e)
        finally:
            if not self.keep_video:
                for p in (video_path, audio_path):
                    try:
                        if p and os.path.exists(p):
                            os.remove(p)
                    except Exception:
                        pass
        return local

    def _find_video_url(self, payload):
        """从下载接口返回里找视频直链，避开封面图。"""
        if not isinstance(payload, dict):
            return None
        for key in ("videoUrl", "downloadUrl", "playUrl", "video_url", "url"):
            v = payload.get(key)
            if isinstance(v, str) and self._looks_video(v):
                return v
        for res in (payload.get("resources") or payload.get("resource") or []):
            if isinstance(res, dict):
                for key in ("downloadUrl", "videoUrl", "playUrl", "url"):
                    v = res.get(key)
                    if isinstance(v, str) and self._looks_video(v):
                        return v
        # 递归兜底
        best = None
        for v in self._walk_strings(payload):
            if self._looks_video(v):
                if "douyinvod" in v or "finder.video.qq.com" in v or ".mp4" in v:
                    return v
                best = best or v
        return best

    @staticmethod
    def _walk_strings(obj):
        if isinstance(obj, str):
            yield obj
        elif isinstance(obj, dict):
            for v in obj.values():
                yield from RedFoxExtractor._walk_strings(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                yield from RedFoxExtractor._walk_strings(v)

    @staticmethod
    def _looks_video(u):
        if not isinstance(u, str) or not u.startswith("http"):
            return False
        low = u.lower()
        if any(x in low for x in ("cover", ".jpg", ".jpeg", ".png", ".webp")):
            return False
        return any(x in low for x in (".mp4", "douyinvod", "finder.video.qq.com", "video/tos"))

    def _download_video(self, url, platform):
        tmp_dir = util.project_path((self.cfg.get("paths") or {}).get("tmp_dir") or "data/tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        path = os.path.join(tmp_dir, f"{platform}-{util.short_hash(url, 10)}.mp4")
        headers = {"User-Agent": UA, "Referer": "https://www.douyin.com/" if platform == "douyin" else "https://channels.weixin.qq.com/"}
        with requests.get(url, headers=headers, stream=True, timeout=120) as r:
            r.raise_for_status()
            total = 0
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > 300 * 1024 * 1024:
                        raise ExtractionError("视频超过 300MB，停止下载")
                    f.write(chunk)
        if not os.path.exists(path) or os.path.getsize(path) < 1024:
            raise ExtractionError("下载的视频为空")
        return path

    def _extract_audio(self, video_path):
        tmp_dir = os.path.dirname(video_path)
        audio_path = os.path.splitext(video_path)[0] + ".wav"
        cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", audio_path]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        except FileNotFoundError:
            raise ExtractionError("未找到 ffmpeg，请安装并加入 PATH")
        except subprocess.TimeoutExpired:
            raise ExtractionError("ffmpeg 抽音频超时")
        if p.returncode != 0 or not os.path.exists(audio_path):
            raise ExtractionError("ffmpeg 抽音频失败：" + (p.stderr or "")[-300:])
        return audio_path

    # ---------- 工具 ----------

    def _apply_meta(self, out, meta):
        for key in ("video_id", "author", "author_id", "title", "description",
                    "duration_sec", "publish_time", "cover_url"):
            if not out.get(key) and meta.get(key) is not None:
                out[key] = meta[key]
        if meta.get("stats"):
            for k, v in meta["stats"].items():
                if out["stats"].get(k) is None and v is not None:
                    out["stats"][k] = v
        if meta.get("tags"):
            tags = list(out.get("tags") or [])
            for t in meta["tags"]:
                if t and t not in tags:
                    tags.append(t)
            out["tags"] = tags

    @staticmethod
    def _merge_meta(primary, extra):
        out = dict(primary or {})
        for k, v in (extra or {}).items():
            if k == "stats":
                stats = dict(out.get("stats") or {})
                for sk, sv in (v or {}).items():
                    if stats.get(sk) is None and sv is not None:
                        stats[sk] = sv
                out["stats"] = stats
            elif k == "tags":
                tags = list(out.get("tags") or [])
                for t in v or []:
                    if t and t not in tags:
                        tags.append(t)
                out["tags"] = tags
            elif out.get(k) in (None, "", [], {}):
                out[k] = v
        return out

    @staticmethod
    def _duration_sec(v):
        if v is None:
            return None
        try:
            f = float(v)
        except Exception:
            return None
        if f <= 0:
            return None
        return round(f / 1000.0, 2) if f > 1000 else round(f, 2)

    @staticmethod
    def _time_sec(v):
        if v is None:
            return None
        try:
            f = float(v)
        except Exception:
            return None
        return round(f / 1000.0, 2) if f > 1000 else round(f, 2)

    @staticmethod
    def _tags_from_text(text):
        return re.findall(r"#([^\s#]+)", str(text or ""))
