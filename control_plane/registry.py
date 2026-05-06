# registry — skill catalog and lookup
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"


@dataclass(frozen=True)
class SkillEntry:
    name: str
    path: Path
    accepts_input: bool
    description: str


SKILL_REGISTRY: dict[str, SkillEntry] = {
    "morning_brief": SkillEntry(
        name="morning_brief",
        path=_SKILLS_ROOT / "morning_brief",
        accepts_input=False,
        description="Reads vault/daily/ logs and writes a morning brief to vault/daily/.",
    ),
    "vault_cleanup": SkillEntry(
        name="vault_cleanup",
        path=_SKILLS_ROOT / "vault_cleanup",
        accepts_input=False,
        description="Promotes structured files from vault/raw/ to vault/wiki/ and writes a cleanup report.",
    ),
    "research_digest": SkillEntry(
        name="research_digest",
        path=_SKILLS_ROOT / "research_digest",
        accepts_input=True,
        description="Converts a raw note (--input path) into a structured digest in vault/wiki/.",
    ),
    "continuation_brief": SkillEntry(
        name="continuation_brief",
        path=_SKILLS_ROOT / "continuation_brief",
        accepts_input=False,
        description="Writes a session handoff template to vault/daily/ for context continuation.",
    ),
    "policy_simulator": SkillEntry(
        name="policy_simulator",
        path=_SKILLS_ROOT / "policy_simulator",
        accepts_input=True,
        description="[Phase 2] Simulates policy decisions for proposed actions. Placeholder.",
    ),
}


def get_skill(name: str) -> SkillEntry:
    if name not in SKILL_REGISTRY:
        available = ", ".join(sorted(SKILL_REGISTRY))
        raise ValueError(f"Unknown skill {name!r}. Available: {available}")
    return SKILL_REGISTRY[name]


def list_skills() -> list[SkillEntry]:
    return list(SKILL_REGISTRY.values())
