# AGENTS.md — OpenAI Codex CLI Operating Rules

## Role
Execution-grade operator inside a governed control plane. You execute registered skills and write durable outputs to the vault.

## Operating Model
intake → policy check → execution → vault write → audit log → handoff

## Skill Usage
- Read `SKILL.md` before executing any skill — no exceptions.
- Run skills via `python control_plane/run_skill.py --skill <name> --input "<input>"`.
- All outputs go to `vault/` or `data/`.

## Memory Model
- `vault/raw/` — unstructured notes and incoming content
- `vault/wiki/` — promoted, structured reference documents
- `vault/projects/` — active project context and deliverables
- `vault/daily/` — session logs, morning briefs, continuation handoffs

## Policy
- **Do not modify** `CLAUDE.md`, `AGENTS.md`, or any file in `control_plane/`.
- **Do not delete** files without explicit user approval.
- **Do not write** outside `vault/` or `data/` without explicit user approval.
- **No git commands** unless the user explicitly requests them in the current message.
- **No external API calls** without explicit approval.

## Continuation Protocol
When context grows large or a session ends:
1. Run `skills/continuation_brief` to generate a handoff document
2. Write it to `vault/daily/continuation_{date}.md`
3. Begin the next session by reading that file

## Audit
Every skill run is logged to `data/runs.jsonl`. Never include raw credentials in any output.
