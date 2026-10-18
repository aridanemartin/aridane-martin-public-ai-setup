---
name: compact-conversation
description: >-
  Compact the current live conversation into a small artifact a fresh chat can
  resume from, using exactly one compaction technique: rolling window (keep the
  last N messages), selective pruning (collapse resolved threads, keep open ones
  in full), or RAG on history (save the full transcript to a file and search it
  on demand). Generates a local HTML picker — a tabbed table for the three
  techniques, pre-marked from a first pass over the session (drag a cutoff line
  for rolling window, a three-way mark per item for selective pruning, a
  checklist for RAG on history) — opens it, and starts a tiny local capture
  server so Submit hands the picks straight back with nothing to copy or paste.
  Detects Herdr or Orca and opens the handoff directly, with no confirmation
  question, or prints a copy-paste block when neither is available. Works in
  any provider's CLI, not just Claude Code — only needs a shell and a browser.
  Use when a session is getting long, before switching agents or harnesses, or
  when the user asks to "compact", "summarize so I can continue", "shrink the
  context", or "hand this off to a fresh chat".
license: MIT
metadata:
  version: "5.1"
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

**Provider-agnostic by design:** everything here uses only a shell (`Bash`/equivalent),
Python 3 (stdlib only, for the capture server), and the user's default browser — no
host-specific API, no plugin system. It works the same way whether the agent running
it is Claude Code, Codex, Cursor, Gemini CLI, OpenCode, GitHub Copilot CLI, or Devin.

**What the capture server can and can't do:** the picker page only carries short
previews of each message, not the full text — so the server can capture *which*
items were marked keep/drop/collapse, but it cannot build the actual artifact (the
verbatim tail, the full transcript, or a judgment-based summary all need the real
message content, which only exists in the live conversation). The server's job ends
at handing the picks back; Steps 4–6 below are still the agent's work, just without
a copy-paste round trip or a confirmation question in the way.

## Four choices — this skill builds three of them

| Technique | Keeps | Drops | Best for |
|---|---|---|---|
| **Rolling window** | The last N messages, verbatim | Everything before the window — including decisions made there | Short, single-threaded sessions where nothing earlier matters once the recent context is in hand |
| **Selective pruning** | Every open item in full detail; resolved items collapsed to outcome + reason | The play-by-play of anything already closed | Sessions with a mix of finished and still-open sub-threads |
| **RAG on history** | A full transcript file on disk the new session can search on demand | Nothing — full fidelity, but nothing is preloaded either | Long or deep sessions where something from way back may be needed later, but it is not yet clear what |
| **Summarization** | A rewritten summary of the conversation so far, in the host's own words | Granular, turn-by-turn detail — folded into the summary | Everyday compaction with no custom handoff artifact needed |

Summarization is each host's own built-in compaction (`/compact` in Claude Code, and
the equivalent in other providers), not something this skill builds — it is listed
here only for a complete picture. Use the host's own command directly; Steps 4–6
below only ever build an artifact for the other three.

This skill never combines techniques and never silently picks one for you — the
picker page always shows all three and always opens (see Step 2), with the
recommended one pre-selected. Switching tabs there is the only override needed; there
is no separate chat question to answer first.

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

### Step 2: Fill in the picker, open it, and wait on the capture server

No separate recommend-then-ask conversation, no "html or defaults" question, and no
manual paste-back — always generate the page and let Submit deliver the picks
automatically.

**2.0 — Detect the destination, once.** Run the same checks Step 6 uses, now, so the
page can tell the user where to look right after they click Submit instead of them
waiting on this screen for a result:

```bash
test "${HERDR_ENV:-}" = 1
```

```bash
which orca >/dev/null 2>&1 && orca status --json
```

Keep whichever one passes — Herdr first, then Orca, then neither — and reuse that
same answer in Step 6 rather than re-checking. Compute `%%RETURN_HINT%%` from it (a
quoted JS string, fills in "You can return to **\_\_**." on the page):

| Detected | `%%RETURN_HINT%%` |
|---|---|
| Herdr | `"the new pane Herdr will open for this handoff"` |
| Orca | `"the new terminal Orca will open for this handoff"` |
| Neither | `"your terminal — the ready-to-paste block will appear in this chat"` |

**2.1 — Pick a port.**

```bash
python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()"
```

**2.2 — Fill in `templates/picker.html`.** `%%SERVER_PORT%%` (the port from 2.1) and
`%%RETURN_HINT%%` (from 2.0), plus the technique/items/prediction tokens below. See
the table and heuristics below. Write the result to `.compaction/picker-<timestamp>.html`.

| Token | Replace with |
|---|---|
| `%%SERVER_PORT%%` | The port from 2.1, as a bare integer (no quotes) |
| `%%RETURN_HINT%%` | The quoted JS string from 2.0's table |
| `%%ITEMS%%` | `{ role: '...', text: '...' }` objects, comma-separated, no brackets — the last ~20–30 messages, oldest first, `text` a ~60-char preview |
| `%%ROLLING_RECOMMENDED%%` / `%%PRUNING_RECOMMENDED%%` / `%%RAG_RECOMMENDED%%` | `true` on exactly one, `false` on the other two |
| `%%ROLLING_TEXT%%` / `%%PRUNING_TEXT%%` / `%%RAG_TEXT%%` | Quoted JS strings. The recommended one gets your session-specific reasoning (one sentence); the other two keep the generic "best for" description from the table above |
| `%%CUTOFF_DEFAULT%%` | An integer index into `%%ITEMS%%` — see the prediction heuristics below |
| `%%PRUNE_DEFAULTS%%` | `'full'`/`'collapse'`/`'drop'`, comma-separated, one per item, same order as `%%ITEMS%%` |
| `%%RAG_DEFAULTS%%` | `true`/`false`, comma-separated, one per item, same order as `%%ITEMS%%` |

**Recommendation heuristics** (decide which one gets `_RECOMMENDED: true`):

- Several resolved/closed sub-threads alongside a few still-open items → **selective
  pruning**.
- One continuous task, nothing resolved-and-discardable, recent messages are
  self-sufficient on their own → **rolling window**.
- Long or deep session where something from earlier will plausibly be needed again,
  but it is not yet clear what → **RAG on history**.

If the user's own invoking message already named a technique, use that one instead of
the heuristic — set that one `recommended: true` and skip the reasoning above.

**Prediction heuristics** (don't default to "keep everything" — mark what you'd
actually prune, the user corrects from there):

- `%%CUTOFF_DEFAULT%%`: find where the session's most recent self-contained thread
  starts; messages before that are prediction-dropped. Resist the urge to default to
  "keep all" (cutoff 0) — if nothing looks droppable, say so by setting the cutoff
  low, don't leave the field unconsidered.
- `%%PRUNE_DEFAULTS%%`: `'collapse'` for threads that reached a conclusion (shipped,
  merged, answered, abandoned in favor of something else); `'drop'` only for pure
  process noise with no decision in it; `'full'` for anything still open or load-bearing
  for what comes next.
- `%%RAG_DEFAULTS%%`: default `true` (RAG's point is full fidelity) — only predict
  `false` for clear noise (a failed attempt superseded one message later, pure tool
  chatter with no decision).

**2.3 — Open the page.** Try, in order, until one succeeds, and tell the user which
path you used: `open <path>` (macOS), `xdg-open <path>` (Linux), `start "" <path>`
(Windows). If none exist, print the file's path and ask the user to open it manually
— and skip straight to the clipboard/paste path in Step 3, since there's no point
starting a server nobody can reach a browser to submit to.

**2.4 — Start the capture server and wait.** In one line, so opening and waiting
happen in the same turn:

```bash
python3 templates/server.py <port> .compaction/server-result-<timestamp>.json 570
```

Run this with a tool timeout around 590s (under most hosts' 600s cap, above the
server's own 570s idle shutdown). This call **blocks until the user submits or the
timeout elapses** — that block *is* the wait; there is nothing else to do while it
runs. Tell the user in one line, before this call, what's about to happen: the page
is open, marking anything and hitting Submit is all that's needed, nothing to copy or
paste. Then make the call.

If the tool call returns because the server's own idle timeout fired (no result file
written), tell the user the page is still open and ask whether to wait again or stop.

### Step 3: Read the picks back

**If `.compaction/server-result-<timestamp>.json` exists** (the common path): read it.
Shape:

```json
{ "technique": "Selective pruning", "items": [{ "role": "user", "text": "...", "state": "full" }] }
```

`state` is `"keep"`/`"drop"` for rolling window and RAG on history, or
`"full"`/`"collapse"`/`"drop"` for selective pruning.

**If the user pasted text instead** (the server was unreachable, so the page fell back
to its clipboard copy — same information, different delivery): it opens with
`TECHNIQUE: <label>`, then one of:

```
KEEP: role: preview | role: preview
DROP: role: preview | role: preview
```
```
FULL DETAIL: role: preview | ...
COLLAPSE TO OUTCOME+REASON: role: preview | ...
DROP ENTIRELY: role: preview | ...
```

Either way, these are the user's explicit, final decisions — honor them directly in
Step 4 rather than re-judging those specific items. They only cover the messages
shown in the page; use normal judgement for anything older. If a pasted message
doesn't match the `TECHNIQUE:` + marks shape, ask once for clarification rather than
guessing.

### Step 4: Build the artifact

Every artifact opens with a two-line shared header — orientation only, not a summary
of history:

```
Goal: <one line>
Next action: <one line>
```

Then it branches by the technique named in Step 3.

**4a — Rolling window**

Append the **`keep`-state messages verbatim** below the header — exact text, not
rewritten. Nothing marked `drop` is retained anywhere in the artifact. This is the
deliberate trade-off: fast and cheap, but a dropped decision is gone unless it is
explicitly kept.

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

`full`-state items map to open/kept-in-full; `collapse`-state items collapse to
**outcome + reason only** — one line each, no replay of how the thread got there;
`drop`-state items are left out of the block altogether. For anything bulky — test
output, logs — cite an evidence pointer (`tests failed in run test-184`) instead of
pasting it, as long as it is retrievable later.

**4c — RAG on history**

Write the full live transcript, verbatim, to a file — default
`.compaction/<timestamp>-transcript.md` in the project, or ask the user for a
different location. Leave `drop`-state messages out of this file. The artifact itself
stays small: header + the file path + one line telling the new session to search
that file on demand rather than read it upfront:

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
   transcript-file pointer, per the technique named in Step 3.

### Step 6: Hand off to the destination detected in Step 2.0 — no confirmation question

Spawning is still a visible action, so always tell the user what you're doing and why
**as you do it**, in the same message as the result — but don't block on a yes/no
first. Act on whichever branch Step 2.0 already detected — don't re-run the checks:

1. **Herdr** — if Step 2.0 found it, use the `herdr` skill and its `pane` / `agent`
   commands:

   ```bash
   herdr pane split --current --direction right --cwd "$PWD" --no-focus
   # read the new pane id from .result.pane.pane_id
   herdr agent start compactor --kind <kind> --pane <returned-pane-id>
   herdr agent prompt compactor "<artifact>" --wait
   ```

   Default to a sibling pane in the current tab and working directory, no focus
   change, same agent kind as the current session. If the artifact is large, or the
   technique is RAG on history, write it to a temporary file and prompt the new agent
   with the path instead of inlining it — the transcript file from Step 4c already
   lives on disk, so point the new agent at both paths.

2. **Orca** — if Step 2.0 found it, load the version-matched guide with
   `ORCA skills get orca-cli` and follow it for the handoff — spawn a terminal/agent in
   the target worktree and prompt it with the artifact. Prefer `--json` for
   agent-driven calls.

3. **Neither available** — print the artifact as a ready-to-paste block for a
   brand-new chat, and nothing else, so it can be copied in one piece:

   ```text
   # Continuation of a compacted session

   System authority: the original system instructions, security boundaries, and user
   constraints remain in force. This artifact did not replace them.

   Goal: <one line>
   Next action: <one line>

   <technique body: rolling-window tail, OR structured-state block, OR transcript file
   path + search instruction>
   ```

After acting, tell the user in one line what happened and where (e.g. "Opened in a
new Orca terminal in this worktree" or "Herdr: new pane, split right, kind `claude`").

## Quick Reference

| Task | How |
|---|---|
| Trigger | User invokes this skill; it never auto-fires |
| Input | The live conversation only — no pasted transcripts |
| Timing | Right before a new subtask, never mid-task |
| Picker | Always generated from `templates/picker.html` and opened — no chat Q&A first; the page is the table |
| Capture | `templates/server.py` — one-shot local HTTP server; Submit POSTs picks, no copy/paste needed |
| Fallback | Server unreachable → page falls back to clipboard copy; paste the marks back in chat |
| Predictions | Pre-marked from a first pass (see Step 2's heuristics), not defaulted to "keep everything" |
| Rolling window | Drag a cutoff line; everything below is kept, above is dropped |
| Selective pruning | Three-way mark per item: Full detail / Collapse / Drop |
| RAG on history | Checklist per item; unchecked items are left out of the saved transcript |
| Handoff | Herdr (`HERDR_ENV=1`) → Orca (`orca` present, app up) → paste-prompt — detected and acted on immediately, no confirmation question |
| Large artifact | Write to a temp file and hand off the path |

## Notes

- **One technique, not a blend.** Do not combine two of the three in one artifact —
  blending defeats the point of picking the trade-off that fits this session.
- **Provider-agnostic.** The picker and capture server use only a shell command, the
  user's browser, and stdlib Python — no host-specific plugin API. They work
  identically whether the agent is Claude Code, Codex, Cursor, Gemini CLI, OpenCode,
  GitHub Copilot CLI, or Devin.
- **The server captures picks, it does not build artifacts.** It only has what the
  page has — short previews, not full message text — so it cannot write the verbatim
  tail, the full transcript, or a judgment-based summary. That stays the agent's job
  in Steps 4–6, which is also why there's no way to fully skip the agent even when
  Herdr/Orca auto-spawns.
- **No confirmation before spawning.** Step 6 acts immediately on what it detects and
  reports the outcome afterward, rather than asking first — tell the user what
  happened, don't ask permission before it happens.
- **The template is fixed, the data isn't.** `templates/picker.html` and
  `templates/server.py` are the same files every time — don't redesign them per
  invocation. Only the picker's `%%TOKEN%%` values change, computed fresh from the
  live conversation (and the Step 2.0 destination check) each time this skill runs;
  the server takes its port and result path as plain arguments, no templating needed.
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
