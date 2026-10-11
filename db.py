"""SQLite 存储层：账号快照 + 作品明细。"""
import os
import json
import sqlite3
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "data", "xmt.db")

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


def upsert_works(con, account_id, platform, items):
    now = datetime.now().isoformat(timespec="seconds")
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
             now, now),
        )


if __name__ == "__main__":
    init()
    print("db initialized at", DB_PATH)
