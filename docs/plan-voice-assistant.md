# Plan: Voice Assistant (Voice Assistant)

> Local-first, voice-driven desktop assistant for macOS.
> "The Siri that Apple never built."

## Decisions (locked)

- **Start with Claude API** (smartest model, de-risk the agent loop)
- **Goal: migrate to local Ollama models** over time
- **Hammerspoon hotkey + voice only** (no visual UI for now)
- **Confirmation before every tool execution** (voice or prompt)
- **Conversational memory** (multi-turn context)
- **Minimal action set first** (apps, web, shell, TTS), expand later
- **No delegation to Claude Code/Codex** for now

## Architecture

```
User speaks (hold-to-talk hotkey)
    |
    v
mlx-whisper (local STT on Apple Silicon)
    |
    v
Python agent (orchestrator)
    |--- conversation history (in-memory, persisted to JSON)
    |--- system prompt with tool definitions
    |
    v
LLM API (swappable backend)
    |--- Claude API (api.anthropic.com) ← start here
    |--- Ollama (localhost:11434)       ← migrate to this
    |--- Gemini (generativelanguage.googleapis.com) ← available
    |
    v
Tool calls returned by LLM
    |
    v
Confirmation prompt (TTS: "Open Safari?", user says "yes"/"no")
    |
    v
Hammerspoon executes action via HTTP (localhost:18880)
    |--- /action/open_app
    |--- /action/search_web
    |--- /action/run_shell
    |--- /action/window_manage
    |--- /action/type_text
    |--- /action/press_keys
    |--- /action/read_screen
    |--- /action/speak (TTS response)
    |
    v
Result sent back to LLM for next turn
    |
    v
Final response spoken via Kokoro TTS
```

## Phases

### P0: Agent loop spike (terminal-based, no voice)
**Goal**: Prove the LLM → tool → response loop works.

- [ ] Create `scripts/assistant.py` — thin agent using Anthropic SDK
- [ ] Define 4 starter tools: `open_app`, `search_web`, `run_shell`, `speak`
- [ ] Implement tool execution via Hammerspoon HTTP endpoints
- [ ] Add confirmation step before each tool execution (terminal y/n)
- [ ] Conversation memory (list of messages, in-memory)
- [ ] Test: "Open Safari" → confirms → opens → "Safari is now open"
- [ ] Test: "Search for flights to Lisbon" → opens browser → searches
- [ ] Test: "What time is it?" → runs `date` → speaks result

**Backend**: Claude API (Sonnet) via Anthropic Python SDK
**Input**: Typed text in terminal
**Output**: Printed + spoken via voice-ctl

### P1: Voice input loop
**Goal**: Replace typed input with voice.

- [ ] Add mlx-whisper integration for hold-to-talk
- [ ] Hammerspoon hotkey (e.g., ⌥A) triggers recording
- [ ] Audio captured → mlx-whisper transcribes → text sent to agent
- [ ] Agent response spoken via Kokoro TTS
- [ ] Full voice loop: speak → hear → speak → hear

**Input**: Voice (mlx-whisper)
**Output**: Voice (Kokoro TTS)

### P2: Expand action vocabulary
**Goal**: Make the assistant genuinely useful.

- [ ] Window management: move, resize, maximize, tile
- [ ] System controls: volume, brightness, Do Not Disturb
- [ ] File operations: open file, read file, list directory
- [ ] Clipboard: read clipboard, set clipboard
- [ ] Notifications: show notification with message
- [ ] Calendar/reminders: read today's events (via osascript)
- [ ] Music: play/pause/next (via osascript to Music.app)
- [ ] Screen reading: AX-based text extraction (from research doc)

### P3: Smart confirmation + permissions
**Goal**: User controls what runs automatically vs. what needs approval.

- [ ] Permission system: allow-once, allow-always, deny
- [ ] Persisted to `~/.config/voice-automation/permissions.json`
- [ ] Voice confirmation: "I want to open Safari. Should I go ahead?"
- [ ] User responds "yes" / "no" / "always allow" via voice
- [ ] Low-risk actions auto-approved: speak, search, read screen
- [ ] High-risk actions always confirm: shell commands, file writes

### P4: Ollama migration
**Goal**: Run entirely local, no cloud dependency.

- [ ] Abstract LLM backend behind a common interface
- [ ] Add Ollama backend (OpenAI-compatible endpoint)
- [ ] Test with Qwen2.5 7B for tool use
- [ ] Compare quality: which tasks work well locally, which don't
- [ ] Fallback strategy: try local first, fall back to Claude if tool use fails

### P5: Visual context (backlog)
**Goal**: "What's on my screen?"

- [ ] Screenshot capture via `screencapture` or Hammerspoon
- [ ] Send to vision-capable LLM (Claude Sonnet, Qwen2-VL)
- [ ] "Read this error", "Summarize this page", "What app is this"

### P6: Desktop summon UI (backlog)
**Goal**: Visual input bar like Claude Desktop.

- [ ] SwiftUI floating panel (non-activating, always-on-top)
- [ ] Screenshot capture widget (drag to select area)
- [ ] Text input + voice toggle
- [ ] Shows conversation history
- [ ] Communicates with agent via HTTP

## Tool Schema (P0 starter set)

```json
{
  "tools": [
    {
      "name": "open_app",
      "description": "Open a macOS application by name",
      "parameters": {
        "app_name": "string — e.g. 'Safari', 'Terminal', 'Finder'"
      }
    },
    {
      "name": "search_web",
      "description": "Search the web using the default browser",
      "parameters": {
        "query": "string — the search query"
      }
    },
    {
      "name": "run_shell",
      "description": "Run a shell command and return the output. Use for system info, file operations, etc.",
      "parameters": {
        "command": "string — the shell command to execute"
      }
    },
    {
      "name": "speak",
      "description": "Speak text aloud to the user via TTS. Use for responses, confirmations, and information.",
      "parameters": {
        "text": "string — the text to speak aloud"
      }
    }
  ]
}
```

## Menu Bar Integration

The existing Kokoro menu bar dot becomes the unified status indicator:

- **Green ●** — ready (Kokoro server online, assistant idle)
- **Blue ●** — speaking (TTS playback active)
- **Yellow ●** — paused
- **Purple ●** — listening (STT recording active, P1)
- **Orange ●** — thinking (waiting for LLM response)
- **Red ●** — offline

Dropdown expands to include assistant controls:
- Current mode (TTS only / Assistant)
- Conversation history (last N exchanges)
- Backend selector (Claude / Ollama / Gemini)
- Settings (voice, speed, language)
- Clear conversation

## File Structure (planned)

```
scripts/
  assistant.py           # Agent orchestrator (thin — ~100 lines)
  assistant_tools.py     # Tool definitions and execution
  assistant_backends.py  # LLM backend abstraction (Claude, Ollama, Gemini)
  assistant_memory.py    # Conversation history and persistence
  voice-agent            # CLI entry point (like voice-ctl)
config/
  assistant/
    system_prompt.txt    # System prompt for the assistant
    permissions.json     # User-configured tool permissions
```

## System Prompt (draft)

```
You are Voice Assistant, a local macOS voice assistant. You help the user
by executing actions on their computer and answering questions.

You have access to tools for opening apps, searching the web,
running shell commands, and speaking to the user.

Rules:
- Always confirm before executing destructive actions
- Prefer brief, spoken responses (the user is listening, not reading)
- If unsure, ask for clarification
- Respond in the same language the user speaks to you
- Be concise — you're a voice assistant, not a chatbot
```

## Backend Interface (for swappability)

All backends implement the same interface:

```python
class LLMBackend:
    def chat(self, messages: list, tools: list) -> dict:
        """Send messages + tools, return response with optional tool_calls."""
        ...
```

Implementations:
- `ClaudeBackend` — uses `anthropic` Python SDK
- `OllamaBackend` — uses `openai` Python SDK pointed at localhost:11434
- `GeminiBackend` — uses `google-generativeai` SDK
```
