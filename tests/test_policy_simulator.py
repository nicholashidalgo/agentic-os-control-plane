import json
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_skill(tmp_path, entries: list[dict]) -> str:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(entries), encoding="utf-8")

    skill_path = _REPO_ROOT / "skills" / "policy_simulator"
    import importlib.util
    spec = importlib.util.spec_from_file_location("skill_run", skill_path / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    rel = str(manifest.relative_to(_REPO_ROOT)) if manifest.is_relative_to(_REPO_ROOT) else str(manifest)
    outputs = module.run(rel if manifest.is_relative_to(_REPO_ROOT) else str(manifest))
    assert len(outputs) == 1
    out = _REPO_ROOT / outputs[0]
    return out.read_text(encoding="utf-8")


def test_output_written_to_vault_projects(tmp_path):
    entries = [{"action": "file_read", "path": "vault/raw/note.md"}]
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps(entries), encoding="utf-8")

    skill_path = _REPO_ROOT / "skills" / "policy_simulator"
    import importlib.util
    spec = importlib.util.spec_from_file_location("skill_run", skill_path / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    outputs = module.run(str(manifest))
    assert outputs[0].startswith("vault/projects/policy_simulation_")


def test_allow_decision_in_report(tmp_path):
    content = _run_skill(tmp_path, [{"action": "file_read", "path": "vault/raw/note.md"}])
    assert "ALLOW" in content


def test_deny_decision_for_blocked_write(tmp_path):
    content = _run_skill(tmp_path, [{"action": "file_write", "path": "control_plane/policy.py"}])
    assert "DENY" in content


def test_require_approval_for_git_commit(tmp_path):
    content = _run_skill(tmp_path, [{"action": "git_commit"}])
    assert "REQUIRE APPROVAL" in content


def test_unknown_action_denied(tmp_path):
    content = _run_skill(tmp_path, [{"action": "launch_rocket"}])
    assert "DENY" in content
    assert "unrecognized action" in content


def test_totals_line_present(tmp_path):
    entries = [
        {"action": "file_read", "path": "vault/raw/note.md"},
        {"action": "git_commit"},
        {"action": "file_write", "path": "control_plane/policy.py"},
    ]
    content = _run_skill(tmp_path, entries)
    assert "Totals:" in content
    assert "1 allowed" in content
    assert "1 require approval" in content
    assert "1 denied" in content


def test_sample_manifest_covers_all_decisions():
    manifest_path = _REPO_ROOT / "vault" / "raw" / "sample_action_manifest.json"
    entries = json.loads(manifest_path.read_text())
    actions = {e["action"] for e in entries}
    assert "file_read" in actions
    assert "file_write" in actions
    assert "git_commit" in actions or "git_push" in actions or "shell_exec" in actions

    from agentic_os.control_plane.policy import ActionType, PolicyDecision, check_action
    action_map = {
        "file_read": ActionType.FILE_READ,
        "file_write": ActionType.FILE_WRITE,
        "file_delete": ActionType.FILE_DELETE,
        "git_commit": ActionType.GIT_COMMIT,
        "git_push": ActionType.GIT_PUSH,
        "email_send": ActionType.EMAIL_SEND,
        "api_write": ActionType.API_WRITE,
        "shell_exec": ActionType.SHELL_EXEC,
    }
    decisions = set()
    for entry in entries:
        raw = entry["action"].lower()
        at = action_map.get(raw)
        if at is None:
            decisions.add(PolicyDecision.DENY)
        else:
            decisions.add(check_action(at, entry.get("path")).decision)

    assert PolicyDecision.ALLOW in decisions
    assert PolicyDecision.REQUIRE_APPROVAL in decisions
    assert PolicyDecision.DENY in decisions


def test_no_input_raises():
    skill_path = _REPO_ROOT / "skills" / "policy_simulator"
    import importlib.util
    spec = importlib.util.spec_from_file_location("skill_run", skill_path / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(ValueError, match="requires --input"):
        module.run("")
