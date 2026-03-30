import AVFoundation
import Foundation

/// Synthesizes speech via Kokoro HTTP API and plays with AVAudioPlayer.
/// No process spawning — everything in-process.
final class TTSEngine: NSObject, AVAudioPlayerDelegate {

    private let status: StatusManager
    private var player: AVAudioPlayer?
    private var currentTask: URLSessionDataTask?

    private let host: String
    private let port: String
    private let voice: String

    init(status: StatusManager) {
        self.status = status
        self.host = ProcessInfo.processInfo.environment["KOKORO_HOST"] ?? "localhost"
        self.port = ProcessInfo.processInfo.environment["KOKORO_PORT"] ?? "8880"
        self.voice = ProcessInfo.processInfo.environment["KOKORO_EN_VOICE"] ?? "af_heart"
        super.init()
    }

    // MARK: - Public API

    /// Synthesize text via Kokoro and play it. Stops any current playback first.
    func speak(_ text: String) {
        stop()
        guard !text.isEmpty else { return }

        status.setProcessing()

        synthesize(text) { [weak self] data in
            guard let self else { return }

            guard let data else {
                self.status.setError()
                return
            }

            self.play(data)
        }
    }

    /// Stop any active synthesis or playback.
    func stop() {
        currentTask?.cancel()
        currentTask = nil
        player?.stop()
        player = nil
        status.setIdle()
    }

    // MARK: - AVAudioPlayerDelegate

    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        self.player = nil
        status.setIdle()
    }

    // MARK: - Private

    private func synthesize(_ text: String, completion: @escaping (Data?) -> Void) {
        guard let url = URL(string: "http://\(host):\(port)/v1/audio/speech") else {
            completion(nil)
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30

        let body: [String: Any] = ["input": text, "voice": voice]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        let task = URLSession.shared.dataTask(with: request) { data, response, error in
            let http = response as? HTTPURLResponse
            guard error == nil,
                  http?.statusCode == 200,
                  let data, !data.isEmpty else {
                let reason = error?.localizedDescription ?? "HTTP \(http?.statusCode ?? 0)"
                print("[VoiceFlow] Synthesis failed: \(reason)")
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
            player?.play()
            status.setPlaying()
        } catch {
            print("[VoiceFlow] Playback error: \(error)")
            status.setError()
        }
    }
}
