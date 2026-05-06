# Skill: continuation_brief

## Purpose
Write a session handoff document to `vault/daily/` so the next agent session can resume without losing context.

## Input
None required. Optionally pass a short description of the current session via `--input`.

## Output
Writes `vault/daily/continuation_{YYYY-MM-DD}.md` containing:
- Session date and timestamp
- Optional session description (from --input)
- Handoff template sections: Current Focus, Open Tasks, Key Decisions, Next Steps, Files Changed

## Constraints
- Writes only to `vault/daily/`
- No network calls
