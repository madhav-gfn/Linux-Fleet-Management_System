from __future__ import annotations

from pydantic import BaseModel, Field


class NodeCreate(BaseModel):
    ip: str = Field(..., min_length=1, description="IP address or SSH-resolvable host alias")
    ssh_user: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    status: str = "unknown"
    autonomy_level: int = Field(default=0, ge=0)


class Node(NodeCreate):
    id: int
    created_at: str
    updated_at: str


class CommandRequest(BaseModel):
    command: str = Field(..., min_length=1)
    triggered_by: str = "user"
    timeout_seconds: float | None = Field(default=None, gt=0)


class CommandResult(BaseModel):
    node_id: int
    node_label: str
    command: str
    stdout: str
    stderr: str
    exit_code: int


class BroadcastRequest(BaseModel):
    command: str = Field(..., min_length=1)
    triggered_by: str = "user"
    timeout_seconds: float | None = Field(default=None, gt=0)


class AuditLog(BaseModel):
    id: int
    timestamp: str
    node_id: int | None
    node_label: str | None
    command: str
    triggered_by: str
    mode: str
    output_summary: str
    exit_code: int | None

