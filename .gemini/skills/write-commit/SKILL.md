---
name: write-commit
description: Use when the user wants to commit staged or unstaged changes — generates a conventional commit message from the diff, stages files if needed, and commits.
metadata:
  type: technique
  scope: root
---

# Write Commit

Analyzes the current git diff to craft a precise conventional commit message, then commits.

---

## When to Use

- "Commit this", "commit my changes", "make a commit"
- "Write a commit message for this"
- After finishing a feature, fix, or refactor and the user wants it committed

## When NOT to Use

- User asks to push — commit first, then ask about pushing separately
- No changes are staged and no files were specified — confirm what to include

---

## Workflow

### Step 1 — Inspect the diff

Run these in parallel:

```bash
git status
git diff HEAD
git log --oneline -5
```

Use `git log` to match the existing commit style (conventional vs free-form).

### Step 2 — Determine what to stage

- If the user named specific files, stage only those: `git add <files>`
- If user said "everything" or the intent is clear, stage all tracked changes: `git add -u`
- **Never** run `git add .` (catches untracked files including `.env`, build artifacts)
- If unsure, list unstaged files and ask

### Step 3 — Craft the commit message

Follow **Conventional Commits** unless the repo uses a different style (check `git log`):

```
<type>(<optional scope>): <short imperative summary>

<optional body — explain WHY, not what>
```

**Types:** `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `style`, `perf`, `ci`

Rules:
- Summary line ≤ 72 characters, imperative mood ("add X", not "added X")
- Body only when the WHY is non-obvious
- No period at end of summary
- Reference issue numbers if visible in branch name or diff (`fixes #123`)

### Step 4 — Commit

Use a HEREDOC to avoid shell escaping issues:

```bash
git commit -m "$(cat <<'EOF'
feat(auth): add JWT refresh token rotation

Prevents token reuse after logout by invalidating the previous token
on each refresh cycle.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

Always append the `Co-Authored-By` trailer.

### Step 5 — Confirm

Run `git log --oneline -3` and show the user the new commit.

---

## Commit Type Quick Reference

| Type | When |
|------|------|
| `feat` | New user-facing feature |
| `fix` | Bug fix |
| `refactor` | Code change with no behavior change |
| `chore` | Tooling, deps, config, scripts |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `style` | Formatting, whitespace (no logic) |
| `perf` | Performance improvement |
| `ci` | CI/CD pipeline changes |

---

## Common Mistakes

- **Vague messages** ("update stuff", "fix bug") — always describe what and why
- **Past tense** ("added") — use imperative ("add")
- **Staging everything with `git add .`** — use `git add -u` or specific paths
- **Skipping the body** when the diff is non-obvious — add a brief WHY
