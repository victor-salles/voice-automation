# VoiceFlow roadmap

Ordered backlog and research notes. MVP product direction lives in [specs/2026-03-30-voiceflow-mvp-design.md](specs/2026-03-30-voiceflow-mvp-design.md).

## Backlog (next up)

- **Web “read the article” via Accessibility** — Deferred; see [Research: web content selection](#research-web-content-selection-accessibility) below. No further heuristic tuning until there is a clear scope (landmark scoping vs browser extension / DOM).
- **⌥S while paused** — If playback is paused, ⌥S in another app can resume old audio instead of speaking the new context. Track in review notes; fix when revisiting hotkey / state machine behavior.
- **Duplex / conversational voice** — ASR + turn-taking + barge-in; see [research-asr-duplex.md](research-asr-duplex.md) for model families (Whisper, faster-whisper, NeMo/Parakeet, Apple Speech, WhisperKit) and an incremental adoption path.

## Research: web content selection (Accessibility)

**Context.** We briefly explored a browser path: bounded BFS under focus plus ancestor walk, `focusedSpeakSurface()`, caret-first then longest `AXValue` among plausible roles. It did not reliably yield “main article” text and was **removed** from the app; this section records what we learned.

**Problem (if we revisit).** Inferring speakable `AXValue` from the focused web subtree without DOM help is fragile. A simple strategy improves some cases but **does not equal “main article text.”**

**Examples studied**

| Site / pattern | What goes wrong |
|----------------|-----------------|
| Static blogs (e.g. Hugo / PaperMod) | Many small `AXStaticText` leaves; footer, “Powered by”, or other chrome competes with body; longest-string or traversal order can pick the wrong region. |
| TechCrunch single post | Article lives in `.entry-content.wp-block-post-content`. Infinite-scroll UI below exposes real copy **“Loading the next article”** in `.seamless-scroll__loader` ([example article](https://techcrunch.com/2026/03/31/openai-not-yet-public-raises-3b-from-retail-investors-in-monster-122b-fund-raise/)). That string is legitimate AX content, not a bug in the page — the heuristic can legally select it. |

**What helps today**

- **Native text areas** — `speakSelection()` uses `focusedTextArea()` (e.g. Apple Notes) for cursor + paragraph when the focused control is a real text area.
- **Browsers** — Use an **explicit text selection** and ⌥S; there is no inferred “read the page” path in the shipped app after dropping the experiment above.

**Directions (when we reopen this)**

1. Validate in Accessibility Inspector whether **`main` / landmark** (or equivalent) is exposed; if so, **scope** candidate collection to that subtree before scoring.
2. Avoid one-off **string denylists** unless we accept high fragility.
3. For “always read the article,” plan on **DOM-level** extraction (extension, Readability-style, or `main` / known content selectors) — AX-only will keep failing on SPAs and infinite scroll.

**Status:** Paused here intentionally to avoid over-engineering native AX heuristics without a product decision on extension vs scoped AX.

## Git / local files

- **`builds/`** — Intended for local agent outputs (e.g. review queues). Listed in `.gitignore`; do not commit unless you deliberately want those artifacts in the repo.
