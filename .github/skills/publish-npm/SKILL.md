---
name: publish-npm
description: Use when the user wants to publish or release a new version of this project to npm.
metadata:
  version: "1.0"
  scope: root
---

This project publishes automatically via CI when pushed to `main`. Never run `npm publish` manually.

## How releases work

The GitHub Actions workflow (`.github/workflows/release.yml`) reads the latest commit message and:

| Commit prefix | Version bump | Example |
|---|---|---|
| `feat:` | minor (x.**Y**.0) | `1.0.0 → 1.1.0` |
| `fix:` / `refactor:` / `perf:` | patch (x.y.**Z**) | `1.1.0 → 1.1.1` |
| `BREAKING CHANGE` in body | major (**X**.0.0) | `1.1.0 → 2.0.0` |
| `chore:` / `docs:` / `ci:` / `test:` | **skipped** | no release |

The workflow bumps `package.json`, tags, and publishes to npm — all automatically.

## Steps to release

1. **Commit with the right prefix** — pick from the table above
2. **Push to `main`** — `git push origin main`
3. **Watch CI** — `gh run watch` or open the Actions tab on GitHub

## Checking the release

```bash
# Watch the workflow run live
gh run watch

# Confirm the published version (replace with this project's npm package name)
npm view <package-name> version

# See all published versions
npm view <package-name> versions --json
```

## Constraints

- Never run `npm publish` manually — the workflow handles version bump + tag + publish atomically
- `NPM_TOKEN` must be set in GitHub repo secrets (`Settings → Secrets → NPM_TOKEN`)
- The workflow skips if the tag already exists (idempotent) — safe to re-run
- Commits with `[skip release]` in the message are ignored (used by the workflow itself)
