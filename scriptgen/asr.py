"""本地兜底 ASR：faster-whisper（默认 medium）+ OpenCC 繁转简。

只在 RedFox 提文案失败时使用。首次运行会下载模型（约 1.5GB）。
"""
import os
import sys
import traceback


def _opencc():
    try:
        from opencc import OpenCC
        return OpenCC("t2s")
    except Exception:
        return None


def _to_simplified(text, cc):
    if not cc or not text:
        return text
    try:
        return cc.convert(text)
    except Exception:
        return text


def transcribe(audio_path, model_name="medium", device="auto", compute_type="int8", language="zh"):
    """转写音频。返回 dict：text / segments / model / device / error。"""
    out = {
        "text": "",
        "segments": [],
        "model": model_name,
        "device": None,
        "language": language,
        "source": "local_whisper",
        "error": None,
    }
    if not audio_path or not os.path.exists(audio_path):
        out["error"] = "音频文件不存在"
        return out
    try:
        from faster_whisper import WhisperModel
    except Exception as e:
        out["error"] = f"faster-whisper 未安装：{type(e).__name__}"
        return out

    attempts = []
    if device == "cpu":
        attempts = [("cpu", compute_type or "int8")]
    elif device == "cuda":
        attempts = [("cuda", "float16"), ("cpu", compute_type or "int8")]
    else:  # auto
        attempts = [("cuda", "float16"), ("cpu", compute_type or "int8")]

    last_err = None
    model = None
    used = None
    for dev, ct in attempts:
        try:
            print(f"[asr] 加载 {model_name}（device={dev}, compute_type={ct}）...",
                  file=sys.stderr, flush=True)
            model = WhisperModel(model_name, device=dev, compute_type=ct)
            used = dev
            break
        except Exception as e:
            last_err = e
            print(f"[asr] {dev} 不可用：{type(e).__name__}: {str(e)[:160]}",
                  file=sys.stderr, flush=True)
    if model is None:
        out["error"] = f"Whisper 模型加载失败：{type(last_err).__name__ if last_err else 'unknown'}"
        return out

    try:
        segments, info = model.transcribe(
            audio_path,
            language=language or "zh",
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        cc = _opencc()
        texts, segs = [], []
        for seg in segments:
            txt = (seg.text or "").strip()
            if not txt:
                continue
            txt = _to_simplified(txt, cc)
            texts.append(txt)
            segs.append({
                "start": round(float(seg.start), 2),
                "end": round(float(seg.end), 2),
                "text": txt,
            })
        out["text"] = "".join(texts).strip()
        out["segments"] = segs
        out["device"] = used
        out["language"] = getattr(info, "language", language) or language
        out["duration"] = round(float(getattr(info, "duration", 0) or 0), 2)
        if not out["text"]:
            out["error"] = "Whisper 返回空文本"
    except Exception as e:
        out["error"] = f"Whisper 转写失败：{type(e).__name__}: {str(e)[:200]}"
        traceback.print_exc()
    finally:
        try:
            del model
        except Exception:
            pass
    return out
