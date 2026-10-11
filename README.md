# xmt · 新媒体账号矩阵数据看板

佳康顺新媒体账号矩阵（抖音 / 小红书 / 视频号）的**免后台登录**数据采集与看板生成工具：每日定时抓取各账号粉丝数、总获赞、作品数，以及作品级明细（点赞 / 评论 / 分享），落 SQLite 并生成单文件 HTML 看板。

## 特性

- **抖音前端免登录采集**：Playwright 驱动本机 Chrome 读取主页分享链接，无需账号密码、无需开放平台 API。
- **小红书前台采集**：复用本机登录态 cookie（文件形式，不上传、不入库）。
- **账号矩阵配置化**：`config/accounts.json` 一处维护全部账号，`url` 为空即视为停用。
- **作品级明细**：记录每个作品的发布时间、点赞 / 评论 / 分享，按账号形成作品库。
- **单文件看板**：`out/dashboard.html` 输出，双击即看，无需服务端。
- **一把梭 cron 入口**：`snapshot.py` 一键编排「采集 → 写快照 → 出看板」。

## 目录结构

```
xmt/
├─ config/
│   └─ accounts.json      # 账号矩阵配置（id/owner/name/platform/url/...）
├─ data/
│   └─ xmt.db             # SQLite：account_snapshots + works（本地生成，不入库）
├─ logs/                  # 运行日志（不入库）
├─ out/
│   └─ dashboard.html     # 看板产物（不入库）
├─ collect_douyin.py      # 抖音采集
├─ collect_xhs.py         # 小红书采集
├─ dashboard.py           # 看板生成
├─ db.py                  # SQLite 存储层（建表 / upsert）
├─ snapshot.py            # 每日编排入口（cron 调这个）
├─ run.cmd                # Windows 双击运行包装
├─ install_cron.cmd       # 注册 Windows 计划任务
└─ requirements.txt
```

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\playwright install chromium

# 全量快照（采集 + 写库 + 出看板）
.venv\Scripts\python snapshot.py

# 或双击
run.cmd
```

环境变量：

| 变量 | 默认 | 说明 |
|------|------|------|
| `XMT_TARGET` | `30` | 每账号抓取的作品条数上限 |

## 数据表

| 表 | 主键 | 内容 |
|----|------|------|
| `account_snapshots` | `(account_id, snap_date)` | 每日账号快照：粉丝数、总获赞、作品数 |
| `works` | `(account_id, work_id)` | 作品明细：标题、类型、发布时间、点赞/评论/分享、`first_seen`/`last_seen` |

两次采集之间用 upsert 更新，`first_seen` 保留首次发现时间，便于做「新增作品」与增长分析。

## 定时任务

```cmd
install_cron.cmd
```

注册 Windows 计划任务，每天调用 `run.cmd`（内部执行 `snapshot.py`，日志追加到 `logs/run.log`）。

## 安全约定

- `小红书cookie.txt` / `config/xhs_cookie.txt` 为**登录凭证，已在 `.gitignore` 中排除，永不入库**。
- `data/`、`logs/`、`out/` 为本地运行产物，不入库。
- 采集仅使用前端公开页面，不涉及开放平台密钥。
