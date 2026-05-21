from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

from agentic_os.control_plane.runner import resolve_output_path


def test_resolve_vault_path_allowed():
    result = resolve_output_path("vault/wiki/note.md")
    assert result is not None
    assert "vault/wiki/note.md" in str(result)


def test_resolve_data_path_allowed():
    result = resolve_output_path("data/runs.jsonl")
    assert result is not None


def test_resolve_traversal_blocked():
    result = resolve_output_path("vault/../../etc/passwd")
    assert result is None


def test_resolve_absolute_outside_repo_blocked():
    result = resolve_output_path("/etc/passwd")
    assert result is None


def test_resolve_control_plane_path_blocked():
    result = resolve_output_path("control_plane/policy.py")
    assert result is None


def test_resolve_root_level_file_blocked():
    result = resolve_output_path("CLAUDE.md")
    assert result is None


def test_resolve_src_path_blocked():
    result = resolve_output_path("src/something.py")
    assert result is None
