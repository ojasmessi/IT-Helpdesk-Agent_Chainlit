"""Ticket storage using SQLite (a database that is just a file - no server needed)."""
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("TICKETS_DB", "tickets.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    conn.execute(
        """CREATE TABLE IF NOT EXISTS tickets (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               user_email TEXT NOT NULL,
               title TEXT NOT NULL,
               description TEXT NOT NULL,
               category TEXT NOT NULL,
               priority TEXT NOT NULL,
               status TEXT NOT NULL DEFAULT 'Open',
               created_at TEXT NOT NULL)"""
    )
    return conn


def create(user_email, title, description, category, priority) -> int:
    with _connect() as conn:
        # "?" placeholders = parameterised query -> prevents SQL injection
        cur = conn.execute(
            "INSERT INTO tickets (user_email, title, description, category, priority, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_email, title, description, category, priority,
             datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        return cur.lastrowid


def get(ticket_id: int, user_email: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM tickets WHERE id = ? AND user_email = ?", (ticket_id, user_email)
        ).fetchone()
        return dict(row) if row else None


def list_for(user_email: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, title, status, priority, created_at FROM tickets "
            "WHERE user_email = ? ORDER BY id DESC LIMIT 10", (user_email,)
        ).fetchall()
        return [dict(r) for r in rows]
