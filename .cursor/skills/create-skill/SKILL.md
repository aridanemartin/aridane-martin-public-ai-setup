---
name: create-skill
description: Scaffold a new skill in ~/.agents/skills/<name>/ and automatically symlink it to .claude/skills/, opencode, and codex.
license: MIT
metadata:
  version: "1.0"
  scope: global
---

# Create Skill

Scaffolds a new skill in `~/.agents/skills/<name>/` and symlinks it to all agent directories so it's discoverable everywhere.

## Skill Layout

Each skill lives in its own directory with a single `SKILL.md`:

```
~/.agents/skills/<name>/SKILL.md       ← canonical source
~/.claude/skills/<name> -> .agents/skills/<name>/
~/.config/opencode/skills/<name> -> .agents/skills/<name>/
~/.codex/skills/<name> -> .agents/skills/<name>/
```

The agent reads the skill from the symlinked path (`.claude/skills/`, `opencode/skills/`, or `codex/skills/`).

## When to Use

- "Create a skill called X that does Y"
- "Add a new skill for ..."
- Any time you want to add a new skill to the global skill set

## Workflow

### Step 1: Gather info

Ask the user for:
1. **Name**: a lowercase-hyphenated identifier (e.g. `video-transcript`, `send-whatsapp`, `seo-audit`)
2. **Description**: 1–2 sentences describing what the skill does and when to use it
3. **Scope**: usually `root` (works anywhere) or `global` (available everywhere)

### Step 2: Scaffold the skill

Create `~/.agents/skills/<name>/SKILL.md` with this template:

```markdown
---
name: <name>
description: <description>
license: MIT
metadata:
  version: "1.0"
  scope: <scope>
---

# <Title Case Name>

<One-sentence description>

## When to Use

- ...

## When NOT to Use

- ...

## Workflow

### Step 1: <Step 1 name>
...

### Step 2: <Step 2 name>
...

## Quick Reference

| Task | Command |
|---|---|
| ... | ... |

## Notes

- ...
```

Customise the sections based on what the skill does. A typical skill has:
- Frontmatter (YAML)
- Title + 1-sentence description
- "When to Use" / "When NOT to Use" bullet lists
- Step-by-step workflow with numbered steps and code blocks
- Quick reference table (optional)
- Notes section for gotchas (optional)

### Step 3: Symlink

```bash
AGENTS="$HOME/.agents/skills/<name>"
CLAUDE="$HOME/.claude/skills/<name>"
OPENCODE="$HOME/.config/opencode/skills/<name>"
CODEX="$HOME/.codex/skills/<name>"

ln -sfn "$HOME/.agents/skills/<name>" "$CLAUDE"
ln -sfn "$HOME/.agents/skills/<name>" "$OPENCODE"
ln -sfn "$HOME/.agents/skills/<name>" "$CODEX"
```

`ln -sfn` — force-create, so it overwrites any existing copy or broken symlink.

### Step 4: Verify

```bash
readlink ~/.claude/skills/<name>
readlink ~/.config/opencode/skills/<name>
readlink ~/.codex/skills/<name>
ls -la "$AGENTS/SKILL.md"
```

All should resolve to the same `SKILL.md` in `.agents/skills/<name>/`.

## Migration: Convert existing duplicates

If an existing skill has real copies in the other directories (not symlinks), convert them:

```bash
AGENTS="$HOME/.agents/skills/<name>"
CLAUDE="$HOME/.claude/skills/<name>"
OPENCODE="$HOME/.config/opencode/skills/<name>"
CODEX="$HOME/.codex/skills/<name>"

for d in "$CLAUDE" "$OPENCODE" "$CODEX"; do
    if [ -d "$d" ] && [ ! -L "$d" ]; then
        # It's a real directory (copy), not a symlink.
        # If it contains a SKILL.md, delete it and symlink instead.
        if [ -f "$d/SKILL.md" ]; then
            rm -rf "$d"
            ln -sfn "$AGENTS" "$d"
        fi
    fi
done
```

## Quick Reference

| Action | Command |
|---|---|
| Create & symlink | Full workflow above |
| Verify symlink | `readlink ~/.agents/skills/<name>` |
| Remove a skill | `rm -rf ~/.agents/skills/<name>` + `rm -f ~/.claude/skills/<name> ~/.config/opencode/skills/<name> ~/.codex/skills/<name>` |
| Force-relink | `ln -sfn ~/.agents/skills/<name> ~/.claude/skills/<name>` (repeat for each dir) |

## Notes

- The canonical copy is **always** in `~/.agents/skills/<name>/SKILL.md`
- Other directories are symlinks — editing them is a no-op (they edit the canonical copy)
- Use `ln -sfn` (not `ln -sf`) — the `n` flag prevents following existing symlinks, avoiding dangling refs
- All agents discover skills from their own `skills/` directory; symlinks ensure every agent sees the same content