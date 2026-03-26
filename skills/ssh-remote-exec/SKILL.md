---
name: ssh-remote-exec
description: >
  Foundational skill for running commands on the remote server (or locally when
  already on the remote). Detects whether SSH is needed or commands can run
  directly. Covers quoting, chaining, file read/write, long jobs, exit codes,
  timeouts, SCP, and tunnels. Use whenever work targets the workspace at
  $SAGENT_WORKSPACE/; load host and options from remote/server.yaml.
tools: [shell]
mcps: []
---

# SSH remote exec (the remote server)

## When to Use

- Any task that must run on **the remote server** instead of the local machine.
- Before other skills assume paths, branches, or tools on the remote host.
- User mentions SSH, the remote server, or canonical repos under `$SAGENT_WORKSPACE/`.

## Local vs Remote Detection

**Before using SSH, determine whether you are already on the remote server.**

Detection logic (check in order):

1. If `SAGENT_IS_REMOTE=true` is set in the environment, you **are** on the
   remote -- run commands directly, do not wrap in SSH.
2. Otherwise, compare `$(hostname -f)` or `$(hostname)` with `$SAGENT_SSH_HOST`.
   If they match (or the host resolves to `localhost`/`127.0.0.1`), you are local
   to the remote -- run commands directly.
3. If neither applies, you are on a different machine -- use SSH as described below.

**When running locally on the remote:**
- Execute commands directly: `cd $SAGENT_WORKSPACE/<repo> && <command>`
- Do NOT wrap in `ssh $SAGENT_SSH_HOST "..."` -- this is redundant and wastes a
  connection.
- SCP/rsync become simple `cp`/`rsync` with local paths.

**When running remotely (need SSH):**
- Use SSH as documented in the instructions below.

## Configuration

- Read **`remote/server.yaml`** in structured-agents for host alias, user, port, identity, and SSH options -- do not hardcode beyond what that file defines.
- **Default workspace**: `$SAGENT_WORKSPACE/` (repos live in subdirectories). Always `cd` to the exact repo path when state matters.

## Instructions

### Command construction (SSH mode only -- skip when local)

1. **Single command**  
   `ssh <host> '<single shell command>'`  
   Prefer a non-interactive login shell only if the repo requires it (`bash -lc '...'`).

2. **Multiple commands**  
   Chain with `&&` when later steps depend on success; use `;` only when you need subsequent steps after failure. Set `-e` inside the remote script if you wrap in `bash -c '...'`.

3. **Quoting**  
   Escape inner quotes so the **local** shell does not strip remote metacharacters. When complexity grows, pass a small script: `ssh host 'bash -s' <<'EOF' ... EOF`.

### File operations

4. **Read**  
   `ssh host "sed -n '1,200p' /path/file"`, `cat`, or `test -f` / `stat` as needed. Prefer bounded reads on huge files.

5. **Write**  
   Use `cat <<'EOF' > file`, `tee`, `vim`/`nano` in interactive sessions, or **scp** (see below). Verify with `ssh host "wc -l file && head file"`.

### Long-running and reliability

6. **Long jobs**  
   Use `nohup`, `tmux`, or `screen` if the session might drop; redirect logs to a file under the repo or `/tmp` and tail them in follow-up SSH calls.

7. **Exit codes**  
   Check `$?` or rely on `&&` chains. Do not report success if any critical remote command failed.

8. **Timeouts**  
   Wrap bounded commands with `timeout <seconds> cmd` when appropriate; if killed, narrow scope or run in background with logging.

9. **Recovery**  
   On transient SSH errors, retry with simpler commands (`hostname`, `pwd`) then re-run. On persistent failure, verify host/config from `server.yaml` and network.

### Transfer and tunnels

10. **SCP / rsync**  
    `scp local host:/remote/path` or reverse for artifacts; preserve permissions only when needed (`-p`). For trees, use `rsync -av` if available and allowed.

11. **Tunneling (e.g. web UI on remote)**  
    `ssh -L localport:127.0.0.1:remoteport host -N` (background with logging). Close when done.

## Security

- **Never** pass tokens, passwords, or private keys on the SSH command line where they appear in process listings or logs.  
- Prefer **environment variables** already set on the remote session, **files** with strict perms, or **SSH agent forwarding** only when policy allows—never echo secrets in command strings sent to the user or artifacts.

## Reporting

Include the exact remote working directory, commands run (redacted), exit status, and paths to logs or outputs on the remote server.
