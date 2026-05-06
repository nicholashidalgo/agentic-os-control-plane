# vault_cleanup skill — promotes structured raw notes to vault/wiki/
from __future__ import annotations

import shutil
from datetime import date, datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_RAW = _REPO_ROOT / "vault" / "raw"
_WIKI = _REPO_ROOT / "vault" / "wiki"
_DAILY = _REPO_ROOT / "vault" / "daily"
_HEADING_THRESHOLD = 2


def _heading_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("#"))


def run(input_str: str) -> list[str]:
    today = date.today().isoformat()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    written: list[str] = []
    promoted: list[str] = []
    skipped: list[str] = []

    for md_file in sorted(_RAW.glob("*.md")):
        if _heading_count(md_file) >= _HEADING_THRESHOLD:
            dest = _WIKI / md_file.name
            shutil.copy2(md_file, dest)
            promoted.append(md_file.name)
            written.append(str(dest.relative_to(_REPO_ROOT)))
        else:
            skipped.append(md_file.name)

    lines = [
        f"# Vault Cleanup Report — {today}",
        f"\n_Generated: {now}_\n",
        f"## Promoted to vault/wiki/ ({len(promoted)})",
    ]
    lines += [f"- {f}" for f in promoted] or ["- none"]
    lines += [f"\n## Skipped — below heading threshold ({len(skipped)})"]
    lines += [f"- {f}" for f in skipped] or ["- none"]

    report_path = _DAILY / f"vault_cleanup_{today}.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    written.append(str(report_path.relative_to(_REPO_ROOT)))
    return written
