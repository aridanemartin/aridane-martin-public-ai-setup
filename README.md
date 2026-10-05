# aridane-martin-ai-setup

My global AI coding setup, adapted for every provider, as a single installable repository.

Point [`ai-setup-cli`](https://github.com/aridanemartin/ai-setup-cli) at this repo and it will
detect which providers your project already uses and install the matching configuration:

```bash
npx ai-setup-cli https://github.com/aridanemartin/aridane-martin-ai-setup
```

The CLI scans the current directory for provider markers (`.claude/`, `.github/`, `.cursor/`,
`.codex/`, `.gemini/`, `.opencode/`/`opencode.json`, `.devin/`), pre-selects what it finds, and
copies only those folders. Add `--all` to install everything, `--dry-run` to preview, and
`--yes` to overwrite without prompting.

## What's inside

The repository mirrors real project paths at its root, so any provider can consume its own
folder directly:

| Provider | Paths |
|----------|-------|
| Claude Code | `.claude/` (agents, skills, settings), `AGENTS.md`, `.mcp.json` |
| GitHub Copilot | `.github/` (`copilot-instructions.md`, agents, skills) |
| Cursor | `.cursor/` (agents, skills) |
| Codex CLI | `.codex/` (config, agents, skills), `AGENTS.md` |
| Gemini CLI | `.gemini/` (settings, skills), `GEMINI.md` |
| OpenCode | `.opencode/` (agents, skills), `opencode.json`, `AGENTS.md` |
| Devin | `.devin/` (config, agents, skills, hooks), `AGENTS.md` |

`AGENTS.md` is the shared source of truth for always-on instructions and is installed once.

## Required environment variables

Secrets are **not** stored here. Configuration that needs credentials uses placeholders:

| Variable | Used by |
|----------|---------|
| `NAN_API_KEY` | `opencode.json` (NaN provider) |
| `CONTEXT7_API_KEY` | `.mcp.json`, `opencode.json`, `.codex/config.toml` |
| `CALLMEBOT_APIKEY` / `CALLMEBOT_PHONE` | `send-whatsapp-to-aridane` skill |

Export them in your shell profile before using the relevant tool.

## Per-provider adaptation

- **Skills** use the `SKILL.md` convention and are mirrored into every provider's `skills/`
  directory.
- **Agents** are authored as markdown (Claude format) and converted per provider: Devin gets
  `allowed-tools`, Copilot gets `.agent.md` files with `tools`, Codex keeps its TOML format.
- **Configs** are minimal and portable: `.claude/settings.json` ships permissions only (hooks
  are machine-specific), and Codex/OpenCode configs have had credentials replaced with
  placeholders.

## Notes

- Personal absolute paths in skills were rewritten to `$HOME`.
