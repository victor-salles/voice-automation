import SwiftUI
import Carbon.HIToolbox

/// Central model that owns all components. Initialized once, held by @State in the App.
@Observable
final class AppModel {

    let status = StatusManager()
    private(set) var tts: TTSEngine!
    let extractor = TextExtractor()
    private var hotkey = HotkeyState()

    init() {
        self.tts = TTSEngine(status: status)
        // Defer hotkey setup to next run loop tick so self is fully initialized
        DispatchQueue.main.async { [weak self] in
            self?.setUpHotkey()
        }
    }

    private func setUpHotkey() {
        hotkey.setUp { [weak self] in
            guard let self else { return }
            if self.status.canStop {
                self.tts.stop()
            } else {
                self.speakSelection()
            }
        }
        print("[VoiceFlow] Ready — ⌥S to speak selection")
    }

    func speakSelection() {
        guard let text = extractor.selectedText(), !text.isEmpty else {
            print("[VoiceFlow] No text selected")
            return
        }
        tts.speak(text)
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
            print("[VoiceFlow] Could not create event tap.")
            print("[VoiceFlow] Grant Accessibility in System Settings → Privacy & Security → Accessibility")
            return
        }

        eventTap = tap
        runLoopSource = CFMachPortCreateRunLoopSource(nil, tap, 0)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, .commonModes)
        CGEvent.tapEnable(tap: tap, enable: true)
        print("[VoiceFlow] Global hotkey ⌥S active")
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
