# Security Model

## Design Principles

**Local-first.** No network calls in production code. All data — vault content, audit logs, manifests — lives on the local filesystem. There is no external service to compromise or misconfigure.

**Least privilege by path.** Skills may only write to `vault/` and `data/`. Every other path requires explicit approval or is blocked unconditionally. The control plane validates output paths after execution, before logging, and rejects any path that escapes the permitted prefixes.

**Approval gates for consequential actions.** Actions that are hard to reverse or that affect shared state (git commits, pushes, email, external API writes, arbitrary shell execution, file deletion) are categorised as REQUIRE\_APPROVAL. In v0.1 this means the run is logged with the action flagged; interactive approval flow is planned for v0.2.

**Heuristic secret blocking.** Content is scanned for common credential patterns before being written to the audit log. This prevents accidental credential leakage into `runs.jsonl`. The scanner is a heuristic — see the Secret Detection section for its scope and known limitations.

**No implicit trust.** Skills are not trusted to self-report what they write. The control plane independently validates every output path returned by a skill against the permitted prefixes. A skill claiming to write to `vault/wiki/note.md` but returning `../../etc/cron.d/evil` will be rejected before any write occurs.

---

## Approved Write Paths

| Path prefix | Rationale |
|-------------|-----------|
| `vault/` | Agent memory store — all tiers (raw, wiki, projects, daily) |
| `data/` | Structured audit data — runs.jsonl, approvals.jsonl |

All other write paths require approval (`REQUIRE_APPROVAL`) unless they match a blocked prefix, in which case they are unconditionally denied.

---

## Unconditionally Blocked Write Paths

| Path | Rationale |
|------|-----------|
| `control_plane/` | Core runtime — must not be modified by agents |
| `CLAUDE.md` | Agent instruction file — authoritative, agent-immutable |
| `AGENTS.md` | Agent instruction file — authoritative, agent-immutable |

---

## Approval-Required Actions

| Action | Reason |
|--------|--------|
| `FILE_DELETE` | Irreversible; no recycle bin |
| `GIT_COMMIT` | Mutates shared history |
| `GIT_PUSH` | Affects remote repository visible to others |
| `EMAIL_SEND` | External, visible, hard to retract |
| `API_WRITE` | External side effect with unknown blast radius |
| `SHELL_EXEC` | Arbitrary process execution; cannot be policy-checked in advance |
| `FILE_WRITE` to unlisted path | Outside approved prefixes; intent is ambiguous |

---

## Secret Detection

`check_content_for_secrets()` in `policy.py` is a **heuristic scanner**. It is not a substitute for dedicated secret scanning in CI/CD (e.g. `trufflehog`, `gitleaks`, `detect-secrets`). Its sole purpose is to prevent common credential patterns from being written into `data/runs.jsonl`.

**Patterns detected:**

| Pattern | Examples matched |
|---------|-----------------|
| Assignment with credential keyword | `api_key=abc123xyz`, `password: hunter2abc`, `token=ghp_...`, `secret=...`, `credential=...` |
| OpenAI-style secret key | `sk-` followed by 20+ alphanumeric characters |
| GitHub personal access token | `ghp_` followed by exactly 36 alphanumeric characters |
| HTTP Bearer token | `Bearer ` followed by 20+ token characters |

**Known false positives:** The keyword pattern matches `api_key`, `api-key`, `secret`, `token`, `password`, `passwd`, and `credential` as substrings before an `=` or `:`. A line like `credential=my_long_username` (not a secret) will trigger a DENY. This is acceptable in v0.1 — false positives cause a log entry to be withheld, not a skill to fail.

---

## Approval Lifecycle

When a skill's output path or action triggers `REQUIRE_APPROVAL`, the control plane halts execution and creates a structured approval record in `data/approvals.jsonl`. The record progresses through the following states:

| Status | Meaning |
|--------|---------|
| `pending` | Created by the control plane; awaiting human decision |
| `approved` | Resolved by a user; skill may rerun if `rerun_after_approval: true` |
| `denied` | Explicitly rejected; skill does not rerun |
| `expired` | Not resolved before `expires_at`; treated as denied |

**Append-only records.** No existing line in `approvals.jsonl` is ever modified. Each state transition appends a new record with the same `approval_id`. The most recent record for a given `approval_id` is the authoritative state.

**Expiry.** The `expires_at` field is set to `created_at + approval_timeout_hours` (default 24 hours, configurable in `config.yaml`). `resolve_approval()` automatically downgrades an approved decision to `expired` if the deadline has passed.

**Inspection and resolution via CLI:**

```bash
# List all pending approvals
python control_plane/run_skill.py --approvals list --status pending

# Approve and rerun
python control_plane/run_skill.py --approvals approve APR-20260505-a3f1c9

# Deny
python control_plane/run_skill.py --approvals deny APR-20260505-a3f1c9
```

---

## What Is Not Protected

- **Vault content is plain Markdown.** Files in `vault/` are not encrypted or access-controlled. Anyone with filesystem access can read or edit them directly.
- **No process-level sandbox.** Skills run as Python functions in the same process as the control plane. A malicious or buggy skill can still make direct filesystem or network calls that bypass `check_action()`. The policy layer is a governance contract, not a kernel-level restriction.
- **No authentication layer.** There is no user authentication, session management, or multi-user access control. v0.1 assumes a single trusted local user.
- **No integrity verification on vault files.** The audit log records what paths were written, but does not hash or sign vault content. A file could be modified after a run without the change appearing in `runs.jsonl`.
