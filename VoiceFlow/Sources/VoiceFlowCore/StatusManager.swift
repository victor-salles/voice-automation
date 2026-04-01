import SwiftUI

/// Single source of truth for app state. Drives the menu bar icon and overlay styling.
///
/// **Iconography:** Waveform when idle/processing; green `pause.circle.fill` while playing; blue `play.circle.fill` when paused; red alert on error (aligned with the floating overlay).
/// **Menu bar tint:** idle and processing use secondary (uncolored); playing green; paused blue; error red.
@Observable
@MainActor
package final class StatusManager {

    package enum Status: Equatable {
        case idle
        case processing
        case playing
        case paused
        case error
    }

    package private(set) var current: Status = .idle

    /// Primary symbol for menu bar and status rows (matches floating overlay transport glyphs).
    package var menuBarSymbolName: String {
        switch current {
        case .idle: return "waveform.circle"
        case .processing: return "waveform.circle.fill"
        case .playing: return "pause.circle.fill"
        case .paused: return "play.circle.fill"
        case .error: return "exclamationmark.circle.fill"
        }
    }

    /// Short label for submenu / accessibility.
    package var statusMenuTitle: String {
        switch current {
        case .idle: return "Idle"
        case .processing: return "Preparing audio…"
        case .playing: return "Playing"
        case .paused: return "Paused — press ⌥S to resume"
        case .error: return "Error"
        }
    }

    /// When non-`nil`, tint the menu bar icon with this color; otherwise use secondary (uncolored).
    package var menuBarAccentColor: Color? {
        switch current {
        case .idle, .processing: return nil
        case .playing: return .green
        case .paused: return .blue
        case .error: return .red
        }
    }

    package var canPause: Bool { current == .playing }
    package var canResume: Bool { current == .paused }

    /// Full stop: cancels synthesis and playback (processing, playing, or paused).
    package var canStop: Bool {
        switch current {
        case .processing, .playing, .paused: return true
        case .idle, .error: return false
        }
    }

    package init() {}

    // MARK: - State transitions

    package func setProcessing() { current = .processing }
    package func setPlaying() { current = .playing }
    package func setPaused() { current = .paused }
    package func setIdle() { current = .idle }

    package func setError() {
        current = .error
        Task { [weak self] in
            try? await Task.sleep(for: .seconds(3))
            guard let self, self.current == .error else { return }
            self.current = .idle
        }
    }
}
