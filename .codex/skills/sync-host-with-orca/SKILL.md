---
name: sync-host-with-orca
description: Use when the user wants to update one specific Git repository on one specific Orca-connected host (a paired environment such as a Mac mini, or this machine) to the latest remote commit, by running the real git commands on that host through the Orca CLI. Fetches, fast-forwards the current branch, stashing and restoring any uncommitted work automatically, and reports the result. Use for "sync this repo on <host>", "pull latest for this project on the Mac mini", or "update my Mac mini copy of this repo".
license: MIT
metadata:
  version: "1.0"
  scope: global
---

# Sync Host With Orca

Updates **one** Git repository on **one** Orca-connected host — this machine or a paired
environment (e.g. a Mac mini) — to the latest remote commit, by running the actual `git`
commands on that host through an Orca terminal.

**Run it by default.** Invoking this skill means: perform the sync now, using the defaults
below, then report. The safe stash → update → restore flow is built in — don't stop to ask
permission for it. Only a conflict, a diverged branch, or an unreachable host should interrupt
the run.

It never pushes, never force-updates, and never leaves the repo checked out on a different
branch than it started.

## When to Use

- "Sync this repo on the Mac mini", "pull the latest on &lt;host&gt; for this project"
- After pushing from this machine, to bring one specific other host's checkout up to date
- "Is my Mac mini copy of X up to date? If not, update it."

## When NOT to Use

- Every repo on every host → use `sync-repos-with-all-hosts-using-orca` instead
- The host is this machine and you're already sitting at it → just `git pull --ff-only`
- The user wants to push, rebase, or publish → this skill never pushes

## Resolve the Orca CLI

Same resolution rules as the `orca-cli` skill: use `$ORCA_CLI_COMMAND` if set, else `orca-dev`
in a dev checkout, else `orca-ide` on Linux outside an Orca-managed terminal, else plain `orca`.
Call it `ORCA` below. If the `orca-cli` skill is installed, load its guide
(`ORCA skills get orca-cli`) for the exact current flags — the commands below are the ones
verified to work, but Orca's CLI surface changes between releases and that guide is the
version-matched source of truth.

## Workflow

### Step 1 — Identify the target host

```bash
ORCA host list --json
```

Each row has a `selector` field that is the literal flag to reuse, e.g. `--host local` or
`--environment "Mac mini"`. If the user named a host, match it by `name` (case-insensitive). If
they didn't, and there is exactly one paired environment besides "this machine", use it; if
there are several, ask which one. Confirm it's actually reachable before doing anything else:

```bash
ORCA status --environment "<host>" --json   # omit --environment entirely for local
```

Check `result.runtime.reachable` and `result.runtime.state == "ready"`. If not reachable, stop
and report that instead of guessing.

### Step 2 — Identify the target repo on that host

If the user named a repo, match by name. Otherwise infer it from the current directory:

```bash
git remote get-url origin   # canonical identity to match against
```

Then find it on the target host:

```bash
ORCA repo list --environment "<host>" --json   # omit --environment for local
```

Match an entry in `result.repos[]` by `gitRemoteIdentity.canonicalKey` (preferred) or by
`displayName` / the `path` basename. Use its `path`. If nothing matches, say so — don't guess a
path that was never confirmed to exist on that host.

### Step 3 — Get a terminal open on that repo

Reuse one if it already exists, otherwise create one:

```bash
ORCA terminal list --environment "<host>" --worktree "path:<repoPath>" --json
# if the list is empty:
ORCA terminal create --environment "<host>" --worktree "path:<repoPath>" --title "sync-<repo>" --json
```

Keep the returned `handle` — every later call for this terminal needs it **and** the same
`--environment` flag (see Common Mistakes).

### Step 4 — Run the sync on the host

Send one self-contained script, with a unique sentinel so completion is unambiguous (don't
reuse a fixed string — old scrollback can contain it):

```bash
TOKEN="SYNC_DONE_$(date +%s)_$$"
ORCA terminal send --terminal "<handle>" --environment "<host>" --enter --wait-submit 5 --json --text '
cd "<repoPath>" || { echo "CD-FAILED"; exit; }
STASHED=0
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  git stash push --include-untracked -m "sync-host-with-orca $(date +%F)" >/dev/null 2>&1 && STASHED=1
fi
git fetch --all --quiet 2>/dev/null
branch=$(git symbolic-ref --short -q HEAD)
if [ -z "$branch" ]; then
  echo "DETACHED"
else
  out=$(git pull --ff-only 2>&1)
  echo "RESULT [$branch] -> $out"
fi
if [ "$STASHED" = "1" ]; then
  pop=$(git stash pop 2>&1)
  echo "$pop" | grep -qi conflict && echo "STASH-CONFLICT" || echo "STASH-RESTORED"
fi
echo "<TOKEN>"
'
```

Substitute the real `<repoPath>`, `<handle>`, `<host>` and `$TOKEN` before sending — the
placeholders above are not literal text to send.

### Step 5 — Wait, then read

```bash
until ORCA terminal read --terminal "<handle>" --environment "<host>" --json 2>/dev/null | grep -q "$TOKEN"; do sleep 2; done
```

Run that with Bash `run_in_background` — it's a bounded wait for one event, not a repeating
stream, so it does not belong on `Monitor`. Once it finishes:

```bash
ORCA terminal read --terminal "<handle>" --environment "<host>" --limit 500 --json
```

Report the `RESULT` line (branch + fast-forward outcome), or `CONFLICT`/`STASH-CONFLICT` if the
stash pop collided, or `DETACHED` if the repo wasn't on a branch.

## Safety Rules

- Never push. Never force-update (`-f`, `reset --hard`, `clean -fd`).
- Never discard local work — stash and restore it automatically; on a pop conflict, leave the
  stash entry in place and report it instead of resolving it.
- Fast-forward only (`git pull --ff-only`) — on real divergence, stop and report, don't force.

## Common Mistakes

- **Omitting `--environment <host>` on `terminal send` / `terminal read` / `terminal list`.**
  The handle alone is not enough — every call touching a remote terminal needs the same
  `--environment` (or `--host`) flag it was created with, or Orca routes the call to the local
  runtime instead and returns a misleading `terminal_handle_stale` error. If that error shows up
  right after the terminal was listed as connected, check for a missing `--environment` before
  concluding the handle is actually gone.
- Matching the wrong repo on a host with similarly-named folders — match by
  `gitRemoteIdentity.canonicalKey`, not just the folder name.
- Treating `accepted: true` on `terminal send` as proof the command finished — it only proves
  the input was accepted. Wait for the sentinel, not for the send call to return.
- Reaching for `Monitor` on this one-shot wait — use a bounded `until`-loop in the background
  instead; `Monitor` is for repeating or unbounded event streams.
