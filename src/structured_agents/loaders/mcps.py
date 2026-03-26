"""Load MCP server configurations from mcps/*.yaml."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml

from structured_agents.models.mcp import MCPServerConfig

log = logging.getLogger(__name__)


def load_mcps(mcps_dir: Path) -> dict[str, MCPServerConfig]:
    """Read mcps/ and return a mapping of MCP name -> MCPServerConfig."""
    mcps: dict[str, MCPServerConfig] = {}

    if not mcps_dir.is_dir():
        log.warning("MCPs directory not found: %s", mcps_dir)
        return mcps

    for path in sorted(mcps_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue

        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            log.error("Failed to parse %s: %s", path, exc)
            continue

        if not raw.get("name"):
            raw["name"] = path.stem

        mcp = MCPServerConfig(
            **{k: v for k, v in raw.items() if k in MCPServerConfig.model_fields},
            source_path=str(path),
        )

        if mcp.optional and mcp.required_env:
            mcp.available = bool(os.environ.get(mcp.required_env))
            if not mcp.available:
                log.debug("MCP %s unavailable (missing env var %s)", mcp.name, mcp.required_env)
        else:
            env_vars = mcp.environment_variables
            missing = [k for k in env_vars if not os.environ.get(k)]
            mcp.available = len(missing) == 0
            if missing:
                log.debug("MCP %s: missing env vars %s", mcp.name, missing)

        mcps[mcp.name] = mcp
        log.debug("Loaded MCP: %s (available=%s)", mcp.name, mcp.available)

    log.info("Loaded %d MCPs (%d available)", len(mcps), sum(1 for m in mcps.values() if m.available))
    return mcps
