---
name: linkedin-post
description: Generate a ready-to-copy LinkedIn post promoting a blog article. Matches the author's voice and follows LinkedIn SEO best practices. Never publishes directly.
license: MIT
metadata:
  version: "1.0"
  scope: root
---

# LinkedIn Post Generator

Generates a complete, copy-paste-ready LinkedIn post promoting a published or upcoming
article from the user's blog. Matches the author's voice and applies LinkedIn SEO best practices.

**Never publishes directly.** Output is always plain text for the user to review and copy.

---

## When to Use

- "Write a LinkedIn post for [article]"
- "Create a LinkedIn post about [topic]"
- Just published or about to publish an article and want to promote it

---

## Prerequisites

Ask the user for (or infer from the project):

- The **blog base URL** (e.g. `https://example.com`), used to build the article link
- The **article path** — a local file or URL to read from

Read the article to extract:

- Title, subtitle, and description
- Key section headings (H2s) and opening paragraphs
- Any surprising stats, benchmarks, or contrarian claims
- Tags (for hashtag mapping)
- Article slug → builds the URL: `<blog-base-url>/blog/<slug>`

If the article lives in a CMS or content directory, read it from there — do not hardcode a
personal path. Accept either a file path supplied by the user or the article text pasted inline.

---

## Voice Reference

Match the **author's** voice, inferred from the article itself. Common traits of a strong
developer-blog voice:

- **Punchy and direct** — no filler, no corporate speak
- **Second person** — "you" as a fellow developer
- **Practical** — leads with what you can *do*, not just what it *is*
- **Short lines** — one clause per line on LinkedIn
- **Opinionated** — shares a clear take, doesn't hedge

Study the article's opening sentence — it almost always contains the best hook. If the user has
given voice guidance, follow it over these defaults.

---

## LinkedIn SEO Rules

1. **Hook in the first 2 lines** — fold at ~210 chars, must land before "...see more"
2. **No external link in body** — LinkedIn penalizes reach; put URL at the very end after a blank line
3. **Optimal length: 1,200–1,500 characters**
4. **5–7 hashtags max** — on the last line, space-separated
5. **Blank line every 2–3 lines** — LinkedIn collapses text walls
6. **Bullets with →** — not `-` or `*`

---

## Post Structure

```
[Hook — 1-2 punchy lines, before the fold]

[2-3 lines of context: problem or why it matters now]

[Transition: "In the article I cover:" / "Here's what changed my thinking:"]

→ Key takeaway 1
→ Key takeaway 2
→ Key takeaway 3
→ Key takeaway 4
→ Key takeaway 5 (optional)

[1-line closing: question, observation, or invitation]

→ Full article: <blog-base-url>/blog/<slug>

#Hashtag1 #Hashtag2 #Hashtag3 #Hashtag4 #Hashtag5
```

---

## Hook Variants

Always generate 3 options with different angles:

| Type | Pattern |
|---|---|
| **Stat / number** | "[Metric]. [Why it matters]." |
| **Contrarian** | "[Common belief] isn't enough. / [Assumption] is wrong." |
| **Story** | "I [did X without Y]. [Unexpected result]." |

---

## Hashtag Mapping

Map the article's own tags to relevant LinkedIn hashtags. Example mapping:

| Article tag | LinkedIn hashtags |
|---|---|
| Agent Workflows | #AIAgents #AgentEngineering #DeveloperTools |
| Context Engineering | #ContextEngineering #LLM #AIEngineering |
| Prompt Engineering | #PromptEngineering #GenerativeAI #AI |
| Copilot Customization | #GitHubCopilot #AICoding #Copilot |
| Agent Skills | #ClaudeCode #AgentSkills #AIWorkflows |
| Terminal | #Terminal #DeveloperProductivity #DevTools |
| Editor Workflow | #VSCode #DeveloperExperience #IDE |
| WebMCP | #WebMCP #AIAgents #WebDevelopment |
| macOS | #macOS #DeveloperTools #Productivity |

Always include `#SoftwareDevelopment` or `#WebDevelopment` as a broad anchor.

---

## Output Format

Present in three parts:

**1. Hook Variants (A / B / C)** — user picks one

**2. Full Post** — plain text, no markdown, actual line breaks, ready to copy

**3. Quick Stats**
- Character count
- Best posting window: Tue–Thu 8–10am local time

---

## Example

**Hook A (Stat):** Same model. 10x better results. Zero fine-tuning.
**Hook B (Contrarian):** Prompt engineering isn't enough anymore. It never was.
**Hook C (Story):** I just automated a full bug-fix pipeline without writing a single prompt.

---

Same model. 10x better results. Zero fine-tuning.

The difference? The harness.

Most developers obsess over which model to use. But the model is just the engine. What you build around it — the tools, constraints, and feedback loops — determines whether it actually works reliably.

That's harness engineering. And it's where the real leverage is.

In the article I cover:

→ Why Agent = Model + Harness (and why this reframes everything)
→ Guides vs Sensors: the two controls every harness needs
→ Three regulation categories: maintainability, architecture fitness, behaviour
→ Empirical evidence: a big accuracy jump from changing only the harness format
→ Four pillars to build your first harness today

What does your current harness look like?

→ Full article: <blog-base-url>/blog/harness-engineering

#AIAgents #AgentEngineering #ContextEngineering #PromptEngineering #AIEngineering #DeveloperTools #SoftwareDevelopment

---

*~1,340 chars · Best posted Tue–Thu 8–10am*
