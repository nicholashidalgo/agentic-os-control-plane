import pytest
from agentic_os.control_plane.registry import SKILL_REGISTRY, get_skill, list_skills


def test_all_skills_present():
    expected = {"morning_brief", "vault_cleanup", "research_digest", "continuation_brief", "policy_simulator"}
    assert set(SKILL_REGISTRY.keys()) == expected


def test_get_skill_returns_entry():
    entry = get_skill("morning_brief")
    assert entry.name == "morning_brief"
    assert entry.path.exists()


def test_get_skill_unknown_raises():
    with pytest.raises(ValueError, match="Unknown skill"):
        get_skill("nonexistent_skill")


def test_get_skill_error_lists_available():
    with pytest.raises(ValueError, match="morning_brief"):
        get_skill("bogus")


def test_list_skills_returns_all():
    skills = list_skills()
    assert len(skills) == len(SKILL_REGISTRY)


def test_skill_paths_have_run_py():
    for entry in list_skills():
        run_py = entry.path / "run.py"
        assert run_py.exists(), f"Missing run.py for skill {entry.name!r}"


def test_skill_paths_have_skill_md():
    for entry in list_skills():
        skill_md = entry.path / "SKILL.md"
        assert skill_md.exists(), f"Missing SKILL.md for skill {entry.name!r}"


def test_research_digest_accepts_input():
    entry = get_skill("research_digest")
    assert entry.accepts_input is True


def test_morning_brief_no_input():
    entry = get_skill("morning_brief")
    assert entry.accepts_input is False
