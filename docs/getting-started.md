# Getting Started

## 1. Prerequisites

- Python 3.12 or later
- `git`
- Basic terminal comfort (cd, chmod, pip)

## 2. Install

```bash
git clone https://github.com/nicholashidalgo/agentic-os-control-plane
cd agentic-os-control-plane
chmod +x install.sh
./install.sh
```

`install.sh` creates required directories (`vault/`, `data/`, `logs/`), copies `config.example.yaml` to `config.yaml` on first run, and installs Python dependencies. It is safe to rerun — it never overwrites an existing `config.yaml`.

## 3. Configure

Open `config.yaml` in any editor:

```yaml
vault_path: vault                              # where the memory vault lives
data_path: data                                # where audit logs are written
logs_path: logs                                # where runtime logs go
default_output_folder: vault/projects          # default skill output location
require_approval_for_destructive_actions: true # gate FILE_DELETE, GIT_COMMIT, etc.
allow_demo_skills: true                        # enable the bundled demo skills
```

All paths are relative to the repo root. Change `vault_path` if you want skills to write into a directory outside the repo (not recommended for first-time use).

## 4. Run a demo skill

```bash
# Generate a morning brief from recent daily logs
python control_plane/run_skill.py --skill morning_brief

# Convert a raw note into a structured wiki digest
python control_plane/run_skill.py --skill research_digest --input vault/raw/sample_note.md

# Simulate policy decisions for a batch of proposed actions
python control_plane/run_skill.py --skill policy_simulator --input vault/raw/sample_action_manifest.json
```

List all registered skills:

```bash
python control_plane/run_skill.py --list
```

Each run prints the run ID and the paths it wrote:

```
ok  RUN-20260505-211446
    wrote: vault/daily/morning_brief_2026-05-05.md
```

## 5. Inspect the audit log

Every run appends one JSON line to `data/runs.jsonl`:

```bash
cat data/runs.jsonl
```

Example record:

```json
{
  "run_id": "RUN-20260505-211446",
  "skill": "morning_brief",
  "inputs_hash": "e3b0c44298fc",
  "outputs": ["vault/daily/morning_brief_2026-05-05.md"],
  "status": "success",
  "timestamp": "2026-05-05T21:14:46.612285+00:00"
}
```

| Field | Meaning |
|-------|---------|
| `run_id` | Unique ID for this execution — format `RUN-YYYYMMDD-HHMMSS` |
| `skill` | Name of the skill that ran |
| `inputs_hash` | First 12 hex chars of SHA-256 of the input string — raw input is never stored |
| `outputs` | List of paths written by the skill |
| `status` | `success`, `error`, or `path_violation` |
| `timestamp` | UTC ISO-8601 timestamp |

## 6. Create your own skill

```bash
# 1. Copy the template
cp -r skills/template skills/my_skill

# 2. Fill in the contract
#    Open skills/my_skill/SKILL.md and describe your skill's
#    purpose, inputs, outputs, and constraints.

# 3. Implement the logic
#    Edit skills/my_skill/run.py. The only required interface is:
#    def run(input_str: str) -> list[str]

# 4. Register it
#    Add an entry to SKILL_REGISTRY in control_plane/registry.py

# 5. Run it
python control_plane/run_skill.py --skill my_skill
```

See [how-to-write-a-skill.md](how-to-write-a-skill.md) for the full skill contract, path rules, and a complete worked example.

## 7. Next steps

- [how-to-write-a-skill.md](how-to-write-a-skill.md) — complete skill authoring guide
- [architecture.md](architecture.md) — component map, execution flow, memory model
- [security-model.md](security-model.md) — policy matrix, write paths, secret detection
- [roadmap.md](roadmap.md) — planned features (approval workflow, dashboard, MCP)
