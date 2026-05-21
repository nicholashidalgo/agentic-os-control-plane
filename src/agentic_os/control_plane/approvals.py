# approvals — approval record lifecycle management
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _data_path() -> Path:
    try:
        from agentic_os.control_plane.config import get_config
        return _REPO_ROOT / get_config().get("data_path", "data")
    except Exception:
        return _REPO_ROOT / "data"


def _approvals_log() -> Path:
    return _data_path() / "approvals.jsonl"


def _read_all() -> list[dict]:
    path = _approvals_log()
    if not path.exists():
        return []
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def is_expired(record: dict) -> bool:
    """Return True if the approval record is past its expires_at timestamp."""
    expires_at = record.get("expires_at")
    if not expires_at:
        return False
    try:
        expiry = datetime.fromisoformat(expires_at)
        return datetime.now(timezone.utc) >= expiry
    except (ValueError, TypeError):
        return False


def list_approvals(status: str | None = None) -> list[dict]:
    """Return all approval records, optionally filtered by status.

    Only returns records that have an approval_id (v2 schema).
    """
    all_records = _read_all()
    v2 = [r for r in all_records if "approval_id" in r]

    if status is None:
        return v2
    return [r for r in v2 if r.get("status") == status]


def get_approval(approval_id: str) -> dict | None:
    """Return the most recent record for the given approval_id, or None."""
    records = _read_all()
    # Walk in reverse to get the latest resolution if multiple entries exist
    for record in reversed(records):
        if record.get("approval_id") == approval_id:
            return record
    return None


def resolve_approval(
    approval_id: str,
    decision: str,
    resolved_by: str = "user",
) -> dict:
    """Resolve an approval record with 'approved', 'denied', or 'expired'.

    Appends a new resolved record to approvals.jsonl.
    Does not mutate any existing record in place.
    Returns the resolved record.

    Raises ValueError on bad decision or unknown approval_id.
    """
    if decision not in ("approved", "denied", "expired"):
        raise ValueError(f"decision must be 'approved', 'denied', or 'expired'; got {decision!r}")

    original = get_approval(approval_id)
    if original is None:
        raise ValueError(f"approval_id {approval_id!r} not found")

    current_status = original.get("status", "pending")
    if current_status not in ("pending",):
        raise ValueError(
            f"approval {approval_id!r} is already resolved (status={current_status!r})"
        )

    # Force expired status if the record is past its deadline
    if is_expired(original) and decision != "expired":
        decision = "expired"

    now = datetime.now(timezone.utc).isoformat()
    resolved = {
        **original,
        "status": decision,
        "resolved_at": now,
        "resolved_by": resolved_by,
    }

    from agentic_os.control_plane.audit_log import append_approval_record
    append_approval_record(resolved)
    return resolved
