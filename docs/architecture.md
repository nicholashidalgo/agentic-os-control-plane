# Architecture

## Overview

`agentic-os-control-plane` is a local-first governed execution layer for workflow automation. It separates operator intent from system side effects and forces that work through policy checks, approval routing, bounded write paths, and append-only audit records.

The supported runtime surface lives under `src/agentic_os/`.

## Component Map

```text
agentic-os-control-plane/
├── src/agentic_os/
│   ├── cli.py
│   └── control_plane/
│       ├── approvals.py
│       ├── audit_log.py
│       ├── config.py
│       ├── policy.py
│       ├── registry.py
│       └── runner.py
├── skills/
│   ├── <name>/SKILL.md
│   └── <name>/run.py
├── vault/
│   ├── raw/
│   ├── wiki/
│   ├── projects/
│   └── daily/
└── data/
    ├── approvals.jsonl
    └── runs.jsonl
```

## Execution Flow

1. An operator invokes `agentic-os run <skill>` or `python -m agentic_os.cli run <skill>`.
2. The CLI resolves the skill through `registry.py`.
3. `runner.py` loads the skill implementation from `skills/<name>/run.py`.
4. The skill returns repository-relative output paths.
5. `runner.py` validates each output path against the configured allowed prefixes.
6. If a proposed action is outside approved bounds, policy returns `REQUIRE_APPROVAL` or `DENY`.
7. Successful executions append a durable record to `data/runs.jsonl`.
8. Approval-required actions append a durable record to `data/approvals.jsonl`.

## Policy Gate Table

| Action | Path condition | Decision |
| --- | --- | --- |
| `FILE_READ` | any | `ALLOW` |
| `FILE_WRITE` | starts with `vault/` or `data/` | `ALLOW` |
| `FILE_WRITE` | protected control surfaces | `DENY` |
| `FILE_WRITE` | any other path | `REQUIRE_APPROVAL` |
| `FILE_DELETE` | any | `REQUIRE_APPROVAL` |
| `GIT_COMMIT` | any | `REQUIRE_APPROVAL` |
| `GIT_PUSH` | any | `REQUIRE_APPROVAL` |
| `EMAIL_SEND` | any | `REQUIRE_APPROVAL` |
| `API_WRITE` | any | `REQUIRE_APPROVAL` |
| `SHELL_EXEC` | any | `REQUIRE_APPROVAL` |

## Vault Model

| Path | Purpose |
| --- | --- |
| `vault/raw/` | incoming unstructured notes |
| `vault/wiki/` | promoted reference material |
| `vault/projects/` | active project outputs |
| `vault/daily/` | dated handoffs, briefs, and logs |

The vault model keeps durable workflow artifacts separate from the codebase while still inside approved write boundaries.

## Operational Characteristics

- **Approval-aware**: high-risk actions are routed, not silently blocked.
- **Path-bounded**: outputs are constrained to governed repository zones.
- **Append-only**: runs and approvals are written as immutable log records.
- **Inspectable**: both business-facing documentation and machine-readable records are present in the same repository.
