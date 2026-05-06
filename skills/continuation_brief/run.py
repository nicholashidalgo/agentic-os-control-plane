# continuation_brief skill — writes session handoff template to vault/daily/
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DAILY = _REPO_ROOT / "vault" / "daily"


def run(input_str: str) -> list[str]:
    today = date.today().isoformat()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    description = input_str.strip() if input_str.strip() else "_(no description provided)_"

    content = f"""# Continuation Brief — {today}

_Generated: {now}_
_Session: {description}_

---

## Current Focus
<!-- What was the primary goal of this session? -->


## Open Tasks
- [ ]
- [ ]

## Key Decisions
<!-- Decisions made this session that affect future work -->


## Next Steps
1.
2.

## Files Changed
<!-- List key files modified or created -->


## Context to Reload
<!-- Links to vault docs, project files, or daily logs needed next session -->
- vault/daily/{today}.md

---
_Resume next session by reading this file first._
"""

    output_path = _DAILY / f"continuation_{today}.md"
    output_path.write_text(content, encoding="utf-8")
    return [str(output_path.relative_to(_REPO_ROOT))]
