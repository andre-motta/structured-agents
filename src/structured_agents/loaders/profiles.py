"""Load repository profiles from profiles/*.yaml."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from structured_agents.models.profile import RepoProfile

log = logging.getLogger(__name__)


def load_profiles(profiles_dir: Path) -> dict[str, RepoProfile]:
    """Read profiles/ and return a mapping of profile name -> RepoProfile."""
    profiles: dict[str, RepoProfile] = {}

    if not profiles_dir.is_dir():
        log.warning("Profiles directory not found: %s", profiles_dir)
        return profiles

    for path in sorted(profiles_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue

        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            log.error("Failed to parse %s: %s", path, exc)
            continue

        if not raw.get("name"):
            raw["name"] = path.stem

        profile = RepoProfile(
            **{k: v for k, v in raw.items() if k in RepoProfile.model_fields},
            source_path=str(path),
        )
        profiles[profile.name] = profile
        log.debug("Loaded profile: %s", profile.name)

    log.info("Loaded %d profiles", len(profiles))
    return profiles
