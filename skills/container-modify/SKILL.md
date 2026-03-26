---
name: container-modify
description: >
  Edits Containerfiles and related build configuration for Red Hat AI / RHAIIS
  and base-images style repos. Applies UBI9, DNF, and multi-stage patterns,
  accelerator/Python layer conventions, and light validation. Use when changing
  images, packages, stages, or CI-facing container build inputs in repos under
  $SAGENT_WORKSPACE.
tools: [shell, ssh, write]
mcps: []
---

# Container modify

## When to Use

- Task touches `Containerfile`, `Containerfile.*`, `.containerignore`, build args, or image CI that consumes them.
- Base image is **UBI9** (or family) and packages install via **dnf**/`microdnf`.
- Repo follows **RHAIIS** or **base-images** layouts (variants, Python stacks, accelerator images).

## Local vs Remote

Follow the detection logic in **ssh-remote-exec** to determine whether you are
already on the remote server. If local to the remote, access files and run
builds directly. Only use SSH when on a different machine.

## Skill Discovery

Before modifying containers, load repo-specific guidance:

1. **ai-helpers** (always available):
   - `${SAGENT_WORKSPACE}/ai-helpers/helpers/skills/oci-cve-checker/SKILL.md`
     -- for comparing CVEs between image versions when evaluating base image changes.

2. **Target repo**: Check `${SAGENT_WORKSPACE}/<repo>/` for:
   - `AGENTS.md` for container conventions (known: `containers/AGENTS.md` and
     `rhaiis/containers/AGENTS.md` covering RHAIIS release automation, Konflux
     MCP, and Claude Code workflows).
   - `.claude/skills/*/SKILL.md` for repo-specific container skills.

3. If repo-specific guidance is found, **follow it first**.
   Supplement with the generic steps below for anything not covered.

## Generic Instructions (fallback)

1. **Read before edit**  
   Load the full Containerfile chain: final stage, builder stages, `ARG`/`ENV`, `USER`, `ENTRYPOINT`/`CMD`. Note which stage installs runtime vs build-only deps.

2. **Match platform conventions**  
   - **UBI9**: use `dnf install -y` (or documented `microdnf`) with `--setopt=install_weak_deps=0` when the repo already does; respect `RUN` layering order to maximize cache.  
   - **Multi-stage**: copy artifacts with explicit `COPY --from=`; keep secrets and credentials out of layers (no `ARG` for tokens unless pattern is already established and documented).  
   - **RHAIIS / base-images**: preserve variant naming (e.g. accelerator vs CPU), Python layer ordering, and shared partials if the repo includes included snippets or generated stages -- mirror neighboring Containerfiles.

3. **Package changes**  
   Pin or version-lock consistently with sibling images. Prefer repos' existing `RUN` grouping (one dnf layer vs split) unless splitting fixes cache or clarity without duplicating metadata refresh.

4. **Apply edits**  
   Use **write** or editors directly (if local) or per **ssh-remote-exec** (if remote); keep line endings and indentation consistent with the file. Touch only stages and args required by the task.

5. **Lint / sanity check**  
   Run whatever the repo documents (`make validate`, `podman build --dry-run` if available, or `podman build` with a narrow target). At minimum:  
   - Parse-check: `podman build -f <file> --target <stage> ...` with a throwaway tag, or `hadolint`/`dockerfile_lint` if present in CI.  
   - Fix duplicate `FROM` labels, bad `COPY` paths, and broken line continuations before reporting done.

6. **Report**  
   List Containerfiles changed, images/tags affected, build command used, and pass/fail of validation.

## Error Handling

- **Build fails**: capture the failing `RUN` line and stderr; adjust package names, arches, or repos -- do not silence errors with `|| true` unless the repo already does.  
- **Ambiguous pattern**: open a second Containerfile in the same directory family and copy its structure.
