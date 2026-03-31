import SwiftUI
import Carbon.HIToolbox

// MARK: - File-based debug logging

private let logURL = URL(fileURLWithPath: "/tmp/voiceflow-debug.log")

func debugLog(_ message: String) {
    let line = "[\(ISO8601DateFormatter().string(from: Date()))] \(message)\n"
    if let data = line.data(using: .utf8) {
        if FileManager.default.fileExists(atPath: logURL.path) {
            if let handle = try? FileHandle(forWritingTo: logURL) {
                handle.seekToEndOfFile()
                handle.write(data)
                handle.closeFile()
            }
        } else {
            try? data.write(to: logURL)
        }
    }
}

/// Central model that owns all components. Initialized once, held by @State in the App.
@Observable
final class AppModel {

    let status = StatusManager()
    private(set) var tts: TTSEngine!
    let extractor = TextExtractor()
    private var hotkey = HotkeyState()

    init() {
        self.tts = TTSEngine(status: status)
        debugLog("AppModel.init() — components created")
        // Defer hotkey setup to next run loop tick so self is fully initialized
        DispatchQueue.main.async { [weak self] in
            self?.setUpHotkey()
        }
    }

    private func setUpHotkey() {
        hotkey.setUp { [weak self] in
            guard let self else { return }
            debugLog("Hotkey fired — canStop=\(self.status.canStop)")
            if self.status.canStop {
                self.tts.stop()
            } else {
                self.speakSelection()
            }
        }
        debugLog("Ready — ⌥S to speak selection")
    }

    func speakSelection() {
        debugLog("speakSelection() called")
        let text = extractor.selectedText()
        debugLog("selectedText() returned: \(text == nil ? "nil" : "\(text!.count) chars: \(String(text!.prefix(80)))")")
        guard let text, !text.isEmpty else {
            debugLog("No text selected")
            return
        }
        let segments = TextProcessor.segment(text)
        debugLog("TextProcessor.segment() returned \(segments.count) segments")
        for (i, seg) in segments.enumerated() {
            debugLog("  segment[\(i)]: \(seg.prefix(60))...")
        }
        guard !segments.isEmpty else {
            debugLog("No speakable content after processing")
            return
        }
        tts.speakSegments(segments)
    }

    func stop() {
        tts.stop()
    }

    func quit() {
        hotkey.tearDown()
        NSApplication.shared.terminate(nil)
    }
}

// MARK: - App Entry Point

@main
struct VoiceFlowApp: App {

    @State private var model = AppModel()

    var body: some Scene {
        MenuBarExtra {
            Button("Speak Selection  ⌥S") {
                debugLog("Menu button 'Speak Selection' clicked")
                model.speakSelection()
            }
            .disabled(model.status.current == .processing)

            Button("Stop") {
                model.stop()
            }
            .disabled(!model.status.canStop)

            Divider()

            Button("Quit VoiceFlow") {
                model.quit()
            }
        } label: {
            Image(systemName: model.status.currentIcon)
        }
    }
}

// MARK: - Global Hotkey via CGEvent Tap

/// Encapsulates the CGEvent tap lifecycle for the ⌥S hotkey.
/// Plain class — not @Observable because it doesn't drive any UI.
final class HotkeyState {

    private var eventTap: CFMachPort?
    private var runLoopSource: CFRunLoopSource?
    private var action: (() -> Void)?

    /// Register the ⌥S global hotkey. Call once on app launch.
    func setUp(action: @escaping () -> Void) {
        self.action = action

        let refcon = Unmanaged.passUnretained(self).toOpaque()

        guard let tap = CGEvent.tapCreate(
            tap: .cgSessionEventTap,
            place: .headInsertEventTap,
            options: .defaultTap,
            eventsOfInterest: CGEventMask(1 << CGEventType.keyDown.rawValue),
            callback: hotkeyCallback,
            userInfo: refcon
        ) else {
            debugLog("Could not create event tap.")
            debugLog("Grant Accessibility in System Settings → Privacy & Security → Accessibility")
            return
        }

        eventTap = tap
        runLoopSource = CFMachPortCreateRunLoopSource(nil, tap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, .commonModes)
        CGEvent.tapEnable(tap: tap, enable: true)
        debugLog("Global hotkey ⌥S active")
    }

    /// Remove the event tap. Call before quit.
    func tearDown() {
        if let tap = eventTap {
            CGEvent.tapEnable(tap: tap, enable: false)
            if let source = runLoopSource {
                CFRunLoopRemoveSource(CFRunLoopGetCurrent(), source, .commonModes)
            }
        }
        eventTap = nil
        runLoopSource = nil
        action = nil
    }

    /// Called from the C callback on the main thread.
    fileprivate func handleKeyDown(_ event: CGEvent) -> Bool {
        let keyCode = event.getIntegerValueField(.keyboardEventKeycode)
        let flags = event.flags

        // ⌥S: keyCode 1, Option modifier only
        let modifiers = flags.intersection([.maskAlternate, .maskShift, .maskControl, .maskCommand])
        guard keyCode == 1, modifiers == .maskAlternate else { return false }

        DispatchQueue.main.async { [weak self] in
            self?.action?()
        }
        return true
    }
}

/// C-compatible callback for the CGEvent tap.
private func hotkeyCallback(
    proxy: CGEventTapProxy,
    type: CGEventType,
    event: CGEvent,
    refcon: UnsafeMutableRawPointer?
) -> Unmanaged<CGEvent>? {
    guard type == .keyDown, let refcon else {
        return Unmanaged.passRetained(event)
    }
    let state = Unmanaged<HotkeyState>.fromOpaque(refcon).takeUnretainedValue()
    if state.handleKeyDown(event) {
        return nil // consumed
    }
    return Unmanaged.passRetained(event)
}
