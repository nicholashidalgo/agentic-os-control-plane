# audit_log — append-only run and approval log writer
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _data_path() -> Path:
    try:
        from control_plane.config import get_config
        return _REPO_ROOT / get_config().get("data_path", "data")
    except Exception:
        return _REPO_ROOT / "data"


def _runs_log() -> Path:
    return _data_path() / "runs.jsonl"


def _approvals_log() -> Path:
    return _data_path() / "approvals.jsonl"


def _run_id() -> str:
    return "RUN-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _inputs_hash(input_str: str) -> str:
    return hashlib.sha256(input_str.encode()).hexdigest()[:12]


def _append(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def log_run(
    skill: str,
    input_str: str,
    outputs: list[str],
    status: str,
    error: str | None = None,
) -> str:
    run_id = _run_id()
    record = {
        "run_id": run_id,
        "skill": skill,
        "inputs_hash": _inputs_hash(input_str),
        "outputs": outputs,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if error:
        record["error"] = error
    _append(_runs_log(), record)
    return run_id


def log_approval_request(
    run_id: str,
    skill: str,
    action: str,
    path: str | None,
    reason: str,
) -> None:
    record = {
        "run_id": run_id,
        "skill": skill,
        "action": action,
        "path": path,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "outcome": "pending",
    }
    _append(_approvals_log(), record)
