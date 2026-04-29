from __future__ import annotations

import asyncio
import sqlite3

from fastapi import FastAPI, HTTPException, Query, Response, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from .database import initialize_database
from .repository import (
    add_audit_log,
    add_broadcast_audit,
    create_node,
    delete_node,
    get_node,
    list_audit_logs,
    list_nodes,
    summarize_output,
    update_node_status,
)
from .schemas import AuditLog, BroadcastRequest, CommandRequest, CommandResult, Node, NodeCreate
from .ssh_service import StreamEvent, run_command, stream_command


app = FastAPI(title="Linux Fleet Manager", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "manager-up"}


@app.get("/api/nodes", response_model=list[Node])
def api_list_nodes() -> list[Node]:
    return list_nodes()


@app.post("/api/nodes", response_model=Node, status_code=status.HTTP_201_CREATED)
def api_create_node(node: NodeCreate) -> Node:
    try:
        return create_node(node)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="node label already exists") from exc


@app.get("/api/nodes/{node_id}", response_model=Node)
def api_get_node(node_id: int) -> Node:
    node = get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="node not found")
    return node


@app.delete("/api/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def api_delete_node(node_id: int) -> Response:
    if not delete_node(node_id):
        raise HTTPException(status_code=404, detail="node not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/nodes/{node_id}/command", response_model=CommandResult)
async def api_run_node_command(node_id: int, request: CommandRequest) -> CommandResult:
    node = get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="node not found")

    result = await run_command(node, request.command, request.timeout_seconds)
    update_node_status(node.id, "offline" if result.exit_code == -1 else "online")
    add_audit_log(
        node_id=node.id,
        node_label=node.label,
        command=request.command,
        triggered_by=request.triggered_by,
        mode="single",
        output_summary=summarize_output(result.stdout, result.stderr),
        exit_code=result.exit_code,
    )
    return CommandResult(
        node_id=node.id,
        node_label=node.label,
        command=request.command,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
    )


@app.post("/api/nodes/broadcast", response_model=list[CommandResult])
async def api_broadcast_command(request: BroadcastRequest) -> list[CommandResult]:
    nodes = list_nodes()
    ssh_results = await asyncio.gather(
        *(run_command(node, request.command, request.timeout_seconds) for node in nodes)
    )

    response: list[CommandResult] = []
    audit_rows: list[tuple[int, str, str, str, int]] = []
    for node, result in zip(nodes, ssh_results, strict=True):
        update_node_status(node.id, "offline" if result.exit_code == -1 else "online")
        response.append(
            CommandResult(
                node_id=node.id,
                node_label=node.label,
                command=request.command,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
            )
        )
        audit_rows.append((node.id, node.label, result.stdout, result.stderr, result.exit_code))

    add_broadcast_audit(audit_rows, request.command, request.triggered_by)
    return response


@app.get("/api/audit", response_model=list[AuditLog])
def api_audit(limit: int = Query(default=100, ge=1, le=1000)) -> list[AuditLog]:
    return list_audit_logs(limit)


@app.websocket("/ws/nodes/{node_id}/command")
async def ws_node_command(websocket: WebSocket, node_id: int, command: str | None = None, triggered_by: str = "user") -> None:
    await websocket.accept()
    node = get_node(node_id)
    if node is None:
        await websocket.send_json({"type": "error", "detail": "node not found"})
        await websocket.close(code=1008)
        return

    if command is None:
        try:
            payload = await websocket.receive_json()
            command = str(payload.get("command", "")).strip()
            triggered_by = str(payload.get("triggered_by", triggered_by))
        except Exception:
            await websocket.send_json({"type": "error", "detail": "send JSON with a command field"})
            await websocket.close(code=1003)
            return

    if not command:
        await websocket.send_json({"type": "error", "detail": "command is required"})
        await websocket.close(code=1008)
        return

    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    exit_code = -1

    try:
        await websocket.send_json({"type": "start", "node_id": node.id, "node_label": node.label, "command": command})
        async for event in stream_command(node, command):
            if isinstance(event, StreamEvent):
                if event.stream == "stdout":
                    stdout_parts.append(event.line)
                else:
                    stderr_parts.append(event.line)
                await websocket.send_json({"type": "output", "stream": event.stream, "line": event.line})
            else:
                exit_code = event
                await websocket.send_json({"type": "exit", "exit_code": exit_code})
        update_node_status(node.id, "offline" if exit_code == -1 else "online")
    except WebSocketDisconnect:
        return
    except Exception as exc:
        message = str(exc) or exc.__class__.__name__
        stderr_parts.append(message)
        await websocket.send_json({"type": "error", "detail": message})
    finally:
        add_audit_log(
            node_id=node.id,
            node_label=node.label,
            command=command,
            triggered_by=triggered_by,
            mode="stream",
            output_summary=summarize_output("".join(stdout_parts), "".join(stderr_parts)),
            exit_code=exit_code,
        )
        await websocket.close()
