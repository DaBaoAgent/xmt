"""xmt 拍摄脚本模块：对标视频提取 → 本地知识库 → 三号逐字稿。

入口：
    python -m scriptgen add "<链接/分享文本>" [--account oral|brand|personal]
    python -m scriptgen approve <编号...>
    python -m scriptgen sync <编号...>

设计口径见 docs/拍摄脚本模块.md 与 config/scriptgen.json。
"""
__version__ = "0.1.0"
