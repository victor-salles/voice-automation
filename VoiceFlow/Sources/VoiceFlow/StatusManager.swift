import SwiftUI

/// Single source of truth for app state. Drives the menu bar icon.
@Observable
final class StatusManager {

    enum Status {
        case idle
        case processing
        case playing
        case error
    }

    private(set) var current: Status = .idle

    /// SF Symbol name for the current state.
    var currentIcon: String {
        switch current {
        case .idle:       return "speaker.wave.2"
        case .processing: return "speaker.badge.exclamationmark"
        case .playing:    return "speaker.wave.2.fill"
        case .error:      return "speaker.slash"
        }
    }

    /// Whether the stop action is available.
    var canStop: Bool {
        current == .processing || current == .playing
    }

    // MARK: - State transitions

    func setProcessing() { current = .processing }
    func setPlaying()    { current = .playing }
    func setIdle()       { current = .idle }

    func setError() {
        current = .error
        // Auto-reset to idle after 3 seconds
        DispatchQueue.main.asyncAfter(deadline: .now() + 3) { [weak self] in
            guard let self, self.current == .error else { return }
            self.current = .idle
        }
    }
}
