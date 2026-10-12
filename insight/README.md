# insight · 洞察层（数据 → 选题 → 文案 → 下一步方向）

把 `xmt` 采集到的数据（账号快照 / 作品明细 / 热搜 / 关键词搜索）加工成**可以开拍的东西**：
选题池、小红书图文笔记、抖音口播稿、下一步拍摄方向。

- 全中文输出（注释、日志、产物）
- 只依赖**标准库 + requests**（DB 走项目自带的 `db.py`，不改动 db.py / collectors/ / config/）
- **没有可用 LLM key 也能跑**：所有生成函数自动降级为规则模板版，产出完整中文内容（有自检项标注生成方式）

## 目录

```
insight/
├─ __init__.py     # 包说明
├─ llm.py          # 统一 LLM 调用（OpenAI 兼容 /chat/completions）
├─ topics.py       # 素材汇总 + 选题生成 → topics 表
├─ copy.py         # 小红书笔记 / 抖音口播稿 + 合规体检
├─ direction.py    # 下一步拍摄方向 → insights 表 + out/next_direction.md
└─ README.md       # 本文件
```

## 接口契约（签名固定，供上层调度用）

```python
from insight import llm, topics, copy, direction

llm.chat(messages, model=None, temperature=0.7, max_tokens=2000) -> str | None
llm.available() -> bool
topics.generate_topics(platform=None, account_id=None, n=10, use_llm=True) -> list[dict]
topics.collect_material(platform=None) -> dict
copy.write_xhs_note(topic: dict, account: dict, use_llm=True) -> dict
copy.write_douyin_script(topic: dict, account: dict, use_llm=True) -> dict
direction.next_direction(days=7, use_llm=True) -> str
```

写库位置：`topics.generate_topics` → `topics` 表；`direction.next_direction` → `insights(kind='direction')`
并写 `out/next_direction.md`。

## CLI

```bash
# 素材汇总（只读，不生成）
.venv/Scripts/python.exe -m insight.topics --material

# 生成 10 条选题并落库
.venv/Scripts/python.exe -m insight.topics --n 10
.venv/Scripts/python.exe -m insight.topics --n 8 --platform douyin
.venv/Scripts/python.exe -m insight.topics --account-id sxy_brand_xhs --no-llm

# 看选题池 / 看风格库
.venv/Scripts/python.exe -m insight.copy --list-topics
.venv/Scripts/python.exe -m insight.copy --list-styles

# 小红书笔记（标题≤19字 / 正文300-500字 / 正好5个话题标签）
.venv/Scripts/python.exe -m insight.copy --mode xhs --topic-id 3 --account-id sxy_brand_xhs
.venv/Scripts/python.exe -m insight.copy --mode xhs --title "骨折车支持租赁啦" --platform xiaohongshu

# 抖音口播稿（3 秒钩子 + 正文 + 拍摄提示）
.venv/Scripts/python.exe -m insight.copy --mode douyin --topic-id 3 --out out/douyin_3.md

# 下一步拍摄方向（落 insights 表 + 写 out/next_direction.md）
.venv/Scripts/python.exe -m insight.direction --days 7
.venv/Scripts/python.exe -m insight.direction --days 14 --json    # 只看指标，不生成方向

# LLM 连通性自检 / 单轮问答
.venv/Scripts/python.exe -m insight.llm --check
.venv/Scripts/python.exe -m insight.llm --ask "一句话说清电动轮椅选购先看什么"
```

## LLM key 解析优先级（llm.py）

按顺序找，找到第一个可用就停；**全都找不到时 `available()` 返回 False，生成函数自动走规则模板版**：

1. 环境变量 `XMT_LLM_API_KEY` 或 `DEEPSEEK_API_KEY`（走 DeepSeek `https://api.deepseek.com/v1`）
2. 文件 `config/llm.local.json`：
   `{"provider":"deepseek","base_url":"https://api.deepseek.com/v1","model":"deepseek-chat","api_key":"..."}`
3. Hermes 配置 `~/AppData/Local/hermes/config.yaml` 的 `api_keys:` 段（按 provider 名匹配 `deepseek` 优先；
   路径可用环境变量 `XMT_HERMES_CONFIG` 覆盖）
4. 环境变量 `SILICONFLOW_API_KEY` / `ZHIPU_API_KEY` / `SUBLYX_API_KEY`（各自配 base_url）

其它可调环境变量：

| 变量 | 作用 |
|---|---|
| `XMT_LLM_MODEL` | 全局覆盖模型名（如换更便宜的模型） |
| `XMT_LLM_BASE_URL` | 全局覆盖 base_url |
| `XMT_LLM_DISABLED=1` | **强制降级**，用于验证无 key 时的产出 |
| `XMT_STYLE_GUIDE` | 覆盖小红书风格指南路径（默认 `D:\@kaifa\xhs\小红书爆款风格指南.md`，**只读**） |

调用细节：OpenAI 兼容 `/chat/completions`，`requests`，超时 120s，失败重试 2 次后返回 `None`；
`chat()` 吞掉所有异常并返回 `None`，绝不向上抛。**key 不进日志、不进文件、不进标准输出**——
错误信息里只出现 provider / base_url / model。

## 降级（无 key）行为

| 模块 | 降级版做法 | 仍然保证 |
|---|---|---|
| topics | 品类痛点库（16 个场景）× 账号 role 匹配 + 用量均衡 + 素材证据打分 | 10 条完整中文选题，含钩子/结构/证据/推荐度 |
| copy（小红书） | 3 种正文结构轮换 + 12 条细节句库 + 8 种标题钩子公式 | 标题≤19字、正文300-500字、正好5个标签、5-10 个 emoji |
| copy（抖音） | 口播三段式骨架 + 6 条拍摄提示 | 3 秒钩子 + 口语正文 200-400 字 + 拍摄提示 |
| direction | 题材效果排序（近 N 天作品）+ 账号涨粉 + 题材效果反推方向 + 排期表 | 六节完整 markdown（现状/规律/方向/排期/合规/数据缺口） |

窗口内没有新作品时，direction 会自动回退到更大的素材窗口（`days*4`，30–90 天）并在文件里写明口径。

## 合规与质量闸门

- **医疗器械红线**：不承诺疗效、不做诊断表述；文案层自动替换 `治疗/治愈/疗效/最/第一/绝对/神器/一秒` 等词
- **极限词/夸张词**：`COMPLIANCE_MAP` 统一替换；LLM 输出与模板补齐段落都会过一遍
- **去 AI 味**：`soften()` 清掉「首先/其次/综上/大家好」等套话；`_self_check` 逐条自检并在产物里打印
- **不可编造数据**：命中 `xx%`「据统计」「调研显示」等无法核实表述时，自检会给出 ⚠ 提示
- **价格/引流**：命中「价格/元/微信/电话/二维码」等字样时自检告警
- 小红书硬指标（≤19字标题 / 300-500字正文 / 正好5标签）**程序化强制**，LLM 超长会被截断、不足会补细节块

## 产物与运行时文件

| 路径 | 说明 |
|---|---|
| `out/next_direction.md` | 下一步拍摄方向（每次运行覆盖） |
| `out/*.md` | `--out` 指定的文案产物（示例：`out/xhs_note_demo.md`） |
| `data/xhs_style_history.json` | 视觉风格使用历史，用于「禁止连续两篇同风格」（`data/` 已在 .gitignore） |
| `topics` / `insights` 表 | 选题池与结论（`data/xmt.db`，本地生成） |

## `.gitignore` 需要新增的条目（父代理处理，本目录不修改 .gitignore）

```gitignore
# LLM 密钥（本地私密，永不入库）
config/llm.local.json
config/*.local.json
```

说明：
- `config/llm.local.json` 存 API key，**必须**排除。
- `config/*.local.json` 兜底覆盖同类本地私密配置。
- `data/`（含 `data/xhs_style_history.json`）与 `out/` 已有规则覆盖，无需新增。
- `insight/__pycache__/` 已由 `__pycache__/` 规则覆盖。
