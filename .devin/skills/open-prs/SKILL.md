---
name: open-prs
description: Reports every open pull request across all GitHub repos and returns a list with URLs. Use when the user types /open-prs or asks to "list my open PRs", "show my open pull requests", "what PRs do I have open", "open-prs" — anywhere you need an inventory of the user's open PRs with links.
metadata:
  author: aridane-martin
  type: technique
  scope: root
---

# Open PRs

Lists every open pull request across all of the user's GitHub repos and returns a clean list with URLs.

---

## When to Use

- `/open-prs`
- "List my open PRs", "show my open pull requests", "what PRs do I have open globally?"
- Any request for a cross-repo inventory of the user's open PRs

## When NOT to Use

- PRs for a single specific repo → just run `gh pr list -R <owner/repo> --state open`
- Opening a new PR → use `create-pr`
- Triaging issues → use `triage`

---

## Workflow

### Step 1 — Pre-flight checks

Run these first (in parallel):

```bash
which gh && gh --version          # gh must be installed
gh auth status                    # must show an authenticated active account
```

If `gh` is missing or unauthenticated, stop and report the failure — do not try to work around it.

### Step 2 — Fetch all open PRs across every repo

The primary source is a single GitHub search over all repos authored by the current user:

```bash
gh search prs \
  --author @me \
  --state open \
  --limit 200 \
  --json number,title,url,repository,isDraft,createdAt,updatedAt
```

This returns a flat JSON array covering every repo the user has access to. Capture the raw result (save it to a variable or temp file) so you can group and format it.

> **"all gh repos" note:** `--author @me` covers PRs the user opened anywhere. If the user explicitly wants **all** open PRs inside their repos (including PRs authored by teammates/bots), fall back to iterating repos:
>
> ```bash
> gh repo list --limit 1000 --json nameWithOwner --jq '.[].nameWithOwner'
> ```
>
> then for each repo: `gh pr list -R <nameWithOwner> --state open --json number,title,url,isDraft`.

### Step 3 — Format the list

Group PRs by repository and return each PR as a line with its **URL** and a short label. Minimum per entry:

- Pull request URL
- PR title
- Repo (if grouping isn't obvious)
- Draft marker if `isDraft` is true

Example of the final output shape:

```
Open PRs (3 in 2 repos):

aridanemartin/ai-engineer-interview-prep
  [1] AI Notes lessons — 2026-08-30
      https://github.com/aridanemartin/ai-engineer-interview-prep/pull/1

aridanemartin/connectia-students
  [42] feat(auth): password reset (draft)
      https://github.com/aridanemartin/connectia-students/pull/42
```

Serve the URLs as clickable markdown links: `[title](url)`.

### Step 4 — Report

- Print the grouped list, one line per PR, always including the URL.
- If the result set is empty, say "No open PRs" — don't report a fabricated error.
- If any repo iteration fails (auth/lookup error), note it and continue with the rest.

---

## Output Contract

The deliverable is a list of **URLs** — every open PR must have its URL present. Don't hand back a count alone; give the clickable list.

## Common Mistakes

- **Omitting URLs** — the whole point is links; always include them.
- **Using `gh pr list` with no `-R`** in a directory that isn't a repo — scope explicitly or rely on `gh search prs`.
- **Forgetting drafts** — keep `isDraft` in output; drafts are still open PRs.
- **Failing silently on empty results** — return "No open PRs" instead of noise.
