# policy — action policy engine for the control plane
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto


class ActionType(Enum):
    FILE_DELETE = auto()
    FILE_WRITE = auto()
    FILE_READ = auto()
    GIT_COMMIT = auto()
    GIT_PUSH = auto()
    EMAIL_SEND = auto()
    API_WRITE = auto()
    SHELL_EXEC = auto()


class PolicyDecision(Enum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


@dataclass(frozen=True)
class PolicyResult:
    decision: PolicyDecision
    reason: str


ALLOWED_WRITE_PREFIXES = ("vault/", "data/")
BLOCKED_WRITE_PREFIXES = ("control_plane/", "CLAUDE.md", "AGENTS.md")

_REQUIRE_APPROVAL_ACTIONS = {
    ActionType.FILE_DELETE,
    ActionType.GIT_COMMIT,
    ActionType.GIT_PUSH,
    ActionType.EMAIL_SEND,
    ActionType.API_WRITE,
    ActionType.SHELL_EXEC,
}

# Heuristic patterns — not a substitute for dedicated secret scanning.
_SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|secret|token|password|passwd|credential)\s*[=:]\s*\S{8,}'),
    re.compile(r'sk-[A-Za-z0-9]{20,}'),
    re.compile(r'ghp_[A-Za-z0-9]{36}'),
    re.compile(r'Bearer\s+[A-Za-z0-9\-._~+/]{20,}'),
]


def check_action(action: ActionType, path: str | None = None) -> PolicyResult:
    if action == ActionType.FILE_READ:
        return PolicyResult(PolicyDecision.ALLOW, "reads are unrestricted")

    if action == ActionType.FILE_WRITE and path is not None:
        norm = path.lstrip("/")
        for blocked in BLOCKED_WRITE_PREFIXES:
            if norm == blocked or norm.startswith(blocked):
                return PolicyResult(PolicyDecision.DENY, f"writes to {blocked!r} are blocked")
        for allowed in ALLOWED_WRITE_PREFIXES:
            if norm.startswith(allowed):
                return PolicyResult(PolicyDecision.ALLOW, f"path is under permitted prefix {allowed!r}")
        return PolicyResult(PolicyDecision.REQUIRE_APPROVAL, f"path {path!r} is outside permitted write prefixes")

    if action in _REQUIRE_APPROVAL_ACTIONS:
        return PolicyResult(PolicyDecision.REQUIRE_APPROVAL, f"{action.name} always requires approval")

    return PolicyResult(PolicyDecision.ALLOW, "no policy restricts this action")


def check_content_for_secrets(content: str) -> PolicyResult:
    """Heuristic secret scan. Not exhaustive — use dedicated scanning in CI."""
    for pattern in _SECRET_PATTERNS:
        if pattern.search(content):
            return PolicyResult(PolicyDecision.DENY, "content appears to contain credentials; redact before logging")
    return PolicyResult(PolicyDecision.ALLOW, "no credential patterns detected")
