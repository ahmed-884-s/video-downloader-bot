"""SQLite database layer with full schema"""

import sqlite3
import os
import json
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "guardian.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS group_settings (
    chat_id     INTEGER PRIMARY KEY,
    lang        TEXT    DEFAULT 'ar',
    antispam    INTEGER DEFAULT 1,
    antilink    INTEGER DEFAULT 1,
    antiflood   INTEGER DEFAULT 1,
    flood_limit INTEGER DEFAULT 5,
    captcha     INTEGER DEFAULT 0,
    welcome     INTEGER DEFAULT 1,
    farewell    INTEGER DEFAULT 1,
    welcome_msg TEXT    DEFAULT '',
    farewell_msg TEXT   DEFAULT '',
    warn_limit  INTEGER DEFAULT 3,
    warn_action TEXT    DEFAULT 'ban',
    rules       TEXT    DEFAULT ''
);

CREATE TABLE IF NOT EXISTS locks (
    chat_id   INTEGER,
    lock_type TEXT,
    PRIMARY KEY (chat_id, lock_type)
);

CREATE TABLE IF NOT EXISTS warnings (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id  INTEGER NOT NULL,
    user_id  INTEGER NOT NULL,
    reason   TEXT    DEFAULT 'No reason',
    date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS filters (
    chat_id  INTEGER,
    keyword  TEXT,
    response TEXT,
    PRIMARY KEY (chat_id, keyword)
);

CREATE TABLE IF NOT EXISTS notes (
    chat_id  INTEGER,
    name     TEXT,
    content  TEXT,
    PRIMARY KEY (chat_id, name)
);

CREATE TABLE IF NOT EXISTS blacklist (
    chat_id INTEGER,
    word    TEXT,
    PRIMARY KEY (chat_id, word)
);

CREATE TABLE IF NOT EXISTS gbans (
    user_id INTEGER PRIMARY KEY,
    reason  TEXT,
    date    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS flood_tracker (
    chat_id    INTEGER,
    user_id    INTEGER,
    count      INTEGER DEFAULT 0,
    last_msg   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (chat_id, user_id)
);
"""


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─── Group Settings ──────────────────────────────────────────────────────────

def get_settings(chat_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM group_settings WHERE chat_id=?", (chat_id,)
        ).fetchone()
        if not row:
            conn.execute(
                "INSERT OR IGNORE INTO group_settings (chat_id) VALUES (?)", (chat_id,)
            )
            return get_settings.__wrapped__(chat_id, conn)
        return dict(row)

def _get_settings_inner(chat_id, conn):
    row = conn.execute("SELECT * FROM group_settings WHERE chat_id=?", (chat_id,)).fetchone()
    return dict(row) if row else {}

get_settings.__wrapped__ = _get_settings_inner


def get_settings(chat_id: int) -> dict:
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO group_settings (chat_id) VALUES (?)", (chat_id,))
        row = conn.execute("SELECT * FROM group_settings WHERE chat_id=?", (chat_id,)).fetchone()
        return dict(row)


def update_setting(chat_id: int, key: str, value):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO group_settings (chat_id) VALUES (?)", (chat_id,))
        conn.execute(f"UPDATE group_settings SET {key}=? WHERE chat_id=?", (value, chat_id))


def get_lang(chat_id: int) -> str:
    s = get_settings(chat_id)
    return s.get("lang", "ar")


# ─── Warnings ────────────────────────────────────────────────────────────────

def add_warn(chat_id: int, user_id: int, reason: str) -> int:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO warnings (chat_id, user_id, reason) VALUES (?,?,?)",
            (chat_id, user_id, reason)
        )
        count = conn.execute(
            "SELECT COUNT(*) FROM warnings WHERE chat_id=? AND user_id=?",
            (chat_id, user_id)
        ).fetchone()[0]
    return count


def remove_warn(chat_id: int, user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM warnings WHERE chat_id=? AND user_id=? ORDER BY id DESC LIMIT 1",
            (chat_id, user_id)
        ).fetchone()
        if row:
            conn.execute("DELETE FROM warnings WHERE id=?", (row[0],))
            return True
    return False


def get_warns(chat_id: int, user_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT reason, date FROM warnings WHERE chat_id=? AND user_id=? ORDER BY id",
            (chat_id, user_id)
        ).fetchall()
    return [dict(r) for r in rows]


def clear_warns(chat_id: int, user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM warnings WHERE chat_id=? AND user_id=?", (chat_id, user_id))


# ─── Filters ─────────────────────────────────────────────────────────────────

def add_filter(chat_id: int, keyword: str, response: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO filters (chat_id, keyword, response) VALUES (?,?,?)",
            (chat_id, keyword.lower(), response)
        )


def remove_filter(chat_id: int, keyword: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM filters WHERE chat_id=? AND keyword=?", (chat_id, keyword.lower()))


def get_filters(chat_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT keyword, response FROM filters WHERE chat_id=?", (chat_id,)).fetchall()
    return [dict(r) for r in rows]


def check_filter(chat_id: int, text: str):
    text_lower = text.lower()
    with get_conn() as conn:
        rows = conn.execute("SELECT keyword, response FROM filters WHERE chat_id=?", (chat_id,)).fetchall()
    for r in rows:
        if r["keyword"] in text_lower:
            return r["response"]
    return None


# ─── Notes ───────────────────────────────────────────────────────────────────

def save_note(chat_id: int, name: str, content: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO notes (chat_id, name, content) VALUES (?,?,?)",
            (chat_id, name.lower(), content)
        )


def delete_note(chat_id: int, name: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM notes WHERE chat_id=? AND name=?", (chat_id, name.lower()))


def get_note(chat_id: int, name: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT content FROM notes WHERE chat_id=? AND name=?", (chat_id, name.lower())).fetchone()
    return row["content"] if row else None


def get_notes(chat_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT name FROM notes WHERE chat_id=?", (chat_id,)).fetchall()
    return [r["name"] for r in rows]


# ─── Blacklist ────────────────────────────────────────────────────────────────

def add_blacklist(chat_id: int, word: str):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO blacklist (chat_id, word) VALUES (?,?)", (chat_id, word.lower()))


def remove_blacklist(chat_id: int, word: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM blacklist WHERE chat_id=? AND word=?", (chat_id, word.lower()))


def get_blacklist(chat_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT word FROM blacklist WHERE chat_id=?", (chat_id,)).fetchall()
    return [r["word"] for r in rows]


def check_blacklist(chat_id: int, text: str) -> str | None:
    words = get_blacklist(chat_id)
    text_lower = text.lower()
    for w in words:
        if w in text_lower:
            return w
    return None


# ─── Locks ───────────────────────────────────────────────────────────────────

def add_lock(chat_id: int, lock_type: str):
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO locks (chat_id, lock_type) VALUES (?,?)", (chat_id, lock_type))


def remove_lock(chat_id: int, lock_type: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM locks WHERE chat_id=? AND lock_type=?", (chat_id, lock_type))


def get_locks(chat_id: int) -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT lock_type FROM locks WHERE chat_id=?", (chat_id,)).fetchall()
    return [r["lock_type"] for r in rows]


def is_locked(chat_id: int, lock_type: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM locks WHERE chat_id=? AND lock_type=?", (chat_id, lock_type)).fetchone()
    return row is not None


# ─── GBan ─────────────────────────────────────────────────────────────────────

def gban_user(user_id: int, reason: str):
    with get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO gbans (user_id, reason) VALUES (?,?)", (user_id, reason))


def ungban_user(user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM gbans WHERE user_id=?", (user_id,))


def is_gbanned(user_id: int) -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT reason FROM gbans WHERE user_id=?", (user_id,)).fetchone()
    return row["reason"] if row else None


def get_gbans() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT user_id, reason, date FROM gbans ORDER BY date DESC").fetchall()
    return [dict(r) for r in rows]


# ─── Flood Tracker ────────────────────────────────────────────────────────────

def track_flood(chat_id: int, user_id: int) -> int:
    """Returns current flood count after increment. Resets if last msg > 5 seconds ago."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT count, last_msg FROM flood_tracker WHERE chat_id=? AND user_id=?",
            (chat_id, user_id)
        ).fetchone()
        if row:
            from datetime import datetime, timezone
            last = datetime.fromisoformat(row["last_msg"])
            now  = datetime.now()
            diff = (now - last).total_seconds()
            if diff > 5:
                count = 1
            else:
                count = row["count"] + 1
            conn.execute(
                "UPDATE flood_tracker SET count=?, last_msg=CURRENT_TIMESTAMP WHERE chat_id=? AND user_id=?",
                (count, chat_id, user_id)
            )
        else:
            count = 1
            conn.execute(
                "INSERT INTO flood_tracker (chat_id, user_id, count) VALUES (?,?,1)",
                (chat_id, user_id)
            )
    return count


def reset_flood(chat_id: int, user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM flood_tracker WHERE chat_id=? AND user_id=?", (chat_id, user_id))
