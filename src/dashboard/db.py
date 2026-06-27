"""
db.py — ASAS dashboard ma'lumotlar bazasi (SQLite).

Ikki jadval:
  cameras — qo'shilgan kameralar (IP/USB)
  events  — har bir shubhali hodisa (rasm, AI bahosi, FACEID, holat)
"""
from __future__ import annotations

import sqlite3
import threading

DB_PATH = "asas.db"
_LOCK = threading.Lock()


def _conn(path: str = DB_PATH) -> sqlite3.Connection:
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def init_db(path: str = DB_PATH) -> None:
    with _conn(path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS cameras(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, source TEXT, location TEXT,
            active INTEGER DEFAULT 1)""")
        con.execute("""CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id INTEGER, camera_name TEXT, ts TEXT,
            snapshot TEXT, face TEXT, reason TEXT,
            det_conf REAL, ai_score REAL, ai_recommend INTEGER,
            identity TEXT, status TEXT DEFAULT 'new')""")
        con.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)")
        con.commit()


def get_setting(key: str, default=None):
    with _conn() as con:
        r = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r["value"] if r else default


def set_setting(key: str, value) -> None:
    with _LOCK, _conn() as con:
        con.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
        con.commit()


# ---------- Kameralar ----------
def add_camera(name: str, source: str, location: str = "") -> int:
    with _LOCK, _conn() as con:
        cur = con.execute(
            "INSERT INTO cameras(name, source, location, active) VALUES(?,?,?,1)",
            (name, str(source), location))
        con.commit()
        return cur.lastrowid


def list_cameras() -> list[dict]:
    with _conn() as con:
        return [dict(r) for r in con.execute("SELECT * FROM cameras ORDER BY id")]


def get_camera(cid: int) -> dict | None:
    with _conn() as con:
        r = con.execute("SELECT * FROM cameras WHERE id=?", (cid,)).fetchone()
        return dict(r) if r else None


def set_camera_active(cid: int, active: bool) -> None:
    with _LOCK, _conn() as con:
        con.execute("UPDATE cameras SET active=? WHERE id=?", (1 if active else 0, cid))
        con.commit()


def delete_camera(cid: int) -> None:
    with _LOCK, _conn() as con:
        con.execute("DELETE FROM cameras WHERE id=?", (cid,))
        con.commit()


# ---------- Hodisalar ----------
def add_event(camera_id, camera_name, ts, snapshot, face, reason,
              det_conf, ai_score, ai_recommend, identity, status="new") -> int:
    with _LOCK, _conn() as con:
        cur = con.execute(
            """INSERT INTO events(camera_id, camera_name, ts, snapshot, face, reason,
               det_conf, ai_score, ai_recommend, identity, status)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (camera_id, camera_name, ts, snapshot, face, reason,
             det_conf, ai_score, 1 if ai_recommend else 0, identity, status))
        con.commit()
        return cur.lastrowid


def list_events(limit: int = 100, status: str | None = None) -> list[dict]:
    q = "SELECT * FROM events"
    args: tuple = ()
    if status:
        q += " WHERE status=?"
        args = (status,)
    q += " ORDER BY id DESC LIMIT ?"
    args += (limit,)
    with _conn() as con:
        return [dict(r) for r in con.execute(q, args)]


def get_event(eid: int) -> dict | None:
    with _conn() as con:
        r = con.execute("SELECT * FROM events WHERE id=?", (eid,)).fetchone()
        return dict(r) if r else None


def set_event_status(eid: int, status: str) -> None:
    with _LOCK, _conn() as con:
        con.execute("UPDATE events SET status=? WHERE id=?", (status, eid))
        con.commit()


def stats() -> dict:
    with _conn() as con:
        total = con.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        new = con.execute("SELECT COUNT(*) FROM events WHERE status='new'").fetchone()[0]
        sent = con.execute("SELECT COUNT(*) FROM events WHERE status='sent'").fetchone()[0]
        rec = con.execute(
            "SELECT COUNT(*) FROM events WHERE status='new' AND ai_recommend=1").fetchone()[0]
        cams = con.execute("SELECT COUNT(*) FROM cameras WHERE active=1").fetchone()[0]
    return {"total": total, "new": new, "sent": sent, "recommended": rec, "active_cameras": cams}
