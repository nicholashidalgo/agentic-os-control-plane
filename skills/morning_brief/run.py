# morning_brief skill — summarizes recent vault/daily/ logs
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DAILY = _REPO_ROOT / "vault" / "daily"
_MAX_LOGS = 7


def _summarize(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    headings = [l for l in lines if l.startswith("#")]
    open_items = [l for l in lines if l.startswith("- [ ]")]
    body = "\n".join(headings[:4])
    if open_items:
        body += "\n\nOpen items:\n" + "\n".join(open_items[:5])
    return body or "(no structured content)"


def run(input_str: str) -> list[str]:
    today = date.today().isoformat()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    logs = sorted(
        [f for f in _DAILY.glob("*.md") if not f.name.startswith("morning_brief")],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:_MAX_LOGS]

    sections: list[str] = [f"# Morning Brief — {today}\n\n_Generated: {now}_\n"]

    if not logs:
        sections.append("\n_No daily logs found in vault/daily/_\n")
    else:
        sections.append(f"\n## Recent Logs ({len(logs)} files)\n")
        for log in logs:
            sections.append(f"\n### {log.name}\n\n{_summarize(log)}\n")

    output_path = _DAILY / f"morning_brief_{today}.md"
    output_path.write_text("\n".join(sections), encoding="utf-8")
    return [str(output_path.relative_to(_REPO_ROOT))]
