# Skill: research_digest

## Purpose
Convert a raw Markdown note into a structured research digest and save it to `vault/wiki/`.

## Input
`--input <path>` — path to a Markdown file in `vault/raw/` (relative to repo root).

## Output
Writes `vault/wiki/digest_{stem}_{YYYY-MM-DD}.md` containing:
- Original title (first H1) or filename as title
- Extraction date and source reference
- Key points (all bullet list items from source)
- All headings preserved as sections
- Full original content appended under "## Source"

## Constraints
- Reads only from the provided input path
- Writes only to `vault/wiki/`
- No network calls
