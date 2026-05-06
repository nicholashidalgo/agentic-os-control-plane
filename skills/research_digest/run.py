# research_digest skill — converts raw note to structured wiki digest
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_WIKI = _REPO_ROOT / "vault" / "wiki"


def run(input_str: str) -> list[str]:
    if not input_str:
        raise ValueError("research_digest requires --input <path to raw note>")

    source_path = (_REPO_ROOT / input_str).resolve()
    content = source_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    today = date.today().isoformat()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    title = next((l.lstrip("# ").strip() for l in lines if l.startswith("# ")), source_path.stem)
    key_points = [l for l in lines if l.startswith("- ") and not l.startswith("- [ ]")]
    headings = [l for l in lines if l.startswith("#")]

    digest_lines = [
        f"# Research Digest: {title}",
        f"\n_Source: {input_str}_  \n_Extracted: {now}_\n",
        "## Key Points",
    ]
    digest_lines += key_points if key_points else ["- (no bullet points in source)"]
    digest_lines += ["\n## Structure"]
    digest_lines += headings if headings else ["- (no headings in source)"]
    digest_lines += ["\n## Source\n", content]

    stem = source_path.stem.replace(" ", "_")
    output_path = _WIKI / f"digest_{stem}_{today}.md"
    output_path.write_text("\n".join(digest_lines), encoding="utf-8")
    return [str(output_path.relative_to(_REPO_ROOT))]
