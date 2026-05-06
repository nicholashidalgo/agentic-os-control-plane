# Skill template — copy this file to skills/<your-skill-name>/run.py
#
# CONTRACT:
#   - Define run(input_str: str) -> list[str]
#   - input_str is the value passed via --input (empty string if not provided)
#   - Return a list of output paths, each relative to the repo root
#   - All returned paths MUST start with "vault/" or "data/"
#   - The control plane validates every path before logging; violations exit 1
#
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_OUTPUT_DIR = _REPO_ROOT / "vault" / "projects"


def run(input_str: str) -> list[str]:
    today = date.today().isoformat()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- Read input (if your skill requires one) ---
    # input_path = (_REPO_ROOT / input_str).resolve() if input_str else None
    # source_text = input_path.read_text(encoding="utf-8") if input_path else ""

    # --- Produce output ---
    content = f"""# Skill Output — {today}

_Generated: {now}_

## Result

Replace this with your skill's actual output.
"""

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _OUTPUT_DIR / f"template_output_{today}.md"
    output_path.write_text(content, encoding="utf-8")

    # Return list of paths relative to repo root
    return [str(output_path.relative_to(_REPO_ROOT))]
