# Skill: <your-skill-name>

> This file is read by Claude Code and OpenAI Codex before execution.
> Fill in every section. Keep descriptions concrete and accurate.

## Purpose
One paragraph describing what this skill does, why it exists, and what problem it solves.

## Inputs
`--input <value>` — describe what the input string represents.  
Leave blank or write "None required" if the skill takes no input.

## Outputs
List every file this skill may write, with path pattern and description:
- `vault/projects/<output-name>_{date}.md` — description of what this file contains

All output paths must fall under `vault/` or `data/`. The control plane rejects any path outside these prefixes.

## Allowed Actions
- FILE_READ — reading source files from vault/
- FILE_WRITE — writing output to vault/projects/

## Blocked Actions
- FILE_DELETE — never deletes files
- GIT_COMMIT, GIT_PUSH — no git operations
- SHELL_EXEC — no shell commands
- EMAIL_SEND, API_WRITE — no external calls

## Confirmation Required
No — this skill runs without user confirmation.  
(Change to "Yes" and describe the prompt if your skill performs destructive or external actions.)

## Output Structure
Describe the format of the output file(s):

```
# Title — {date}

_Generated: {timestamp}_

## Section 1
...

## Section 2
...
```
