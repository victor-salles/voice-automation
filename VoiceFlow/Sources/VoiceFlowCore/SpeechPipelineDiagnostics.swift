import Foundation

/// Inspect how raw selection maps to segmentation (for investigating paragraph / newline issues).
package enum SpeechPipelineDiagnostics {

    package struct Snapshot: Sendable {
        package let rawCharacterCount: Int
        package let rawUTF16Length: Int
        package let rawNewlineCount: Int
        package let rawCarriageReturnCount: Int
        /// Runs of newline + optional horizontal whitespace + newline (typical blank line between paragraphs).
        package let rawParagraphGapPatternCount: Int
        package let preprocessedForBlocksCharacterCount: Int
        package let selectionRecoveryChangedInput: Bool
        package let preprocessedVisibleExcerpt: String
        package let blockCountBeforeClean: Int
        package let blockSummaries: [String]
        package let finalSegmentCount: Int
    }

    package static func makeSnapshot(rawInput: String, segments: [String]) -> Snapshot {
        let nl = rawInput.filter { $0 == "\n" }.count
        let cr = rawInput.filter { $0 == "\r" }.count
        let gaps = countParagraphGapPatterns(in: rawInput)
        let recovered = TextProcessor.recoverSpacingWhenSourceStripsNewlines(rawInput)
        let preprocessed = TextProcessor.preprocessForSegmentation(rawInput)
        let blocks = TextProcessor.debugBlocksFromPreprocessed(preprocessed)
        let summaries = blocks.enumerated().map { index, block -> String in
            let preview = Self.visibleOneLine(String(block.prefix(200)))
            return "block[\(index)] len=\(block.count) \(preview)"
        }
        let excerpt = Self.visibleOneLine(String(preprocessed.prefix(500)))
        return Snapshot(
            rawCharacterCount: rawInput.count,
            rawUTF16Length: rawInput.utf16.count,
            rawNewlineCount: nl,
            rawCarriageReturnCount: cr,
            rawParagraphGapPatternCount: gaps,
            preprocessedForBlocksCharacterCount: preprocessed.count,
            selectionRecoveryChangedInput: recovered != rawInput,
            preprocessedVisibleExcerpt: excerpt + (preprocessed.count > 500 ? " …" : ""),
            blockCountBeforeClean: blocks.count,
            blockSummaries: summaries,
            finalSegmentCount: segments.count
        )
    }

    package static func formatSnapshot(_ s: Snapshot, source: String) -> [String] {
        var lines: [String] = []
        lines.append("speechPath=\(source)")
        lines.append("rawCharCount=\(s.rawCharacterCount) rawUTF16=\(s.rawUTF16Length)")
        lines.append("rawNewlines=\(s.rawNewlineCount) rawCR=\(s.rawCarriageReturnCount) rawParagraphGaps(\\n[space]*\\n)=\(s.rawParagraphGapPatternCount)")
        lines.append("selectionRecoveryChanged=\(s.selectionRecoveryChangedInput) preprocessedForBlocksCharCount=\(s.preprocessedForBlocksCharacterCount)")
        lines.append("preprocessedVisibleExcerpt(500): \(s.preprocessedVisibleExcerpt)")
        lines.append("blocksBeforeClean=\(s.blockCountBeforeClean) finalSegments=\(s.finalSegmentCount)")
        lines.append("blocks:")
        lines.append(contentsOf: s.blockSummaries.map { "  \($0)" })
        return lines
    }

    package static func formatRawSelectionExcerpt(_ raw: String, maxCharacters: Int = 1200) -> [String] {
        let excerpt: String
        if raw.count <= maxCharacters {
            excerpt = raw
        } else {
            excerpt = String(raw.prefix(maxCharacters)) + " …(truncated, totalChars=\(raw.count))"
        }
        return [
            "rawVisible (\\n shown as ⏎, \\r as ↵):",
            visibleOneLine(excerpt),
        ]
    }

    package static func formatSegments(_ segments: [String]) -> [String] {
        var lines: [String] = ["segments:"]
        for (i, seg) in segments.enumerated() {
            lines.append("  [\(i)] len=\(seg.count) \(visibleOneLine(String(seg.prefix(160))))")
        }
        return lines
    }

    package static func visibleOneLine(_ s: String) -> String {
        s
            .replacingOccurrences(of: "\r\n", with: "⏎")
            .replacingOccurrences(of: "\n", with: "⏎")
            .replacingOccurrences(of: "\r", with: "↵")
    }

    private static func countParagraphGapPatterns(in raw: String) -> Int {
        guard !raw.isEmpty else { return 0 }
        do {
            let regex = try NSRegularExpression(pattern: #"\n[ \t]*\n"#, options: [])
            let range = NSRange(location: 0, length: (raw as NSString).length)
            return regex.numberOfMatches(in: raw, options: [], range: range)
        } catch {
            return 0
        }
    }

    /// Writes a structured block to the VoiceFlow log when logging is enabled (see `VoiceFlowLogging`).
    package static func logSpeechPipelineIfEnabled(source: String, rawText: String, segments: [String]) {
        guard VoiceFlowLogging.isEnabled else { return }
        let snap = makeSnapshot(rawInput: rawText, segments: segments)
        var lines = formatSnapshot(snap, source: source)
        lines.append("")
        lines.append(contentsOf: formatRawSelectionExcerpt(rawText))
        lines.append("")
        lines.append(contentsOf: formatSegments(segments))
        VoiceFlowLogging.appendBlock(title: "speech pipeline", lines: lines)
    }
}
