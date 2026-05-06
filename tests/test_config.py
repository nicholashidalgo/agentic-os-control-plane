import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from control_plane.config import get_config


def test_get_config_returns_dict():
    result = get_config()
    assert isinstance(result, dict)


def test_vault_path_key_exists_and_is_string():
    result = get_config()
    assert "vault_path" in result
    assert isinstance(result["vault_path"], str)


def test_data_path_key_exists_and_is_string():
    result = get_config()
    assert "data_path" in result
    assert isinstance(result["data_path"], str)


def test_require_approval_is_bool():
    result = get_config()
    assert "require_approval_for_destructive_actions" in result
    assert isinstance(result["require_approval_for_destructive_actions"], bool)


def test_allow_demo_skills_is_bool():
    result = get_config()
    assert "allow_demo_skills" in result
    assert isinstance(result["allow_demo_skills"], bool)


def test_get_config_does_not_crash_when_config_yaml_absent(tmp_path, monkeypatch):
    # Point the config module's _REPO_ROOT to a temp dir with no yaml files
    import control_plane.config as cfg_module
    monkeypatch.setattr(cfg_module, "_REPO_ROOT", tmp_path)
    result = cfg_module.get_config()
    assert isinstance(result, dict)
    assert result.get("vault_path") == "vault"
    assert result.get("data_path") == "data"


def test_get_config_uses_example_yaml_as_fallback(tmp_path, monkeypatch):
    import control_plane.config as cfg_module
    example = tmp_path / "config.example.yaml"
    example.write_text("vault_path: custom_vault\ndata_path: custom_data\n")
    monkeypatch.setattr(cfg_module, "_REPO_ROOT", tmp_path)
    result = cfg_module.get_config()
    assert result["vault_path"] == "custom_vault"
    assert result["data_path"] == "custom_data"


def test_config_yaml_overrides_example(tmp_path, monkeypatch):
    import control_plane.config as cfg_module
    (tmp_path / "config.example.yaml").write_text("vault_path: example_vault\n")
    (tmp_path / "config.yaml").write_text("vault_path: live_vault\n")
    monkeypatch.setattr(cfg_module, "_REPO_ROOT", tmp_path)
    result = cfg_module.get_config()
    assert result["vault_path"] == "live_vault"
