import AVFoundation
import Foundation

/// Synthesizes speech via Kokoro HTTP API and plays with AVAudioPlayer.
/// Supports queued playback: plays segment N while pre-synthesizing N+1.
@MainActor
package final class TTSEngine: NSObject, @preconcurrency AVAudioPlayerDelegate {

    private let status: StatusManager
    private var player: AVAudioPlayer?
    private var currentTask: URLSessionDataTask?

    private let host: String
    private let port: String
    private let englishVoice: String
    private let portugueseVoice: String

    /// Kokoro voice for the active `speakSegments` queue (set when a batch starts).
    private var activeVoice: String = ""

    /// Playback speed multiplier. Applied to every segment via AVAudioPlayer.rate.
    /// Range 0.5–2.0; 1.0 is normal speed.
    package var speed: Float = 1.0

    // Queue state
    private var segments: [String] = []
    private var currentIndex = 0
    private var preBuffer: Data?       // pre-synthesized audio for next segment
    private var preSynthTask: URLSessionDataTask?
    private var generation = 0         // bumped on stop() to discard stale callbacks
    /// True while the current segment was paused via `pause()` (AVAudioPlayer paused).
    private var pausedByUser = false

    /// Fired after playback-related status changes so the app can refresh the floating overlay.
    package var playbackUiRefresh: (@MainActor () -> Void)?

    package init(status: StatusManager) {
        self.status = status
        self.host = ProcessInfo.processInfo.environment["KOKORO_HOST"] ?? "localhost"
        self.port = ProcessInfo.processInfo.environment["KOKORO_PORT"] ?? "8880"
        self.englishVoice = ProcessInfo.processInfo.environment["KOKORO_EN_VOICE"] ?? "af_heart"
        self.portugueseVoice = ProcessInfo.processInfo.environment["KOKORO_PT_BR_VOICE"] ?? "pf_dora"
        super.init()
    }

    // MARK: - Public API

    /// Speak a single piece of text (no segmentation).
    package func speak(_ text: String, language: InferredSpeakLanguage? = nil) {
        let resolved = language ?? LanguageInference.infer(from: text)
        speakSegments([text], language: resolved)
    }

    /// Speak a list of segments in order. Pre-synthesizes the next segment
    /// while the current one plays, so transitions are near-instant.
    package func speakSegments(_ newSegments: [String], language: InferredSpeakLanguage? = nil) {
        debugLog("speakSegments() called with \(newSegments.count) segments")
        stop()
        pausedByUser = false
        let filtered = newSegments.filter { !$0.isEmpty }
        guard !filtered.isEmpty else {
            debugLog("All segments were empty after filtering")
            return
        }

        let joinedForInference = filtered.joined(separator: "\n\n")
        let resolvedLanguage = language ?? LanguageInference.infer(from: joinedForInference)
        activeVoice = kokoroVoice(for: resolvedLanguage)
        debugLog("TTS language=\(resolvedLanguage.rawValue) voice=\(activeVoice)")

        segments = filtered
        currentIndex = 0
        status.setProcessing()
        playbackUiRefresh?()
        debugLog("Status → processing, synthesizing segment 0: \(segments[0].prefix(60))...")

        let gen = generation
        synthesize(segments[0]) { [weak self] data in
            guard let self else { debugLog("self was nil in synthesis callback"); return }
            guard self.generation == gen else { debugLog("Stale generation (\(gen) vs \(self.generation)), discarding"); return }
            guard let data else {
                debugLog("Synthesis returned nil data")
                self.status.setError()
                self.playbackUiRefresh?()
                return
            }
            debugLog("Synthesis OK, got \(data.count) bytes, playing...")
            self.play(data)
            self.preSynthNext()
        }
    }

    /// Stop all playback and cancel pending synthesis.
    package func stop() {
        generation += 1
        pausedByUser = false
        currentTask?.cancel()
        currentTask = nil
        preSynthTask?.cancel()
        preSynthTask = nil
        player?.stop()
        player = nil
        preBuffer = nil
        segments = []
        currentIndex = 0
        status.setIdle()
    }

    /// Pause the current segment. No-op if nothing is playing.
    package func pause() {
        guard let p = player, p.isPlaying else { return }
        p.pause()
        pausedByUser = true
        status.setPaused()
        playbackUiRefresh?()
    }

    /// Resume after `pause()`. No-op if not user-paused or player missing.
    package func resume() {
        guard pausedByUser, let p = player else { return }
        guard p.play() else { return }
        pausedByUser = false
        status.setPlaying()
        playbackUiRefresh?()
    }

    // MARK: - AVAudioPlayerDelegate

    package func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        self.player = nil
        advanceToNext()
    }

    // MARK: - Queue Management

    private func advanceToNext() {
        pausedByUser = false
        currentIndex += 1
        guard currentIndex < segments.count else {
            status.setIdle()
            playbackUiRefresh?()
            return
        }

        let gen = generation

        // Use pre-buffered audio if available
        if let buffered = preBuffer {
            preBuffer = nil
            play(buffered)
            preSynthNext()
        } else {
            // Pre-synth wasn't ready — synthesize on demand
            status.setProcessing()
            playbackUiRefresh?()
            synthesize(segments[currentIndex]) { [weak self] data in
                guard let self, self.generation == gen else { return }
                guard let data else {
                    self.status.setError()
                    self.playbackUiRefresh?()
                    return
                }
                self.play(data)
                self.preSynthNext()
            }
        }
    }

    /// Pre-synthesize the next segment in the background.
    private func preSynthNext() {
        let nextIndex = currentIndex + 1
        guard nextIndex < segments.count else { return }

        let gen = generation
        preSynthTask?.cancel()

        synthesize(segments[nextIndex]) { [weak self] data in
            guard let self, self.generation == gen else { return }
            self.preBuffer = data
        }
    }

    // MARK: - Synthesis and Playback

    private func kokoroVoice(for language: InferredSpeakLanguage) -> String {
        switch language {
        case .americanEnglish: englishVoice
        case .brazilianPortuguese: portugueseVoice
        }
    }

    private func synthesize(_ text: String, completion: @escaping (Data?) -> Void) {
        let isLocal = host == "localhost" || host == "127.0.0.1"
        let scheme = isLocal ? "http" : "https"
        guard let url = URL(string: "\(scheme)://\(host):\(port)/v1/audio/speech") else {
            completion(nil)
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30

        let body: [String: Any] = ["input": text, "voice": activeVoice]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            let http = response as? HTTPURLResponse
            guard error == nil,
                  http?.statusCode == 200,
                  let data, !data.isEmpty else {
                let reason = error?.localizedDescription ?? "HTTP \(http?.statusCode ?? 0)"
                debugLog("Synthesis failed: \(reason)")
                DispatchQueue.main.async { completion(nil) }
                return
            }
            DispatchQueue.main.async { completion(data) }
        }
        currentTask = task
        task.resume()
    }

    private func play(_ data: Data) {
        do {
            player = try AVAudioPlayer(data: data)
            player?.delegate = self
            player?.enableRate = true
            player?.rate = speed
            player?.play()
            status.setPlaying()
            playbackUiRefresh?()
        } catch {
            debugLog("Playback error: \(error)")
            status.setError()
            playbackUiRefresh?()
        }
    }
}
