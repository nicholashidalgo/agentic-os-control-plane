# policy_simulator skill — runs a JSON action manifest through policy.py
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PROJECTS = _REPO_ROOT / "vault" / "projects"

from agentic_os.control_plane.policy import ActionType, PolicyDecision, PolicyResult, check_action

_ACTION_MAP: dict[str, ActionType] = {
    "file_read": ActionType.FILE_READ,
    "file_write": ActionType.FILE_WRITE,
    "file_delete": ActionType.FILE_DELETE,
    "git_commit": ActionType.GIT_COMMIT,
    "git_push": ActionType.GIT_PUSH,
    "email_send": ActionType.EMAIL_SEND,
    "api_write": ActionType.API_WRITE,
    "shell_exec": ActionType.SHELL_EXEC,
}

_DECISION_LABEL = {
    PolicyDecision.ALLOW: "ALLOW",
    PolicyDecision.REQUIRE_APPROVAL: "REQUIRE APPROVAL",
    PolicyDecision.DENY: "DENY",
}


def _evaluate(entry: dict) -> tuple[str, str, PolicyResult]:
    raw_action = str(entry.get("action", "")).lower().strip()
    path = entry.get("path")

    action_type = _ACTION_MAP.get(raw_action)
    if action_type is None:
        result = PolicyResult(PolicyDecision.DENY, "unrecognized action")
    else:
        result = check_action(action_type, path)

    display_action = raw_action or "(empty)"
    display_path = path or ""
    return display_action, display_path, result


def run(input_str: str) -> list[str]:
    if not input_str:
        raise ValueError("policy_simulator requires --input <path to JSON manifest>")

    manifest_path = (_REPO_ROOT / input_str).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    today = date.today().isoformat()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    rows: list[tuple[str, str, PolicyResult]] = [_evaluate(e) for e in manifest]

    n_allow = sum(1 for _, _, r in rows if r.decision == PolicyDecision.ALLOW)
    n_approval = sum(1 for _, _, r in rows if r.decision == PolicyDecision.REQUIRE_APPROVAL)
    n_deny = sum(1 for _, _, r in rows if r.decision == PolicyDecision.DENY)

    col_action = max(len("Action"), max(len(a) for a, _, _ in rows))
    col_path = max(len("Path"), max((len(p) for _, p, _ in rows), default=0))
    col_decision = max(len("Decision"), max(len(_DECISION_LABEL[r.decision]) for _, _, r in rows))
    col_reason = len("Reason")

    def row_line(a: str, p: str, dec: str, reason: str) -> str:
        return f"| {a:<{col_action}} | {p:<{col_path}} | {dec:<{col_decision}} | {reason} |"

    sep = f"| {'-' * col_action} | {'-' * col_path} | {'-' * col_decision} | {'-' * col_reason} |"
    header = row_line("Action", "Path", "Decision", "Reason")

    table_lines = [header, sep]
    for action_str, path_str, result in rows:
        table_lines.append(row_line(
            action_str,
            path_str,
            _DECISION_LABEL[result.decision],
            result.reason,
        ))

    lines = [
        f"# Policy Simulation Report — {today}",
        f"\n_Generated: {now}_  \n_Input manifest: `{input_str}`_\n",
        "## Results\n",
        "\n".join(table_lines),
        f"\n**Totals:** {n_allow} allowed / {n_approval} require approval / {n_deny} denied",
    ]

    _PROJECTS.mkdir(parents=True, exist_ok=True)
    output_path = _PROJECTS / f"policy_simulation_{today}.md"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [str(output_path.relative_to(_REPO_ROOT))]
