# Getting Started

## 1. Prerequisites

- Python 3.12 or later
- basic shell access

## 2. Install

```bash
chmod +x install.sh
./install.sh
```

`install.sh` creates required directories, copies `config.example.yaml` to `config.yaml` on first run, installs Python dependencies, and installs the local package in editable mode.

## 3. Configure

Open `config.yaml` and adjust paths or behavior as needed:

```yaml
vault_path: vault
data_path: data
logs_path: logs
default_output_folder: vault/projects
require_approval_for_destructive_actions: true
allow_demo_skills: true
approval_timeout_hours: 24
rerun_after_approval: true
```

All paths are relative to the repository root unless you override them deliberately.

## 4. List the available skills

```bash
agentic-os list
```

Module form:

```bash
PYTHONPATH=src python -m agentic_os.cli list
```

## 5. Run a skill

```bash
agentic-os run morning_brief
agentic-os run research_digest --input vault/raw/sample_note.md
agentic-os run policy_simulator --input vault/raw/sample_action_manifest.json
```

Expected success output:

```text
ok  RUN-20260505-211446
    wrote: vault/daily/morning_brief_2026-05-05.md
```

## 6. Inspect approvals

```bash
agentic-os approvals list --status pending
```

Approve or deny a pending record:

```bash
agentic-os approvals approve APR-20260505-a3f1c9
agentic-os approvals deny APR-20260505-a3f1c9
```

## 7. Inspect the audit log

Every execution appends a JSON line to `data/runs.jsonl`:

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

## 8. Create a new skill

```bash
cp -r skills/template skills/my_skill
```

Then:

1. define the contract in `skills/my_skill/SKILL.md`
2. implement `run(input_str: str) -> list[str]` in `skills/my_skill/run.py`
3. register the skill in `src/agentic_os/control_plane/registry.py`
4. run `agentic-os list` to confirm registration

See [docs/how-to-write-a-skill.md](how-to-write-a-skill.md) for the full authoring guide.
