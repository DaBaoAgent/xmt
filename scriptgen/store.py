"""本地知识库与脚本库：SQLite 新表 + Markdown 落盘。

设计：
  - 结构化字段进 data/xmt.db（sg_* 表），原始对标文案/拆解摘要落 knowledge/reference/
  - 打印版 Word 落 out/<序号>_<号>_<标题>.docx（只含逐字稿/对白稿）
  - 内部 Markdown/批次落 data/scriptgen/；已通过后可同步公司 KB marketing 库
  - knowledge/ 含第三方对标原文，已在 .gitignore 排除，避免误入公开仓库
"""
import os
import json
from datetime import datetime

from . import util

STATUS_PENDING = "待审"
STATUS_APPROVED = "已通过"
STATUS_REJECTED = "已退回"
STATUS_COMPLIANCE = "合规待修"
STATUS_SYNCED = "已同步"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sg_reference_videos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    platform        TEXT NOT NULL,
    video_key       TEXT NOT NULL,
    video_id        TEXT,
    url             TEXT,
    resolved_url    TEXT,
    author          TEXT,
    author_id       TEXT,
    title           TEXT,
    description     TEXT,
    duration_sec    REAL,
    stats_json      TEXT,
    publish_time    TEXT,
    tags_json       TEXT,
    cover_url       TEXT,
    metadata_source TEXT,
    raw_meta_json   TEXT,
    first_seen      TEXT,
    last_seen       TEXT,
    UNIQUE(platform, video_key)
);
CREATE INDEX IF NOT EXISTS idx_sg_ref_author ON sg_reference_videos(platform, author);

CREATE TABLE IF NOT EXISTS sg_transcripts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    platform      TEXT NOT NULL,
    video_key     TEXT NOT NULL,
    source        TEXT,
    language      TEXT,
    text          TEXT,
    segments_json TEXT,
    task_id       TEXT,
    warnings_json TEXT,
    created_at    TEXT,
    updated_at    TEXT,
    UNIQUE(platform, video_key)
);

CREATE TABLE IF NOT EXISTS sg_breakdowns (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    platform           TEXT NOT NULL,
    video_key          TEXT NOT NULL,
    breakdown_json     TEXT,
    summary_md         TEXT,
    account_guess      TEXT,
    account_confidence REAL,
    product_guess      TEXT,
    product_confidence REAL,
    created_at         TEXT,
    updated_at         TEXT,
    UNIQUE(platform, video_key)
);

CREATE TABLE IF NOT EXISTS sg_scripts (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    code                 TEXT NOT NULL UNIQUE,
    created_at           TEXT,
    updated_at           TEXT,
    status               TEXT NOT NULL DEFAULT '待审',
    account_id           TEXT,
    account_label        TEXT,
    presenters_json      TEXT,
    source_platform      TEXT,
    video_key            TEXT,
    benchmark_url        TEXT,
    benchmark_title      TEXT,
    product_model        TEXT,
    product_doc_ids_json TEXT,
    title                TEXT,
    body_json            TEXT,
    body_md              TEXT,
    shooting_tips_json   TEXT,
    publish_json         TEXT,
    compliance_json      TEXT,
    facts_json           TEXT,
    word_count           INTEGER,
    estimated_seconds    REAL,
    target_seconds       REAL,
    file_path            TEXT,
    docx_path            TEXT,
    version              INTEGER DEFAULT 1,
    approved_at          TEXT,
    approved_by          TEXT,
    sync_status          TEXT,
    synced_at            TEXT,
    kb_doc_id            TEXT,
    notes                TEXT
);
CREATE INDEX IF NOT EXISTS idx_sg_scripts_status ON sg_scripts(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sg_scripts_account ON sg_scripts(account_id, created_at DESC);

CREATE TABLE IF NOT EXISTS sg_script_versions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id       INTEGER NOT NULL,
    version         INTEGER NOT NULL,
    created_at      TEXT,
    instruction     TEXT,
    body_md         TEXT,
    publish_json    TEXT,
    compliance_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_sg_versions_script ON sg_script_versions(script_id, version DESC);

CREATE TABLE IF NOT EXISTS sg_batches (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_code           TEXT NOT NULL UNIQUE,
    created_at           TEXT,
    updated_at           TEXT,
    source_text          TEXT,
    total                INTEGER,
    succeeded            INTEGER,
    failed               INTEGER,
    pending_confirmation INTEGER,
    report_path          TEXT,
    result_json          TEXT
);

CREATE TABLE IF NOT EXISTS sg_usage (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT,
    batch_code TEXT,
    platform   TEXT,
    video_key  TEXT,
    operation  TEXT,
    calls      INTEGER,
    note       TEXT
);
"""

SCRIPT_JSON_FIELDS = {
    "presenters": "presenters_json",
    "body": "body_json",
    "shooting_tips": "shooting_tips_json",
    "publish": "publish_json",
    "compliance": "compliance_json",
    "facts": "facts_json",
    "product_doc_ids": "product_doc_ids_json",
}


def connect():
    import db
    return db.connect()


def init():
    import db
    db.init()
    con = connect()
    con.executescript(SCHEMA)
    # 轻量迁移：旧库补 target_seconds
    cols = [r[1] for r in con.execute("PRAGMA table_info(sg_scripts)").fetchall()]
    if "target_seconds" not in cols:
        con.execute("ALTER TABLE sg_scripts ADD COLUMN target_seconds REAL")
    if "docx_path" not in cols:
        con.execute("ALTER TABLE sg_scripts ADD COLUMN docx_path TEXT")
    con.commit()
    con.close()
    util.ensure_dirs()
    return True


def video_key(platform, video_id, url):
    if video_id:
        return str(video_id)
    return "url-" + util.short_hash(url or platform, 12)


def _json(v):
    return json.dumps(v, ensure_ascii=False) if v is not None else None


def _loads(v, default=None):
    if not v:
        return default
    try:
        return json.loads(v)
    except Exception:
        return default


# ---------- 对标 ----------

def upsert_reference(con, ref, raw_meta=None):
    now = util.now_iso()
    platform = ref.get("platform")
    key = video_key(platform, ref.get("video_id"), ref.get("resolved_url") or ref.get("url"))
    stats = ref.get("stats") or {}
    tags = ref.get("tags") or []
    con.execute(
        """INSERT INTO sg_reference_videos(
             platform,video_key,video_id,url,resolved_url,author,author_id,title,description,
             duration_sec,stats_json,publish_time,tags_json,cover_url,metadata_source,
             raw_meta_json,first_seen,last_seen)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(platform,video_key) DO UPDATE SET
             video_id=COALESCE(excluded.video_id,sg_reference_videos.video_id),
             url=COALESCE(excluded.url,sg_reference_videos.url),
             resolved_url=COALESCE(excluded.resolved_url,sg_reference_videos.resolved_url),
             author=COALESCE(excluded.author,sg_reference_videos.author),
             author_id=COALESCE(excluded.author_id,sg_reference_videos.author_id),
             title=COALESCE(excluded.title,sg_reference_videos.title),
             description=COALESCE(excluded.description,sg_reference_videos.description),
             duration_sec=COALESCE(excluded.duration_sec,sg_reference_videos.duration_sec),
             stats_json=COALESCE(excluded.stats_json,sg_reference_videos.stats_json),
             publish_time=COALESCE(excluded.publish_time,sg_reference_videos.publish_time),
             tags_json=COALESCE(excluded.tags_json,sg_reference_videos.tags_json),
             cover_url=COALESCE(excluded.cover_url,sg_reference_videos.cover_url),
             metadata_source=COALESCE(excluded.metadata_source,sg_reference_videos.metadata_source),
             raw_meta_json=COALESCE(excluded.raw_meta_json,sg_reference_videos.raw_meta_json),
             last_seen=excluded.last_seen""",
        (platform, key, ref.get("video_id"), ref.get("url"), ref.get("resolved_url"),
         ref.get("author"), ref.get("author_id"), ref.get("title"), ref.get("description"),
         ref.get("duration_sec"), _json(stats), ref.get("publish_time"), _json(tags),
         ref.get("cover_url"), ref.get("metadata_source"), _json(raw_meta),
         now, now),
    )
    return key


def _reference_row_to_dict(row):
    if not row:
        return None
    d = dict(row)
    d["stats"] = _loads(d.pop("stats_json", None), {}) or {}
    d["tags"] = _loads(d.pop("tags_json", None), []) or []
    d["raw_meta"] = _loads(d.pop("raw_meta_json", None), {}) or {}
    return d


def get_reference(con, platform, key):
    row = con.execute(
        "SELECT * FROM sg_reference_videos WHERE platform=? AND video_key=?",
        (platform, key)).fetchone()
    return _reference_row_to_dict(row)


def find_reference_by_url(con, platform, url):
    row = con.execute(
        """SELECT * FROM sg_reference_videos
           WHERE platform=? AND (url=? OR resolved_url=?)
           ORDER BY last_seen DESC LIMIT 1""",
        (platform, url, url)).fetchone()
    return _reference_row_to_dict(row)


def save_transcript(con, platform, key, transcript, warnings=None):
    now = util.now_iso()
    con.execute(
        """INSERT INTO sg_transcripts(platform,video_key,source,language,text,segments_json,
               task_id,warnings_json,created_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(platform,video_key) DO UPDATE SET
             source=excluded.source, language=excluded.language, text=excluded.text,
             segments_json=excluded.segments_json, task_id=excluded.task_id,
             warnings_json=excluded.warnings_json, updated_at=excluded.updated_at""",
        (platform, key, transcript.get("source"), transcript.get("language"),
         transcript.get("text"), _json(transcript.get("segments") or []),
         transcript.get("task_id"), _json(warnings or []), now, now))


def get_transcript(con, platform, key):
    row = con.execute(
        "SELECT * FROM sg_transcripts WHERE platform=? AND video_key=?",
        (platform, key)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["segments"] = _loads(d.pop("segments_json", None), []) or []
    d["warnings"] = _loads(d.pop("warnings_json", None), []) or []
    return d


def save_breakdown(con, platform, key, breakdown, summary_md=None):
    now = util.now_iso()
    account = (breakdown.get("account_selection") or {})
    product = (breakdown.get("product_selection") or {})
    con.execute(
        """INSERT INTO sg_breakdowns(platform,video_key,breakdown_json,summary_md,
               account_guess,account_confidence,product_guess,product_confidence,created_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(platform,video_key) DO UPDATE SET
             breakdown_json=excluded.breakdown_json, summary_md=excluded.summary_md,
             account_guess=excluded.account_guess, account_confidence=excluded.account_confidence,
             product_guess=excluded.product_guess, product_confidence=excluded.product_confidence,
             updated_at=excluded.updated_at""",
        (platform, key, _json(breakdown), summary_md,
         account.get("account"), account.get("confidence"),
         product.get("model") or product.get("category"), product.get("confidence"),
         now, now))


def get_breakdown(con, platform, key):
    row = con.execute(
        "SELECT * FROM sg_breakdowns WHERE platform=? AND video_key=?",
        (platform, key)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["breakdown"] = _loads(d.pop("breakdown_json", None), {}) or {}
    return d


# ---------- 脚本 ----------

def _next_code(con):
    day = datetime.now().strftime("%Y%m%d")
    prefix = f"SG-{day}-"
    row = con.execute(
        "SELECT code FROM sg_scripts WHERE code LIKE ? ORDER BY code DESC LIMIT 1",
        (prefix + "%",)).fetchone()
    n = 1
    if row and row["code"]:
        try:
            n = int(str(row["code"]).split("-")[-1]) + 1
        except Exception:
            n = 1
    return f"{prefix}{n:03d}"


def create_script(con, data):
    now = util.now_iso()
    code = data.get("code") or _next_code(con)
    presenters = data.get("presenters") or []
    body = data.get("body")
    tips = data.get("shooting_tips") or []
    publish = data.get("publish") or {}
    compliance = data.get("compliance") or {}
    facts = data.get("facts") or []
    product_docs = data.get("product_doc_ids") or []
    con.execute(
        """INSERT INTO sg_scripts(
             code,created_at,updated_at,status,account_id,account_label,presenters_json,
             source_platform,video_key,benchmark_url,benchmark_title,product_model,
             product_doc_ids_json,title,body_json,body_md,shooting_tips_json,publish_json,
             compliance_json,facts_json,word_count,estimated_seconds,target_seconds,
             file_path,version,notes)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (code, now, now, data.get("status") or STATUS_PENDING,
         data.get("account_id"), data.get("account_label"), _json(presenters),
         data.get("source_platform"), data.get("video_key"), data.get("benchmark_url"),
         data.get("benchmark_title"), data.get("product_model"), _json(product_docs),
         data.get("title"), _json(body), data.get("body_md"), _json(tips), _json(publish),
         _json(compliance), _json(facts), data.get("word_count"),
         data.get("estimated_seconds"), data.get("target_seconds"),
         data.get("file_path"), int(data.get("version") or 1),
         data.get("notes")))
    return code


def _script_row_to_dict(row):
    d = dict(row)
    d["presenters"] = _loads(d.pop("presenters_json", None), []) or []
    d["body"] = _loads(d.pop("body_json", None), {}) or {}
    d["shooting_tips"] = _loads(d.pop("shooting_tips_json", None), []) or []
    d["publish"] = _loads(d.pop("publish_json", None), {}) or {}
    d["compliance"] = _loads(d.pop("compliance_json", None), {}) or {}
    d["facts"] = _loads(d.pop("facts_json", None), []) or []
    d["product_doc_ids"] = _loads(d.pop("product_doc_ids_json", None), []) or []
    return d


def get_script(con, code):
    row = con.execute("SELECT * FROM sg_scripts WHERE code=?", (code,)).fetchone()
    return _script_row_to_dict(row) if row else None


def list_scripts(con, status=None, account_id=None, date=None, limit=50):
    sql = "SELECT * FROM sg_scripts WHERE 1=1"
    args = []
    if status:
        sql += " AND status=?"
        args.append(status)
    if account_id:
        sql += " AND account_id=?"
        args.append(account_id)
    if date:
        sql += " AND created_at LIKE ?"
        args.append(date + "%")
    sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
    args.append(int(limit))
    return [_script_row_to_dict(r) for r in con.execute(sql, args).fetchall()]


def update_script(con, code, **fields):
    allowed = {
        "status", "account_id", "account_label", "presenters_json", "title", "body_json",
        "body_md", "shooting_tips_json", "publish_json", "compliance_json", "facts_json",
        "product_model", "product_doc_ids_json", "word_count", "estimated_seconds",
        "target_seconds", "file_path", "docx_path", "version", "approved_at", "approved_by", "sync_status", "synced_at",
        "kb_doc_id", "notes",
    }
    sets, args = [], []
    for k, v in fields.items():
        if k in SCRIPT_JSON_FIELDS:
            k = SCRIPT_JSON_FIELDS[k]
            v = _json(v)
        if k not in allowed:
            continue
        sets.append(f"{k}=?")
        args.append(v)
    if not sets:
        return False
    sets.append("updated_at=?")
    args.append(util.now_iso())
    args.append(code)
    con.execute(f"UPDATE sg_scripts SET {', '.join(sets)} WHERE code=?", args)
    return True


def add_version(con, script_id, version, instruction, body_md, publish=None, compliance=None):
    con.execute(
        """INSERT INTO sg_script_versions(script_id,version,created_at,instruction,body_md,
               publish_json,compliance_json)
           VALUES(?,?,?,?,?,?,?)""",
        (script_id, version, util.now_iso(), instruction, body_md,
         _json(publish), _json(compliance)))


def list_versions(con, script_id):
    rows = con.execute(
        "SELECT * FROM sg_script_versions WHERE script_id=? ORDER BY version DESC",
        (script_id,)).fetchall()
    return [dict(r) for r in rows]


# ---------- 批次 ----------

def create_batch(con, batch_code, source_text, result):
    now = util.now_iso()
    con.execute(
        """INSERT OR REPLACE INTO sg_batches(batch_code,created_at,updated_at,source_text,
               total,succeeded,failed,pending_confirmation,report_path,result_json)
           VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (batch_code, now, now, source_text,
         result.get("total"), result.get("succeeded"), result.get("failed"),
         result.get("pending_confirmation"), result.get("report_path"), _json(result)))


def get_batch(con, batch_code):
    row = con.execute("SELECT * FROM sg_batches WHERE batch_code=?", (batch_code,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["result"] = _loads(d.pop("result_json", None), {}) or {}
    return d


def list_batches(con, limit=20):
    rows = con.execute("SELECT * FROM sg_batches ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["result"] = _loads(d.pop("result_json", None), {}) or {}
        out.append(d)
    return out


def log_usage(con, batch_code, platform, key, operation, calls=1, note=None):
    con.execute(
        "INSERT INTO sg_usage(ts,batch_code,platform,video_key,operation,calls,note) VALUES(?,?,?,?,?,?,?)",
        (util.now_iso(), batch_code, platform, key, operation, int(calls or 1), note))


# ---------- 路径 ----------

def reference_path(ref):
    platform = ref.get("platform") or "unknown"
    # 目录名走 fs_safe：中文目录名会被本机安全钩子拦
    author = util.fs_safe(ref.get("author") or "unknown-author", 32)
    key = ref.get("video_key") or video_key(platform, ref.get("video_id"), ref.get("url"))
    key = util.fs_safe(str(key).replace("/", "-").replace("\\", "-"), 60)
    return os.path.join(util.project_path("knowledge/reference"), platform, author, f"{key}.md")


def _scripts_dir():
    cfg = (util.config().get("paths") or {})
    return util.project_path(cfg.get("scripts_dir") or "data/scriptgen/scripts")


def _batch_dir():
    cfg = (util.config().get("paths") or {})
    return util.project_path(cfg.get("batch_dir") or "data/scriptgen/batches")


def script_path(script):
    day = (script.get("created_at") or util.now_iso())[:10]
    # 目录名用账号 id（ASCII）避开中文目录名被安全钩子拦；文件名仍保留中文可读
    account = util.fs_safe(script.get("account_id") or "acct", 24)
    title = util.slugify(script.get("title") or script.get("benchmark_title") or "脚本", 36)
    return os.path.join(_scripts_dir(), day, account, f"{script.get('code')}_{title}.md")


def docx_path(script):
    seq = int(script.get("id") or 0)
    # Word 在 out/ 下，中文名不触发钩子，保留可读性
    account = util.slugify(script.get("account_label") or script.get("account_id") or "未分号", 16)
    title = util.slugify(script.get("title") or "逐字稿", 40)
    return os.path.join(util.project_path("out"), f"{seq:03d}_{account}_{title}.docx")


def batch_path(batch_code):
    return os.path.join(_batch_dir(), f"{batch_code}.md")


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")
    return path


def rebuild_index(con):
    from . import render
    scripts = list_scripts(con, limit=200)
    path = os.path.join(_scripts_dir(), "index.md")
    write_text(path, render.render_index(scripts))
    return path
