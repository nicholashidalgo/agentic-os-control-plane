# Skill: vault_cleanup

## Purpose
Promote structured notes from `vault/raw/` to `vault/wiki/` and write a cleanup report.

## Input
None required.

## Promotion Criteria
A file in `vault/raw/` is promoted if it contains **2 or more Markdown headings** (lines starting with `#`). Promoted files are copied to `vault/wiki/` with their original filename. The source file in `vault/raw/` is left in place.

## Output
- Promoted files written to `vault/wiki/`
- Cleanup report written to `vault/daily/vault_cleanup_{YYYY-MM-DD}.md`

## Constraints
- Reads from `vault/raw/`
- Writes only to `vault/wiki/` and `vault/daily/`
- Does not delete source files
- No network calls
