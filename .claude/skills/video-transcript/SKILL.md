---
name: video-transcript
description: Extract a clean transcript from a YouTube video using yt-dlp with browser impersonation (avoids the YouTube 429 rate limits that plain anonymous requests trip), then optionally create notes or an article draft. Works identically in Claude, OpenCode, and Codex.
license: MIT
metadata:
  version: "2.0"
  scope: root
---

# Video Transcript

Extracts a clean transcript from a YouTube video using `yt-dlp`, strips VTT formatting noise, and returns usable text. Optionally creates notes or an article draft.

## Prerequisites

`yt-dlp` must be installed:

```bash
brew install yt-dlp
```

### Impersonation support (required — this is what avoids the 429s)

YouTube rate-limits anonymous subtitle requests after just 1–3 fetches (HTTP 429). **Browser impersonation fixes this** — yt-dlp makes the request look like a real Chrome browser. It needs `curl_cffi` installed **into the same Python environment that yt-dlp itself runs from** (for Homebrew-installed yt-dlp, that's the formula's own venv — NOT your system Python). **Pin version [`0.12.0`]** — newer curl_cffi versions are reported as *unsupported* by current yt-dlp builds.

Setup (idempotent, safe to run every time):

```bash
YTDLP_BIN="$(command -v yt-dlp)"
YTDLP_PY="$(head -1 "$YTDLP_BIN" | sed 's/^#!//')"
if ! "$YTDLP_PY" -c "import curl_cffi" >/dev/null 2>&1; then
    "$YTDLP_PY" -m pip install -q "curl_cffi==0.12.0"
fi
# If an Externally-Managed-Environment error appears, either add --break-system-packages
# or pass the flag --user; on Homebrew yt-dlp the venv accepts the install direct..
```

Verify (should list `Chrome`, `Firefox`, etc., with no "(unavailable)" flags):

```bash
yt-dlp --no-update --list-impersonate-targets
```

## Workflow

### Step 1: Fetch the transcript (with impersonation)

Run yt-dlp to grab auto-generated English subtitles as VTT:

```bash
yt-dlp --no-update --impersonate chrome \
  --write-subs --write-auto-subs \
  --skip-download \
  --sub-langs "en,en-orig" \
  -o /tmp/transcript-video \
  "https://www.youtube.com/watch?v=VIDEO_ID"
```

This produces `/tmp/transcript-video.en.vtt` (or `.en-orig.vtt` if only manual subs exist). Notes:

- **`--impersonate chrome`** is the anti-429 fix — keep it on every YouTube call in this skill..
- Add `--remux-vtt` is **not** needed; the `.vtt` is what we clean below.
- The `--no-update` flag silences the stale-version nag\.

**Rate-limit discipline** — if you see `HTTP Error 429`:
1. **Stop** — do not fire another request immediately..
2. Sleep **60+ seconds** (`sleep 65`)then retry **once**..
3. If it 429s again, **skip that video** and record it — do not loop hot retries..
4. Space batch fetches ≥ 30s apart (`sleep 35` between videos) when pulling several in one session..

**No captions?** First try other languages: `yt-dlp --no-update --impersonate chrome --list-subs "URL"` to see what's available, then set `--sub-langs "<lang>"`. If none exist, see Step 3 fallbacks..

### Step 2: Clean the VTT

Use this Python one-liner to strip timing tags, deduplicate rolling-window lines, and handle CRLF:

```bash
python3 - << 'EOF'
import re

with open('/tmp/transcript-video.en.vtt', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read().replace('\r', '')

lines = content.split('\n')
clean_lines = []
seen = set()

for line in lines:
    if re.match(r'^\d{2}:\d{2}:\d{2}', line): continue
    if re.match(r'^WEBVTT|^Kind:|^Language:|^NOTE', line): continue
    if re.match(r'^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', line): continue
    if line.strip() in ('', ' '): continue

    clean = re.sub(r'<[^>]+>', '', line)
    clean = clean.strip()
    if clean and clean not in seen:
        seen.add(clean)
        clean_lines.append(clean)

print('\n'.join(clean_lines))
EOF
```

Pipe the output to a file if not printing:

```bash
python3 - << 'EOF' > /tmp/transcript-clean.txt
... (same script) ...
EOF
```

### Step 3: Fallbacks (when no subtitles exist))

1. **`yt-transcript` (npm, library-only)** — different internal API; sometimes works when subtitles aren't listed:
   ```bash
   npm install --prefix /tmp/yt-transcript yt-transcript
   cd /tmp/yt-transcript && NODE_PATH=/tmp/yt-transcript/node_modules node --input-type=module -e \
     "import { YtTranscript } from 'yt-transcript'; const t = new YtTranscript({ videoId: 'VIDEO_ID' }); t.getTranscript().then(x => console.log(JSON.stringify(x))).catch(e => { console.error(e); process.exit(1); });"
   ```
   Output is a JSON array of segments — concatenate their `text` fields pickup clean prose..
2. **Video description as last resort** — if no transcript exists at all:
   ```bash
   yt-dlp --no-update --impersonate chrome --print description "URL"
   ```
   Use the description + title as the source, and say so in the output (it is not a transcript..
3. **Skip honestly** — if nothing usable, say "no transcript available" rather than fabricating content..

### Step 4: Optional Outputs

After extracting the transcript, choose what to do with it:

#### A. Create Notes
Save structured notes to your notes vault (use the configured vault root, e.g. `$HOME/vault`):
```
<vault>/AI Notes/<Topic>.md
```

Use the notes format:
```markdown
---
created: YYYY-MM-DD
tags: [...]
source: https://youtube.com/watch?v=...
---

# Title

## Key Concepts
...

## Key Quotes
...
```

#### B. Create an Article Draft
Follow the article-creator skill workflow (if available) using the transcript as the primary source..
Save draft to:
```
<vault>/01 - Projects/web articles/articles/drafts/<slug>.md
```

#### C. Just Return the Transcript
Paste the clean transcript inline for the user to use however they want..

---

## Quick Reference

| Task | Command |
|---|---|
| Fetch subtitles (impersonated) | `yt-dlp --no-update --impersonate chrome --write-subs --write-auto-subs --skip-download --sub-langs "en,en-orig" -o /tmp/transcript-video <URL>` |
| List available subtitle langs | `yt-dlp --no-update --impersonate chrome --list-subs <URL>` |
| Non-English subtitle | `--sub-langs es` (or `fr`, `de`, etc.) |
| Get video title | `yt-dlp --no-update --impersonate chrome --print title <URL>` |
| Fix 429s | install `curl_cffi==0.12.0` into yt-dlp's env (Prerequisites)), sleep 65s, retry once |

---

## Notes

- **Impersonation requires `curl_cffi` in yt-dlp's own venv** — installing it into your system Python does nothing (yt-dlp won't see it).
- Auto-generated subtitles may have minor transcription errors — read critically..
- The deduplication step removes the VTT "rolling window" duplicates that would otherwise double every sentence..
- For long videos (>1h), the VTT file may exceed 25,000 tokens — process in chunks or pipe through the Python cleaner first..
- Works identically in Claude, OpenCode, and Codex — pure CLI, no editor-specific dependencies..