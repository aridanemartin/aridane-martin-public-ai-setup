---
name: sync-repos-with-all-hosts-using-orca
description: Use when the user wants to update every Git repository registered in Orca, across every Orca-connected host (this machine plus every paired environment), to the latest remote commit. For each host, discovers its repos via the Orca CLI, runs one fetch + fast-forward pass per repo (stashing and restoring uncommitted work automatically) through a single Orca terminal, and reports a per-host, per-repo summary. Use for "sync all my repos everywhere using Orca", "make sure every machine is up to date", or "pull latest on every project on every host".
license: MIT
metadata:
  version: "1.0"
  scope: global
---

# Sync Repos With All Hosts Using Orca

Updates **every** Git repository registered in Orca, on **every** Orca-connected host — this
machine plus every paired environment (e.g. a Mac mini) — to the latest remote commit, by
running the real `git` commands on each host through one Orca terminal per host.

**Run it by default.** Invoking this skill means: perform the sync now, across every host,
using the defaults below, then report a table. The safe stash → update → restore flow is built
in — don't stop to ask permission for it. Only a conflict, a diverged branch, or an unreachable
host should interrupt that one repo or host; everything else in the batch still runs.

It never pushes, never force-updates, and never leaves a repo checked out on a different branch
than it started.

## When to Use

- "Sync everything everywhere", "make sure every machine has the latest", "pull latest on every
  project on every host using Orca"
- After pushing from this machine, to catch every other connected host up in one pass

## When NOT to Use

- Just one repo on one host → use `sync-host-with-orca` instead, it's much cheaper
- Repos that aren't registered in Orca (`orca repo list` won't see them) → fall back to
  `sync-workspace-repos` for a plain folder sweep on this machine
- The user wants to push, rebase, or publish → this skill never pushes

## Resolve the Orca CLI

Same rules as `sync-host-with-orca` / the `orca-cli` skill: `$ORCA_CLI_COMMAND` → `orca-dev` in
a dev checkout → `orca-ide` on Linux outside an Orca-managed terminal → plain `orca`. Called
`ORCA` below. If the `orca-cli` skill is installed, prefer its version-matched guide
(`ORCA skills get orca-cli`) over memorized flags.

## Workflow

### Step 1 — Discover every host

```bash
ORCA host list --json
```

Each row's `selector` is the literal flag to reuse for every later command on that host
(`--host local` or `--environment "<name>"`). Include local — syncing it is a harmless no-op if
it's already current. For each host, confirm it before using it:

```bash
ORCA status --environment "<host>" --json   # omit --environment for local
```

Skip (and report as unreachable) any host where `reachable` is false or `state != "ready"`,
rather than hanging on it.

### Step 2 — Per host: discover its repos

```bash
ORCA repo list --environment "<host>" --json   # omit --environment for local
```

Keep only entries where `kind == "git"` — a `kind == "folder"` entry (e.g. an imported home
folder) is not a checkout to pull. Collect each kept entry's `path`. If a host has zero git
repos, report "no repos" for it and move to the next host.

### Step 3 — Per host: one terminal, one loop

Anchor a terminal at the first repo on that host (reuse an idle one from `terminal list` if one
is already open there, otherwise create one):

```bash
ORCA terminal create --environment "<host>" --worktree "path:<firstRepoPath>" --title "sync-all-repos" --json
```

Send a single script that walks every repo path discovered in Step 2, stash-protects dirty
trees, fetches, fast-forwards, restores, and prints one line per repo, ending in a unique
sentinel (don't reuse a fixed string — old scrollback can contain it):

```bash
TOKEN="SYNC_DONE_$(date +%s)_$$"
ORCA terminal send --terminal "<handle>" --environment "<host>" --enter --wait-submit 10 --json --text '
for d in <repoPath1> <repoPath2> <repoPath3>; do
  if [ ! -d "$d/.git" ]; then echo "SKIP-MISSING $d"; continue; fi
  cd "$d" || { echo "SKIP-CD $d"; continue; }
  STASHED=0
  if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    git stash push --include-untracked -m "sync-repos-with-all-hosts-using-orca $(date +%F)" >/dev/null 2>&1 && STASHED=1
  fi
  git fetch --all --quiet 2>/dev/null
  branch=$(git symbolic-ref --short -q HEAD)
  if [ -z "$branch" ]; then
    echo "DETACHED $d"
  else
    out=$(git pull --ff-only 2>&1)
    echo "OK $d [$branch] -> $out"
  fi
  if [ "$STASHED" = "1" ]; then
    pop=$(git stash pop 2>&1)
    echo "$pop" | grep -qi conflict && echo "STASH-CONFLICT $d"
  fi
done
echo "<TOKEN>"
'
```

List every discovered `path` from Step 2 on the `for d in ...` line — the placeholders above
(including `<TOKEN>`) must be substituted with real values before sending, not left literal.
Don't hardcode a different, remembered repo set than what that host actually has registered
right now.

### Step 4 — Wait, then read, per host

```bash
until ORCA terminal read --terminal "<handle>" --environment "<host>" --json 2>/dev/null | grep -q "$TOKEN"; do sleep 3; done
```

Run that with Bash `run_in_background` (bounded wait for one event — not `Monitor`, which is for
repeating/unbounded streams). Once it finishes:

```bash
ORCA terminal read --terminal "<handle>" --environment "<host>" --limit 2000 --json
```

Parse the `OK` / `SKIP-*` / `DETACHED` / `STASH-CONFLICT` lines. Repeat Steps 3–4 for the next
host — one host's slow `git fetch` shouldn't block starting the next host's terminal.

### Step 5 — Report

One table: host → repo → result. Put anything needing attention (conflicts, unreachable hosts,
detached HEADs) at the top, then the routine OK/already-up-to-date rows.

## Safety Rules

- Never push. Never force-update (`-f`, `reset --hard`, `clean -fd`).
- Never discard local work — stash and restore automatically; on a pop conflict, leave the
  stash entry in place and flag that one repo instead of resolving it.
- Fast-forward only — a real divergence is reported, not forced.
- An unreachable host is reported and skipped; it doesn't abort the hosts that do answer.

## Common Mistakes

- **Omitting `--environment <host>` on any `terminal` subcommand** (`send`, `read`, `list`)
  once the terminal was created on a remote host — the single most common failure mode, and it
  surfaces as a misleading `terminal_handle_stale`, not as a "missing flag" error. Carry the
  same host selector through every later call for that terminal.
- Opening one terminal **per repo** instead of one per host — far slower and churns through
  terminal tabs; one loop per host is the cheap path this skill exists to take.
- Forgetting to filter out `kind == "folder"` entries from `orca repo list` before looping —
  those aren't git checkouts.
- Treating a timed-out wait as failure — re-check with a longer timeout before concluding a
  host hung; `git fetch` across many repos can legitimately take a while.
