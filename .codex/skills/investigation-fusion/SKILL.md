---
name: investigation-fusion
description: Audits a frozen set of claims against authoritative documentation using a blind, heterogeneous multi-model jury coordinated through Orca. Freezes the target, dispatches one independent read-only investigator per model, requires every investigator before classifying, then produces a cited verdict sheet (accurate/outdated/incorrect/unsupported × unanimous/partial/contradictory) with proposed — never applied — changes. Use to deep-dive documentation, verify course or docs content, or fact-check version-sensitive claims with more than one model.
license: MIT
metadata:
  version: "1.2"
  scope: global
---

# Investigation Fusion

A bounded jury for documentation investigation: **freeze the claims, hand them to blind read-only investigators running different models, treat their agreement as evidence, and hand back a cited verdict sheet — not edits.**

This is the audit-first shape of the model-fusion pattern. Investigators do the deep documentation dive; a judge on a different model adjudicates where they split; the coordinator owns the frozen target, the classification, and the report.

## When to Use

- Deep-diving official documentation to verify whether a set of claims still holds.
- Auditing course material, guides, or onboarding docs for staleness after a version bump.
- Fact-checking version-sensitive statements: API names, defaults, limits, deprecations, renames.
- Any question where a single model's *memory* of the docs is the specific risk you are paying to avoid.

## When NOT to Use

- Routine single-source lookups — one agent plus a citation is enough. That is routing, not a jury.
- Code review or diffs — this skill audits *claims against documentation*, not code changes.
- Anything that must be edited in the same pass. This skill **proposes**; a human or a separate agent applies.
- When you cannot get two distinct models and the correlated-judge risk is unacceptable. The skill warns instead of failing silently (see Guardrails).

## Roles

| Role | Who | Sees | Never sees |
|---|---|---|---|
| **Coordinator** | The main agent | Everything | — |
| **Investigator** | One blind, read-only agent per model | The frozen claim list + shared rubric | Any other investigator's output |
| **Judge** | One agent on a model *not* in the investigator set | Investigators' structured findings | Investigators' raw reasoning |

The coordinator **never edits content during the investigation**. Detection and action are different jobs.

## Allowed research tools

Investigators research **only** with `chrome-devtools` MCP, `playwright` MCP, and `context7` MCP — nothing else. No generic `WebFetch`/`WebSearch`, no `curl`/`Bash` HTTP calls, no spawning another agent to browse for them. This is enforced two ways, not just requested:

1. **In the brief** (see the investigator brief template) — stated explicitly, every time.
2. **At launch, per agent type** (see [Launch reference](#launch-reference)) — technically restricted where the agent's CLI supports it:
   - **Claude:** `--tools "Bash,Read" --mcp-config investigator-mcp-config.json --strict-mcp-config` (bundled alongside this skill) — hard-blocks `Task`/`Agent` (closes the self-forking hole at the tool level, not just by instruction), `Write`/`Edit`, `WebFetch`, `WebSearch`, and every MCP server except the three sanctioned ones.
   - **Codex:** `--sandbox read-only --disable web_search` — hard-blocks file writes and the native web-search feature. Codex has no subagent-spawning tool, so no forking risk there. `chrome-devtools`/`playwright`/`context7` must already be registered via `codex mcp add` (one-time host setup, same as any model in the resolution table).
   - **opencode/nan:** launch with `--agent investigator`, a global agent definition at `~/.config/opencode/agents/investigator.md` (bundled alongside this skill; copy it there once per host) whose `permission` block denies `edit`, `write`, `webfetch`, `websearch`, `task` and allows only `bash` (needed for orchestration reporting — see the caveat below) plus the three MCP tool families.

**Known gap:** opencode's `bash` permission cannot be scoped to "only the `orca` commands you were given" the way Claude's `Bash(orca *)` pattern can — it's allow or ask, and "ask" recreates the unanswerable-permission-prompt stall this skill already had to fix once (see Known failure modes). So `bash: allow` stays broad for opencode investigators; the read-only guarantee for that agent type still rests partly on the brief's instruction, not purely on the permission block. Claude and codex don't have this gap.

If any of these three MCP servers isn't installed on the host, say so and ask before dispatching — same rule as an unresolvable model name.

## Decision Protocol

1. **Freeze** — one immutable, numbered, atomic claim list. No "have a look around".
2. **Blind** — every investigator gets the byte-identical target and rubric; none sees another's work.
3. **All-required** — no claim is classified until every investigator has reported.
4. **Investigator agreement is the gate** — a claim is `unanimous` only when every investigator independently reaches the same verdict. Grouping is done by the coordinator.
5. **The judge adjudicates, it does not re-investigate** — it resolves `partial` and `contradictory` claims and writes the verdict sheet.
6. **Propose, never apply** — the report contains proposed changes, explicitly marked as proposals.

## Vocabulary

| Term | Meaning |
|---|---|
| **Setup** | A named `role → (agent, model)` mapping. |
| **Dispatch** | Send the frozen claim set to one investigator. |
| **Collect** | Wait for `worker_done` from every investigator. |
| **Classify** | Derive the two-axis verdict per claim from agreement. |
| **Synthesize** | Coordinator writes the report and proposed changes. |

Do **not** use Orca's word *handoff*. A full handoff transfers ownership and never returns results. This pattern needs results back, so it is **supervised orchestration** (Run / Task / Dispatch / `worker_done`).

## Presets

Present every option with its full setup in parentheses.

| Preset | Investigators | Judge |
|---|---|---|
| `nan` | `mimo`, `qwen` | `deepseek` |
| `cross-opus` | `claude`, `codex`, `deepseek` | `opus` |
| `cross-codex` | `claude`, `deepseek` | `codex` |
| `custom` | user-authored | user-authored |

Example rendering:

```text
nan          (investigators: mimo, qwen · judge: deepseek)
cross-opus   (investigators: claude, codex, deepseek · judge: opus)
cross-codex  (investigators: claude, deepseek · judge: codex)
custom       (write your own role → agent, model mapping)
```

### Model resolution

| Short name | Agent | Orca model arg |
|---|---|---|
| `claude` | `claude` | agent default |
| `opus` | `claude` | `--model opus` |
| `codex` | `codex` | agent default |
| `deepseek` | `opencode` | `nan/deepseek-v4-flash` |
| `mimo` | `opencode` | `nan/mimo-v2.5` |
| `qwen` | `opencode` | `nan/qwen3.8-flash` |

Only resolve a model the host actually has. If a name cannot be resolved to an installed agent/model, say so and ask — never guess.

### Judge rule

The judge's **model** must not appear in the investigator set (model-level distinctness). Provider-*family* overlap is allowed but must be annotated.

- `nan`: judge `deepseek` is not among `mimo, qwen` → clean.
- `cross-codex`: judge `codex` is not among `claude, deepseek` → clean.
- `cross-opus`: judge `opus` shares the Anthropic family with investigator `claude` → allowed, **annotate**: `partial correlation — judge shares family with investigator claude`.

## Workflow

### Step 0 — Ask for the setup

Present the presets with full setups in parentheses plus `custom`. For `custom`:

1. Accept free text in the form `investigators: <a, b, c>; judge: <d>`.
2. Resolve each name through the model table.
3. **Echo the normalized `role → (agent, model)` mapping back for confirmation.**
4. Validate the judge rule; flag family overlap for annotation.
5. Launch only on an explicit go. If anything is ambiguous, ask instead of guessing.

### Step 1 — Freeze the target

Accept either:

- **(a) A source** — a file, directory, or URL to extract claims from; or
- **(b) Explicit claims** — a list supplied by the user.

Extract or accept **atomic** claims (one assertion each) that are **checkable** (version-sensitive statements, API/command names, defaults, limits, deprecations, factual framing). Report pure opinion/preference items separately as **not checkable** and exclude them.

Print the numbered frozen list and get an explicit go before dispatching. This list is the immutable target.

### Step 2 — Dispatch investigators

1. Create the Run: `orca orchestration run-create --objective "<objective>" --json`.
2. Persist the frozen claim list and the investigator brief to a file.
3. Choose how each investigator receives the target, **by agent type** — this is not optional, it depends on the worktree sandbox:
   - **Direct agents (`claude`, `codex`):** pass the **path/artifact reference**, never a re-summarized prompt (avoid lossy handoffs).
   - **opencode/nan investigators (`deepseek`, `mimo`, `qwen`):** **inline the claim list text directly into the `--spec`/task prompt.** Their sandbox blocks reads outside the dispatched worktree behind an interactive permission prompt nothing can answer non-interactively — a path reference to an out-of-worktree artifact (e.g. a session scratchpad) will stall the investigator indefinitely, not fail loudly.
4. Start one investigator per model, **all before the first wait**.
5. Keep an artifact path per investigator for the collected findings.

Use the launch path that matches the agent type — see [Launch reference](#launch-reference).

### Step 3 — Collect

Wait for every investigator. The default wait:

```text
orca orchestration check --wait --types "worker_done,escalation,question" --timeout-ms 900000 --json
```

A timeout or empty result is a checkpoint, not a failure. Keep waiting; after three consecutive empty waits, enumerate with `worker-list` and read each row's `projection.nextAction`.

**Silent dispatch check:** if one dispatch has produced zero heartbeats for several minutes while its siblings heartbeat normally, don't wait out the full timeout blind — read that dispatch's terminal directly (`orca terminal read --terminal <handle> --screen`). Total silence (not an error, not a failure state) is the exact signature of a dead CLI auth token or a stuck interactive permission prompt — both leave the dispatch sitting at an idle screen forever. A blind `check --wait` cannot distinguish "still starting" from "will never produce output," so verify directly rather than assuming more time will resolve it.

**All-required enforcement:**

- If an investigator fails or times out, re-dispatch it **once** against the same frozen target.
- A CLI-level auth failure (e.g. an expired or already-used refresh token) typically reproduces **identically** on retry — after re-dispatching, check the terminal screen directly to confirm it actually started producing output before waiting out a second full timeout. If it fails the same way again, stop retrying immediately rather than burning a second full wait.
- If it still fails, stamp the run `incomplete` in the report. Claims that investigator would have covered **cannot reach `unanimous`**.

### Step 4 — Classify

The coordinator derives the two-axis verdict per claim. Two axes, because they answer different questions:

**Axis 1 — Verdict (what the docs say):**

| Verdict | Meaning |
|---|---|
| `accurate` | Claim still holds. |
| `outdated` | Held once; docs show it moved on (version bump, deprecation, rename). |
| `incorrect` | Docs contradict the claim as written. |
| `unsupported` | No authoritative source found either way. |

**Axis 2 — Agreement (how the investigators landed):**

| Agreement | Meaning |
|---|---|
| `unanimous` | Every investigator reached the same verdict. |
| `partial` | One or some only. Must stay visible — never silently dropped. |
| `contradictory` | Conclusions cannot all be true → routed to the judge, then the human. |

**Derived action:** `keep` / `update` / `replace` / `flag-for-human`.

Do not average away dissent. A `partial` verdict is a finding, not noise.

### Step 5 — Judge

Dispatch the judge on the preset's model. It receives the **structured findings only** (the collected artifacts), never the investigators' raw reasoning. Its job:

- Adjudicate `partial` and `contradictory` claims using the cited evidence.
- Write the verdict sheet rows.
- Mark anything it cannot resolve as `flag-for-human`.

The judge does not re-investigate, and does not gain edit rights.

### Step 6 — Report

Write the report to a file — default `investigation-fusion-report-<YYYY-MM-DD>.md` in the current working directory, name overridable at launch — and print the verdict sheet summary in chat.

The report contains, per claim:

- the claim text and its verdict `verdict × agreement`;
- the derived action;
- the cited evidence (see [Evidence standard](#evidence-standard));
- the **proposed change**, clearly marked *proposed, not applied*.

Terminal state: report written, verdict sheet printed, run released. Nothing else happens.

### Optional — second-opinion round

**Off by default.** When enabled, and only for claims that came back `contradictory`, run **one** bounded round: a fresh investigator or the judge arbitrates, capped at one round, then escalate to the human. Never let this become an open debate loop.

## Investigator brief (template)

```text
You are an investigator in a documentation audit. Work read-only. Do not edit
any file.

Do NOT spawn your own sub-agents, forks, or parallel tasks to split this work.
Investigate every claim yourself, sequentially, in this one session, and send
exactly one worker_done at the end. A sub-fork can inherit your dispatch
credentials and independently try to report completion, racing you and
corrupting the run.

Research ONLY with chrome-devtools, playwright, and context7 tools. Do not use
generic web fetch/search, do not shell out to curl or another HTTP client, and
do not use any tool not explicitly listed here.

Frozen target: the numbered claims in <path-to-frozen-claims-or-inline>.
Investigate every claim against authoritative documentation. You are blind to
every other investigator: do not ask for, seek, or infer their output.

Rubric (identical for every investigator):
- Is the claim accurate as written for the CURRENT version?
- Is it outdated (renamed, deprecated, changed default, changed limit)?
- Is it incorrect?
- Is it unsupported (no authoritative source can be found)?

Evidence standard — no source, no verdict:
- Cite at least one admissible source per claim with URL (or repo path) +
  version/date + a short quoted excerpt or precise locator.
- Admissible, in priority order: (1) official docs / release notes / changelog
  for the specific version, (2) upstream source, types, or schemas,
  (3) maintainer statements or triaged issues.
- Blog posts, Stack Overflow, and your own memory are NOT admissible as proof.
  They may only point at where to look.
- For `unsupported`, cite nothing but state exactly what you searched.

Return, per claim, in this shape:
- claim id
- verdict: accurate | outdated | incorrect | unsupported
- evidence: source URL/path, version/date, quoted excerpt or locator
- confidence: low | medium | high
- notes: only what affects the verdict

Report findings only. Do not propose edits unless a proposed change is obvious
and one line long.
```

## Judge brief (template)

```text
You are the judge in a documentation audit. Work read-only. Do not edit files.

You receive the investigators' structured findings in <path-to-findings>.
You do NOT receive their raw reasoning, and you must not ask for it.

Your job:
1. For each claim, take the investigators' verdicts as independent evidence.
2. Claims where all investigators agree are settled — leave them.
3. For `partial` and `contradictory` claims, adjudicate using the cited
   evidence only. Decide the verdict and the agreement level.
4. Mark anything you cannot resolve from the evidence as flag-for-human.
5. Never average away dissent. A split is information.

For each claim return: claim id, verdict (accurate | outdated | incorrect |
unsupported), agreement (unanimous | partial | contradictory), the strongest
supporting citation, and a one-line rationale. Flag any claim where the
evidence itself is contradictory rather than merely sparse.
```

## Launch reference

`ORCA` is a placeholder for the resolved Orca executable (see the `orca-cli` skill). Prefer `--json`.

**Direct agents (`claude`, `codex`)** — one call, supports model/effort. Pass the frozen
target as a path reference (their sandbox already covers the worktree). Restrict tools
per [Allowed research tools](#allowed-research-tools):

```text
# Claude — --tools/--mcp-config/--strict-mcp-config are not exposed by worker-start
# directly; launch via a custom terminal command instead of --agent claude when you
# need the tool restriction enforced (worker-start --agent gives you the bare CLI):
orca terminal create --worktree current --title "investigator-claude" \
  --command "claude --tools \"Bash,Read\" --mcp-config /path/to/investigation-fusion/investigator-mcp-config.json --strict-mcp-config" --json
orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
orca orchestration worker-start --task <task_id> --terminal <handle> --json

# Codex — --sandbox and --disable ARE exposed inline via --spec/worker-start flags:
orca orchestration worker-start --spec "<investigator brief + frozen target path>" \
  --worktree current --agent codex --model opus --effort high --json
  # (add --sandbox read-only --disable web_search if your worker-start build passes
  # extra agent flags through; otherwise use the terminal-create form above for codex too)
```

**`opencode` / nan models (`deepseek`, `mimo`, `qwen`)** — two steps, because
`worker-start --model` does not cover opencode; create the terminal with custom argv,
then take lifecycle ownership of it. **Inline the frozen claim list text directly into
the `--spec`, do not pass a path** — opencode's sandbox blocks reads outside the
dispatched worktree behind an interactive permission prompt that will stall the
investigator indefinitely if the target lives anywhere else (e.g. a session scratchpad).
Launch with `--agent investigator` (see [Allowed research tools](#allowed-research-tools))
to restrict tools:

```text
orca orchestration task-create --spec "<investigator brief with claims inlined verbatim>" --json
orca terminal create --worktree active --title "investigator-<name>" \
  --command "opencode --model nan/deepseek-v4-flash --agent investigator" --json
orca terminal wait --terminal <handle> --for tui-idle --timeout-ms 60000 --json
orca orchestration worker-start --task <task_id> --terminal <handle> --json
```

Only send the prompt after `terminal wait` reports `satisfied: true`; a prompt typed into a
still-starting TUI is lost. Use the whole `<repoId>::<path>` worktree id where a worktree
selector is required. If the frozen claim list must live inside the worktree for some
other reason, that also works — the requirement is "not outside the worktree," not
"inline only."

**Collect:**

```text
orca orchestration check --wait --types "worker_done,escalation,question" --timeout-ms 900000 --json
orca orchestration reply --id <message_id> --body "<answer>" --json
orca orchestration worker-release --dispatch <dispatch_id> --json
```

A review-only `worker_done` authorizes synthesis of findings, **not** coordinator file edits.
Keep the report and the (proposed) content changes separate.

## Evidence standard

**No source, no verdict.**

Every verdict except `unsupported` must cite at least one **primary** source with URL (or repo path) + version/date + a short quoted excerpt or precise locator.

Admissible, in priority order:

1. Official docs / release notes / changelog for the **specific version**.
2. Upstream source, types, or schemas.
3. Maintainer statements or triaged issues.

**Inadmissible as proof:** blog posts, Stack Overflow, and the model's own memory. They may only point at where to look.

`unsupported` requires no citation, but the investigator must state what was searched and found lacking.

## Guardrails

- **Correlated judges.** Investigators decorrelate *only* by model family. If the setup resolves to one model, or the judge shares a family with an investigator, stamp the report: `partial correlation — agreement is not fully independent evidence`.
- **Anchoring.** Never show an investigator the first answer or another investigator's output before its own pass.
- **Weak aggregation.** The rule is fixed: investigators report, coordinator classifies by agreement, judge adjudicates splits. Do not "summarize the answers".
- **Judge bias.** Anonymize nothing is needed across blind investigators, but the judge must never see raw reasoning; it sees structured findings and citations only.
- **Immutable target.** If scope needs to change mid-run, stop the run and re-freeze. Do not widen the target in flight.
- **No edits.** Investigators and the judge are read-only. The report proposes; applying is a separate, explicit step.
- **Completeness.** A partial jury is not a jury. Re-dispatch a failed investigator once, then mark the run `incomplete` and surface it.
- **Self-forking investigators.** An investigator must never spawn its own sub-agents/forks to split the claim list — a sub-fork can inherit the coordinator's dispatch credentials and independently race to send `worker_done`, producing rejected or mutually-inconsistent completion reports. The prohibition belongs in the brief itself (see the template), not just here — state it up front for every model, every time, not only after a run breaks.
- **opencode/nan sandbox.** opencode-backed investigators (`deepseek`, `mimo`, `qwen`) cannot read files outside their dispatched worktree without an interactive permission prompt nothing can answer non-interactively. Inline the frozen claim list into the task spec for these investigators; reserve path references for direct agents (`claude`, `codex`).
- **Silent dispatch.** Zero heartbeats is not evidence a dispatch is "still starting" — it is the same signature as a dead CLI auth token or a stuck permission prompt. Check the terminal screen directly rather than trusting a long `check --wait` to eventually reveal the problem.
- **Tool allowlist.** Investigators research only with chrome-devtools, playwright, and context7 MCP tools — see [Allowed research tools](#allowed-research-tools). Enforce it at launch (per agent type) as well as in the brief; a brief-only instruction is the weaker of the two and shouldn't be the only layer when the CLI supports a harder restriction.

## Quick Reference

| Action | How |
|---|---|
| Ask for setup | Print presets with full setups + `custom` |
| Custom setup | Free text → normalize → echo for confirmation → validate judge rule |
| Freeze target | Atomic, checkable claims → numbered list → explicit go |
| Direct agent launch | `worker-start --spec … --agent claude\|codex --model … --effort …` (path reference OK) |
| Nan model launch | `terminal create --command "opencode --model nan/<id>"` → `worker-start --task … --terminal …` (**inline claims, never a path**) |
| Collect | `check --wait --types "worker_done,escalation,question"`; if one dispatch is silent while siblings heartbeat, `terminal read --screen` it directly |
| Classify | verdict `accurate/outdated/incorrect/unsupported` × agreement `unanimous/partial/contradictory` |
| Judge | Structured findings only; adjudicate splits; write verdict sheet |
| Report | `investigation-fusion-report-<date>.md` + chat summary; proposals marked, not applied |
| Second opinion | Opt-in, `contradictory` claims only, one round, then human |

## Notes

- This skill is provider-agnostic in intent but grounded in Orca's current command surface. If Orca's CLI changes, load the version-matched guide with `ORCA skills get orchestration` before adjusting commands — do not guess flags.
- Every model name in the presets must resolve to an **installed** agent/model on the host. Unresolvable names are reported, never guessed.
- The presets differ mainly in the judge; that is the axis being varied. Keep the investigator set identical when comparing two judges (`cross-opus` vs `cross-codex`) so the comparison is clean.

## Known failure modes (v1.1)

Observed directly in a live `cross-opus` run (course-material staleness audit, 2026-09-20) before the fixes above existed:

1. A `claude` investigator, given a brief with no anti-forking instruction, used its own Agent/Task tool to fan the claim list out to sub-forks. The sub-forks inherited the coordinator's dispatch capability and raced to send `worker_done`, producing one accepted completion and three rejected, mutually-inconsistent duplicates. Fixed by the explicit prohibition now in the investigator brief template.
2. Two opencode-backed investigators stalled indefinitely on an interactive "Allow this directory?" permission prompt when the frozen claim list was referenced by a path outside their worktree (a session scratchpad). Fixed by requiring inlined claims for opencode/nan investigators.
3. A codex dispatch sat at an idle prompt with zero heartbeats for the entire wait window because its CLI had a dead, already-used refresh token — indistinguishable from "still starting" under a blind `check --wait`. A retry failed identically. Fixed by the silent-dispatch check and the "auth failures reproduce identically" note in the all-required enforcement rule.

**v1.1 verified (2026-09-20, same day):** re-ran the identical 16-claim audit with the identical `cross-opus` stack. Fixes #1 and #2 both held on the first try — claude sent exactly one clean `worker_done`, and both opencode-backed investigators started researching immediately with no permission-prompt stall. codex's retry-once flow also worked cleanly against a *different* failure (an external process kill, not the original dead-token scenario, which wasn't reproduced since codex's auth was healthy this time).

## v1.2 changes

- **`glm` removed from every preset** (`nan`, `cross-opus`, `cross-codex`) and the model resolution table. It was consistently the slowest investigator across two live runs and, in the second run, was the only one of four that never completed within the wait window (while actively researching, not stuck) — removed rather than chased with indefinite retries. `nan` is now a 2-investigator preset (`mimo`, `qwen`); `cross-codex` is now a 2-investigator preset (`claude`, `deepseek`). Both still satisfy the "two distinct models minimum" rule in When NOT to Use, but are thinner juries than before — say so if a user asks for either.
- **Tool allowlist added** (chrome-devtools/playwright/context7 MCP only) — see [Allowed research tools](#allowed-research-tools). Requested by the skill's maintainer after observing investigators default to generic `WebFetch`/`WebSearch`/upstream-repo `curl` calls instead of a consistent tool surface. Bundled artifacts: `investigator-mcp-config.json` (Claude's `--mcp-config`) and a global opencode agent at `~/.config/opencode/agents/investigator.md` — both live alongside this skill file and must be copied/available on any new host before dispatching.
