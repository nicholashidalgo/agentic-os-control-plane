#!/usr/bin/env python3
# run_skill — governed CLI entrypoint for skill execution
from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from control_plane.audit_log import log_run
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


def _run(args: argparse.Namespace) -> int:
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

    try:
        module = _load_skill_module(entry.path)
        raw_outputs: list[str] = module.run(input_str)
    except Exception as exc:
        run_id = log_run(args.skill, input_str, [], "error", error=str(exc))
        print(f"error: skill execution failed: {exc}", file=sys.stderr)
        print(f"logged as {run_id}", file=sys.stderr)
        return 1

    valid_outputs: list[str] = []
    blocked = False

    for raw_path in raw_outputs:
        safe = _resolve_output_path(raw_path)
        if safe is None:
            log_run(
                args.skill,
                input_str,
                valid_outputs,
                "path_violation",
                error=f"output path rejected: {raw_path!r}",
            )
            print(f"error: output path rejected (traversal or out-of-bounds): {raw_path!r}", file=sys.stderr)
            blocked = True
            break
        valid_outputs.append(str(safe.relative_to(_REPO_ROOT)))

    if blocked:
        return 1

    run_id = log_run(args.skill, input_str, valid_outputs, "success")
    print(f"ok  {run_id}")
    for p in valid_outputs:
        print(f"    wrote: {p}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="run_skill",
        description="Execute a registered skill inside the governed control plane.",
    )
    parser.add_argument("--skill", help="Skill name to execute")
    parser.add_argument("--input", help="Input string passed to the skill")
    parser.add_argument("--list", action="store_true", help="List all registered skills")
    sys.exit(_run(parser.parse_args()))


if __name__ == "__main__":
    main()
