"""Typer CLI surface for the agentic-os control plane."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from agentic_os.control_plane.registry import list_skills

app = typer.Typer(
    name="agentic-os",
    help="Governed execution layer for workflow automation.",
    no_args_is_help=True,
    add_completion=False,
)

approvals_app = typer.Typer(help="Manage the human approval queue.", no_args_is_help=True)
app.add_typer(approvals_app, name="approvals")


@app.command("list")
def list_cmd() -> None:
    """List all registered skills."""
    for entry in list_skills():
        flag = "[input required]" if entry.accepts_input else "[no input]"
        typer.echo(f"  {entry.name:<22} {flag}  {entry.description}")


@app.command("run")
def run_cmd(
    skill: Annotated[str, typer.Argument(help="Skill name to execute.")],
    input_path: Annotated[
        Optional[str],
        typer.Option("--input", "-i", help="Input value for skills that require one."),
    ] = None,
) -> None:
    """Execute a registered skill through the governed runner."""
    from agentic_os.control_plane.runner import run_skill
    raise typer.Exit(code=run_skill(skill=skill, input_str=input_path or ""))


@approvals_app.command("list")
def approvals_list(
    status: Annotated[
        Optional[str],
        typer.Option("--status", help="pending | approved | denied | expired"),
    ] = None,
) -> None:
    """List approval records."""
    from agentic_os.control_plane.approvals import list_approvals, is_expired
    records = list_approvals(status=status)
    if not records:
        label = f" (status={status})" if status else ""
        typer.echo(f"  no approval records found{label}")
        return
    for r in records:
        exp = " [EXPIRED]" if r.get("status") == "pending" and is_expired(r) else ""
        typer.echo(
            f"  {r['approval_id']}  {r.get('status','?'):<10}"
            f"  skill={r.get('skill','')}  action={r.get('action','')}"
            f"  path={r.get('path') or ''}{exp}"
        )


@approvals_app.command("approve")
def approvals_approve(
    approval_id: Annotated[str, typer.Argument(help="Approval ID.")],
) -> None:
    """Approve a pending approval; rerun the skill if config allows."""
    from agentic_os.control_plane.approvals import resolve_approval
    from agentic_os.control_plane.config import get_config
    from agentic_os.control_plane.runner import run_skill
    resolved = resolve_approval(approval_id, "approved")
    typer.echo(f"  {resolved['approval_id']}  ->  {resolved['status']}")
    if get_config().get("rerun_after_approval", True):
        skill_name = resolved.get("skill", "")
        if skill_name:
            typer.echo(f"  rerunning skill '{skill_name}'...")
            raise typer.Exit(code=run_skill(skill=skill_name, input_str=resolved.get("path") or ""))


@approvals_app.command("deny")
def approvals_deny(
    approval_id: Annotated[str, typer.Argument(help="Approval ID.")],
) -> None:
    """Deny a pending approval."""
    from agentic_os.control_plane.approvals import resolve_approval
    resolved = resolve_approval(approval_id, "denied")
    typer.echo(f"  {resolved['approval_id']}  ->  {resolved['status']}")


if __name__ == "__main__":
    app()
