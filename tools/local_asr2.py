"""本地 ASR（绕开 faster_whisper 的 PyAV 解码，改用 numpy 读 wav）。

原因：本机 av 版本与 faster_whisper 不兼容（av.open 不接受 metadata_errors）。

用法：
  .venv/Scripts/python.exe tools/local_asr2.py <wav路径> [模型]
"""
import io
import sys
import os
import wave
import subprocess

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def to_wav(src):
    if src.lower().endswith(".wav"):
        return src
    dst = os.path.splitext(src)[0] + ".wav"
    subprocess.run(["ffmpeg", "-y", "-i", src, "-vn", "-ac", "1",
                    "-ar", "16000", "-c:a", "pcm_s16le", dst],
                   check=True, capture_output=True)
    return dst


def read_wav(path):
    import numpy as np
    with wave.open(path, "rb") as w:
        n = w.getnframes()
        raw = w.readframes(n)
        ch = w.getnchannels()
        sw = w.getsampwidth()
    dt = {1: np.uint8, 2: np.int16, 4: np.int32}.get(sw)
    a = np.frombuffer(raw, dtype=dt).astype(np.float32)
    if sw == 2:
        a /= 32768.0
    elif sw == 1:
        a = (a - 128) / 128.0
    elif sw == 4:
        a /= 2147483648.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    return a


def main():
    src = sys.argv[1]
    model_name = sys.argv[2] if len(sys.argv) > 2 else "medium"
    wav = to_wav(src)
    audio = read_wav(wav)
    print("音频: %.1f 秒 (%d 采样点)" % (len(audio) / 16000, len(audio)))

    from faster_whisper import WhisperModel
    print("加载模型 %s …" % model_name)
    m = WhisperModel(model_name, device="cpu", compute_type="int8")
    print("转写中 …")
    segs, info = m.transcribe(audio, language="zh", beam_size=5,
                              vad_filter=True,
                              initial_prompt="以下是普通话短视频口播文案。")
    rows = []
    for s in segs:
        rows.append((s.start, s.text.strip()))
        print("[%5.1fs] %s" % (s.start, s.text.strip()))
    full = "".join(t for _, t in rows)
    n = len(full.replace(" ", ""))
    print("\n全文（%d 字）: %s" % (n, full))
    out = os.path.splitext(wav)[0] + "_转写.txt"
    with io.open(out, "w", encoding="utf-8") as f:
        for st, t in rows:
            f.write("[%5.1fs] %s\n" % (st, t))
        f.write("\n全文：%s\n" % full)
    print("已存:", out)


if __name__ == "__main__":
    main()
