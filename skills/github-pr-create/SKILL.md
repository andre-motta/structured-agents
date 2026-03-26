---
name: github-pr-create
description: >
  Creates GitHub pull requests using the gh CLI for repositories such as fromager
  and structured-agents. Sets title, body, labels, reviewers, and base branch.
  Use when the remote is github.com (or GitHub Enterprise) and the user wants a PR
  opened after push, or when git-ops must mirror GitLab MR practices on GitHub.
tools: [shell]
mcps: []
---

# GitHub pull request create

## When to Use

- Repo remote is **GitHub** (`github.com` or GHE host) and a branch is ready for review.
- Projects like **fromager** or **structured-agents** where MRs are PRs.
- User requests labels, reviewers, draft PR, or a specific **base** branch.

## Prerequisites

- **`gh` CLI** installed and authenticated (`gh auth status`).
- Current directory in the repo (or pass `--repo owner/name`).
- Branch pushed to `origin` (or the remote used for the PR).
- Optional: `profiles/<repo>.yaml` for title/body/label conventions (same idea as GitLab repos).

## Instructions

1. **Confirm remote and default branch**  
   `git remote -v` and `gh repo view --json defaultBranchRef`. Align **base** with the profile or team standard (often `main`).

2. **Draft vs ready**  
   - Draft: `gh pr create --draft ...`  
   - Ready: omit `--draft`.

3. **Create PR**  
   Example (adjust flags):

   ```bash
   gh pr create \
     --base main \
     --head my-feature-branch \
     --title "PROJ-123: short description" \
     --body "## Summary
   ...
   ## Test plan
   - [ ] ...
   " \
     --label "kind/feature" \
     --reviewer alice,bob
   ```

   Use `--fill` or `--fill-first` to reuse commit messages when appropriate.

4. **Labels and reviewers**  
   - Labels must exist on the repo (or use `gh label create` if your workflow allows).  
   - Reviewers: GitHub usernames or team slugs as supported by `gh`.

5. **Verify**  
   `gh pr view --web` or print the URL returned by `gh pr create`. Confirm base, head, and draft flag.

6. **Cross-links**  
   If Jira or another system tracks work, put the issue key and links in the **body** (GitHub does not mirror GitLab’s MR metadata the same way).

## Error Handling

- **Authentication failed**: Run `gh auth login`; do not embed tokens in commands.
- **No commits between base and head**: Push commits or fix base/head; report the `gh` error verbatim.
- **Label/reviewer invalid**: Retry without failing the whole PR—create with title/body only, then `gh pr edit` to add metadata.
- **Wrong repo**: Pass `--repo owner/name` explicitly when not in the project directory.
