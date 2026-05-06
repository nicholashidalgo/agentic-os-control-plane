# Skill: policy_simulator

## Purpose
Accept a JSON action manifest, run each action through `policy.py`, and write a Markdown report summarizing the policy decision for each entry.

## Input
`--input <path>` — path to a JSON manifest file (relative to repo root).

Manifest format:
```json
[
  {"action": "file_write", "path": "vault/wiki/example.md"},
  {"action": "git_commit"},
  {"action": "file_read", "path": "vault/raw/note.md"}
]
```

Supported action strings (case-insensitive): `file_read`, `file_write`, `file_delete`, `git_commit`, `git_push`, `email_send`, `api_write`, `shell_exec`. Unknown strings → DENY with reason "unrecognized action".

## Output
Writes `vault/projects/policy_simulation_{YYYY-MM-DD}.md` containing:
- Date and input file reference
- Summary table: Action | Path | Decision | Reason
- Totals line: X allowed / Y require approval / Z denied

## Constraints
- Reads the manifest file from the path provided via `--input`
- Writes only to `vault/projects/`
- No network calls
- No side effects — policy is evaluated read-only against `policy.py`
