# xmt · 新媒体账号矩阵数据与销售平台

佳康顺新媒体业务的一体化数据工具：**账号矩阵数据采集 + 对标/选题分析 + 销售租赁报表 + 汇报材料生成**，全部本地运行、SQLite 存储、单文件 HTML 看板。

> 数据口径：**有押金 = 租赁订单，无押金 = 销售订单**（业务口径，全项目统一）。
>
> 运营主线（2026-10 起）：面向**高客单价医疗器械辅具**（1,000–5,500 元），内容改为
> **A 线全实拍（真人真机真场景）+ B 线 AI 漫剧系列软植入**，KPI 从「点赞」换成「留资 / 到店试车 / 成交」。
> 完整流程见 **[docs/运营流程.md](docs/运营流程.md)**。

## 模块地图

| 模块 | 作用 | 入口 |
|---|---|---|
| `collect_douyin.py` / `collect_xhs.py` | 自有 12 个账号的粉丝/作品采集（抖音免登录、小红书带 cookie） | `python -m collect_douyin` |
| `collectors/hot.py` | 平台热搜：抖音热榜、微博热搜、百度热搜 | `python -m collectors.hot` |
| `collectors/rival.py` | **找对标**：监控关键词搜索（抖音/小红书）+ 对标账号主页采集 | `python -m collectors.rival --search` |
| `analytics/` | **分析**：增长归因、爆款结构与时段、自有 vs 对标差距 | `python -m analytics.growth` |
| `analytics/discover.py` | **找对标**：从关键词搜索命中反推值得盯的对标号，可写入 `config/rivals.json` | `python -m analytics.discover --top 10 [--write]` |
| `insight/` | **出活**：选题池、小红书笔记/抖音口播文案、下一步拍摄方向 | `python -m insight.topics` |
| `sales/` | **销售与租赁报表**：解析 xlsx、月度指标、董事长汇报材料（md + Word） | `python -m sales.speech --month 9 --docx` |
| `dashboard.py` | 矩阵看板（自有 + 对标 + 爆款榜 + 热搜 + 结论） | `python dashboard.py` |
| `report.py` | 中文 markdown 周报 | `python report.py` |
| `snapshot.py` | 每日总编排（采集→分析→洞察→销售→看板） | `python snapshot.py` |
| `docs/运营流程.md` | **运营流程（高客单辅具版）**：内容双线、平台分工、转化链路、KPI、合规红线、发布自检 | 文档 |

## 运营策略（高客单价医疗器械辅具）

客单价 1,000–5,500 元、决策周期 3–15 天、常需家人共同决策 —— 低价快消那套「冲点赞」打法不适用。
内容目标改为**建立专业信任 + 抓到留资**。

| 维度 | 做法 |
|---|---|
| A 线（主力） | **全实拍**：真人、真机、真场景，一物一故事；开头 3 秒必须出现「人 + 动作」，产品只做配角 |
| B 线（增量） | **AI 漫剧系列软植入**：一季 30 集、固定世界观与 5–6 个角色；产品露脸 ≤15%，每集只植入 1 个卖点，周更 2–3 集 |
| 平台分工 | 小红书=决策参考主战场，抖音=拉新信任，视频号=私域，美团/地图=**到店成交**，闲鱼=合规补位 |
| 转化链路 | 内容 → 留资钩子（上门试车/以旧换新评估/适老化评估）→ 加微 → 到店试车 → 成交 → 回访转介绍 |
| KPI | 留资数、到店试车数、成交单数 —— **点赞与播放量只作参考** |
| 合规红线 | 禁疗效承诺、禁极限词、禁编造数据；漫剧画面常驻「剧情演绎」标注 |

完整流程（拍摄规范、漫剧生产 SOP、产能节奏、发布前 30 秒自检清单）见 **[docs/运营流程.md](docs/运营流程.md)**。
每日方向报告 `out/next_direction.md` 的「〇、当前运营主线」固定输出这条策略，不随数据波动。

## 快速开始

```bash
# 环境（venv 由 uv 创建，无 pip 模块，用 uv 装包）
uv pip install --python .venv/Scripts/python.exe playwright requests python-docx

# 全流程
.venv/Scripts/python.exe snapshot.py

# 只更新自有账号数据与看板（快）
.venv/Scripts/python.exe snapshot.py --quick

# 单独出某个模块
.venv/Scripts/python.exe -m collectors.rival --search --platform xiaohongshu
.venv/Scripts/python.exe -m analytics.bench
.venv/Scripts/python.exe -m sales.speech --month 9 --docx
```

环境变量：`XMT_TARGET`（每账号抓取作品条数，默认 30）、`XMT_TOPICS`（每次生成选题数，默认 10）。

## 销售 / 租赁报表模块

- 输入：`销售报表/` 目录下的 xlsx（WPS 导出，每个 sheet 一个月，如「九月销售」）。
- 解析：`sales/xlsx.py` 零依赖读 OOXML（openpyxl 3.0/3.1 都会因该文件的空 `<fill/>` 样式报错）；`sales/parse.py` 清洗口语化数据。
- 口径与清洗规则：
  - 有押金 → 租赁；无押金 → 销售
  - 日期 `9.8` / `9·8` / `10·8` 混写统一解析
  - 金额 `13·5` 还原为 `13.5`
  - 押金 `600{已归还}` / `2000（已归还）` → 数值 + 归还状态
  - 去重按「月 + 日期 + 客户 + 金额 + 渠道」，**同日同客户同金额才算重复**（避免把同一客户两笔真实业务合并）
- 输出：`out/董事长汇报材料_<年>年<月>月.md` 与 `.docx`，含要点速览、收入结构、渠道战果（含环比）、问题、下一步、**可直接念的口头逐字稿**、明细附表。

## 数据表（SQLite `data/xmt.db`）

| 表 | 内容 |
|---|---|
| `accounts` | 账号主表，`kind=own` 自有 / `kind=rival` 对标 |
| `account_snapshots` | 账号每日快照（粉丝、总获赞、作品数） |
| `works` | 作品明细（标题、类型、发布时间、点赞/评论/分享） |
| `work_snapshots` | 作品每日指标（算「哪条还在涨」） |
| `hot_items` | 热搜榜快照 |
| `search_hits` | 关键词搜索到的对标爆款 |
| `keywords` | 监控关键词（源 `config/rivals.json`） |
| `topics` | 选题池（含证据链） |
| `insights` | 分析结论与拍摄方向 |

## 配置

- `config/accounts.json` —— 自有账号矩阵；抖音填主页分享链接 `url`，小红书填 `xhs_id`。
- `config/rivals.json` —— 对标账号 + 监控关键词。
- `config/douyin_cookie.txt`（不入库）—— 抖音**搜索页**需登录态，否则跳验证码中间页。
- `小红书cookie.txt` / `config/xhs_cookie.txt`（不入库）—— 小红书登录态。
- `config/llm.local.json`（不入库）—— insight 层 LLM 配置，格式：
  ```json
  {"provider": "deepseek", "base_url": "https://api.deepseek.com/v1",
   "model": "deepseek-chat", "api_key": "..."}
  ```

## 定时任务

```cmd
install_cron.cmd
```

注册 Windows 计划任务，每天 05:00 调用 `run.cmd`（内部执行 `snapshot.py`，日志追加到 `logs/run.log`）。全流程约 10–25 分钟。

## 安全与合规

- 登录 cookie、`config/llm.local.json`、`data/`、`logs/`、`out/`、`销售报表/` 全部在 `.gitignore` 中，**不入公开仓库**（销售明细含客户姓名）。
- 采集只用前端公开页面，账号间有随机间隔；请勿高频批量抓取。
- 对标数据仅用于自身内容决策；第三方开源工具（如 MediaCrawler，非商用学习许可）只在本机研究使用，代码不进入本仓库。
