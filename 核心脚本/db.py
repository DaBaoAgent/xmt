"""SQLite 存储层 v2：自有账号 + 对标账号 + 作品明细 + 作品趋势 + 热点 + 选题 + 洞察。

v1 兼容：init/connect/upsert_snapshot/upsert_works 签名与行为不变（upsert_works 多了可选参数）。
v2 新增：
  - accounts         账号主表（自有 kind=own / 对标 kind=rival），从 config/*.json 同步
  - work_snapshots   作品每日指标快照（算「哪条在涨」「爆款何时起量」）
  - hot_items        平台热点/热搜榜快照
  - keywords         监控关键词（源 config/rivals.json，DB 为准）
  - topics           选题池（含证据链）
  - insights         分析结论与拍摄方向（markdown 正文 + 数据 JSON）
"""
import os
import json
import sqlite3
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "data", "xmt.db")
ACCOUNTS_JSON = os.path.join(HERE, "config", "accounts.json")
RIVALS_JSON = os.path.join(HERE, "config", "rivals.json")

SCHEMA = """
CREATE TABLE IF NOT EXISTS account_snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id  TEXT NOT NULL,
    snap_date   TEXT NOT NULL,          -- YYYY-MM-DD
    ts          TEXT NOT NULL,          -- ISO 采集时间
    followers   INTEGER,               -- 粉丝数
    total_likes INTEGER,               -- 总获赞
    works_count INTEGER,               -- 作品总数
    note        TEXT,
    UNIQUE(account_id, snap_date)
);

CREATE TABLE IF NOT EXISTS works (
    account_id   TEXT NOT NULL,
    work_id      TEXT NOT NULL,
    platform     TEXT NOT NULL,
    title        TEXT,
    work_type    INTEGER,              -- 0=视频 1=图文
    publish_ts   INTEGER,              -- 发布时间戳(秒)
    publish_time TEXT,                 -- 格式化
    digg         INTEGER,              -- 点赞
    comment      INTEGER,             -- 评论
    share        INTEGER,             -- 分享
    play         INTEGER,             -- 播放(前台多为空)
    url          TEXT,
    first_seen   TEXT,
    last_seen    TEXT,
    PRIMARY KEY(account_id, work_id)
);

CREATE INDEX IF NOT EXISTS idx_snap_acct ON account_snapshots(account_id, snap_date);
CREATE INDEX IF NOT EXISTS idx_work_acct ON works(account_id, publish_ts DESC);

-- ===== v2 =====

CREATE TABLE IF NOT EXISTS accounts (
    id          TEXT PRIMARY KEY,
    platform    TEXT NOT NULL,          -- douyin / xiaohongshu / channels
    name        TEXT,
    owner       TEXT,
    role        TEXT,
    kind        TEXT NOT NULL DEFAULT 'own',   -- own=自有 rival=对标
    enabled     INTEGER NOT NULL DEFAULT 1,
    url         TEXT,                   -- 抖音主页分享链接
    xhs_id      TEXT,                   -- 小红书号
    blue_v      TEXT,
    note        TEXT,
    followers   INTEGER,                -- 最新粉丝（对标号便于排序）
    extra_json  TEXT,
    updated_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_acct_kind ON accounts(kind, platform);

CREATE TABLE IF NOT EXISTS work_snapshots (
    account_id  TEXT NOT NULL,
    work_id     TEXT NOT NULL,
    snap_date   TEXT NOT NULL,
    ts          TEXT NOT NULL,
    digg        INTEGER,
    comment     INTEGER,
    share       INTEGER,
    play        INTEGER,
    PRIMARY KEY(account_id, work_id, snap_date)
);

CREATE INDEX IF NOT EXISTS idx_wsnap_date ON work_snapshots(snap_date);

CREATE TABLE IF NOT EXISTS hot_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    platform    TEXT NOT NULL,
    kind        TEXT NOT NULL,          -- hot_search / hot_video / hot_note
    rank        INTEGER,
    title       TEXT NOT NULL,
    score       INTEGER,
    url         TEXT,
    snap_date   TEXT NOT NULL,
    ts          TEXT NOT NULL,
    UNIQUE(platform, kind, title, snap_date)
);

CREATE TABLE IF NOT EXISTS keywords (
    keyword     TEXT NOT NULL,
    platform    TEXT NOT NULL,
    enabled     INTEGER NOT NULL DEFAULT 1,
    note        TEXT,
    added_at    TEXT,
    PRIMARY KEY(keyword, platform)
);

CREATE TABLE IF NOT EXISTS topics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT,                   -- hot / rival / own_hit / llm
    platform    TEXT,
    account_id  TEXT,                   -- 建议投放的账号
    title       TEXT NOT NULL,
    hook        TEXT,                   -- 开头钩子
    outline     TEXT,                   -- 结构要点
    score       REAL,                   -- 推荐度 0-100
    evidence    TEXT,                   -- 数据证据（哪条爆款/热搜支撑）
    status      TEXT DEFAULT 'new',     -- new / picked / used / dropped
    created_at  TEXT,
    UNIQUE(title, platform, account_id)
);

CREATE TABLE IF NOT EXISTS insights (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,          -- growth_report / hit_analysis / bench / direction
    scope       TEXT,                   -- 账号 id / all / 平台
    title       TEXT,
    body_md     TEXT,
    data_json   TEXT,
    created_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_insights_kind ON insights(kind, created_at DESC);

CREATE TABLE IF NOT EXISTS search_hits (
    platform     TEXT NOT NULL,
    keyword      TEXT NOT NULL,
    work_id      TEXT NOT NULL,
    author_name  TEXT,
    author_id    TEXT,
    title        TEXT,
    work_type    INTEGER,
    digg         INTEGER,
    comment      INTEGER,
    share        INTEGER,
    play         INTEGER,
    publish_ts   INTEGER,
    publish_time TEXT,
    url          TEXT,
    snap_date    TEXT NOT NULL,
    ts           TEXT NOT NULL,
    PRIMARY KEY(platform, keyword, work_id, snap_date)
);

CREATE INDEX IF NOT EXISTS idx_hits_kw ON search_hits(platform, keyword, snap_date, digg DESC);
"""


def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init():
    con = connect()
    con.executescript(SCHEMA)
    con.commit()
    con.close()
    return sync_accounts()


# ---------- 账号 / 关键词同步 ----------

def _load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sync_accounts():
    """把 config/accounts.json(自有) 与 config/rivals.json(对标) 同步进 accounts 表。"""
    now = datetime.now().isoformat(timespec="seconds")
    rows = []
    for a in (_load_json(ACCOUNTS_JSON).get("accounts") or []):
        rows.append((a.get("id"), a.get("platform"), a.get("name"), a.get("owner"),
                     a.get("role"), "own", 1 if a.get("enabled", True) else 0,
                     a.get("url"), a.get("xhs_id"), a.get("blue_v"), a.get("note"), now))
    for a in (_load_json(RIVALS_JSON).get("rivals") or []):
        rows.append((a.get("id"), a.get("platform"), a.get("name"), a.get("owner"),
                     a.get("role"), "rival", 1 if a.get("enabled", True) else 0,
                     a.get("url"), a.get("xhs_id"), a.get("blue_v"), a.get("note"), now))
    if not rows:
        return 0
    con = connect()
    con.executemany(
        """INSERT INTO accounts(id,platform,name,owner,role,kind,enabled,url,xhs_id,blue_v,note,updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
             platform=excluded.platform, name=excluded.name, owner=excluded.owner,
             role=excluded.role, kind=excluded.kind, enabled=excluded.enabled,
             url=excluded.url, xhs_id=excluded.xhs_id, blue_v=excluded.blue_v,
             note=excluded.note, updated_at=excluded.updated_at""", rows)
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    con.close()
    return n


def get_accounts(platform=None, kind=None, enabled_only=True):
    con = connect()
    sql = "SELECT * FROM accounts WHERE 1=1"
    args = []
    if platform:
        sql += " AND platform=?"
        args.append(platform)
    if kind:
        sql += " AND kind=?"
        args.append(kind)
    if enabled_only:
        sql += " AND enabled=1"
    sql += " ORDER BY kind, platform, id"
    rows = [dict(r) for r in con.execute(sql, args).fetchall()]
    con.close()
    return rows


def get_keywords(platform=None, enabled_only=True):
    """监控关键词：先以 config/rivals.json 为源补录，再读 DB。"""
    kws = []
    src = (_load_json(RIVALS_JSON).get("keywords") or {})
    if platform:
        kws = [(k, platform) for k in (src.get(platform) or [])]
    else:
        for p, lst in src.items():
            kws += [(k, p) for k in (lst or [])]
    if kws:
        now = datetime.now().isoformat(timespec="seconds")
        con = connect()
        con.executemany(
            """INSERT INTO keywords(keyword,platform,enabled,added_at) VALUES(?,?,1,?)
               ON CONFLICT(keyword,platform) DO NOTHING""",
            [(k, p, now) for k, p in kws])
        con.commit()
        con.close()
    con = connect()
    sql = "SELECT * FROM keywords WHERE 1=1"
    args = []
    if platform:
        sql += " AND platform=?"
        args.append(platform)
    if enabled_only:
        sql += " AND enabled=1"
    rows = [dict(r) for r in con.execute(sql, args).fetchall()]
    con.close()
    return rows


# ---------- v1 接口（签名兼容） ----------

def upsert_snapshot(con, account_id, followers, total_likes, works_count, note=None, snap_date=None):
    now = datetime.now()
    snap_date = snap_date or now.strftime("%Y-%m-%d")
    con.execute(
        """INSERT INTO account_snapshots(account_id, snap_date, ts, followers, total_likes, works_count, note)
           VALUES(?,?,?,?,?,?,?)
           ON CONFLICT(account_id, snap_date) DO UPDATE SET
             ts=excluded.ts, followers=excluded.followers,
             total_likes=excluded.total_likes, works_count=excluded.works_count,
             note=excluded.note""",
        (account_id, snap_date, now.isoformat(timespec="seconds"),
         followers, total_likes, works_count, note),
    )


def upsert_works(con, account_id, platform, items, with_snapshot=True):
    """写作品明细；with_snapshot=True 同时记录当日指标快照（趋势分析用）。"""
    now = datetime.now()
    now_iso = now.isoformat(timespec="seconds")
    snap_date = now.strftime("%Y-%m-%d")
    for it in items:
        con.execute(
            """INSERT INTO works(account_id, work_id, platform, title, work_type,
                    publish_ts, publish_time, digg, comment, share, play, url, first_seen, last_seen)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(account_id, work_id) DO UPDATE SET
                 title=excluded.title, work_type=excluded.work_type,
                 publish_ts=excluded.publish_ts, publish_time=excluded.publish_time,
                 digg=excluded.digg, comment=excluded.comment, share=excluded.share,
                 play=excluded.play, url=excluded.url, last_seen=excluded.last_seen""",
            (account_id, it["work_id"], platform, it.get("title"), it.get("work_type"),
             it.get("publish_ts"), it.get("publish_time"), it.get("digg"),
             it.get("comment"), it.get("share"), it.get("play"), it.get("url"),
             it.get("first_seen") or now_iso, now_iso),
        )
        if with_snapshot:
            con.execute(
                """INSERT INTO work_snapshots(account_id, work_id, snap_date, ts, digg, comment, share, play)
                   VALUES(?,?,?,?,?,?,?,?)
                   ON CONFLICT(account_id, work_id, snap_date) DO UPDATE SET
                     ts=excluded.ts, digg=excluded.digg, comment=excluded.comment,
                     share=excluded.share, play=excluded.play""",
                (account_id, it["work_id"], snap_date, now_iso,
                 it.get("digg"), it.get("comment"), it.get("share"), it.get("play")),
            )


# ---------- v2 写入接口 ----------

def upsert_hot(con, platform, kind, rows, snap_date=None):
    """rows: [{rank,title,score,url}]"""
    now = datetime.now()
    snap_date = snap_date or now.strftime("%Y-%m-%d")
    ts = now.isoformat(timespec="seconds")
    n = 0
    for r in rows:
        if not r.get("title"):
            continue
        con.execute(
            """INSERT INTO hot_items(platform, kind, rank, title, score, url, snap_date, ts)
               VALUES(?,?,?,?,?,?,?,?)
               ON CONFLICT(platform, kind, title, snap_date) DO UPDATE SET
                 rank=excluded.rank, score=excluded.score, url=excluded.url, ts=excluded.ts""",
            (platform, kind, r.get("rank"), r["title"], r.get("score"), r.get("url"), snap_date, ts))
        n += 1
    return n


def save_topics(con, topics):
    """topics: [{source,platform,account_id,title,hook,outline,score,evidence}]"""
    now = datetime.now().isoformat(timespec="seconds")
    n = 0
    for t in topics:
        if not t.get("title"):
            continue
        con.execute(
            """INSERT INTO topics(source, platform, account_id, title, hook, outline, score, evidence, created_at)
               VALUES(?,?,?,?,?,?,?,?,?)
               ON CONFLICT(title, platform, account_id) DO UPDATE SET
                 hook=excluded.hook, outline=excluded.outline,
                 score=excluded.score, evidence=excluded.evidence""",
            (t.get("source"), t.get("platform"), t.get("account_id"), t["title"],
             t.get("hook"), t.get("outline"), t.get("score"), t.get("evidence"), now))
        n += 1
    return n


def save_insight(con, kind, scope, title, body_md, data=None):
    con.execute(
        """INSERT INTO insights(kind, scope, title, body_md, data_json, created_at)
           VALUES(?,?,?,?,?,?)""",
        (kind, scope, title, body_md,
         json.dumps(data, ensure_ascii=False) if data is not None else None,
         datetime.now().isoformat(timespec="seconds")))


if __name__ == "__main__":
    init()
    con = connect()
    print("db initialized at", DB_PATH)
    for t in ("accounts", "account_snapshots", "works", "work_snapshots",
              "hot_items", "keywords", "topics", "insights"):
        n = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"  {t}: {n}")
    con.close()
