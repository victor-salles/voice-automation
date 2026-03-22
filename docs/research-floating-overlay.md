# Research: Grammarly-like Floating Overlay for TTS Controls

> Goal: Non-intrusive floating widget for play/pause/stop that appears near active content.
> Researched: 2026-03-22

## Context

The user wants a small floating widget similar to Grammarly's text field icon — but for TTS playback controls. It should appear in selected applications, be non-intrusive, and integrate with the Hammerspoon HTTP server (control plane).

---

## Approach 1: Hammerspoon Canvas API

`hs.canvas` can draw shapes, text, and images as a floating overlay.

### Capabilities

- Drawable shapes, text, images, clickable buttons
- Click handling via `canvasMouseEvents()` callback
- App detection via `hs.window.focusedWindow()` for show/hide
- Transparency and rounded rectangles supported

### Limitations

- **Focus stealing**: Canvas takes focus when clicked (bad if user is typing)
- No shadow effects
- Text rendering is basic (no CSS)
- Manual redraw required

### UX Quality: MEDIUM

Visual polish limited to basic shapes. Focus stealing is a significant drawback.

### Example

```lua
local widget = hs.canvas.new({x=100, y=100, w=150, h=50})
widget[1] = {
  type = "rectangle",
  filled = true,
  fillColor = {red=0.2, green=0.8, blue=0.2, alpha=0.9},
  roundedRectRadius = {xRadius=8, yRadius=8},
}
widget[2] = {
  type = "text",
  text = "▶",
  textSize = 20,
  textColor = {red=1, green=1, blue=1},
}
widget:canvasMouseEvents(true, true)
widget:mouseCallback(function(canvas, event, id, x, y)
  if event == "mouseUp" then
    -- Toggle playback via HTTP server
  end
end)
widget:show()
```

### Verdict: Good for quick MVP, bad for production due to focus stealing.

---

## Approach 2: Hammerspoon WebView

`hs.webview` renders HTML/CSS/JS as a native window.

### Capabilities

- Full HTML/CSS/JS — modern, polished UI
- Frameless window via `styleMask` options
- Always-on-top via `level` parameter

### Limitations

- **Focus stealing**: Clicking the webview activates it and steals focus (same problem as Canvas)
- Can partially work around by making UI keyboard-shortcut-only, but defeats the purpose

### UX Quality: HIGH visually, POOR interactively

Beautiful but unusable if it steals focus during typing.

### Verdict: NOT RECOMMENDED due to focus stealing.

---

## Approach 3: Native Swift/SwiftUI Companion App — RECOMMENDED

This is how Grammarly actually implements it — a separate native helper process.

### Key Advantage: No Focus Stealing

`NSPanel` with `.nonActivating` style mask won't take focus when clicked. This is the only approach that solves the focus problem.

### Capabilities

- Full SwiftUI visual capabilities (animations, translucency, vibrancy)
- Window level control: `.floating` (always on top)
- Native Accessibility support
- Communicates with Hammerspoon via HTTP server

### Implementation

```swift
import SwiftUI

@main
struct KokoroWidgetApp: App {
    var body: some Scene {
        Window("Kokoro", id: "main") {
            ControlsView()
                .frame(width: 180, height: 60)
        }
        .windowStyle(.hiddenTitleBar)
        .windowLevel(.floating)
    }
}

struct ControlsView: View {
    @State private var isPlaying = false

    var body: some View {
        HStack(spacing: 12) {
            Button(action: { togglePlayback() }) {
                Image(systemName: isPlaying ? "pause.fill" : "play.fill")
            }
            Button(action: { stop() }) {
                Image(systemName: "stop.fill")
            }
        }
        .padding(10)
        .background(.ultraThinMaterial)
        .cornerRadius(8)
    }

    func togglePlayback() {
        let url = URL(string: "http://localhost:18880/pause")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        URLSession.shared.dataTask(with: request).resume()
    }

    func stop() {
        let url = URL(string: "http://localhost:18880/stop")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        URLSession.shared.dataTask(with: request).resume()
    }
}
```

### NSPanel Configuration (AppKit alternative for fine control)

```swift
let panel = NSPanel(
    contentRect: NSRect(x: 0, y: 0, width: 180, height: 60),
    styleMask: [.nonactivatingPanel, .borderless],
    backing: .buffered,
    defer: false
)
panel.level = .floating
panel.isOpaque = false
panel.backgroundColor = .clear
panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
```

### Permissions

- No special permissions needed — communicates via localhost HTTP
- Hammerspoon can launch/manage it via `hs.task`

### Complexity: MEDIUM

- ~100-150 lines of Swift
- Separate Xcode project (or swift build with Package.swift)
- Must be built and placed in Applications or project bin/

### Verdict: BEST option for production. Only approach without focus stealing.

---

## Approach 4: Accessibility Overlay (Smart Positioning)

Use `hs.axuielement` to detect focused text fields and position widget near them.

### How It Works

1. Monitor focused window via `hs.window.focusedWindow()`
2. Get AX element tree via `hs.axuielement.windowElement()`
3. Find focused `AXTextField` / `AXTextArea`
4. Extract frame via `AXPosition` + `AXSize`
5. Position widget relative to the field

### App Compatibility

| App Type | Works? |
|----------|--------|
| TextEdit, Mail, Messages, Notes | Yes |
| Safari (web forms) | Mostly |
| VS Code | Partially |
| Canvas-based editors, games | No |

### Limitations

- Not all apps expose focused element reliably
- Needs frequent polling (500ms-1s) for position updates
- ~70% app coverage

### Verdict: Nice enhancement for Phase 3, not a standalone approach.

---

## Comparison Matrix

| Criteria | Canvas | WebView | Swift App | AX Overlay |
|----------|--------|---------|-----------|-----------|
| Visual Polish | Low | High | High | Medium |
| Focus Stealing | YES | YES | NO | NO |
| Implementation | 2-3 hours | 3-4 hours | 4-6 hours | 2-3 hours |
| Permissions | Already granted | Already granted | None extra | Already granted |
| How Grammarly Does It | No | No | YES | Enhancement |

---

## Recommended Strategy

### Phase 1: Hammerspoon Canvas (Quick MVP)

- Simple icon-only widget (play/pause/stop)
- Fixed position (bottom-right of screen)
- Accept focus-stealing limitation for validation
- 2-3 hours to build

### Phase 2: Swift Companion App (Production)

- Non-intrusive, never steals focus
- Full visual polish
- Communicates with Hammerspoon HTTP server
- 4-6 hours to build
- Hammerspoon launches it on startup

### Phase 3: Smart Positioning (Enhancement)

- AX-based text field detection
- Position widget near active input
- Show/hide based on app type
- Only if user feedback demands it

---

## Integration with HTTP Server

The widget (any approach) communicates with Hammerspoon's HTTP server:

```
POST /speak       → add text to queue and start
POST /stop        → stop current playback
POST /pause       → pause/resume current playback
GET  /status      → {state, currentItem, queueLength}
```
