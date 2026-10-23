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
| `collect_douyin.py` | 自有抖音号粉丝/作品采集（免登录） | `python -m collect_douyin` |
| `collect_redfox.py` | **小红书 / 视频号采集（RedFox API）**：账号级指标，替代已停用的 cookie 方案 | `python collect_redfox.py [--platform xiaohongshu]` |
| `collect_xhs.py` | 旧小红书采集（Playwright + cookie），2026-10-19 起停用，仅作历史保留 | — |
| `collectors/hot.py` | 平台热搜：抖音热榜、微博热搜、百度热搜 | `python -m collectors.hot` |
| `collectors/rival.py` | **找对标**：监控关键词搜索（抖音/小红书）+ 对标账号主页采集 | `python -m collectors.rival --search` |
| `import_rivals.py` | **导入对标**：把 `对标账号.txt` 里的手写清单解析进 `config/rivals.json` | `python import_rivals.py [--dry-run]` |
| `analytics/` | **分析**：增长归因、爆款结构与时段、自有 vs 对标差距 | `python -m analytics.growth` |
| `analytics/discover.py` | **找对标**：从关键词搜索命中反推值得盯的对标号，可写入 `config/rivals.json` | `python -m analytics.discover --top 10 [--write]` |
| `insight/` | **出活**：选题池、小红书笔记/抖音口播文案、下一步拍摄方向 | `python -m insight.topics` |
| `sales/` | **销售与租赁报表**：解析 xlsx、月度指标、董事长汇报材料（md + Word） | `python -m sales.speech --month 9 --docx` |
| `dashboard.py` | 矩阵看板（自有 + 对标 + 爆款榜 + 热搜 + 结论） | `python dashboard.py` |
| `report.py` | 中文 markdown 周报 | `python report.py` |
| `snapshot.py` | 每日总编排（采集→分析→洞察→销售→看板） | `python snapshot.py` |
| `scriptgen/` | **拍摄脚本**：对标视频提取→本地知识库→三号逐字稿→审核/同步（不含三平台发布包） | `python -m scriptgen add "<链接>"` |
| `jiaoben/` | **口播脚本资产库**：24 套 + 4 套 + 36 套分镜脚本、17 个生成器、各产品实拍图与产品资料 | 见 `jiaoben/README.md` |
| `tools/make_showroom_scripts.py` | **展厅分镜出稿**（无对标模式）：4 分镜×7 秒、一产品 4 套，数据驱动生成 txt/docx | `python tools/make_showroom_scripts.py` |
| `docs/运营流程.md` | **运营流程（高客单辅具版）**：内容双线、平台分工、转化链路、KPI、合规红线、发布自检 | 文档 |
| `docs/拍摄脚本模块.md` | 拍摄脚本模块的使用、配置、合规与实测记录 | 文档 |

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
uv pip install --python .venv/Scripts/python.exe -r requirements.txt

# 拍摄脚本模块（首次初始化；之后在对话里发链接给 Claude 即可）
.venv/Scripts/python.exe -m scriptgen init
.venv/Scripts/python.exe -m scriptgen add "https://v.douyin.com/xxxx/"
.venv/Scripts/python.exe -m scriptgen estimate "<链接...>"

# 全流程
.venv/Scripts/python.exe snapshot.py

# 只更新自有账号数据与看板（快）
.venv/Scripts/python.exe snapshot.py --quick

# 单独出某个模块
.venv/Scripts/python.exe -m collectors.rival --search --platform xiaohongshu
.venv/Scripts/python.exe -m analytics.bench
.venv/Scripts/python.exe -m sales.speech --month 9 --docx
```

环境变量：`XMT_TARGET`（每账号抓取作品条数，默认 30）、`XMT_TOPICS`（每次生成选题数，默认 10）、`REDFOX_API_KEY`（小红书/视频号采集密钥，已持久化为用户级环境变量）。

## 小红书 / 视频号采集通道（RedFox API）

2026-10-19 平台就 cookie + 浏览器自动化采集发出风险提示后，小红书改走 RedFox API，视频号亦接入同一通道：

| 平台 | 接口 | 现状（2026-10-20 实测） |
|---|---|---|
| 小红书 | `xiaohongshu.get_account(account_id=小红书号)` | **2/3 可采**（账号级：粉丝/获赞与收藏/作品数）；`49313135003` 返回 `3203` 优质库未收录 |
| 小红书 | `xiaohongshu.get_user_works` | **0/3**（全部 3203），作品明细暂缺，`works` 表沿用历史数据 |
| 视频号 | `wechat_channels.search_users` / `get_user_works` | **0/3**（精确昵称搜索 total=0，作品 total=0），库未收录矩阵账号 |

注意两点口径问题：
1. RedFox 的小红书数据为第三方缓存口径，`accountUpdateTime` 通常滞后平台实时数日（本次为 10-14），不宜当作当日实时值。
2. 看板账号卡片标注了「数据 YYYY-MM-DD」，非当日数据会以橙色提示，避免旧值被误读为当天数据。

## 拍摄脚本模块（scriptgen）

2026-10-20 上线。你发抖音/视频号链接，模块自动：

1. 提取口播文案 + 作品元数据（RedFox 为主；失败自动 RedFox 下载 + 本地 faster-whisper `medium` 兜底）
2. 存入本地知识库（`knowledge/reference/` + `data/xmt.db` 的 `sg_*` 表）
3. 文本级拆解钩子/节奏/卖点/CTA
4. 自动判断给口播号/品牌号/个人号里的哪个号；低置信度不硬猜，批次末尾列待确认
5. 从**阳光展厅可拍清单**里选品（F2Q、HS180P、小福车等；P21/希维尔待确认）
6. **贴对标原句改写**出逐字稿（骨架照搬、词换近义）+ 3-5 条拍摄提示，严格合规扫描
7. 人工审核后可同步公司知识库 `marketing`（只同步脚本 + 拆解摘要 + 方法论）

```bash
python -m scriptgen add "<链接1>" "<链接2>"     # 批量提取/出稿
python -m scriptgen resolve <批次号> --choice "1:personal:F2Q"
python -m scriptgen approve <编号...>
python -m scriptgen revise <编号> --instruction "压到 50 秒，开头更直"
python -m scriptgen sync <编号...> --dry-run
python -m scriptgen search 折叠
python -m scriptgen personas
```

- 三号人设、拍摄地（苏州阳光大厦展厅 911 室）、出镜人（翔哥 / 心悦+小冯 / 小冯）见 [docs/拍摄脚本模块.md](docs/拍摄脚本模块.md)。
- **打印版 Word 在 `out/001_...docx`、`002_...docx`（按序号排序）**，只含标题、账号/出镜人和逐字稿/对白稿；对标拆解、拍摄提示、合规自检、批次报告都在 `data/scriptgen/`，不打印。
- Word 版式按 001 定稿：微软雅黑 10.5pt、单倍行距、正文首行缩进 32pt、段后 8pt，A4 页边距上下 2.2cm/左右 2.4cm。
- **不生成三平台标题/标签/封面发布包**。
- 同一链接成功转写后走缓存；批次预计超过 50 次计费调用时需 `--yes`；兜底下载视频默认用完即删。
- 合规依据《广告法》第十六条与《医疗器械广告审查办法》的保守口径，只做草稿扫描，不替代法务/广告审查。

## 展厅分镜出稿（无对标模式，2026-10-23 固化）

没有对标视频时的第二条出稿路线，技能沉淀在 `jiaoben/`（2026-10-23 从
`D:\kaifa\jiaoben` 并入），方法论见 `.workbuddy/skills/scriptgen-writing/展厅分镜脚本技能.md`：

- **结构**：每条 4 分镜 × 7 秒（0-7s 钩子 / 7-14s 卖点一 / 14-21s 卖点二 / 21-28s 情绪收尾），
  镜1 必须「人 + 动作」入画
- **配比**：一个产品 4 套，角度不重样（痛点 ×1 + 口碑场景 ×1 + 功能参数 ×1 + 反差/黑科技 ×1），
  同批 4 套卖点不重复
- **风格库** 24 种（避坑指南/亲戚口碑/反常识/老板吐槽/场景故事/对比反差/颜值切入/功能拆解/
  踩坑吐槽/用户视角/对比科普/黑科技/家庭场景/参数拆解/中老年痛点/女生视角/极简/细节控/
  夏天痛点/安全/王师傅偶遇/方庄店介绍/旅游痛点）
- **生成器**：`python tools/make_showroom_scripts.py [--spec spec.json] [--name batch01]`，
  内置风格库校验 + 手动款电动词扫描 + 价格词扫描，不合规不产出
- **存量资产**：`jiaoben/6款产品_单人口播脚本24套_全新版`（NIP/朋友2/小福车/P10/F2Q/A3）、
  `jiaoben/小飞燕_单人口播脚本4套`、`jiaoben/博爱方特+新芝车头_单人口播脚本36套`
- ⚠️ 复用旧合集前先核对 `docs/产品参数档案.md`：P10「10 公斤」是车架重量（整车 15.8KG），
  A3「10.4 公斤」待核实；博爱方特/新芝是经销品牌，不写佳康顺背书

```bash
.venv/Scripts/python.exe tools/make_showroom_scripts.py                    # 内置小福车4套示例
.venv/Scripts/python.exe tools/make_showroom_scripts.py --spec my.json     # 自定义产品+角度
```

## 对标抓取与写稿（固定 SOP，2026-10-23 固化）

从「用户发一个对标链接」到「产出四件套」的流程已全部固化，**不再临场发挥**。
完整版见 **[docs/对标抓取与脚本生成流程.md](docs/对标抓取与脚本生成流程.md)**，写稿前同时必读
**[docs/产品参数档案.md](docs/产品参数档案.md)**；技能侧对应 `.workbuddy/skills/scriptgen-writing/`
（`SKILL.md` 铁律一到八 + `速查卡.md`）。

| 步 | 动作 | 关键口径 / 坑 |
|---|---|---|
| 0 | 明确四输入：对标链接、账号、产品、数量风格 | 抖音必须要**主页分享短链**，只有抖音号拿不到数据 |
| 1 | 抓账号：短链 → sec_uid → profile → items | **作品列表只能用 items**，profile 抓不到 |
| 2 | 抓视频 → ffmpeg 转 wav → 本地 Whisper 转写 | URL 要完整（裸 id 报 MissingSchema）；ASR 用 `medium`，`tiny` 会 502 |
| 3 | 写账号分析（五节：基本面/逐句转写/风格拆解/合规雷区/套用建议） | 转写要**逐句带时间戳**，只给全文没法建骨架 |
| 4 | 查产品参数（先档案，后知识库） | 检索 2-3 个正式词最稳（全词 AND）；**竞品参数绝不抄** |
| 5 | 查人设卡 `config/personas.json` | 人设是硬约束，对标角色设定不能照搬 |
| 6 | 写稿：贴对标原句改写 + 合规扫描 | 骨架照搬、词换近义；高危中危必须为 0 |
| 7 | 落库 + 渲染 md/Word | **Word 序号手动接在 `out/` 最大号后面**，再回写数据库 |
| 8 | 刷 TXT + HTML | 新 code 必须进 `tools/export_standalone.py` 的 ORDER 列表 |
| 9 | 质量自查 | 见流程文档第 9 步清单 |
| 10 | 归档 | 只 `git add` 本次相关文件（根目录中文大 txt 会被安全钩子拦） |

**写稿硬参数**

| 项 | 口径 |
|---|---|
| 长度 | 我方时长 / 对标时长 **0.8-1.3 倍**，一句对一句、不加不减；`target_seconds` 必须落在人设区间 |
| 人设 | `oral` 60-90s/260-400 字；`brand` 30-45s/150-240 字（**可单人出镜**）；`personal` 45-60s/200-280 字 |
| 文案 | 骨架照搬、每个词换近义，只做「换词 / 调位 / 替内容」三类改动；禁止照抄原句，也禁止另起炉灶 |
| 合规 | 不写价格、绝对化、疗效承诺、加微信；手动款禁写电机/电池/摇杆/电磁刹车/续航 |
| 收尾 | CTA 跟对标走；**批量稿最后一句必须全库不重复** |

**对标账号登记**（`config/rivals.json`，`role` 分两类）

| 类型 | 账号 | 用途 |
|---|---|---|
| 同类目对标 | 护卫神官方旗舰店、皮皮熊电动车旗舰店 | 看卖什么、怎么运营 |
| 风格对标 | **助行辅具王师傅**（priority 1，个人号首选）、陈大脸甄选（priority 2） | 学表达、学骨架，`style_account` 段带 sec_uid / 骨架 / 语音特征 |

**产出四件套**

| 产物 | 位置 |
|---|---|
| 单独 TXT | `稿子/{口播号\|品牌号\|个人号}/<账号内序号>_<标题>.txt` |
| Word | `out/<全局序号>_<账号>_<标题>.docx` |
| 源 md | `out/scripts/<日期>/<账号id>/<CODE>_<标题>.md` |
| HTML 对照表 | `对照表/index.html` + `对照表/对标对照表-<账号>.html` |

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
| `sg_*` | 拍摄脚本模块：对标元数据、转写、拆解、脚本、版本、批次、调用记录（见 [docs/拍摄脚本模块.md](docs/拍摄脚本模块.md)） |

## 配置

- `config/accounts.json` —— 自有账号矩阵；抖音填主页分享链接 `url`，小红书填 `xhs_id`。
- `config/rivals.json` —— 对标账号 + 监控关键词。**日常维护只需编辑根目录 `对标账号.txt`**（一行一个号，写名字 + 主页链接 / 小红书号即可），然后 `python import_rivals.py` 导入；也可用 `python -m analytics.discover --write` 从搜索命中的高表现号里自动补充。
  - `role` 分两类：`同类目对标`（看卖什么、怎么运营）/ `风格对标`（学表达和骨架，写稿用）。
  - 风格对标必须补 `style_account` 段：`fit_persona` / `duration` / `skeletons` / `voice` / `signature` / `title_formula` / `priority`，并附 `sec_uid` 与分析文档路径 `analysis_doc`。
- `config/douyin_cookie.txt`（不入库）—— 抖音**搜索页**需登录态，否则跳验证码中间页。
- `小红书cookie.txt` / `config/xhs_cookie.txt` —— **已停用**（2026-10-19 平台风控提示），小红书改走 `REDFOX_API_KEY`。
- `config/llm.local.json`（不入库）—— insight 层 LLM 配置。**零密钥模式（当前默认）**：写 `cloud` 段走 WorkBuddy 云服务 LLM，用户不需要自己的 API key：
  ```json
  {"cloud": {"endpoint": "https://xmt-script-assistant.app.workbuddy.host",
             "publishable_key": "wbpk_xxx", "model": "hunyuan-chat"}}
  ```
  **自有 key 模式**：填 `api_key` 段走 OpenAI 兼容接口（优先级高于 cloud 段）：
  ```json
  {"provider": "deepseek", "base_url": "https://api.deepseek.com/v1",
   "model": "deepseek-chat", "api_key": "..."}
  ```
  > 云服务 LLM 只支持 SSE 流式（`stream: true`）；`auto` 等纯推理模型（`onlyReasoning: true`）会只吐 `reasoning_content` 而无正文，出稿请用 `hunyuan-chat` 这类非推理模型。
- `config/redfox.local.json`（不入库）—— RedFox API Key 本地兜底（环境变量 `REDFOX_API_KEY` 优先）。SDK 装法：`pip install git+https://github.com/redfox-data/redfox-python-sdk.git`（PyPI 上的 `redfox` 是同名无关包，**不要装**）。
- `config/scriptgen.json` —— 拍摄脚本模块：路径、RedFox 轮询/阈值、ASR 模型、公司 KB、质量检查。
- `config/personas.json` —— 三号人设卡（draft，可人工校准）。
- `config/showroom_inventory.json` —— 阳光展厅可拍产品（confirmed / candidate / pending）与证据。**2026-10-20 用户确认：阳光确定款为 P11 与希维尔（XFY）800 元款**，两者均已入 confirmed，P21 口径作废。
- `config/compliance.json` —— 医疗广告合规规则、免责声明、发布检查清单。

## 定时任务

```cmd
install_cron.cmd
```

注册 Windows 计划任务，每天 05:00 调用 `run.cmd`（内部执行 `snapshot.py`，日志追加到 `logs/run.log`）。全流程约 10–25 分钟。

> **董事长汇报材料不参与每日流程** —— 一个月一次、按需手动触发：
> ```bash
> .venv/Scripts/python.exe -m sales.speech --month 9 --docx
> ```
> `--month` 省略时自动取「最近一个完整月」。看板上的销售区是直接读 `销售报表/*.xlsx` 的只读展示，不受影响。

## 安全与合规

- 登录 cookie、`config/llm.local.json`、`data/`、`logs/`、`out/`、`销售报表/`、`knowledge/` 全部在 `.gitignore` 中，**不入公开仓库**（销售明细含客户姓名；`knowledge/` 含第三方对标口播原文）。
- 采集只用前端公开页面，账号间有随机间隔；请勿高频批量抓取。
- 对标数据仅用于自身内容决策；第三方开源工具（如 MediaCrawler，非商用学习许可）只在本机研究使用，代码不进入本仓库。
