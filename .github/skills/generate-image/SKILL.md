---
name: generate-image
description: Generate website images locally using stable-diffusion.cpp (sd-server). No API key — runs on your GPU. Output is a PNG ready to pipe into the convert-image skill.
license: MIT
metadata:
  version: "3.0"
  scope: root
---

# Generate Image (Local — stable-diffusion.cpp)

Generates images using **stable-diffusion.cpp** (`sd-server`) running on your local GPU. Best quality approach for SDXL models (e.g. Juggernaut XL).

**Requires:** [sd.cpp release binaries](https://github.com/leejet/stable-diffusion.cpp/releases) and a downloaded SDXL model (`.safetensors`, ~7GB).

---

## Prerequisites

1. Download a model — [Juggernaut XL](https://huggingface.co/RunDiffusion/Juggernaut-XL-v9) is recommended
2. Start `sd-server`:
   ```bash
   sd-server -m /path/to/juggernautXL.safetensors \
     -W 1024 -H 1024 \
     --clip-on-cpu \
     --fa \
     --listen-port 8998
   ```
   This starts the API + web UI at `http://localhost:8998`.

---

## Usage

### From the web UI

Open `http://localhost:8998` — enter prompt, set steps/CFG, generate, download PNG.

### From the API (curl)

```bash
PROMPT="your prompt here"
OUTPUT="output.png"
SEED=$RANDOM

curl -sL "http://localhost:8998/api/generate" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"juggernautXL.safetensors\",
    \"prompt\": \"$PROMPT\",
    \"width\": 1024,
    \"height\": 1024,
    \"seed\": $SEED,
    \"cfg_scale\": 3.0,
    \"steps\": 20,
    \"sampling_method\": \"euler\",
    \"scheduler\": \"karras\",
    \"clip_on_cpu\": true
  }" \
  -o "$OUTPUT" && echo "Saved: $OUTPUT"
```

> sd-server API returns a JSON with `{ "image": "base64..." }`. Parse and save:
> ```bash
> curl -s ... | python3 -c "import sys,base64; d=sys.stdin.read(); b=base64.b64decode(d.split('\"')[3]); open('$OUTPUT','wb').write(b)"
> ```

---

## Best Quality Settings (SDXL)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Model | SDXL (Juggernaut, RealVisXL, etc.) | Avoid SD1.5 — quality gap |
| Resolution | 1024×1024 | Native SDXL training size |
| CFG scale | 3.0–5.0 | 3.0 = creative, 5.0 = faithful |
| Steps | 20–30 | 20 = fast, 30 = polished |
| Sampling | `euler` or `euler_a` | `euler_a` adds slight variance |
| Scheduler | `karras` | Better noise scheduling |
| CLIP | `--clip-on-cpu` | Saves VRAM (recommended for SDXL) |
| VAE | `--vae-on-cpu` (if needed) | Fallback for low VRAM |
| Tiling | `--vae-tiling` | For >1024px images |
| Seed | random (`-1`) | Omits deterministic seed |
| FA | `--fa` | Fast attention (if VRAM >8GB) |

---

## Prompt Style

SDXL works best with **phrase lists** (not full sentences):

```
[subject], [style], [lighting], [mood], [color palette], [details]
```

Order matters — most important concepts first.

**Example — article hero:**
```
cyberpunk city, volumetric lights, night atmosphere, cinematic lighting,
bokeh background, ultra detailed, sharp focus, no text, no watermark
```

---

## Fallback: Pollinations.ai (no key needed)

If sd-server isn't running, use the online API:

```bash
PROMPT="your prompt here"
OUTPUT="output.png"
ENCODED=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$PROMPT")

curl -sL "https://image.pollinations.ai/prompt/${ENCODED}?model=flux&nologo=true" \
  -o "$OUTPUT" && echo "Saved: $OUTPUT"
```

---

## After Generating

Pipe into `convert-image` for WebP + OG JPG (same as before).


