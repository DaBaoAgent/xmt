"""洞察层（insight）：把采集到的数据变成「选题 → 文案 → 下一步拍摄方向」。

模块划分：
  llm.py       统一 LLM 调用（key 四级回退；无 key 时自动降级，函数签名不变）
  topics.py    选题：从热搜 / 对标爆款 / 自有作品汇总素材，产出选题并落库 topics 表
  copy.py      文案：小红书图文笔记 + 抖音口播稿（合规体检 + 反 AI 味）
  direction.py 方向：近 N 天数据复盘，给出下一步拍摄方向，落 insights 表并写 out/

约定：
  - 全部中文输出（注释、日志、产物）；
  - 没找到可用 LLM key 时，所有生成函数自动走规则模板版，仍然产出完整中文内容；
  - 本包只读 db.py / config/ / collectors/，不修改它们（config/llm.local.json 由使用者自行创建）。
"""

__version__ = "1.0.0"

__all__ = ["llm", "topics", "copy", "direction"]
