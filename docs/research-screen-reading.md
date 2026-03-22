# Research: Read What's On Screen (No Selection)

> Goal: Read visible window content without requiring text selection first.
> Researched: 2026-03-22

## Current Flow

1. User selects text
2. Presses Option+S
3. Hammerspoon fires Cmd+C to copy
4. Reads from `hs.pasteboard.getContents()`
5. Sends to Kokoro TTS via `speak.sh`

**Target**: Eliminate step 1 (manual text selection).

---

## Approach 1: Accessibility API (AXUIElement) — PRIMARY

Hammerspoon ships with `hs.axuielement`, a full wrapper around macOS's AXUIElement C API.

### Strategy

1. Get frontmost app via `hs.application.frontmostApplication()`
2. Get focused window via `app:focusedWindow()`
3. Convert to AX element via `hs.axuielement.windowElement(win)`
4. Traverse tree collecting text from `AXStaticText` / `AXTextArea` elements

### Key AX Attributes

- `AXValue` — text content of text fields/areas
- `AXRole` — element type (`AXStaticText`, `AXTextArea`, `AXTextField`, `AXWebArea`)
- `AXChildren` / `AXVisibleChildren` — tree traversal
- `AXVisibleCharacterRange` — visible portion of large text areas
- `AXStringForRange` — text for a specific character range (parameterized)

### Traversal Methods (Hammerspoon)

- `element:elementSearch(callback, criteria, options)` — async breadth-first search
- `element:allDescendantElements(callback)` — search with no filter
- `element:childrenWithRole(role)` — filter by role
- `hs.axuielement.searchCriteriaFunction(criteria)` — build filter functions

### App Compatibility

| App Type | Works? | Notes |
|----------|--------|-------|
| Native Cocoa (TextEdit, Notes, Preview, Mail, Terminal) | Excellent | Full text via AXValue |
| Safari | Good | Web content as AXWebArea with AXStaticText children |
| Chrome/Electron | Partial | AX tree can be incomplete or slow; Chrome auto-enables AX on client connect |
| Terminal/iTerm2 | Good | Full buffer via AXValue on text area |
| VS Code | Partial | Electron-based, large complex AX tree |
| Games/GPU-rendered | No | No accessibility tree |
| PDF in Preview | Partial | Text-based PDFs yes, scanned PDFs no |

### Performance

- Simple apps (TextEdit, Notes): **<100ms**
- Web browsers: **200ms-2s** depending on page complexity
- `elementSearch` is **async** (won't block Hammerspoon)
- `AXVisibleChildren` limits traversal to on-screen content

### Permissions

- Accessibility permission required — **Hammerspoon already has this**
- No additional permissions needed

### Complexity: MODERATE

Main challenge: different apps expose content differently. Need:
1. Generic walker for AXStaticText/AXTextArea elements
2. App-specific ordering logic (reading order vs AX tree order)
3. Handling AXVisibleCharacterRange for large text areas

---

## Approach 2: OCR via Vision Framework — FALLBACK

macOS Vision framework (`VNRecognizeTextRequest`) for screenshot-based text extraction.

### Workflow

1. Capture window screenshot via `screencapture -l <windowID> -x` or `hs.screen:shotAsPNG()`
2. Run OCR using Vision framework
3. Extract recognized text

### Implementation Options

- **Swift CLI helper** (~30-50 lines): Takes window ID, uses `VNRecognizeTextRequest` with `.accurate`, outputs text to stdout. Cleanest approach.
- **Python + pyobjc**: Install `pyobjc-framework-Vision` (not currently installed)
- **macOS Shortcuts**: Via `shortcuts run` CLI (unreliable in testing)

### Accuracy: VERY HIGH

- Works on **everything visible** — images, scanned PDFs, canvas-rendered content
- Handles multiple fonts, sizes, colors
- Supports both English and Portuguese natively

### Performance (M1)

- Fast recognition: ~100-200ms per screen
- Accurate recognition: ~500ms-1.5s per screen
- Running on Apple Silicon Neural Engine

### Permissions

- **Screen Recording permission required** (additional beyond current setup)

### Downsides

- Reading order can be imperfect (columns, sidebars, headers)
- Cannot distinguish UI chrome from content
- Overhead of screenshot + OCR vs direct text access

---

## Approach 3: App-Specific — ENHANCEMENTS

### Browsers (Best approach for web)

**Safari**:
```lua
hs.osascript.applescript('tell application "Safari" to do JavaScript "document.body.innerText" in current tab of front window')
```

**Chrome**:
```lua
hs.osascript.applescript('tell application "Google Chrome" to execute front window\'s active tab javascript "document.body.innerText"')
```

Both are fast (<50ms), clean, and give complete page text. Requires Automation permission in System Settings.

### Terminal/iTerm2

Full buffer accessible via AXValue on the text area. Can get just visible portion via AXVisibleCharacterRange.

### VS Code/Electron

Hardest case. Options: VS Code extension API helper, or fall back to OCR.

---

## Recommended Implementation Strategy

### Tier 1: AX-based (implement first)

New Lua function in `kokoro.lua`:
1. Get focused window's AX element via `hs.axuielement.windowElement()`
2. Detect app type from `hs.application.frontmostApplication():bundleID()`
3. **Browsers**: use `hs.osascript.javascript()` to run `document.body.innerText`
4. **Other apps**: walk AX tree collecting AXValue from AXStaticText/AXTextArea, filtered by AXVisibleChildren
5. Bind to new hotkey (e.g., `Option+R` for "read screen")

Expected coverage: ~80-90% of typical use cases.

### Tier 2: OCR fallback (implement if needed)

Swift CLI tool (~40 lines):
1. Takes window ID as argument
2. Captures window via `CGWindowListCreateImage`
3. Runs `VNRecognizeTextRequest` with `.accurate`
4. Prints text to stdout

Called from Hammerspoon via `hs.task.new()` only when AX returns insufficient text.

### Tier 3: App-specific refinements (iterate)

- Strip navigation/header from web pages
- Terminal: read only last N lines
- VS Code: read active editor tab content

---

## Key References

### Hammerspoon Modules

| Module | Purpose |
|--------|---------|
| `hs.axuielement` | Full AX API access |
| `hs.application` | App management, frontmost app |
| `hs.window` | Window management |
| `hs.screen` | Screen capture |
| `hs.osascript` | Run AppleScript/JXA |
| `hs.task` | Run external processes |

### AX Attributes to Target

- Roles: `AXStaticText`, `AXTextArea`, `AXTextField`, `AXWebArea`, `AXScrollArea`, `AXGroup`
- Content: `AXValue`, `AXTitle`, `AXDescription`
- Traversal: `AXChildren`, `AXVisibleChildren`
- Range: `AXVisibleCharacterRange`, `AXStringForRange` (parameterized)

### macOS Frameworks (for OCR helper)

- `Vision.framework` — `VNRecognizeTextRequest`
- `ScreenCaptureKit.framework` or `CoreGraphics` — `CGWindowListCreateImage`

### Integration Point

The `toggleSpeak()` function in `kokoro.lua` — a new `readScreen()` function follows the same pattern but replaces `Cmd+C` clipboard approach with AX tree traversal.
