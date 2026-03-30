# VoiceFlow MVP — Design Spec

## Goal

Replace the Hammerspoon-based voice-automation stack with a native macOS menu bar app. The MVP proves the approach end-to-end: select text, speak it, show state.

## MVP Scope

**In scope:**
- Select text in any app → press ⌥S (or click menu bar) → hear it spoken
- Menu bar icon reflects state: idle, processing, playing, error
- Press ⌥S while playing → stop
- Menu bar dropdown: "Speak Selection (⌥S)", "Stop", separator, "Quit"
- Kokoro TTS via HTTP (localhost:8880), English voice only

**Deferred to later iterations:**
- History/replay (20 items)
- Text preprocessing (markdown stripping, acronym expansion)
- Portuguese language detection and voice switching
- Clipboard fallback for text extraction (Chrome, Electron apps)
- Reading Mode (paragraph-by-paragraph with pre-synthesis)
- Open at Login

## Architecture

Swift Package Manager executable, assembled into a `.app` bundle via Makefile.

### Files

```
VoiceFlow/
  Package.swift
  Sources/VoiceFlow/
    VoiceFlowApp.swift      — @main, MenuBarExtra scene, wires components
    TextExtractor.swift     — Get selected text via macOS Accessibility API
    TTSEngine.swift         — HTTP POST to Kokoro + AVAudioPlayer
    StatusManager.swift     — Observable state enum, drives menu bar icon
  Makefile
  Info.plist
```

### Dependencies

```
VoiceFlowApp (composition root)
  ├── StatusManager    ← @Observable, drives icon + menu state
  ├── TextExtractor    ← stateless, no dependencies
  └── TTSEngine        ← reads StatusManager, plays audio
```

No circular dependencies. TextExtractor is pure I/O with no state.

## Component Details

### VoiceFlowApp.swift

SwiftUI `@main` app with `.accessory` activation policy (no Dock icon).

Uses `MenuBarExtra` with the SF Symbol driven by `StatusManager.currentIcon`. The menu contains:
- "Speak Selection ⌥S" — calls speakSelection()
- "Stop" — calls TTSEngine.stop(), disabled when idle
- Separator
- "Quit VoiceFlow" — terminates app

Registers a global hotkey (⌥S) on launch. The hotkey toggles: if playing, stop; otherwise, speak selection.

### TextExtractor.swift

Stateless struct. Single public method:

```swift
func selectedText() -> String?
```

Implementation:
1. Get system-wide AX element
2. Get `kAXFocusedUIElement`
3. Read `kAXSelectedTextAttribute`
4. Return the string, or nil if empty/unavailable

No clipboard fallback in MVP. Returns nil for apps that don't expose AX selected text.

### TTSEngine.swift

Manages synthesis and playback. Notifies StatusManager of state transitions.

Public API:
```swift
func speak(_ text: String)    // Synthesize via Kokoro HTTP + play
func stop()                    // Cancel synthesis, stop playback
```

Internal flow:
1. `speak()` → set state to `.processing` → POST to `http://localhost:8880/v1/audio/speech`
2. On response → store audio `Data` → create `AVAudioPlayer` → play → set state to `.playing`
3. On playback finish → set state to `.idle`
4. On any error → set state to `.error`, auto-reset to `.idle` after 3 seconds

The audio `Data` is kept in memory for the current item (enables future replay).

Kokoro payload: `{"input": text, "voice": "af_heart"}`

Timeout: 30 seconds.

### StatusManager.swift

`@Observable` class. Single source of truth for app state.

```swift
enum Status { case idle, processing, playing, error }
var current: Status = .idle
var currentIcon: String  // computed SF Symbol name
```

Icon mapping:
| State | SF Symbol | Rendering |
|---|---|---|
| idle | `speaker.wave.2` | default template |
| processing | `speaker.badge.exclamationmark` | default template |
| playing | `speaker.wave.2.fill` | tinted accent color |
| error | `speaker.slash` | default template |

### Global Hotkey

Uses `CGEvent.tapCreate` for the ⌥S hotkey (same approach as existing VoiceFlow `HotkeyManager`). The hotkey setup lives in `VoiceFlowApp.swift` as a private function — one binding doesn't justify a separate file.

If the event tap fails (no Accessibility permission), print a warning to stdout. The app still works via the menu bar dropdown — the hotkey is a convenience, not a hard requirement.

### Info.plist

```xml
CFBundleIdentifier: com.voiceflow.app
CFBundleName: VoiceFlow
LSUIElement: true              (no Dock icon)
NSAccessibilityUsageDescription: "VoiceFlow needs Accessibility access to read selected text and register global hotkeys."
```

The bundle ID must be stable — Accessibility permission is tied to it.

### Makefile

```
build:     swift build -c release
bundle:    assemble .app from .build/ output + Info.plist
install:   copy VoiceFlow.app to ~/Applications/
sign:      ad-hoc codesign -s -
clean:     rm -rf .build/ VoiceFlow.app
```

`make install` runs build + bundle + sign + copy.

## Environment

- macOS 13+ (Ventura) — required for MenuBarExtra
- Swift 5.9+, Swift Package Manager
- Xcode Command Line Tools only (no Xcode.app)
- Kokoro TTS running locally on port 8880

## Testing Strategy

MVP tests are minimal — focused on proving the build works:
- `TextExtractor`: manual test in 3 apps (Notes, TextEdit, Terminal)
- `TTSEngine`: manual test with Kokoro running
- `StatusManager`: unit testable (state transitions)
- Build pipeline: `make install` produces a working .app

Automated tests expand in iteration 2 when TextProcessor and HistoryStore arrive.

## Success Criteria

The MVP is done when:
1. `make install` produces `~/Applications/VoiceFlow.app`
2. Launching the app shows a speaker icon in the menu bar
3. Selecting text in TextEdit and pressing ⌥S speaks it
4. The icon changes through idle → processing → playing → idle
5. Pressing ⌥S while playing stops playback
6. Clicking "Speak Selection" in the dropdown works
7. Quitting via menu works cleanly

## Future Iterations

1. **History + Replay** — HistoryStore (ring buffer of 20), replay menu items
2. **Text Processing** — Markdown stripping, acronym expansion, Portuguese detection
3. **Clipboard Fallback** — Cmd+C extraction for Chrome/Electron apps
4. **Reading Mode** — Paragraph-by-paragraph with pre-synthesis buffer
5. **VibeVoice** — Evaluate as Kokoro replacement
