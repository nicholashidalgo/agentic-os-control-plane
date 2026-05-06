import pytest
from control_plane.policy import (
    ActionType,
    PolicyDecision,
    check_action,
    check_content_for_secrets,
)


def test_file_read_always_allowed():
    result = check_action(ActionType.FILE_READ)
    assert result.decision == PolicyDecision.ALLOW


def test_file_write_vault_allowed():
    result = check_action(ActionType.FILE_WRITE, "vault/wiki/note.md")
    assert result.decision == PolicyDecision.ALLOW


def test_file_write_data_allowed():
    result = check_action(ActionType.FILE_WRITE, "data/runs.jsonl")
    assert result.decision == PolicyDecision.ALLOW


def test_file_write_control_plane_denied():
    result = check_action(ActionType.FILE_WRITE, "control_plane/policy.py")
    assert result.decision == PolicyDecision.DENY


def test_file_write_claude_md_denied():
    result = check_action(ActionType.FILE_WRITE, "CLAUDE.md")
    assert result.decision == PolicyDecision.DENY


def test_file_write_agents_md_denied():
    result = check_action(ActionType.FILE_WRITE, "AGENTS.md")
    assert result.decision == PolicyDecision.DENY


def test_file_write_other_path_requires_approval():
    result = check_action(ActionType.FILE_WRITE, "some/other/path.py")
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_file_delete_requires_approval():
    result = check_action(ActionType.FILE_DELETE)
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_git_commit_requires_approval():
    result = check_action(ActionType.GIT_COMMIT)
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_git_push_requires_approval():
    result = check_action(ActionType.GIT_PUSH)
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_email_send_requires_approval():
    result = check_action(ActionType.EMAIL_SEND)
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_api_write_requires_approval():
    result = check_action(ActionType.API_WRITE)
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_shell_exec_requires_approval():
    result = check_action(ActionType.SHELL_EXEC)
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_secret_detection_api_key():
    result = check_content_for_secrets("api_key=sk-abc123xyz789qwertyui")
    assert result.decision == PolicyDecision.DENY


def test_secret_detection_bearer_token():
    result = check_content_for_secrets("Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc")
    assert result.decision == PolicyDecision.DENY


def test_secret_detection_clean_content():
    result = check_content_for_secrets("This is a normal log entry with no secrets.")
    assert result.decision == PolicyDecision.ALLOW


def test_secret_detection_gh_token():
    result = check_content_for_secrets("token = ghp_" + "A" * 36)
    assert result.decision == PolicyDecision.DENY
