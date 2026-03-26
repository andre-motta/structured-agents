"""Load skill definitions from skills/*/SKILL.md (YAML frontmatter + markdown body)."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from structured_agents.models.skill import SkillDefinition

log = logging.getLogger(__name__)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a SKILL.md into YAML frontmatter dict and markdown body."""
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}

    body = parts[2].strip()
    return meta, body


def load_skills(skills_dir: Path) -> dict[str, SkillDefinition]:
    """Walk skills/ and return a mapping of skill name -> SkillDefinition."""
    skills: dict[str, SkillDefinition] = {}

    if not skills_dir.is_dir():
        log.warning("Skills directory not found: %s", skills_dir)
        return skills

    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue

        md_path = entry / "SKILL.md"
        if not md_path.exists():
            log.warning("Skipping %s -- no SKILL.md found", entry.name)
            continue

        raw_text = md_path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(raw_text)

        if not meta.get("name"):
            meta["name"] = entry.name

        skill = SkillDefinition(
            **{k: v for k, v in meta.items() if k in SkillDefinition.model_fields},
            instructions=body,
            source_path=str(md_path),
        )
        skills[skill.name] = skill
        log.debug("Loaded skill: %s", skill.name)

    log.info("Loaded %d skills", len(skills))
    return skills
