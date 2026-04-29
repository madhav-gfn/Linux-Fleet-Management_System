from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path(os.getenv("FLEET_DB_PATH", BASE_DIR / "fleet.db"))
    default_ssh_user: str = (
        os.getenv("FLEET_SSH_USER")
        or os.getenv("USER")
        or os.getenv("USERNAME")
        or "ubuntu"
    )
    ssh_connect_timeout: float = float(os.getenv("FLEET_SSH_CONNECT_TIMEOUT", "10"))
    ssh_command_timeout: float = float(os.getenv("FLEET_SSH_COMMAND_TIMEOUT", "120"))
    audit_summary_chars: int = int(os.getenv("FLEET_AUDIT_SUMMARY_CHARS", "1200"))


settings = Settings()

