---
name: convert-image
description: Convert images between formats (PNG/JPG/WEBP/AVIF) using cwebp and sips. Used when adding images to blog articles — produces the webp for the article and jpg for OG.
license: MIT
metadata:
  version: "1.0"
  scope: root
---

# Convert Image

Converts a source image to one or more output formats. Common use case: preparing article cover images for a blog or website project.

## Tools Available

| Tool | Installed | Best For |
|---|---|---|
| `cwebp` | `brew install webp` | PNG/JPG → WebP (quality-controlled) |
| `sips` | macOS built-in | Any → JPG/PNG/TIFF/BMP (fast, no install) |

## Commands

### PNG/JPG → WebP (article cover)
```bash
cwebp -q 85 "<source.png>" -o "<output.webp>"
```
- `-q 85` is the sweet spot: good visual quality, ~70–80% smaller than PNG

### PNG/JPG → JPG (OG image)
```bash
sips -s format jpeg "<source.png>" --out "<output.jpg>"
```

### PNG/JPG → Both at once
```bash
cwebp -q 85 "<source>" -o "<dest>.webp" && sips -s format jpeg "<source>" --out "<dest>.jpg"
```

### Resize while converting (e.g. cap at 1200px wide)
```bash
sips -Z 1200 -s format jpeg "<source>" --out "<output.jpg>"
cwebp -q 85 -resize 1200 0 "<source>" -o "<output.webp>"
```
`-resize 1200 0` keeps aspect ratio (0 = auto height).

### Batch convert a folder
```bash
for f in /path/to/images/*.png; do
  cwebp -q 85 "$f" -o "${f%.png}.webp"
done
```

---

## Blog Article Workflow

When adding a cover image to a new blog article, set the project root to your site's
repository and adjust the content/asset folders to match its structure:

```bash
# Source image
SRC="<path-to-source.png>"
SLUG="<article-slug>"
PROJECT="<path-to-project-root>"
NAME="<camelCaseName>Cover"   # e.g. gitWorktreesAiAgentsCover

# WebP → goes in the article's images folder
cwebp -q 85 "$SRC" -o "$PROJECT/src/content/blog/$SLUG/_images/$NAME.webp"

# JPG → goes in the site's OG image folder
sips -s format jpeg "$SRC" --out "$PROJECT/public/assets/og/$NAME.jpg"
```

Frontmatter references:
```yaml
img: ./_images/<camelCaseName>Cover.webp
ogImage: "/assets/og/<camelCaseName>Cover.jpg"
```

---

## Notes

- Astro's `image()` schema validator requires the `.webp` file to physically exist before `dev`/`build` — always convert before starting the dev server (other frameworks may differ)
- OG images should stay as JPG (broad social media compatibility)
- `cwebp -q 85` targets ~200–250 KB for a 1440px-wide cover; bump to `-q 90` if the image has fine text
- `sips` preserves EXIF by default; add `--stripProfile` to remove it for smaller OG files
