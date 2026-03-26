# SSH Configuration for Structured Agents

## Overview

All agents that need to execute commands, access repositories, or run builds do so via SSH
to a remote server. This document covers setup and usage.

## Prerequisites

- SSH key pair (ed25519 recommended)
- Key added to the remote server's authorized_keys
- The remote server uses key-based authentication only -- passwords should be disabled
- Environment variables configured (see `.env.example`)

## Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SAGENT_SSH_HOST` | Remote server hostname or IP | `myserver.example.com` |
| `SAGENT_SSH_USER` | SSH username | `engineer` |
| `SAGENT_WORKSPACE` | Base directory for repos on the remote server | `/home/engineer/git` |
| `SAGENT_SSH_KEY` | Path to SSH private key (optional) | `~/.ssh/id_ed25519` |

## SSH Config Entry

Add to `~/.ssh/config`:

```
Host myserver
  HostName <server-ip-or-hostname>
  User <your-username>
  IdentityFile ~/.ssh/id_ed25519
  ServerAliveInterval 60
  ServerAliveCountMax 3
```

## Usage Patterns

### Single command
```bash
ssh $SAGENT_SSH_HOST "cd $SAGENT_WORKSPACE/builder && git status"
```

### Multi-command
```bash
ssh $SAGENT_SSH_HOST "cd $SAGENT_WORKSPACE/builder && git checkout -b feature/my-change && git status"
```

### File transfer
```bash
scp local-file.txt $SAGENT_SSH_HOST:$SAGENT_WORKSPACE/structured-agents/workspace/

scp $SAGENT_SSH_HOST:$SAGENT_WORKSPACE/wheels-test/probe-tests/test_new.py ./
```

### Long-running processes
```bash
ssh $SAGENT_SSH_HOST "cd $SAGENT_WORKSPACE/builder && nohup tox -e lint > /tmp/lint.log 2>&1 &"

ssh $SAGENT_SSH_HOST "cat /tmp/lint.log"
```

## Security Notes

- Never pass secrets as command-line arguments (visible in process list)
- Use environment variables or SSH agent forwarding for credentials
- The remote server SSH should be hardened: no root login, no password auth, PubkeyAuthentication only
