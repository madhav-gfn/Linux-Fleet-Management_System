from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from .config import settings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database() -> None:
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                ssh_user TEXT NOT NULL,
                label TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'unknown',
                autonomy_level INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                node_id INTEGER,
                node_label TEXT,
                command TEXT NOT NULL,
                triggered_by TEXT NOT NULL,
                mode TEXT NOT NULL,
                output_summary TEXT NOT NULL DEFAULT '',
                exit_code INTEGER,
                FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE SET NULL
            );
            """
        )
        seed_nodes(conn)


def seed_nodes(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    if count:
        return

    now = utc_now()
    seeds: list[dict[str, Any]] = [
        {
            "ip": os_value("FLEET_MANAGER_HOST", "localhost"),
            "ssh_user": settings.default_ssh_user,
            "label": "manager",
            "status": "unknown",
            "autonomy_level": 0,
        },
        {
            "ip": os_value("FLEET_NODE_1_HOST", "node-1"),
            "ssh_user": settings.default_ssh_user,
            "label": "node-1",
            "status": "unknown",
            "autonomy_level": 1,
        },
        {
            "ip": os_value("FLEET_NODE_2_HOST", "node-2"),
            "ssh_user": settings.default_ssh_user,
            "label": "node-2",
            "status": "unknown",
            "autonomy_level": 1,
        },
    ]
    conn.executemany(
        """
        INSERT INTO nodes (ip, ssh_user, label, status, autonomy_level, created_at, updated_at)
        VALUES (:ip, :ssh_user, :label, :status, :autonomy_level, :created_at, :updated_at)
        """,
        [{**node, "created_at": now, "updated_at": now} for node in seeds],
    )


def os_value(name: str, default: str) -> str:
    import os

    return os.getenv(name, default)
