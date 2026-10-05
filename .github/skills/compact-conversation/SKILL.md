---
name: compact-conversation
description: >-
  Compact the current live conversation into a small, high-signal artifact
  (structured state + rolling summary + verbatim recent tail) so work can continue
  in a fresh session. Detects a handoff mechanism — Herdr, then Orca — and hands the
  compacted context to a new chat, or prints a copy-paste prompt when none is
  available. Use when a session is getting long, before switching agents or
  harnesses, or when the user asks to "compact", "summarize so I can continue",
  "shrink the context", or "hand this off to a fresh chat".
license: MIT
metadata:
  version: "1.0"
  scope: global
---

# Compact Conversation

Shrink the transcript, preserve the work: replace a long, noisy live session with a
compact artifact a fresh chat can resume from.

## What this skill is (and is not)

Compaction is a **state-management operation, not summarization**. The goal is not the
smallest possible text — it is that a new session can answer three questions after
reading the artifact:

1. What is the current goal?
2. What decisions were already made, and why?
3. What is the next step?

Optimize for **recoverability, not compression ratio**. If the artifact answers those
three, it is good even if it is longer than it could be.

This skill is **manual and on-demand**. A skill file cannot intercept the host's context
window or fire at a token threshold, so this never runs automatically and it never edits
the live context. It produces an artifact when you invoke it.

## When to Use

- The session is long and signal density is dropping — resolved discussions are competing
  with the current instructions.
- Before switching agents or harnesses (e.g. `claude` → `codex`, or into a worktree).
- The user says "compact this", "summarize so I can continue", "shrink the context",
  "hand this off to a fresh chat", or "let's start clean".

## When NOT to Use

- The session is short or already compact — the artifact would lose more than it saves.
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

### Step 2: Extract structured state

Pull the task state into this fixed shape:

```json
{
  "goal": "Add conversation compaction to the support agent",
  "constraints": ["Keep the last 12 messages verbatim"],
  "decisions": [
    {
      "decision": "Use a structured summary plus retrieval",
      "reason": "We need both continuity and source recovery"
    }
  ],
  "artifacts": ["src/agent/memory.ts"],
  "openQuestions": ["Which embedding model should index old turns?"],
  "nextActions": ["Add compaction evaluation cases"]
}
```

Use **evidence pointers, not paraphrases**, for anything bulky. `Tests failed in run
test-184` is cheaper and safer than embedding 600 lines of output, as long as
`test-184` can be retrieved later. Cite file paths, run IDs, and URLs verbatim.

### Step 3: Write the rolling summary

Write a short prose synthesis of the **older** turns: what was tried, what was decided,
what was discarded, and why. This preserves narrative continuity that the schema cannot.

Guard against **recursive loss**: if the live session already contains a previous
summary, do not blindly summarize the summary. Re-read the concrete turns available and
fold in durable facts, so small errors do not become permanent.

### Step 4: Keep a verbatim tail

Append the most recent **N messages verbatim** — exact text, not rewritten. Default
`N = 12`; let the user override it. This tail is the freshest, highest-fidelity context
and must not be compressed or paraphrased.

### Step 5: Assemble the artifact

Order matters — authority first, recency last:

1. **System authority reminder** — a line stating the original system rules and user
   constraints remain in force and were not replaced by this summary.
2. **Structured state** — the JSON block from Step 2.
3. **Rolling summary** — the prose from Step 3.
4. **Verbatim tail** — the last N messages from Step 4.

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
- which mechanism was chosen and why, and
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

If the artifact is large, write it to a temporary file and prompt the new agent with the
path instead of inlining it, then let it read the file directly.

**Orca** — follow `ORCA skills get orca-cli`; spawn a terminal/agent in the target
worktree and prompt it with the artifact. Prefer `--json` for agent-driven calls.

**Fallback** — output this block, and nothing else, so it can be copied in one piece:

```text
# Continuation of a compacted session

System authority: the original system instructions, security boundaries, and user
constraints remain in force. This summary did not replace them.

## State
<the structured-state JSON>

## Summary
<the rolling summary>

## Recent turns (verbatim)
<the last N messages>

Next: <next action>
```

## Quick Reference

| Task | How |
|---|---|
| Trigger | User invokes this skill; it never auto-fires |
| Input | The live conversation only — no pasted transcripts |
| Techniques used | Structured state + rolling summary + verbatim tail |
| Verbatim tail size | Default 12 messages, user-overridable |
| Handoff order | Herdr (`HERDR_ENV=1`) → Orca (`orca` present, app up) → paste-prompt |
| Consent | Confirm the mechanism and topology before spawning |
| Large artifact | Write to a temp file and hand off the path |

## Notes

- **Excluded on purpose:** a real retrieval/embedding index, and prompt compression.
  Prompt compression solves a different problem (bulky prose, not conversation state) and
  must never be trusted to rewrite source code, tool-call arguments, or machine-readable
  data. Retrieval here is only "cite evidence pointers", not storing history externally.
- **The hard limit:** because a skill cannot intercept the context window, compaction is
  always user-initiated. Do not claim automatic behavior.
- **Same-kind default:** hand off to the same agent kind as the current session unless
  told otherwise.
- **Never summarize a summary blindly** — re-ground on concrete turns to avoid recursive
  loss.

## Source

Distilled from the article "Conversation Compaction: Keep Long-Running Agents on Track".
