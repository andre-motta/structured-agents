#!/usr/bin/env python3
"""Generate MCP configuration from .env file for Cursor and/or Claude Code.

Usage:
    python scripts/generate-mcp-config.py
    python scripts/generate-mcp-config.py --workspace /path/to/workspace
    python scripts/generate-mcp-config.py --claude-code
    python scripts/generate-mcp-config.py --workspace /path/to/workspace --claude-code

Without --workspace, writes to the structured-agents repo root.
With --workspace, merges into the target workspace (preserving existing servers).
With --claude-code, also writes .mcp.json for Claude Code.
"""

import argparse
import json
import sys
from pathlib import Path


def load_dotenv(env_path: Path) -> dict[str, str]:
    """Parse a .env file into a dict, ignoring comments and blank lines."""
    env = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def build_mcp_servers(env: dict[str, str]) -> dict:
    """Build MCP server entries from env vars. Returns only the servers dict."""
    servers: dict = {}

    jira_token = env.get("JIRA_API_TOKEN", "")
    jira_email = env.get("JIRA_USERNAME", "")
    jira_url = env.get("JIRA_SERVER_URL", "")

    if jira_token and jira_email and jira_url:
        site_name = jira_url.split("//")[-1].split(".")[0]
        servers["atlassian-jira"] = {
            "command": "npx",
            "args": ["-y", "@aashari/mcp-server-atlassian-jira"],
            "env": {
                "ATLASSIAN_SITE_NAME": site_name,
                "ATLASSIAN_USER_EMAIL": jira_email,
                "ATLASSIAN_API_TOKEN": jira_token,
            },
        }
        print(f"  [ok] Jira MCP configured (site: {site_name})")
    else:
        print("  [skip] Jira MCP: missing JIRA_API_TOKEN, JIRA_USERNAME, or JIRA_SERVER_URL")

    gitlab_token = env.get("GITLAB_TOKEN", "")
    gitlab_url = env.get("GITLAB_URL", "https://gitlab.com")

    if gitlab_token:
        servers["gitlab"] = {
            "command": "npx",
            "args": ["-y", "@zereight/mcp-gitlab"],
            "env": {
                "GITLAB_PERSONAL_ACCESS_TOKEN": gitlab_token,
                "GITLAB_API_URL": f"{gitlab_url.rstrip('/')}/api/v4",
                "USE_PIPELINE": "true",
            },
        }
        print(f"  [ok] GitLab MCP configured ({gitlab_url})")
    else:
        print("  [skip] GitLab MCP: missing GITLAB_TOKEN")

    github_token = env.get("GITHUB_TOKEN", "")

    if github_token:
        servers["github"] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": github_token,
            },
        }
        print("  [ok] GitHub MCP configured")
    else:
        print("  [skip] GitHub MCP: missing GITHUB_TOKEN")

    slack_token = env.get("SLACK_BOT_TOKEN", "")

    if slack_token:
        servers["slack"] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-slack"],
            "env": {
                "SLACK_BOT_TOKEN": slack_token,
            },
        }
        print("  [ok] Slack MCP configured")
    else:
        print("  [skip] Slack MCP: SLACK_BOT_TOKEN not set (optional)")

    return servers


def write_mcp_config(mcp_path: Path, new_servers: dict, label: str) -> None:
    """Merge new_servers into an existing mcp.json (or create it)."""
    existing: dict = {}
    if mcp_path.exists():
        existing = json.loads(mcp_path.read_text())
        print(f"  Merging into existing {mcp_path}")
    existing.setdefault("mcpServers", {})

    existing["mcpServers"].update(new_servers)

    mcp_path.parent.mkdir(parents=True, exist_ok=True)
    mcp_path.write_text(json.dumps(existing, indent=2) + "\n")

    total = len(existing["mcpServers"])
    new = len(new_servers)
    print(f"  Wrote {mcp_path} ({total} server(s) total, {new} from structured-agents)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate MCP config from structured-agents .env file"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=None,
        help="Workspace root to write config into. "
        "If set, merges into existing config. "
        "Defaults to the structured-agents repo root.",
    )
    parser.add_argument(
        "--claude-code",
        action="store_true",
        help="Also generate .mcp.json for Claude Code at the workspace root.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    env_path = repo_root / ".env"

    workspace = args.workspace.resolve() if args.workspace else repo_root

    if not env_path.exists():
        print(f"Error: {env_path} not found. Copy .env.example to .env first.", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {env_path}")
    env = load_dotenv(env_path)

    print("Configuring MCP servers:")
    new_servers = build_mcp_servers(env)

    # Cursor: .cursor/mcp.json
    cursor_path = workspace / ".cursor" / "mcp.json"
    print(f"\n[Cursor]")
    write_mcp_config(cursor_path, new_servers, "Cursor")
    print("  Reload Cursor (Ctrl+Shift+P -> 'Reload Window') to activate.")

    # Claude Code: .mcp.json at workspace root
    if args.claude_code:
        claude_path = workspace / ".mcp.json"
        print(f"\n[Claude Code]")
        write_mcp_config(claude_path, new_servers, "Claude Code")
        print("  Claude Code will pick this up automatically on next session.")


if __name__ == "__main__":
    main()
