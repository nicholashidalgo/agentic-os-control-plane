import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent

from agentic_os.control_plane.audit_log import log_approval_request_v2
from agentic_os.control_plane.approvals import (
    get_approval,
    is_expired,
    list_approvals,
    resolve_approval,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def fake_approvals_log(tmp_path, monkeypatch):
    """Redirect approvals log to a temp file and return its path."""
    import agentic_os.control_plane.audit_log as al
    import agentic_os.control_plane.approvals as ap

    log_file = tmp_path / "approvals.jsonl"
    monkeypatch.setattr(al, "_approvals_log", lambda: log_file)
    monkeypatch.setattr(ap, "_approvals_log", lambda: log_file)
    return log_file


def _write_record(log_file: Path, record: dict) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a") as fh:
        fh.write(json.dumps(record) + "\n")


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_approval_record_created_on_require_approval_action(fake_approvals_log):
    record = log_approval_request_v2(
        run_id="RUN-20260505-120000",
        skill="vault_cleanup",
        action="file_delete",
        path="vault/raw/old_note.md",
        reason="file_delete requires explicit user approval",
    )
    assert fake_approvals_log.exists()
    lines = fake_approvals_log.read_text().strip().splitlines()
    assert len(lines) == 1
    saved = json.loads(lines[0])
    assert saved["approval_id"] == record["approval_id"]
    assert saved["status"] == "pending"
    assert saved["skill"] == "vault_cleanup"
    assert saved["action"] == "file_delete"
    assert saved["resolved_at"] is None
    assert saved["resolved_by"] is None


def test_list_approvals_returns_all(fake_approvals_log):
    now = datetime.now(timezone.utc).isoformat()
    for i in range(3):
        _write_record(fake_approvals_log, {
            "approval_id": f"APR-20260505-00000{i}",
            "run_id": f"RUN-20260505-00000{i}",
            "skill": "vault_cleanup",
            "action": "file_delete",
            "path": None,
            "reason": "test",
            "status": "pending",
            "created_at": now,
            "expires_at": now,
            "resolved_at": None,
            "resolved_by": None,
        })
    results = list_approvals()
    assert len(results) == 3


def test_list_approvals_filters_by_status(fake_approvals_log):
    now = datetime.now(timezone.utc).isoformat()
    statuses = ["pending", "approved", "denied"]
    for i, status in enumerate(statuses):
        _write_record(fake_approvals_log, {
            "approval_id": f"APR-20260505-00000{i}",
            "run_id": f"RUN-20260505-00000{i}",
            "skill": "vault_cleanup",
            "action": "file_delete",
            "path": None,
            "reason": "test",
            "status": status,
            "created_at": now,
            "expires_at": now,
            "resolved_at": None,
            "resolved_by": None,
        })
    pending = list_approvals(status="pending")
    assert len(pending) == 1
    assert pending[0]["status"] == "pending"

    approved = list_approvals(status="approved")
    assert len(approved) == 1


def test_get_approval_returns_correct_record(fake_approvals_log):
    now = datetime.now(timezone.utc).isoformat()
    target_id = "APR-20260505-abc123"
    _write_record(fake_approvals_log, {
        "approval_id": "APR-20260505-000000",
        "run_id": "RUN-1",
        "skill": "x",
        "action": "file_delete",
        "path": None,
        "reason": "",
        "status": "pending",
        "created_at": now,
        "expires_at": now,
        "resolved_at": None,
        "resolved_by": None,
    })
    _write_record(fake_approvals_log, {
        "approval_id": target_id,
        "run_id": "RUN-2",
        "skill": "vault_cleanup",
        "action": "file_delete",
        "path": "vault/raw/note.md",
        "reason": "needs approval",
        "status": "pending",
        "created_at": now,
        "expires_at": now,
        "resolved_at": None,
        "resolved_by": None,
    })
    result = get_approval(target_id)
    assert result is not None
    assert result["approval_id"] == target_id
    assert result["skill"] == "vault_cleanup"


def test_resolve_approval_approved(fake_approvals_log):
    now = datetime.now(timezone.utc)
    future = (now + timedelta(hours=24)).isoformat()
    apr_id = "APR-20260505-aaa111"
    _write_record(fake_approvals_log, {
        "approval_id": apr_id,
        "run_id": "RUN-20260505-143022",
        "skill": "vault_cleanup",
        "action": "file_delete",
        "path": "vault/raw/old.md",
        "reason": "requires approval",
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": future,
        "resolved_at": None,
        "resolved_by": None,
    })
    resolved = resolve_approval(apr_id, "approved", resolved_by="test_user")
    assert resolved["status"] == "approved"
    assert resolved["resolved_by"] == "test_user"
    assert resolved["resolved_at"] is not None

    # The resolution must be persisted as a new line
    lines = fake_approvals_log.read_text().strip().splitlines()
    assert len(lines) == 2
    last = json.loads(lines[-1])
    assert last["status"] == "approved"


def test_resolve_approval_denied(fake_approvals_log):
    now = datetime.now(timezone.utc)
    future = (now + timedelta(hours=24)).isoformat()
    apr_id = "APR-20260505-bbb222"
    _write_record(fake_approvals_log, {
        "approval_id": apr_id,
        "run_id": "RUN-20260505-143022",
        "skill": "vault_cleanup",
        "action": "file_delete",
        "path": None,
        "reason": "requires approval",
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": future,
        "resolved_at": None,
        "resolved_by": None,
    })
    resolved = resolve_approval(apr_id, "denied")
    assert resolved["status"] == "denied"

    lines = fake_approvals_log.read_text().strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[-1])["status"] == "denied"


def test_resolve_expired_approval_sets_expired_status(fake_approvals_log):
    now = datetime.now(timezone.utc)
    past = (now - timedelta(hours=1)).isoformat()  # already expired
    apr_id = "APR-20260505-ccc333"
    _write_record(fake_approvals_log, {
        "approval_id": apr_id,
        "run_id": "RUN-20260505-143022",
        "skill": "vault_cleanup",
        "action": "file_delete",
        "path": None,
        "reason": "requires approval",
        "status": "pending",
        "created_at": past,
        "expires_at": past,
        "resolved_at": None,
        "resolved_by": None,
    })
    # Even if caller requests "approved", expired record must resolve to "expired"
    resolved = resolve_approval(apr_id, "approved")
    assert resolved["status"] == "expired"


def test_approval_id_format(fake_approvals_log):
    import re
    record = log_approval_request_v2(
        run_id="RUN-20260505-120000",
        skill="test_skill",
        action="file_delete",
        path=None,
        reason="test",
    )
    # APR-YYYYMMDD-xxxxxx  (6 hex chars)
    assert re.fullmatch(r"APR-\d{8}-[0-9a-f]{6}", record["approval_id"]), (
        f"unexpected format: {record['approval_id']!r}"
    )


def test_resolve_already_resolved_raises(fake_approvals_log):
    now = datetime.now(timezone.utc)
    future = (now + timedelta(hours=24)).isoformat()
    apr_id = "APR-20260505-ddd444"
    resolved_record = {
        "approval_id": apr_id,
        "run_id": "RUN-X",
        "skill": "x",
        "action": "file_delete",
        "path": None,
        "reason": "",
        "status": "approved",  # already resolved
        "created_at": now.isoformat(),
        "expires_at": future,
        "resolved_at": now.isoformat(),
        "resolved_by": "user",
    }
    _write_record(fake_approvals_log, resolved_record)
    with pytest.raises(ValueError, match="already resolved"):
        resolve_approval(apr_id, "denied")


def test_get_approval_returns_none_for_missing(fake_approvals_log):
    result = get_approval("APR-00000000-000000")
    assert result is None
