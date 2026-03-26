# structured-agents

A hierarchical, directory-based multi-agent system that replicates a software engineer's workflow. Works with **Cursor** and **Claude Code**.

Given a Jira ticket, the system reads requirements, plans work, writes code or takes over automation-generated MRs, reviews, tests, merges, and updates Jira -- end to end.

## Compatibility

| Platform | MCP Config | How it works |
|----------|-----------|--------------|
| **Cursor** | `.cursor/mcp.json` | Agents run as chat participants with MCP tool access |
| **Claude Code** | `.mcp.json` | Agents run via Claude Code with the same MCP tools |

Both platforms use the same agent definitions, skills, and profiles. The `generate-mcp-config` script produces configs for either or both from a single `.env` file.

Agents can run **locally** on the development server (when using Cursor SSH Remote or Claude Code directly) or **remotely** over SSH from any machine. The system auto-detects which mode to use.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** -- required by MCP servers (Jira, GitLab, GitHub, Slack). On Windows, if you use `nvm`, run `nvm install 22 && nvm use 22` from an admin terminal.
- **Claude Code** or **Cursor** -- at least one must be installed. Claude Code must be available as `claude` on your `PATH`.

## Setup

1. Copy the environment template and fill in your values:

   ```bash
   cp .env.example .env
   ```

2. Set at least these variables in `.env`:

   | Variable | Purpose |
   |----------|---------|
   | `SAGENT_WORKSPACE` | Base directory where repositories live on the remote server |
   | `SAGENT_SSH_HOST` | Hostname of the remote server (for SSH mode) |
   | `SAGENT_SSH_USER` | SSH username |
   | `SAGENT_SSH_KEY` | Path to SSH private key (must match your `~/.ssh/config`) |
   | `SAGENT_IS_REMOTE` | Set to `true` **only** if running directly on the remote server (e.g. via Cursor SSH Remote). On Windows this is always auto-detected as `false`. |

   See `.env.example` for additional settings (Jira, GitLab, GitHub, Slack).

3. Generate MCP configuration:

   ```bash
   # Linux / macOS (via Makefile)
   make mcp-config WORKSPACE=/path/to/workspace              # Cursor only
   make mcp-config WORKSPACE=/path/to/workspace CLAUDE_CODE=1 # Cursor + Claude Code

   # Any platform (via Python directly)
   python scripts/generate-mcp-config.py                     # Cursor only
   python scripts/generate-mcp-config.py --claude-code       # Cursor + Claude Code
   ```

4. **Windows only** -- the generated `.mcp.json` uses `npx` as the command, but
   Windows requires a wrapper. Open `.mcp.json` and change each server's
   `"command"` from `"npx"` to `"npx.cmd"`:

   ```json
   {
     "mcpServers": {
       "atlassian-jira": {
         "command": "npx.cmd",
         "args": ["-y", "@aashari/mcp-server-atlassian-jira"],
         "env": { ... }
       }
     }
   }
   ```

5. Activate:
   - **Cursor**: Reload the window (`Ctrl+Shift+P` -> "Reload Window")
   - **Claude Code**: Run `/mcp` to reload, or restart the session

## Architecture

```
User provides Jira ticket
    └── orchestrator (top-level router)
        ├── planner        → breaks ticket into tasks
        ├── coder          → writes/modifies code
        ├── reviewer       → reviews changes and MRs
        ├── tester         → writes and runs tests
        ├── packager       → AIPCC packaging specialist
        ├── researcher     → investigations, ADRs, spikes
        ├── git-ops        → branches, MRs, merges
        ├── jira-ops       → ticket lifecycle
        └── infra-ops      → Ansible, containers, CI
```

Each agent is defined declaratively via `agent.yaml` (metadata) + `AGENT.md` (instructions). Skills are reusable capabilities that agents load on demand -- including repo-specific skills discovered dynamically from target repositories.

## Directory Layout

| Directory | Purpose |
|-----------|---------|
| `agents/` | Agent definitions (`agent.yaml` + `AGENT.md` per agent) |
| `skills/` | Reusable capabilities (`SKILL.md` per skill) |
| `profiles/` | Known repository profiles (conventions, key files, workflows) |
| `mcps/` | MCP server configuration docs (Jira, GitLab, GitHub, Slack) |
| `remote/` | SSH remote execution config (`remote/server.yaml`) |
| `scripts/` | Tooling (`generate-mcp-config.py`) |
| `templates/` | Templates for creating new agents, skills, profiles |
| `src/` | Python runtime -- CLI, engine, loaders, backends |
| `workspace/` | Runtime workspace for agent artifacts (gitignored) |

## CLI Usage

Install in development mode:

```bash
# Linux / macOS
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,mcp]"

# Windows
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,mcp]"
```

### Run against a Jira ticket

```bash
# Full orchestration (intake -> plan -> execute -> report)
structured-agents run AIPCC-12095

# Dry run (read-only, no external changes)
structured-agents run AIPCC-12095 --dry-run

# Run a single agent instead of full orchestration
structured-agents run AIPCC-12095 --agent coder --context "Fix the constraint parsing"

# Extra verbosity
structured-agents run AIPCC-12095 -v --dry-run
```

### Inspect definitions

```bash
# List all agents, skills, profiles, and MCPs
structured-agents list

# List only agents
structured-agents list agents

# Validate all definitions (checks cross-references)
structured-agents validate

# Show the fully assembled system prompt for an agent
structured-agents show orchestrator
structured-agents show coder --dry-run
```

Each run creates a workspace directory at `workspace/runs/<ticket>-<timestamp>/` with:
- `run.log` -- full log file
- `plan.yaml` -- the execution plan
- `context.json` -- serialized run context
- `artifacts/` -- per-step output files
- `report.md` -- final summary report

### Cursor users

See [`AGENTS.md`](AGENTS.md) for how to replicate the orchestration flow manually inside Cursor chat.

## Extending

### New agents

See `templates/agent/`. Each agent needs:
- `agent.yaml` -- metadata, capabilities, sub-agents, skills, MCPs
- `AGENT.md` -- system prompt and instructions

### New skills

See `templates/skill/`. Each skill needs:
- `SKILL.md` -- instructions with YAML frontmatter (name, description)

Skills support **dynamic discovery**: when working on a repo, agents check for `.claude/skills/*/SKILL.md` and `AGENTS.md` in the target repo and follow repo-specific instructions before falling back to generic ones. Skills from `ai-helpers` are always available as a shared library.

## License

MIT
