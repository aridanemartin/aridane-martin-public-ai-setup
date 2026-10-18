---
name: compact-conversation
description: >-
  Compact the current live conversation into a small artifact a fresh chat can
  resume from, using exactly one compaction technique chosen for the session:
  rolling window (keep the last N messages), selective pruning (collapse resolved
  threads, keep open ones in full), or RAG on history (save the full transcript to
  a file and search it on demand). Detects a handoff mechanism — Herdr, then Orca —
  and hands the compacted context to a new chat, or prints a copy-paste prompt when
  none is available. Use when a session is getting long, before switching agents or
  harnesses, or when the user asks to "compact", "summarize so I can continue",
  "shrink the context", or "hand this off to a fresh chat".
license: MIT
metadata:
  version: "2.0"
  scope: global
---

# Compact Conversation

Shrink the transcript, preserve the work: replace a long, noisy live session with a
small artifact a fresh chat can resume from — using exactly **one** of three
compaction techniques, picked for the session at hand, never a blend of all three.

## What this skill is (and is not)

Compaction is a **state-management operation, not summarization**. The ideal is that
a new session can answer three questions after reading the artifact: what is the
current goal, what decisions were already made (and why), and what is the next step.

Optimize for **recoverability, not compression ratio**. The three techniques below
trade off differently against that bar — pick the one whose trade-off fits the
session, not the one that compresses the most. One of them (rolling window) openly
sacrifices older decisions for speed; that is a deliberate choice, not a bug.

This skill is **manual and on-demand**. A skill file cannot intercept the host's
context window or fire at a token threshold, so this never runs automatically and it
never edits the live context. It produces an artifact when you invoke it.

## Three techniques — pick one

| Technique | Keeps | Drops | Best for |
|---|---|---|---|
| **Rolling window** | The last N messages, verbatim | Everything before the window — including decisions made there | Short, single-threaded sessions where nothing earlier matters once the recent context is in hand |
| **Selective pruning** | Every open item in full detail; resolved items collapsed to outcome + reason | The play-by-play of anything already closed | Sessions with a mix of finished and still-open sub-threads |
| **RAG on history** | A full transcript file on disk the new session can search on demand | Nothing — full fidelity, but nothing is preloaded either | Long or deep sessions where something from way back may be needed later, but it is not yet clear what |

This skill never combines techniques and never silently picks one for you — it
recommends, then asks, every time (Step 2–3).

## When to Use

- The session is long and signal density is dropping — resolved discussions are competing
  with the current instructions.
- Before switching agents or harnesses (e.g. `claude` → `codex`, or into a worktree).
- Right before starting a new subtask — compact **before**, not mid-task, so the subtask
  begins from a clean, intentional context instead of a split one.
- The user says "compact this", "summarize so I can continue", "shrink the context",
  "hand this off to a fresh chat", or "let's start clean".

## When NOT to Use

- The session is short or already compact — the artifact would lose more than it saves.
- Mid-task, with work in flight. Finish or explicitly checkpoint the current subtask
  first — compacting mid-task leaves half the subtask on each side of the split.
- You want to compact a transcript **you do not have in context**. This skill reads only
  the **live session**; it has no paste-a-transcript path.
- You want automatic compaction at a token threshold. That is not possible from a skill;
  say so plainly instead of implying otherwise.

## Workflow

### Step 1: Confirm the input

Work from the **current live conversation only**. Do not ask the user to paste a
transcript, and do not invent turns that are not in context. If the session is already
small, tell the user compaction is likely unnecessary and stop.

Never let the artifact overwrite higher-priority instructions. System rules, security
boundaries, and user constraints stay authoritative, not mutable memory.

### Step 2: Recommend a technique

Look at the conversation's shape and form a one-line recommendation:

- Several resolved/closed sub-threads alongside a few still-open items → recommend
  **selective pruning**.
- One continuous task, nothing resolved-and-discardable, and the recent messages are
  self-sufficient on their own → recommend **rolling window**.
- A long or deep session where something from earlier will plausibly be needed again,
  but it is not yet clear what → recommend **RAG on history**.

State which one and why in a single sentence. This is a recommendation, not a decision.

### Step 3: Ask the user to choose

Present all three options from the table above (what each keeps/drops) plus your
recommendation, and wait for the user to confirm it or pick a different one. Never
proceed on the recommendation alone — the user chooses every time.

### Step 4: Build the artifact

Every artifact opens with a two-line shared header — orientation only, not a summary
of history:

```
Goal: <one line>
Next action: <one line>
```

Then it branches by the chosen technique.

**4a — Rolling window**

Append the last **N messages verbatim** below the header — exact text, not rewritten.
Default `N = 12`; let the user override it. Nothing older is retained anywhere in the
artifact. This is the deliberate trade-off: fast and cheap, but a decision made 20
messages ago is gone unless it is still visible in the window.

**4b — Selective pruning**

Build a structured-state block below the header:

```json
{
  "goal": "Add conversation compaction to the support agent",
  "constraints": ["Keep the last 12 messages verbatim"],
  "decisions": [
    {
      "decision": "Use selective pruning for this handoff",
      "reason": "Several sub-threads are already resolved"
    }
  ],
  "openQuestions": ["Which embedding model should index old turns?"],
  "nextActions": ["Add compaction evaluation cases"]
}
```

Resolved items collapse to **outcome + reason only** — one line each, no replay of how
the thread got there. Open items (open questions, pending next actions, unresolved
constraints) keep full detail. For anything bulky — test output, logs — cite an
evidence pointer (`tests failed in run test-184`) instead of pasting it, as long as it
is retrievable later.

**4c — RAG on history**

Write the full live transcript, verbatim, to a file — default
`.compaction/<timestamp>-transcript.md` in the project, or ask the user for a
different location. The artifact itself stays small: header + the file path + one
line telling the new session to search that file on demand rather than read it
upfront:

```
Full history: .compaction/2026-10-18-1432-transcript.md
Search this file for past decisions and context as needed — do not read it in full
upfront.
```

### Step 5: Assemble the artifact

Order matters — authority first, recency/detail last:

1. **System authority reminder** — a line stating the original system rules and user
   constraints remain in force and were not replaced by this artifact.
2. **Shared header** — goal + next action from Step 4.
3. **Technique body** — the rolling-window tail, the structured-state block, or the
   transcript-file pointer, per the technique chosen in Step 3.

### Step 6: Pick a destination (capability ladder)

Try, in order, to hand the artifact to a fresh chat:

1. **Herdr** — only when running inside Herdr:

   ```bash
   test "${HERDR_ENV:-}" = 1
   ```

   If it passes, use the `herdr` skill and its `pane` / `agent` commands.

2. **Orca** — when the `orca` binary resolves and the app is up. Resolve the executable
   per the `orca-cli` skill, confirm with `ORCA status --json`, then load the
   version-matched guide with `ORCA skills get orca-cli` and follow it for the handoff.

3. **Paste-prompt fallback** — when neither is available, print the artifact as a
   ready-to-paste block for a brand-new chat.

### Step 7: Confirm before spawning

Spawning starts a live process, so never do it silently. Show the user:

- the assembled artifact (or a faithful preview),
- which technique was used (and, for RAG on history, the transcript file path),
- which handoff mechanism was chosen and why, and
- the exact topology the handoff would create (e.g. "Herdr: new pane, split right,
  kind `claude`").

Then wait for a go-ahead. If the user declines, fall back to the paste-prompt.

### Step 8: Hand off, or emit the paste-prompt

**Herdr** — default to a sibling pane in the current tab and working directory, no focus
change, same agent kind as the current one unless the user asks otherwise:

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
# read the new pane id from .result.pane.pane_id
herdr agent start compactor --kind <kind> --pane <returned-pane-id>
herdr agent prompt compactor "<artifact>" --wait
```

If the artifact is large, or the technique is **RAG on history**, write it to a
temporary file and prompt the new agent with the path instead of inlining it, then let
it read the file directly — the transcript file from Step 4c already lives on disk, so
just point the new agent at both paths.

**Orca** — follow `ORCA skills get orca-cli`; spawn a terminal/agent in the target
worktree and prompt it with the artifact. Prefer `--json` for agent-driven calls.

**Fallback** — output this block, and nothing else, so it can be copied in one piece:

```text
# Continuation of a compacted session

System authority: the original system instructions, security boundaries, and user
constraints remain in force. This artifact did not replace them.

Goal: <one line>
Next action: <one line>

<technique body: rolling-window tail, OR structured-state block, OR transcript file
path + search instruction>
```

## Quick Reference

| Task | How |
|---|---|
| Trigger | User invokes this skill; it never auto-fires |
| Input | The live conversation only — no pasted transcripts |
| Timing | Right before a new subtask, never mid-task |
| Technique choice | Always asked, every time — skill recommends one, user confirms or overrides |
| Rolling window | Last N messages verbatim; default N = 12, user-overridable |
| Selective pruning | Resolved → outcome + reason; open → full detail |
| RAG on history | Full transcript saved to `.compaction/<timestamp>-transcript.md`; artifact holds only the pointer |
| Handoff order | Herdr (`HERDR_ENV=1`) → Orca (`orca` present, app up) → paste-prompt |
| Consent | Confirm technique AND mechanism/topology before spawning |
| Large artifact | Write to a temp file and hand off the path |

## Notes

- **One technique, not a blend.** Do not combine two of the three in one artifact —
  blending defeats the point of picking the trade-off that fits this session.
- **Evidence pointers over paraphrase:** in selective pruning, cite a retrievable
  pointer (file path, run ID, URL) for bulky content instead of pasting it.
- **Excluded on purpose:** prompt compression. It solves a different problem (bulky
  prose, not conversation state) and must never be trusted to rewrite source code,
  tool-call arguments, or machine-readable data.
- **The hard limit:** because a skill cannot intercept the context window, compaction is
  always user-initiated. Do not claim automatic behavior.
- **Same-kind default:** hand off to the same agent kind as the current session unless
  told otherwise.
- **Persistent memory is a separate rung:** facts that should outlive this one handoff —
  standing user preferences, durable architectural decisions — belong in the persistent
  memory system, not just this artifact. The artifact travels with this handoff; memory
  travels with the user across every future session.
- **Exercise this before you need it:** run it on a live session occasionally rather than
  waiting for a context overflow to discover what the artifact is missing.

## Source

Distilled from the article "Conversation Compaction: Keep Long-Running Agents on Track".
