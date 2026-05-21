# runner — pure skill execution engine (no argparse)
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agentic_os.control_plane.audit_log import log_approval_request_v2, log_run
from agentic_os.control_plane.config import get_config
from agentic_os.control_plane.policy import ActionType, PolicyDecision, check_action
from agentic_os.control_plane.registry import get_skill


def _allowed_prefixes() -> tuple[str, ...]:
    cfg = get_config()
    vault = cfg.get("vault_path", "vault").rstrip("/") + "/"
    data = cfg.get("data_path", "data").rstrip("/") + "/"
    return (vault, data)


def resolve_output_path(raw: str) -> Path | None:
    """Return resolved Path if safely under vault/ or data/, else None."""
    p = Path(raw)
    if p.is_absolute():
        try:
            resolved = p.resolve()
        except Exception:
            return None
    else:
        resolved = (_REPO_ROOT / p).resolve()

    try:
        resolved.relative_to(_REPO_ROOT)
    except ValueError:
        return None

    rel = resolved.relative_to(_REPO_ROOT)
    rel_str = str(rel)
    if any(rel_str.startswith(prefix) for prefix in _allowed_prefixes()):
        return resolved
    return None


def _load_skill_module(skill_path: Path):
    spec = importlib.util.spec_from_file_location("skill_run", skill_path / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_skill(skill: str, input_str: str = "") -> int:
    """Execute a registered skill through the governed runner. Returns exit code."""
    try:
        entry = get_skill(skill)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if entry.accepts_input and not input_str:
        print(f"error: skill '{skill}' requires --input", file=sys.stderr)
        return 2

    cfg = get_config()

    try:
        module = _load_skill_module(entry.path)
        raw_outputs: list[str] = module.run(input_str)
    except Exception as exc:
        run_id = log_run(skill, input_str, [], "error", error=str(exc))
        print(f"error: skill execution failed: {exc}", file=sys.stderr)
        print(f"logged as {run_id}", file=sys.stderr)
        return 1

    valid_outputs: list[str] = []
    blocked = False
    approval_needed: list[tuple[str, str]] = []

    for raw_path in raw_outputs:
        safe = resolve_output_path(raw_path)
        if safe is None:
            rel_str = raw_path.lstrip("/")
            policy_result = check_action(ActionType.FILE_WRITE, rel_str)
            if policy_result.decision == PolicyDecision.REQUIRE_APPROVAL:
                approval_needed.append((raw_path, policy_result.reason))
            else:
                log_run(
                    skill,
                    input_str,
                    valid_outputs,
                    "path_violation",
                    error=f"output path rejected: {raw_path!r}",
                )
                print(
                    f"error: output path rejected (traversal or out-of-bounds): {raw_path!r}",
                    file=sys.stderr,
                )
                blocked = True
                break

    if blocked:
        return 1

    if approval_needed:
        timeout_hours = int(cfg.get("approval_timeout_hours", 24))
        run_id = log_run(skill, input_str, [], "pending_approval")
        for raw_path, reason in approval_needed:
            record = log_approval_request_v2(
                run_id=run_id,
                skill=skill,
                action="file_write",
                path=raw_path,
                reason=reason,
                timeout_hours=timeout_hours,
            )
            print(f"  approval required: {record['approval_id']}")
            print(f"  action:  file_write → {raw_path}")
            print(f"  reason:  {reason}")
            print(f"  expires: {record['expires_at']}")
            print()
            print(f"  to approve:  agentic-os approvals approve {record['approval_id']}")
            print(f"  to deny:     agentic-os approvals deny {record['approval_id']}")
        return 2

    run_id = log_run(skill, input_str, valid_outputs, "success")
    print(f"ok  {run_id}")
    for p in valid_outputs:
        print(f"    wrote: {p}")
    return 0
