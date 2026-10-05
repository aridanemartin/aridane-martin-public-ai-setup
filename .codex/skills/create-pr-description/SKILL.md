---
name: create-pr-description
description: Use when the user needs a pull request description drafted — analyzes branch commits and diff vs base branch, then generates a structured markdown body ready to copy or pass to create-pr.
metadata:
  type: technique
  scope: root
---

# Create PR Description

Generates a structured, informative PR description from the current branch's commits and diff.

---

## When to Use

- "Write a PR description for this branch"
- "Draft the PR body / summary"
- Before running `create-pr` when a description is needed

## When NOT to Use

- No commits ahead of the base branch — nothing to describe
- User wants to create the PR directly → use `create-pr` (which calls this internally)

---

## Workflow

### Step 1 — Identify the base branch

```bash
git remote show origin | grep "HEAD branch"   # detect default branch
git log --oneline main..HEAD 2>/dev/null || git log --oneline master..HEAD
```

Default to `main`, fall back to `master`.

### Step 2 — Gather context

Run in parallel:

```bash
git log --oneline main..HEAD          # all commits on this branch
git diff main...HEAD --stat           # files changed, insertions, deletions
git diff main...HEAD                  # full diff for detailed analysis
```

Also check for a related issue number in the branch name (e.g., `feat/123-auth-refresh`).

### Step 3 — Draft the description

Use this structure:

```markdown
## Summary

- <bullet: what changed and why — focus on user/product impact>
- <bullet: any architectural decision worth calling out>
- <bullet: scope / what was intentionally NOT changed>

## Changes

- `path/to/file.ts` — <one-line reason>
- `path/to/other.ts` — <one-line reason>

## Test plan

- [ ] <manual step to verify the happy path>
- [ ] <edge case or regression to check>
- [ ] <any automated tests that cover this>

## Notes

<Optional: breaking changes, migration steps, follow-up tickets, screenshots>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

**Writing rules:**
- Summary bullets describe WHY (motivation, impact), not just what files changed
- Keep Summary to 2-4 bullets — if more, scope is too large
- Test plan must be actionable: someone unfamiliar should be able to follow it
- Omit "Notes" section if empty

### Step 4 — Output

Return the markdown block so the user can copy it, or store it for `create-pr` to consume directly.

---

## Common Mistakes

- **Listing files instead of explaining impact** — files are in the diff; explain motivation
- **Empty test plan** — always include at least one manual verification step
- **Copying commit messages verbatim** — synthesize across commits into a coherent narrative
- **Forgetting breaking changes** — if `git diff` shows removed exports or API changes, flag them in Notes
