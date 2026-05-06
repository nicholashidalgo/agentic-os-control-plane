# Architecture

## Overview

`agentic-os-control-plane` is a local-first governed execution layer. It provides a common runtime that two different agent clients — Claude Code and OpenAI Codex — can both use. The control plane enforces a shared policy contract, routes skill output to a structured vault, and maintains a full append-only audit trail. No network calls are made; all state lives on disk.

---

## Component Map

```
agentic-os-control-plane/
│
├── CLAUDE.md / AGENTS.md       ← agent instruction files (one per client)
│
├── control_plane/
│   ├── run_skill.py            ← CLI entrypoint and orchestrator
│   ├── registry.py             ← skill catalog (name → SkillEntry)
│   ├── policy.py               ← policy engine (check_action, check_content_for_secrets)
│   └── audit_log.py            ← append-only JSONL writer
│
├── skills/
│   ├── <name>/SKILL.md         ← skill contract (purpose, inputs, outputs, constraints)
│   └── <name>/run.py           ← implementation: run(input_str) -> list[str]
│
├── vault/
│   ├── raw/                    ← unstructured incoming notes
│   ├── wiki/                   ← promoted structured documents
│   ├── projects/               ← active project deliverables
│   └── daily/                  ← session logs, briefs, handoffs
│
└── data/
    ├── runs.jsonl              ← skill execution log (append-only)
    └── approvals.jsonl         ← approval request log (append-only)
```

---

## Skill Execution Flow

1. Agent (Claude Code or Codex) reads its instruction file (`CLAUDE.md` or `AGENTS.md`) and resolves the skill name to run.
2. Agent invokes `python control_plane/run_skill.py --skill <name> [--input <value>]`.
3. `run_skill.py` calls `registry.get_skill(name)` — raises `ValueError` with available list on miss.
4. `run_skill.py` checks whether `--input` is required (from `SkillEntry.accepts_input`) and exits 2 if missing.
5. `run_skill.py` dynamically loads `skills/<name>/run.py` and calls `run(input_str)`.
6. The skill executes and returns a list of output path strings (relative to repo root).
7. `run_skill.py` resolves each returned path against the repo root and confirms it falls under `vault/` or `data/`. Any path that escapes this boundary (traversal, absolute path, other prefix) is rejected: the run is logged with `status: "path_violation"` and the process exits 1. No write occurs.
8. `audit_log.log_run()` appends a record to `data/runs.jsonl` with the run ID, skill name, SHA-256 input hash, output paths, status, and timestamp.
9. `run_skill.py` prints the run ID and written paths to stdout and exits 0.

**Policy gate (step 5–7 detail):** `check_action()` is called for any action a skill declares before performing it. For `FILE_WRITE`, the path is checked against `BLOCKED_WRITE_PREFIXES` first (DENY), then `ALLOWED_WRITE_PREFIXES` (ALLOW), then falls through to REQUIRE\_APPROVAL. `check_content_for_secrets()` is called before any content is passed to `audit_log` to prevent credential leakage into `runs.jsonl`.

---

## Policy Gate Table

| Action | Path condition | Decision |
|--------|---------------|----------|
| `FILE_READ` | any | ALLOW |
| `FILE_WRITE` | starts with `vault/` or `data/` | ALLOW |
| `FILE_WRITE` | starts with `control_plane/`, `CLAUDE.md`, or `AGENTS.md` | DENY |
| `FILE_WRITE` | any other path | REQUIRE APPROVAL |
| `FILE_DELETE` | any | REQUIRE APPROVAL |
| `GIT_COMMIT` | — | REQUIRE APPROVAL |
| `GIT_PUSH` | — | REQUIRE APPROVAL |
| `EMAIL_SEND` | — | REQUIRE APPROVAL |
| `API_WRITE` | — | REQUIRE APPROVAL |
| `SHELL_EXEC` | — | REQUIRE APPROVAL |

---

## Memory Model

The vault uses a three-tier promotion model:

**`vault/raw/`** — Landing zone for unstructured content. Notes arrive here without curation. Agents and humans can drop Markdown files freely. Nothing in `raw/` is modified by the control plane.

**`vault/wiki/`** — Promoted reference documents. The `vault_cleanup` skill scans `raw/` and copies any file containing two or more Markdown headings to `wiki/`. Source files remain in `raw/`. The threshold is intentionally simple so promotion behaviour is predictable and auditable.

**`vault/projects/`** — Active workstream context. Skills that produce deliverables tied to an ongoing initiative write here. The `policy_simulator` skill writes its reports here.

**`vault/daily/`** — Session-scoped documents. Morning briefs, vault cleanup reports, continuation handoffs, and policy simulation logs all land in `daily/` with date-stamped filenames. At session start, an agent reads the latest continuation brief; at session end, it runs `continuation_brief` to write a handoff for the next session.

---

## Agent Instruction File Comparison

| Attribute | `CLAUDE.md` | `AGENTS.md` |
|-----------|-------------|-------------|
| Target client | Claude Code (Anthropic CLI) | OpenAI Codex CLI |
| Role | Execution-grade operator inside a governed control plane | Execution-grade operator inside a governed control plane |
| Memory rules | raw/ → wiki/ → projects/, daily/ for session logs | Identical structure |
| Skill invocation | `python control_plane/run_skill.py --skill <name>` | `python control_plane/run_skill.py --skill <name>` |
| Read SKILL.md first | Stated in operating model | Explicitly required — "no exceptions" |
| Protected files | May not write `control_plane/`, `CLAUDE.md`, `AGENTS.md` | May not modify `CLAUDE.md`, `AGENTS.md`, or any file in `control_plane/` |
| Git commands | Require approval; policy enforced | Prohibited unless explicitly requested in the current message |
| Continuation protocol | Run `continuation_brief` when context grows; write to `vault/daily/` | Identical |
| Policy enforcement | Via `policy.py` at runtime | Same runtime; identical rules |
