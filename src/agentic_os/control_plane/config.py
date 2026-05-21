# config — load config.yaml with fallback to config.example.yaml and safe defaults
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_DEFAULTS: dict = {
    "vault_path": "vault",
    "data_path": "data",
    "logs_path": "logs",
    "default_output_folder": "vault/projects",
    "require_approval_for_destructive_actions": True,
    "allow_demo_skills": True,
    "approval_timeout_hours": 24,
    "rerun_after_approval": True,
}


def _load_yaml(path: Path) -> dict:
    try:
        import yaml  # PyYAML — listed in requirements.txt
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_config() -> dict:
    """Return merged config: config.yaml → config.example.yaml → built-in defaults."""
    config = dict(_DEFAULTS)

    example = _REPO_ROOT / "config.example.yaml"
    if example.exists():
        config.update(_load_yaml(example))

    live = _REPO_ROOT / "config.yaml"
    if live.exists():
        config.update(_load_yaml(live))

    return config
