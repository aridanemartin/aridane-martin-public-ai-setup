---
name: article-extract
description: Extract full content from a web article — body text, metadata, and inline images — and return structured output or save as a vault note.
license: MIT
metadata:
  version: "1.0"
  scope: root
---

# Article Extractor

Extracts structured content from any web article: title, author, date, body text, and inline images. Saves to vault or returns inline.

---

## When to Use

- "Extract this article: [URL]"
- "Save this article to my vault: [URL]"
- "Pull the content from [URL] with images"

---

## Workflow

### Step 1: Fetch the Page

Use `WebFetch` with the article URL. Request markdown output to get clean text with image references preserved.

If `WebFetch` is unavailable, fall back to:

```bash
curl -sL "<URL>" | python3 - << 'EOF'
import sys, re
from html.parser import HTMLParser

class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_body = False
        self.skip_tags = {'script', 'style', 'nav', 'footer', 'header', 'aside', 'form'}
        self.current_skip = 0
        self.text_parts = []
        self.images = []
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in self.skip_tags:
            self.current_skip += 1
        if tag == 'img':
            src = attrs.get('src', '')
            alt = attrs.get('alt', '')
            if src:
                self.images.append({'src': src, 'alt': alt})

    def handle_endtag(self, tag):
        if tag in self.skip_tags and self.current_skip > 0:
            self.current_skip -= 1

    def handle_data(self, data):
        if self.current_skip == 0:
            clean = data.strip()
            if clean:
                self.text_parts.append(clean)

html = sys.stdin.read()
parser = ArticleParser()
parser.feed(html)

print("=== TEXT ===")
print('\n'.join(parser.text_parts))
print("\n=== IMAGES ===")
for img in parser.images:
    print(f"[{img['alt']}]({img['src']})")
EOF
```

### Step 2: Extract Metadata

From the fetched content, identify:

| Field | Where to look |
|---|---|
| **Title** | `<title>`, `<h1>`, or `og:title` meta tag |
| **Author** | Byline, `<meta name="author">`, or article header |
| **Published date** | `<time>`, `<meta property="article:published_time">`, or visible date |
| **Description** | `<meta name="description">` or `og:description` |
| **Tags/Topics** | `<meta name="keywords">`, visible category labels, or inferred from content |

### Step 3: Extract Inline Images

Collect all `<img>` tags within the article body:

- **src**: absolute URL (resolve relative paths against the base URL)
- **alt**: caption or description text
- **context**: the surrounding paragraph heading to understand placement

Exclude icons, logos, ads (usually tiny or from CDN domains like `assets.`, `cdn.`, `pixel.`, `analytics.`).

### Step 4: Structure Output

Return in this format:

```markdown
---
title: {{Title}}
author: {{Author or "Unknown"}}
published: {{YYYY-MM-DD or "Unknown"}}
source: {{URL}}
tags: [{{inferred tags}}]
extracted: {{today's date}}
---

# {{Title}}

> {{Description or first meaningful paragraph}}

## Content

{{Full article body — clean prose, no nav/footer/ads}}

## Images

| # | Alt Text | URL |
|---|---|---|
| 1 | {{alt}} | {{src}} |
| 2 | ... | ... |
```

---

## Output Options

After extracting, choose what to do:

### A. Return Inline
Paste the structured output directly in the conversation.

### B. Save as Vault Note
Save to your notes vault (use the vault root configured for the user, e.g. `$HOME/vault/03 - Resources/`):
```
<vault>/03 - Resources/<topic-slug>.md
```

### C. Save as Article Draft
If the article will be used as source material for writing, save to:
```
<vault>/01 - Projects/web articles/articles/<slug>.md
```

---

## Quick Reference

| Task | Approach |
|---|---|
| Clean text only | Use `WebFetch` with markdown output |
| Images + text | Use the curl+Python parser fallback |
| Paywalled content | Can't bypass — fetch whatever is publicly visible |
| PDF articles | Use `Read` tool directly on the downloaded PDF |
| Twitter/X threads | Use `WebFetch`; threads often need scroll — note limitation |

---

## Notes

- Relative image URLs must be resolved: prepend the article's origin (e.g., `https://example.com` + `/images/photo.jpg`)
- Images behind authentication or signed CDN URLs will return 403 — list them but note they may not load
- For very long articles (>8,000 words), summarize sections rather than copying verbatim unless the user asks for full text
- `WebFetch` returns markdown by default — images appear as `![alt](src)` inline, which is ideal
