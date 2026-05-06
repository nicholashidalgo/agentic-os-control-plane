# Skill: morning_brief

## Purpose
Generate a morning brief by summarizing recent daily logs from `vault/daily/`.

## Input
None required.

## Output
Writes `vault/daily/morning_brief_{YYYY-MM-DD}.md` containing:
- Date and generation timestamp
- List of recent daily log files found
- Summary of each file's key content (headings and first paragraph)
- Open items detected (lines starting with `- [ ]`)

## Constraints
- Reads only from `vault/daily/`
- Writes only to `vault/daily/`
- Does not modify source files
- No network calls
