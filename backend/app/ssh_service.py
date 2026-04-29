from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass

import asyncssh

from .config import settings
from .schemas import Node


@dataclass(frozen=True)
class SSHCommandResult:
    stdout: str
    stderr: str
    exit_code: int


@dataclass(frozen=True)
class StreamEvent:
    stream: str
    line: str


def _exit_code(value: object) -> int:
    for attr in ("exit_status", "returncode"):
        code = getattr(value, attr, None)
        if code is not None:
            return int(code)
    return -1


async def run_command(node: Node, command: str, timeout_seconds: float | None = None) -> SSHCommandResult:
    timeout = timeout_seconds or settings.ssh_command_timeout
    try:
        async with asyncssh.connect(
            node.ip,
            username=node.ssh_user,
            known_hosts=None,
            connect_timeout=settings.ssh_connect_timeout,
        ) as conn:
            result = await asyncio.wait_for(conn.run(command, check=False), timeout=timeout)
            return SSHCommandResult(
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                exit_code=_exit_code(result),
            )
    except Exception as exc:
        message = str(exc) or exc.__class__.__name__
        return SSHCommandResult(stdout="", stderr=message, exit_code=-1)


async def stream_command(node: Node, command: str) -> AsyncIterator[StreamEvent | int]:
    async with asyncssh.connect(
        node.ip,
        username=node.ssh_user,
        known_hosts=None,
        connect_timeout=settings.ssh_connect_timeout,
    ) as conn:
        process = await conn.create_process(command)
        queue: asyncio.Queue[StreamEvent | None] = asyncio.Queue()

        async def read_stream(name: str, stream: object) -> None:
            try:
                async for line in stream:  # type: ignore[attr-defined]
                    await queue.put(StreamEvent(stream=name, line=line))
            finally:
                await queue.put(None)

        stdout_task = asyncio.create_task(read_stream("stdout", process.stdout))
        stderr_task = asyncio.create_task(read_stream("stderr", process.stderr))
        closed_streams = 0

        while closed_streams < 2:
            event = await queue.get()
            if event is None:
                closed_streams += 1
                continue
            yield event

        await stdout_task
        await stderr_task
        completed = await process.wait(check=False)
        yield _exit_code(completed)
