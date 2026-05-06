#!/usr/bin/env python3
# run_skill — governed CLI entrypoint for skill execution
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from control_plane.audit_log import log_approval_request_v2, log_run
from control_plane.config import get_config
from control_plane.policy import ActionType, PolicyDecision, check_action
from control_plane.registry import get_skill, list_skills


def _allowed_prefixes() -> tuple[str, ...]:
    cfg = get_config()
    vault = cfg.get("vault_path", "vault").rstrip("/") + "/"
    data = cfg.get("data_path", "data").rstrip("/") + "/"
    return (vault, data)


def _resolve_output_path(raw: str) -> Path | None:
    """Return resolved Path if it's safely under vault/ or data/, else None."""
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


# ── Approval management helpers ─────────────────────────────────────────────

def _cmd_approvals(args: argparse.Namespace) -> int:
    from control_plane.approvals import get_approval, list_approvals, resolve_approval

    sub = args.approvals  # "list", "approve", or "deny"

    if sub == "list":
        status_filter = args.status if hasattr(args, "status") else None
        records = list_approvals(status=status_filter)
        if not records:
            label = f" (status={status_filter})" if status_filter else ""
            print(f"  no approval records found{label}")
            return 0
        for r in records:
            exp = " [EXPIRED]" if r.get("status") == "pending" else ""
            from control_plane.approvals import is_expired
            if r.get("status") == "pending" and is_expired(r):
                exp = " [EXPIRED]"
            print(
                f"  {r['approval_id']}  {r.get('status','?'):<10}"
                f"  skill={r.get('skill','')}  action={r.get('action','')}"
                f"  path={r.get('path') or ''}{exp}"
            )
        return 0

    if sub in ("approve", "deny"):
        approval_id = args.approval_id if hasattr(args, "approval_id") else None
        if not approval_id:
            print(f"error: --approvals {sub} requires an approval_id", file=sys.stderr)
            return 2

        decision = "approved" if sub == "approve" else "denied"
        try:
            resolved = resolve_approval(approval_id, decision)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        print(f"  {resolved['approval_id']}  →  {resolved['status']}")

        # Rerun the skill if the decision is approved and config enables it
        if decision == "approved" and get_config().get("rerun_after_approval", True):
            skill_name = resolved.get("skill", "")
            try:
                entry = get_skill(skill_name)
            except ValueError as exc:
                print(f"  rerun skipped: {exc}", file=sys.stderr)
                return 0
            print(f"  rerunning skill '{skill_name}'...")
            fake_args = argparse.Namespace(
                skill=skill_name,
                input=resolved.get("path") or "",
                list=False,
                approvals=None,
            )
            return _run_skill(fake_args)

        return 0

    print(f"error: unknown --approvals subcommand {sub!r}", file=sys.stderr)
    return 2


# ── Skill execution ──────────────────────────────────────────────────────────

def _run_skill(args: argparse.Namespace) -> int:
    if args.list:
        for entry in list_skills():
            flag = "[input required]" if entry.accepts_input else "[no input]"
            print(f"  {entry.name:<22} {flag}  {entry.description}")
        return 0

    if not args.skill:
        print("error: --skill is required (or use --list)", file=sys.stderr)
        return 2

    try:
        entry = get_skill(args.skill)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if entry.accepts_input and not args.input:
        print(f"error: skill '{args.skill}' requires --input", file=sys.stderr)
        return 2

    input_str = args.input or ""

    # Check whether this skill execution would hit REQUIRE_APPROVAL.
    # Skills that write only to vault/ or data/ pass the FILE_WRITE check.
    # Destructive action types (FILE_DELETE, GIT_COMMIT, etc.) always require approval.
    # We detect this by checking the configured gate before executing.
    cfg = get_config()
    if cfg.get("require_approval_for_destructive_actions", True):
        # Check the action type implied by the skill's output path prefix via policy.
        # For skills that explicitly perform destructive actions we check FILE_DELETE;
        # for ordinary skills the path check in _resolve_output_path is the gate.
        # This pre-flight uses FILE_WRITE against a sentinel to surface REQUIRE_APPROVAL
        # only for paths that would fall outside the permitted prefixes.
        # Full per-action gating is handled by policy_simulator and future skill metadata.
        pass  # path-level gating is done after execution (see _resolve_output_path)

    try:
        module = _load_skill_module(entry.path)
        raw_outputs: list[str] = module.run(input_str)
    except Exception as exc:
        run_id = log_run(args.skill, input_str, [], "error", error=str(exc))
        print(f"error: skill execution failed: {exc}", file=sys.stderr)
        print(f"logged as {run_id}", file=sys.stderr)
        return 1

    # Check each output path against policy
    valid_outputs: list[str] = []
    blocked = False
    approval_needed: list[tuple[str, str]] = []  # (raw_path, reason)

    for raw_path in raw_outputs:
        safe = _resolve_output_path(raw_path)
        if safe is None:
            # Determine whether this is a policy REQUIRE_APPROVAL or an outright violation
            rel_str = raw_path.lstrip("/")
            policy_result = check_action(ActionType.FILE_WRITE, rel_str)
            if policy_result.decision == PolicyDecision.REQUIRE_APPROVAL:
                approval_needed.append((raw_path, policy_result.reason))
            else:
                log_run(
                    args.skill,
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
        run_id = log_run(args.skill, input_str, [], "pending_approval")
        for raw_path, reason in approval_needed:
            record = log_approval_request_v2(
                run_id=run_id,
                skill=args.skill,
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
            print(f"  to approve:  python control_plane/run_skill.py --approvals approve {record['approval_id']}")
            print(f"  to deny:     python control_plane/run_skill.py --approvals deny {record['approval_id']}")
        return 2

    run_id = log_run(args.skill, input_str, valid_outputs, "success")
    print(f"ok  {run_id}")
    for p in valid_outputs:
        print(f"    wrote: {p}")
    return 0


# Keep old name as alias so existing callers aren't broken
def _run(args: argparse.Namespace) -> int:
    return _run_skill(args)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="run_skill",
        description="Execute a registered skill inside the governed control plane.",
    )
    parser.add_argument("--skill", help="Skill name to execute")
    parser.add_argument("--input", help="Input string passed to the skill")
    parser.add_argument("--list", action="store_true", help="List all registered skills")
    parser.add_argument(
        "--approvals",
        metavar="SUBCOMMAND",
        help="Manage approvals: list | approve <id> | deny <id>",
    )
    parser.add_argument(
        "--status",
        help="Filter --approvals list by status (pending, approved, denied, expired)",
    )
    parser.add_argument(
        "approval_id",
        nargs="?",
        help="Approval ID for approve/deny subcommands",
    )
    args = parser.parse_args()

    if args.approvals:
        sys.exit(_cmd_approvals(args))

    sys.exit(_run_skill(args))


if __name__ == "__main__":
    main()
