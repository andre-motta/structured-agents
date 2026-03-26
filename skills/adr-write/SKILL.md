---
name: adr-write
description: >
  Creates Architecture Decision Records in the architecture-decision-records
  repository using MkDocs Material friendly markdown. Sections: Title, Status,
  Context, Decision, Consequences; follows existing ADR numbering and filenames.
  Use when recording a technical decision, superseding an old ADR, or when the
  user asks for a new ADR in the ADR repo.
tools: [shell, ssh, write]
---

# ADR write

## When to Use

- A **significant architectural or technical decision** must be documented.
- Work targets the **architecture-decision-records** repo (MkDocs Material site).

## Skill Discovery

Before writing an ADR, load repo-specific guidance:

1. **Target repo skills** (architecture-decision-records):
   - Read `${SAGENT_WORKSPACE}/architecture-decision-records/.claude/skills/adr-create/SKILL.md`
     for the repo's own ADR creation workflow, template, and numbering conventions.
   - Read `${SAGENT_WORKSPACE}/architecture-decision-records/.claude/skills/adr-review/SKILL.md`
     for review criteria to self-check before submitting.
   - Read `${SAGENT_WORKSPACE}/architecture-decision-records/AGENTS.md`
     for repo-level conventions, MkDocs hooks, and slash-command workflows.

2. If repo-specific skills are found, **follow their instructions first**.
   Supplement with the generic steps below for anything not covered.

## Generic Instructions (fallback)

1. **Discover conventions**  
   Over SSH or local clone, list existing ADR files (e.g. `docs/adr/`, `adr/`, or project-specific path). Note **numbering** (`0001-...`, `ADR-001`, etc.), **kebab-case** titles in filenames, and **status** values already in use (Proposed, Accepted, Deprecated, Superseded).

2. **Pick the next identifier**  
   Use the next sequential number and a short **slug** matching peers (e.g. `0027-use-fromager-for-wheels.md`). Avoid colliding with open branches; check latest on default branch.

3. **Author content (MkDocs Material markdown)**  
   Use clear headings compatible with the site nav. Required sections:

   - **Title** — decision name as H1 or leading title line.
   - **Status** — Proposed / Accepted / Deprecated / Superseded (and links to superseding ADR if applicable).
   - **Context** — problem, constraints, forces, and what triggered the decision.
   - **Decision** — what was chosen and why (bullet list acceptable).
   - **Consequences** — positive, negative, and follow-up work (migrations, risks).

   Keep prose concise; link to tickets, MRs, and prior ADRs.

4. **Wire into the docs site**  
   If the repo uses an **MkDocs nav** (`mkdocs.yml`), add the new page to the ADR section per existing pattern.

5. **Validate**  
   Run `mkdocs build` (or CI-equivalent) if available; fix broken links and frontmatter/nav issues.

6. **Commit path**  
   Place the file where other ADRs live; follow branch naming from `profiles/architecture-decision-records.yaml` if present.

## Error Handling

- **Ambiguous folder**: Search for `adr` and `mkdocs.yml` to locate the canonical path.
- **Supersedes**: In the old ADR, update Status and link to the new file per repo convention.
