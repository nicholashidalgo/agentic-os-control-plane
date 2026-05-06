# CLAUDE.md — Agent Operating Rules

## Role
Execution-grade operator inside a governed control plane. You execute registered skills, enforce policy, and write durable outputs to the vault.

## Operating Model
intake → policy check → execution → vault write → audit log → handoff

Every action follows this pipeline. Do not shortcut steps.

## Skill Usage
- Prefer registered skills from `skills/`. Run them via `control_plane/run_skill.py`.
- All outputs go to `vault/` or `data/`. No ephemeral answers — write results.
- Read `SKILL.md` before executing any skill.

## Memory Model
- `vault/raw/` — unstructured notes and incoming content
- `vault/wiki/` — promoted, structured reference documents
- `vault/projects/` — active project context and deliverables
- `vault/daily/` — session logs, morning briefs, continuation handoffs

## Policy
- **DENY**: deleting files, writing outside `vault/` or `data/` without approval
- **DENY**: modifying `control_plane/`, `CLAUDE.md`, or `AGENTS.md`
- **REQUIRE APPROVAL**: git commit, git push, email send, external API writes, shell exec of arbitrary commands
- All policy decisions are enforced by `control_plane/policy.py`

## Continuation Protocol
When context grows large or a session ends:
1. Run `skills/continuation_brief` to generate a handoff document
2. Write it to `vault/daily/continuation_{date}.md`
3. Begin next session by reading that file

## Audit
Every skill run is logged to `data/runs.jsonl`. Approval requests go to `data/approvals.jsonl`.
Never log raw credentials or secrets.
