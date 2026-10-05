---
name: create-pr
description: Use when the user wants to open a pull request — ensures the branch is pushed, generates a description, and creates the PR via gh CLI with title and body.
metadata:
  type: technique
  scope: root
---

# Create PR

Pushes the current branch if needed and opens a pull request via the `gh` CLI.

---

## When to Use

- "Open a PR", "create a pull request", "submit this for review"
- After finishing work on a feature branch

## When NOT to Use

- Working on `main`/`master` directly — ask the user to create a branch first
- No commits ahead of the base — nothing to PR
- User only wants a description drafted → use `create-pr-description`

---

## Workflow

### Step 1 — Pre-flight checks

Run in parallel:

```bash
git status                            # confirm clean working tree
git branch --show-current             # current branch name
git log --oneline main..HEAD          # commits to be included
git remote -v                         # confirm remote exists
```

If the working tree is dirty, stop and ask the user whether to commit first (offer to run `write-commit`).

### Step 2 — Push the branch

```bash
git push -u origin HEAD
```

If push is rejected (non-fast-forward), stop and explain — do NOT force-push without explicit user confirmation.

### Step 3 — Generate the PR description

Use `create-pr-description` to draft the body. Derive the title from the branch name and commits:

**Title rules:**
- ≤ 70 characters
- Conventional commit style if the repo uses it: `feat(scope): summary`
- Imperative mood, no trailing period
- Extract from the most significant commit or branch name

### Step 4 — Create the PR

```bash
gh pr create \
  --title "feat(auth): add JWT refresh token rotation" \
  --body "$(cat <<'EOF'
## Summary

- Adds refresh token rotation to prevent reuse after logout
- Invalidates the previous token on each refresh cycle

## Test plan

- [ ] Log in, log out, attempt to use old refresh token — expect 401
- [ ] Normal refresh flow still works after login

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Always use a HEREDOC for the body to avoid quoting issues.

### Step 5 — Confirm

Show the user the PR URL returned by `gh pr create`. Offer to open it in the browser:

```bash
gh pr view --web
```

---

## Flags Reference

| Flag | Purpose |
|------|---------|
| `--title` | PR title (required) |
| `--body` | PR description markdown |
| `--base` | Override base branch (default: repo default) |
| `--draft` | Open as draft PR |
| `--reviewer` | Request reviewers by username |
| `--label` | Apply labels |
| `--assignee @me` | Self-assign |

---

## Common Mistakes

- **Force-pushing without asking** — never do this; stop and explain the conflict
- **Pushing to main directly** — confirm the branch is a feature branch before pushing
- **Creating PR without commits ahead** — check `git log main..HEAD` first
- **Missing `--base`** — default is fine for most repos; only override if the user specifies
- **Skipping the description** — a blank body PR is hard to review; always generate one
