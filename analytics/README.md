# analytics · 分析层

佳康顺新媒体矩阵的**只读**分析层。所有模块通过 `db.connect()` 读取 `data/xmt.db`，
**不写任何业务数据**；唯一的写入是 `report.py` 落一条洞察到 `insights` 表（`kind='growth_report'`）。

- 只用 Python 3.12 标准库 + `sqlite3`，无第三方依赖。
- 数据库为空 / 表为空（首次运行）时，所有函数返回空结构而不抛异常。
- 输出全中文，表格按东亚字符显示宽度对齐。
- 每个模块可独立运行：`python -m analytics.growth`（在 `D:\@kaifa\xmt` 下用 `.venv/Scripts/python.exe`）。

## 目录

```
analytics/
├─ __init__.py    # 共享工具：数字/百分比格式化、中文对齐表格、时间解析
├─ growth.py      # 增长分析
├─ hits.py        # 爆款作品分析
├─ bench.py       # 对标分析
└─ README.md      # 本文件
report.py         # 周报生成器（位于项目根，依赖 analytics 三件套）
```

## 通用约定

- 平台：`douyin`=抖音 / `xiaohongshu`=小红书 / `channels`=视频号（`PLATFORM_LABEL` 映射为中文）。
- 账号类型：`kind='own'` 自有 / `kind='rival'` 对标（中文为「自有 / 对标」）。
- 数值可能为 `None`（前台采集常缺），格式化时统一显示为 `—`。
- 窗口口径：多数函数以「库内最新快照日」为期末，往前 `days` 天为窗口；
  `hit_works` 例外，以**今天**为基准。

## `__init__.py` 共享工具

| 函数 | 签名 | 用途 |
|---|---|---|
| `disp_width` | `disp_width(s) -> int` | 文本显示宽度（东亚宽/全角字符按 2 列计） |
| `pad` | `pad(s, width, align="left") -> str` | 按显示宽度补齐；`align ∈ {left,right,center}` |
| `fmt_num` | `fmt_num(n) -> str` | 中文数字：≥1亿→`x.xx亿`，≥1万→`x.x万`，否则千分位；`None→—` |
| `fmt_delta` | `fmt_delta(n) -> str` | 带符号增量，正数补 `+` |
| `fmt_pct` | `fmt_pct(x, signed=True) -> str` | 百分比，`None→—` |
| `fmt_ratio` | `fmt_ratio(x, nd=3) -> str` | 小数比率（互动效率等），`None→—` |
| `render_table` | `render_table(headers, rows, aligns=None) -> str` | 生成对齐的纯文本表格 |
| `parse_date` | `parse_date(s) -> date\|None` | 解析 `YYYY-MM-DD` |
| `date_str` | `date_str(d) -> str\|None` | `date → "YYYY-MM-DD"` |
| `today_str` | `today_str() -> str` | 今天 `YYYY-MM-DD` |
| `parse_time` | `parse_time(s) -> datetime\|None` | 兼容 `Y-m-d H:M:S` / `Y-m-d H:M` / `Y-m-d` / `/` 与 `.` 分隔、ISO |
| `work_dt` | `work_dt(row) -> datetime\|None` | 从作品行取发布时间：优先 `publish_ts`，回退 `publish_time` |

---

## `growth.py` · 增长分析

### `account_growth(account_id=None, days=30) -> dict`

单账号（传 `account_id`）或全部自有账号（不传）的粉丝 / 获赞 / 作品数变化、日增、环比。

- 期初值 = 窗口开始日**之前**最近的一条快照（无则退化为窗口内最早一条）
- 期末值 = 期末日**及之前**最近的一条快照
- 日增 = 变化 / 实际跨度天数；环比 = (本期变化 − 上期变化) / |上期变化| × 100%

返回结构：

```python
{
  "scope": "all" | "<account_id>",
  "days": 30,
  "start_date": "YYYY-MM-DD" | None,
  "end_date":   "YYYY-MM-DD" | None,
  "accounts": [
    {
      "account_id": str, "name": str, "platform": str, "kind": str,
      "period": {"start": str, "end": str, "days": int},
      "metrics": {
        "followers":    {"start": int|None, "end": int|None, "delta": int|None,
                         "daily_avg": float|None, "prev_delta": int|None, "mom_pct": float|None},
        "total_likes":  {...同构...},
        "works_count":  {...同构...},
      }
    }
  ],
  "total": {  # 各指标跨账号合计，结构同 metrics 的单个指标
    "followers": {...}, "total_likes": {...}, "works_count": {...}
  }
}
```

空数据：`accounts=[]`，`total` 各字段为 `None`。

### `growth_ranking(days=7) -> list[dict]`

自有账号按窗口内涨粉降序排名（无快照的账号不入选）。

```python
[ {"rank": 1, "account_id": str, "name": str, "platform": str,
   "followers_start": int|None, "followers_end": int|None, "followers_delta": int|None,
   "daily_avg": float|None, "likes_delta": int|None, "works_delta": int|None,
   "mom_pct": float|None, "period": {"start","end","days"}} ]
```

空数据：`[]`。

命令行：`python -m analytics.growth [days]` —— 打印增长明细表 + 涨粉榜。

---

## `hits.py` · 爆款作品分析

### `hit_works(platform=None, account_id=None, min_digg=None, days=30, limit=20) -> list[dict]`

最近 `days` 天发布的作品，按点赞降序取前 `limit` 条（`min_digg` 为点赞下限，`None` 表示不限）。

```python
[ {"rank": int, "account_id": str, "account_name": str,
   "platform": str, "platform_label": str,
   "work_id": str, "title": str,
   "work_type": int|None, "work_type_label": "视频"|"图文"|"—",
   "digg": int, "comment": int, "share": int, "play": int|None,
   "interact": int,                      # = digg+comment+share
   "publish_time": str|None, "publish_dt": "YYYY-MM-DD HH:MM", "days_ago": int,
   "url": str|None} ]
```

空数据或无符合条件作品：`[]`。

### `title_patterns(works) -> dict`

对一批作品（`hit_works` 的返回值即可）做标题特征统计。

```python
{
  "count": int,
  "length": {"avg": float, "min": int, "max": int,
             "buckets": {"≤10": int, "11-20": int, "21-30": int, "31-50": int, ">50": int}},
  "top_words": [{"word": str, "count": int}],   # 话题标签 + 高频中文双字词（count≥2），最多 15
  "question_ratio": float,       # 疑问句占比 %
  "number_ratio": float,         # 含阿拉伯数字 %
  "exclamation_ratio": float,    # 含感叹号 %
  "emoji_ratio": float,          # 含表情 %
  "hashtag_avg": float,          # 平均话题标签数
}
```

空输入：`count=0`，其余为零值/空列表。

### `hit_timing(works) -> dict`

发布时段 / 星期分布 vs 点赞表现（哪个时间发最容易爆）。

```python
{
  "count": int,                       # 可解析发布时间的作品数
  "by_hour":    {"21时": {"count","total_digg","avg_digg"}, ...},
  "by_weekday": {"周一": {...}, ...},
  "slots":      {"晚间 18-24": {...}, "早间 6-9": {...}, ...},  # 0-6/6-9/9-12/12-14/14-18/18-24
  "best_hour":    {"key","avg_digg","count"} | None,
  "best_weekday": {"key","avg_digg","count"} | None,
  "best_slot":    {"key","avg_digg","count"} | None,
}
```

`best_*` 按 `avg_digg` 取最高（同分取条数多者）。空输入：`count=0`，`best_*` 为 `None`。

### `rising_works(days=7, min_delta=100) -> list[dict]`

基于 `work_snapshots` 计算「仍在涨」的作品：窗口内点赞增量 ≥ `min_delta`，按增量降序。

```python
[ {"rank": int, "account_id": str, "account_name": str, "platform": str|None,
   "work_id": str, "title": str,
   "digg_start": int, "digg_end": int, "delta_digg": int,
   "delta_comment": int, "delta_share": int,
   "growth_rate_pct": float|None,     # delta/digg_start×100，start=0 时为 None
   "snap_from": "YYYY-MM-DD", "snap_to": "YYYY-MM-DD", "days": int,
   "url": str|None} ]
```

`work_snapshots` 为空（首次采集后不足两次快照）返回 `[]`。

命令行：`python -m analytics.hits [days]` —— 打印爆款榜、标题特征、发布时机、上升作品。

---

## `bench.py` · 对标分析

### `bench_table(platform=None) -> list[dict]`

逐账号对标表。粉丝 / 作品数取最新快照，无快照则粉丝回退 `accounts.followers`、作品数回退 `works` 计数；
平均点赞等取 `works` 表全量均值；更新频率 = 近 30 天发布数 ÷(30/7) → 周均条数；
互动效率 = 平均(点赞+评论+分享) / 粉丝数 × 100。

```python
[ {"account_id": str, "name": str, "platform": str, "platform_label": str,
   "kind": "own"|"rival", "kind_label": "自有"|"对标",
   "followers": int|None, "works_count": int,
   "avg_digg": float|None, "avg_comment": float|None, "avg_share": float|None,
   "avg_interact": float|None,        # 平均互动（赞+评+享）
   "freq_weekly": float,              # 周均更新条数
   "engagement_rate": float|None,     # 每百粉互动量（%）
   "data_days": int} ]                # 快照天数
```

空数据：`[]`。

### `gap_summary() -> dict`

自有 / 对标两组汇总 + 差距比例 + 可执行结论。

```python
{
  "own":   {"accounts","followers","works","avg_works","avg_digg",
            "avg_freq","avg_engagement","avg_followers"},
  "rival": {...同构...},
  "gaps": [ {"metric": "粉丝总量", "own": 51000, "rival": 0,
             "ratio": float|None,      # own/rival，rival 为 0/None 时为 None
             "verdict": "自有领先"|"自有落后"|"基本持平"|"对标样本不足"} ],
  "conclusions": [ "中文结论", ... ],
}
```

结论覆盖：账号规模、更新频率对比、互动效率对比、平均点赞对比；对标无有效数据时给出补齐提示。

命令行：`python -m analytics.bench [douyin|xiaohongshu|channels]` —— 打印对标表 + 差距摘要 + 结论。

---

## `report.py` · 周报生成器

### `build_weekly_report(days=7) -> str`

汇总 `growth` / `hits` / `bench` 三类分析，产出中文 markdown 周报。副作用：

1. 写文件 `out/weekly_report.md`
2. 落库 `insights(kind='growth_report', scope='all')`（`db.save_insight`）

周报包含九节：总览 / 账号涨粉榜 / 增长明细 / 爆款作品 TOP / 标题特征 / 发布时机 /
仍在涨的作品 / 对标差距 / 行动建议。空数据时各节以提示语占位，不抛异常。

命令行：`python report.py [days]` —— 打印 markdown、写文件并入库。

---

## 自测

```bash
cd D:\@kaifa\xmt
.venv\Scripts\python.exe -m analytics.growth
.venv\Scripts\python.exe -m analytics.hits
.venv\Scripts\python.exe -m analytics.bench
.venv\Scripts\python.exe report.py 7
```

空库 / 造数两阶段自验：临时 sqlite 中建表 → 断言空结构 → 插入样例 → 断言计算结果。
