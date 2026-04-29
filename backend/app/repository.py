from __future__ import annotations

import sqlite3
from typing import Iterable

from .config import settings
from .database import connection, utc_now
from .schemas import AuditLog, Node, NodeCreate


def row_to_node(row: sqlite3.Row) -> Node:
    return Node(**dict(row))


def row_to_audit(row: sqlite3.Row) -> AuditLog:
    return AuditLog(**dict(row))


def list_nodes() -> list[Node]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM nodes ORDER BY id").fetchall()
    return [row_to_node(row) for row in rows]


def get_node(node_id: int) -> Node | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
    return row_to_node(row) if row else None


def create_node(node: NodeCreate) -> Node:
    now = utc_now()
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO nodes (ip, ssh_user, label, status, autonomy_level, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node.ip,
                node.ssh_user,
                node.label,
                node.status,
                node.autonomy_level,
                now,
                now,
            ),
        )
        node_id = cursor.lastrowid
    created = get_node(int(node_id))
    if created is None:
        raise RuntimeError("node was inserted but could not be loaded")
    return created


def delete_node(node_id: int) -> bool:
    with connection() as conn:
        cursor = conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
    return cursor.rowcount > 0


def update_node_status(node_id: int, status: str) -> None:
    with connection() as conn:
        conn.execute(
            "UPDATE nodes SET status = ?, updated_at = ? WHERE id = ?",
            (status, utc_now(), node_id),
        )


def summarize_output(stdout: str, stderr: str) -> str:
    combined = "\n".join(part for part in [stdout.strip(), stderr.strip()] if part)
    if len(combined) <= settings.audit_summary_chars:
        return combined
    return combined[: settings.audit_summary_chars - 3] + "..."


def add_audit_log(
    *,
    node_id: int | None,
    node_label: str | None,
    command: str,
    triggered_by: str,
    mode: str,
    output_summary: str,
    exit_code: int | None,
) -> None:
    with connection() as conn:
        conn.execute(
            """
            INSERT INTO audit_logs
                (timestamp, node_id, node_label, command, triggered_by, mode, output_summary, exit_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                utc_now(),
                node_id,
                node_label,
                command,
                triggered_by,
                mode,
                output_summary,
                exit_code,
            ),
        )


def list_audit_logs(limit: int = 100) -> list[AuditLog]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [row_to_audit(row) for row in rows]


def add_broadcast_audit(results: Iterable[tuple[int, str, str, str, int]], command: str, triggered_by: str) -> None:
    for node_id, node_label, stdout, stderr, exit_code in results:
        add_audit_log(
            node_id=node_id,
            node_label=node_label,
            command=command,
            triggered_by=triggered_by,
            mode="broadcast",
            output_summary=summarize_output(stdout, stderr),
            exit_code=exit_code,
        )
