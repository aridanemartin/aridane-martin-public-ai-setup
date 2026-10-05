---
name: sync-workspace-repos
description: Use when the user wants to update every Git repository under the workspace folder (default ~/workspace) to the latest remote changes. By default it fetches all remotes, fast-forwards each repository's main (or master) branch — stashing and restoring any uncommitted work automatically — and reports the result. Use for "update all my repos", "sync my workspace", or "pull latest on every project".
license: MIT
metadata:
  version: "1.0"
  scope: global
---

# Sync Workspace Repos

Sweeps every Git repository inside the workspace folder, fetches upstream, and
fast-forwards each repo's **main** branch (falling back to **master**) to the
latest remote commit.

**Run it by default.** Invoking this skill means: perform the sync now, using
the defaults below, then report. Do not stop to ask for permission for the
default path — the safe stash → update → restore flow is built in. The only
things that should interrupt the run are a conflict or a diverged branch, which
you report instead of resolving.

It never pushes, never force-updates, and never leaves a repo checked out on a
different branch than it started.

---

## When to Use

- "Update all my repos", "sync my workspace", "pull latest on every project"
- "Go into every repository and update main to the latest"
- Periodically keeping a workspace of many clones up to date in one pass

## When NOT to Use

- A single repository → just `git pull --ff-only`
- The user wants to push, rebase, or publish → this skill never pushes
- The workspace path is something other than `~/workspace` and the user named it → use that path instead

---

## Defaults (applied automatically)

| Setting | Default |
|---------|---------|
| Workspace root | `~/workspace` (override with first arg or `WORKSPACE`) |
| Target branch | `main`, falling back to `master` |
| Sync strategy | Fast-forward only (never merge/rebase on the user's behalf) |
| Dirty repos | `git stash push --include-untracked` → update → `git stash pop` |
| Non-checked-out target | Update the local ref with `git fetch origin <branch>:<branch>` |
| No remote | Skip, report as "no remote" |
| Push | Never |

---

## Workflow

### Step 1 — Discover repositories

Find every repo, including ones nested one or two levels deep (e.g.
`workspace/group/project`), but do not descend into a repo to find repos inside
it:

```bash
WORKSPACE="${WORKSPACE:-$HOME/workspace}"
find "$WORKSPACE" -maxdepth 3 -name .git -type d -prune \
  | sed 's|/.git$||' | sort
```

### Step 2 — Fetch everything first (read-only)

Fetching is safe and must happen before any decision, so `behind` counts are
accurate:

```bash
while IFS= read -r repo; do
  if git -C "$repo" remote get-url origin >/dev/null 2>&1; then
    git -C "$repo" fetch --all --prune --quiet
  fi
done <<< "$REPOS"
```

### Step 3 — Assess each repo

```bash
git -C "$repo" symbolic-ref --short -q HEAD          # current branch
git -C "$repo" status --porcelain | wc -l            # 0 = clean, >0 = dirty
# target branch = main if it exists, else master
git -C "$repo" rev-list --left-right --count "origin/$TARGET...$TARGET"  # behind / ahead
git -C "$repo" remote -v                             # remote presence
```

Classification:

- **No remote** → skip; nothing to sync.
- **behind == 0** → already up to date; nothing to do.
- **clean & behind** → fast-forward.
- **dirty & behind** → stash → update → restore (automatic).
- **not on the target branch** → update the target ref without switching (Step 5).

Prefer the literal `main`/`master` even when `origin/HEAD` points at a feature
branch (some remotes default to e.g. `001-repository-foundation`).

### Step 4 — Stash uncommitted work (automatic)

For each dirty repo that is behind:

```bash
git -C "$repo" stash push --include-untracked -m "sync-workspace-repos $(date +%F)"
git -C "$repo" stash list | head -1   # remember the entry for restore
```

Never use `git checkout --`, `git reset --hard`, or `git clean` to make room.
The stash is the safe path and is restored in Step 6.

### Step 5 — Update the target branch

- **Target branch is checked out:**
  ```bash
  git -C "$repo" merge --ff-only "origin/$TARGET"
  ```
- **Target branch is not checked out** (feature branch or another branch is current):
  ```bash
  git -C "$repo" fetch origin "$TARGET:$TARGET"
  ```
  This refuses a non-fast-forward update — exactly what you want. If it fails,
  stop and report the divergence; do **not** force.

### Step 6 — Restore stashed changes

```bash
git -C "$repo" stash pop
```

If the pop conflicts, leave the stash entry in place, report the conflicting
files, and move on. Do not attempt to resolve the user's work.

### Step 7 — Report

One row per repo: repo, target branch, result
(`updated N commits` / `already up to date` / `no remote` / `stash restored` /
`conflict`). Put anything needing attention at the top.

---

## Safety Rules

- **Never push.** This skill only pulls/fetches.
- **Never force-update** a branch (`-f`, `+refspec`, `reset --hard`, `clean -fd`).
- **Never discard local work** — stash and restore it.
- **Never leave a repo on a different branch** than it started.
- Fetch before classifying, so "behind" counts are real.
- On a non-fast-forward update, stop and report.

---

## Common Mistakes

- Judging "behind" from stale remote-tracking refs — always fetch first.
- Trusting `origin/HEAD` when the remote's default is a feature branch — prefer literal `main`/`master`.
- Running `git pull` (merge) on a dirty tree and creating stray merge commits — use `--ff-only`.
- Forgetting `--include-untracked`, then a later `stash pop` reports a dirty tree.
- Switching branches to update a non-checked-out target — use `git fetch origin <branch>:<branch>`.
- Losing untracked files by reaching for `git clean`.
