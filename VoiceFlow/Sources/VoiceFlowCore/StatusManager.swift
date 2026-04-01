import SwiftUI

/// Single source of truth for app state. Drives the menu bar icon.
@Observable
@MainActor
package final class StatusManager {

    package enum Status {
        case idle
        case processing
        case playing
        case error
    }

    package private(set) var current: Status = .idle

    /// SF Symbol name for the current state.
    package var currentIcon: String {
        switch current {
        case .idle:       return "speaker.wave.2"
        case .processing: return "speaker.badge.exclamationmark"
        case .playing:    return "speaker.wave.2.fill"
        case .error:      return "speaker.slash"
        }
    }

    /// Whether the stop action is available.
    package var canStop: Bool {
        current == .processing || current == .playing
    }

    package init() {}

    // MARK: - State transitions

    package func setProcessing() { current = .processing }
    package func setPlaying()    { current = .playing }
    package func setIdle()       { current = .idle }

    package func setError() {
        current = .error
        // Auto-reset to idle after 3 seconds
        Task { [weak self] in
            try? await Task.sleep(for: .seconds(3))
            guard let self, self.current == .error else { return }
            self.current = .idle
        }
    }
}
