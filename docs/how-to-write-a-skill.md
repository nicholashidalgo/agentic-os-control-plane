# How to Write a Skill

## 1. Skill contract

Every skill is a directory under `skills/<name>/` containing exactly two files:

| File | Role |
|------|------|
| `SKILL.md` | Human- and agent-readable contract. Read by Claude Code and OpenAI Codex before execution. |
| `run.py` | Python implementation. Must define `run(input_str: str) -> list[str]`. |

`SKILL.md` must contain these sections:

- **Purpose** — what the skill does and why
- **Inputs** — what `--input` expects, or "None required"
- **Outputs** — every file the skill may write, with path pattern
- **Allowed Actions** — FILE_READ, FILE_WRITE (to vault/ or data/ only)
- **Blocked Actions** — what this skill explicitly will not do
- **Confirmation Required** — Yes or No, and why
- **Output Structure** — format of the output file(s)

Agents read `SKILL.md` before calling `run_skill.py`. Keep it accurate — it is the source of truth for what a skill does.

## 2. run.py interface

```python
def run(input_str: str) -> list[str]:
    ...
    return ["vault/projects/my_output_2026-01-01.md"]
```

- `input_str` — the value passed via `--input`, or an empty string if omitted
- Return value — a list of output paths, **each relative to the repo root**
- Every returned path must start with `vault/` or `data/`
- The control plane resolves and validates every path before logging; any path outside these prefixes causes the run to exit 1 and log a `path_violation`
- Never return absolute paths; never use `../`

Use `Path(__file__).resolve().parent.parent.parent` to reach the repo root from inside a skill:

```python
from pathlib import Path
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_OUTPUT_DIR = _REPO_ROOT / "vault" / "projects"
```

## 3. Registering a skill

Add an entry to `SKILL_REGISTRY` in `control_plane/registry.py`:

```python
from control_plane.registry import SkillEntry

SKILL_REGISTRY["my_skill"] = SkillEntry(
    name="my_skill",
    path=_SKILLS_ROOT / "my_skill",
    accepts_input=True,          # False if --input is not used
    description="One-line description shown by --list",
)
```

After adding the entry, verify it appears:

```bash
python control_plane/run_skill.py --list
```

## 4. Policy rules

The policy engine in `control_plane/policy.py` governs what skills are allowed to do. You cannot override it from inside a skill.

| Action | Decision |
|--------|----------|
| `FILE_READ` | Always ALLOW |
| `FILE_WRITE` → `vault/` or `data/` | ALLOW |
| `FILE_WRITE` → `control_plane/`, `CLAUDE.md`, `AGENTS.md` | DENY |
| `FILE_WRITE` → any other path | REQUIRE APPROVAL |
| `FILE_DELETE` | REQUIRE APPROVAL |
| `GIT_COMMIT`, `GIT_PUSH` | REQUIRE APPROVAL |
| `EMAIL_SEND`, `API_WRITE`, `SHELL_EXEC` | REQUIRE APPROVAL |

Skills that return paths outside `vault/` or `data/` are blocked by `run_skill.py` before any write occurs — the policy check happens at the path level, not inside `run()`. Keep all output paths inside the permitted prefixes.

## 5. Testing your skill

Use `tmp_path` (pytest built-in fixture) to avoid writing into the live vault during tests. Load the skill module dynamically the same way `run_skill.py` does:

```python
import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

def _load_skill(name: str):
    skill_path = _REPO_ROOT / "skills" / name / "run.py"
    spec = importlib.util.spec_from_file_location("skill_run", skill_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_my_skill_writes_output(tmp_path):
    module = _load_skill("my_skill")
    # Monkeypatch _REPO_ROOT inside the module if needed, or
    # pass a tmp_path-based input and check the returned path list.
    outputs = module.run("")
    assert len(outputs) == 1
    assert outputs[0].startswith("vault/")
```

Check that:
- The returned list has the expected number of paths
- Every path starts with `vault/` or `data/`
- The output file exists and contains expected content
- Passing an empty input raises `ValueError` if the skill requires `--input`

## 6. Example — a complete minimal skill

**`skills/word_count/SKILL.md`**

```markdown
# Skill: word_count

## Purpose
Count words in a raw vault note and write a summary to vault/projects/.

## Inputs
`--input <path>` — path to a Markdown file in vault/raw/, relative to repo root.

## Outputs
- `vault/projects/wordcount_{stem}_{date}.md` — word count summary

## Allowed Actions
- FILE_READ — reads the input file
- FILE_WRITE — writes to vault/projects/

## Blocked Actions
- All others

## Confirmation Required
No

## Output Structure
# Word Count: {filename}
Words: {count}
Lines: {count}
```

**`skills/word_count/run.py`**

```python
from __future__ import annotations
from datetime import date, datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_OUTPUT_DIR = _REPO_ROOT / "vault" / "projects"

def run(input_str: str) -> list[str]:
    if not input_str:
        raise ValueError("word_count requires --input <path to file>")

    source = (_REPO_ROOT / input_str).resolve()
    text = source.read_text(encoding="utf-8")
    words = len(text.split())
    lines = text.count("\n")

    today = date.today().isoformat()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    content = f"# Word Count: {source.name}\n\n_Generated: {now}_\n\nWords: {words}\nLines: {lines}\n"

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = _OUTPUT_DIR / f"wordcount_{source.stem}_{today}.md"
    output.write_text(content, encoding="utf-8")
    return [str(output.relative_to(_REPO_ROOT))]
```

**`control_plane/registry.py` entry**

```python
"word_count": SkillEntry(
    name="word_count",
    path=_SKILLS_ROOT / "word_count",
    accepts_input=True,
    description="Counts words and lines in a vault/raw/ note.",
),
```

**`tests/test_word_count.py`**

```python
import importlib.util
from pathlib import Path
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent

def _load():
    spec = importlib.util.spec_from_file_location(
        "skill_run", _REPO_ROOT / "skills" / "word_count" / "run.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def test_no_input_raises():
    with pytest.raises(ValueError):
        _load().run("")

def test_output_path_in_vault(tmp_path):
    sample = _REPO_ROOT / "vault" / "raw" / "sample_note.md"
    outputs = _load().run(str(sample.relative_to(_REPO_ROOT)))
    assert outputs[0].startswith("vault/projects/")
```
