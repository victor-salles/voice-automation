import SwiftUI
import Carbon.HIToolbox
import VoiceFlowCore

/// Central model that owns all components. Initialized once, held by @State in the App.
@Observable
@MainActor
final class AppModel {

    let status = StatusManager()
    private(set) var tts: TTSEngine!
    let extractor = TextExtractor()
    private var hotkey = HotkeyState()
    @ObservationIgnored private var overlayPanel = OverlayPanel()

    init() {
        self.tts = TTSEngine(status: status)
        debugLog("AppModel.init() — components created")
        tts.playbackUiRefresh = { [weak self] in
            self?.syncOverlayWithPlaybackState()
        }
        overlayPanel.onPrimaryAction = { [weak self] in
            self?.handleOverlayPrimaryAction()
        }
        // Defer hotkey setup to next run loop tick so self is fully initialized
        Task { @MainActor [weak self] in
            self?.setUpHotkey()
        }
    }

    private func setUpHotkey() {
        hotkey.setUp { @MainActor [weak self] in
            guard let self else { return }
            debugLog("Hotkey fired — status=\(self.status.current)")
            switch self.status.current {
            case .processing:
                self.stop()
            case .playing:
                self.tts.pause()
            case .paused:
                self.tts.resume()
            default:
                self.speakSelection()
            }
        }
        debugLog("Ready — ⌥S to speak selection")
    }

    func speakSelection() {
        debugLog("speakSelection() called")
        if let area = extractor.focusedTextArea(),
           let text = extractor.textFromCurrentParagraph(in: area.element),
           !text.isEmpty {
            debugLog("text-area path: \(text.count) chars from cursor paragraph")
            overlayPanel.show(at: area.frame)
            // Do not call `syncOverlayWithPlaybackState()` here: status is still `.idle` until
            // `speakSegments` sets `.processing`, and idle handling would immediately `hide()` the panel.
            let segments = TextProcessor.segment(text)
            debugLog("TextProcessor.segment() returned \(segments.count) segments")
            guard !segments.isEmpty else {
                debugLog("No speakable content after processing")
                overlayPanel.hide()
                return
            }
            tts.speakSegments(segments)
            return
        }

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

    var speed: Float {
        get { tts.speed }
        set { tts.speed = newValue }
    }

    func stop() {
        tts.stop()
        overlayPanel.hide()
    }

    func pauseSpeaking() {
        tts.pause()
    }

    func resumeSpeaking() {
        tts.resume()
    }

    func handleOverlayPrimaryAction() {
        switch status.current {
        case .playing:
            tts.pause()
        case .paused:
            tts.resume()
        default:
            stop()
        }
    }

    func syncOverlayWithPlaybackState() {
        guard overlayPanel.hasVisiblePanel else { return }
        switch status.current {
        case .idle:
            overlayPanel.hide()
        case .processing, .playing, .paused, .error:
            overlayPanel.sync(with: status.current)
        }
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
            HStack(spacing: 8) {
                Image(systemName: model.status.menuBarSymbolName)
                    .symbolRenderingMode(.monochrome)
                    .foregroundStyle(model.status.menuBarAccentColor ?? Color.secondary)
                Text(model.status.statusMenuTitle)
                    .foregroundStyle(.secondary)
            }
            .padding(.vertical, 2)
            .disabled(true)

            Divider()

            Button("Speak Selection  ⌥S") {
                debugLog("Menu button 'Speak Selection' clicked")
                model.speakSelection()
            }
            .disabled(model.status.current == .processing)

            Button("Pause") {
                model.pauseSpeaking()
            }
            .disabled(!model.status.canPause)

            Button("Resume") {
                model.resumeSpeaking()
            }
            .disabled(!model.status.canResume)

            Button("Stop") {
                model.stop()
            }
            .disabled(!model.status.canStop)

            Divider()

            Menu("Speed") {
                ForEach([0.75, 1.0, 1.15, 1.25, 1.5, 2.0] as [Float], id: \.self) { preset in
                    Button {
                        model.speed = preset
                    } label: {
                        let label = preset == 1.0 ? "1×  (normal)" : "\(String(format: "%g", preset))×"
                        if model.speed == preset {
                            Label(label, systemImage: "checkmark")
                        } else {
                            Text(label)
                        }
                    }
                }
            }

            Divider()

            Button("Quit VoiceFlow") {
                model.quit()
            }
        } label: {
            if let accent = model.status.menuBarAccentColor {
                Image(systemName: model.status.menuBarSymbolName)
                    .symbolRenderingMode(.monochrome)
                    .foregroundStyle(accent)
            } else {
                Image(systemName: model.status.menuBarSymbolName)
                    .foregroundStyle(.secondary)
            }
        }
        .onChange(of: model.status.current) { _, _ in
            model.syncOverlayWithPlaybackState()
        }
    }
}

// MARK: - Global Hotkey via CGEvent Tap

/// Encapsulates the CGEvent tap lifecycle for the ⌥S hotkey.
/// Plain class — not @Observable because it doesn't drive any UI.
final class HotkeyState {

    private var eventTap: CFMachPort?
    private var runLoopSource: CFRunLoopSource?
    private var action: (@MainActor () -> Void)?

    /// Register the ⌥S global hotkey. Call once on app launch.
    func setUp(action: @escaping @MainActor () -> Void) {
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
            guard let action = self?.action else { return }
            MainActor.assumeIsolated { action() }
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
