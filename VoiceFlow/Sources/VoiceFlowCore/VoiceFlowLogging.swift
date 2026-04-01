import Foundation

/// Central switch for file logging (`/tmp/voiceflow-debug.log` by default).
/// - **Debug builds:** always on.
/// - **Release builds (e.g. `make install`):** set `VOICEFLOW_DEBUG_LOG=1` or `VOICEFLOW_DEBUG_LOG_FILE=/path/to.log`.
package enum VoiceFlowLogging {

    package static var isEnabled: Bool {
        #if DEBUG
        true
        #else
        let flag = ProcessInfo.processInfo.environment["VOICEFLOW_DEBUG_LOG"]?.lowercased()
        if flag == "1" || flag == "true" || flag == "yes" { return true }
        let path = ProcessInfo.processInfo.environment["VOICEFLOW_DEBUG_LOG_FILE"] ?? ""
        return path.hasPrefix("/") && !path.isEmpty
        #endif
    }

    package static var logFileURL: URL {
        if let path = ProcessInfo.processInfo.environment["VOICEFLOW_DEBUG_LOG_FILE"], path.hasPrefix("/") {
            return URL(fileURLWithPath: path)
        }
        return URL(fileURLWithPath: "/tmp/voiceflow-debug.log")
    }

    package static func appendLine(_ line: String) {
        guard isEnabled else { return }
        let ts = ISO8601DateFormatter().string(from: Date())
        let payload = "[\(ts)] \(line)\n"
        guard let data = payload.data(using: .utf8) else { return }
        let url = logFileURL
        if FileManager.default.fileExists(atPath: url.path) {
            guard let handle = try? FileHandle(forWritingTo: url) else { return }
            handle.seekToEndOfFile()
            handle.write(data)
            try? handle.close()
        } else {
            try? data.write(to: url)
        }
    }

    package static func appendBlock(title: String, lines: [String]) {
        guard isEnabled else { return }
        appendLine("--- \(title) ---")
        for line in lines {
            appendLine(line)
        }
        appendLine("--- end \(title) ---")
    }
}
