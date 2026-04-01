import Foundation
import NaturalLanguage

/// Pure text processing: clean markup, segment into speakable chunks.
/// No I/O, no side effects — fully testable.
package enum TextProcessor {

    // MARK: - Segmentation

    /// Target upper size for one synthesis segment (Swift `Character` count).
    /// Roughly aligned with Kokoro-FastAPI server chunking (~175–250 tokens); shorter chunks
    /// tend to sound less rushed and give natural pauses between queue items.
    private static let maxSegmentCharacterCount = 320

    /// Split text into speakable segments: paragraphs, list items, sentences.
    /// Each segment is cleaned and ready for TTS.
    package static func segment(_ text: String) -> [String] {
        let blocks = splitIntoBlocks(preprocessForSegmentation(text))

        // Clean each block, split long ones at linguistic sentence boundaries
        var segments: [String] = []
        for block in blocks {
            let cleaned = clean(block)
            guard !cleaned.isEmpty else { continue }

            if cleaned.count > maxSegmentCharacterCount {
                segments.append(contentsOf: packSentencesIntoChunks(cleaned, maxCharacters: maxSegmentCharacterCount))
            } else {
                segments.append(cleaned)
            }
        }

        // Merge only very short fragments (< 12 chars) into the following segment so typical
        // markdown lines (~15–40 chars) keep clause boundaries and queue pauses.
        return mergeShortSegments(segments, minLength: 12)
    }

    /// Recovery pass + em dash expansion, in the same order as `segment(_:)`.
    package static func preprocessForSegmentation(_ text: String) -> String {
        preprocessEmDashesForParagraphBreaks(recoverSpacingWhenSourceStripsNewlines(text))
    }

    /// Same dash → newline preprocessing as `segment(_:)` (for diagnostics only).
    package static func preprocessEmDashesForParagraphBreaks(_ text: String) -> String {
        text.replacingOccurrences(
            of: #"\s*[—–]\s*"#,
            with: "\n\n",
            options: .regularExpression
        )
    }

    /// Many apps return `kAXSelectedText` with **no newlines** between paragraphs (e.g. chat / web views).
    /// Insert missing spaces so words are not glued (`it.Logging` → `it. Logging`) and list markers breathe (`behavior1.` → `behavior 1.`).
    package static func recoverSpacingWhenSourceStripsNewlines(_ text: String) -> String {
        var t = text
        t = replaceRegex(t, pattern: #"(\p{Ll})\.(\p{Lu})"#, template: "$1. $2")
        t = replaceRegex(t, pattern: #"([!?…])(\p{Lu})"#, template: "$1 $2")
        t = replaceRegex(t, pattern: #"(\p{Ll}{4,})([1-9]\d?\.)"#, template: "$1 $2")
        t = replaceRegex(t, pattern: #"([^\s•])•"#, template: "$1 •")
        t = replaceRegex(t, pattern: #"\s•\s"#, template: "\n• ")
        return t
    }

    private static func replaceRegex(_ string: String, pattern: String, template: String) -> String {
        guard let regex = try? NSRegularExpression(pattern: pattern, options: []) else { return string }
        let range = NSRange(location: 0, length: (string as NSString).length)
        return regex.stringByReplacingMatches(in: string, options: [], range: range, withTemplate: template)
    }

    /// Block list after full `preprocessForSegmentation` and `splitIntoBlocks` — **before** `clean` (for logging).
    package static func debugBlocksFromPreprocessed(_ preprocessedText: String) -> [String] {
        splitIntoBlocks(preprocessedText)
    }

    /// Split text into structural blocks: blank-line paragraphs, list items, and logical lines in markdown.
    ///
    /// Single newlines become **new blocks** unless the next line looks like a hard-wrapped continuation
    /// (previous line does not end a sentence; next line starts with a lowercase letter). That keeps
    /// editor-wrapped prose as one block while giving pauses between markdown lines that start a new thought.
    private static func splitIntoBlocks(_ text: String) -> [String] {
        var blocks: [String] = []
        var pending: String?

        func flushPending() {
            if let p = pending {
                blocks.append(p)
                pending = nil
            }
        }

        for line in text.components(separatedBy: "\n") {
            let trimmed = line.trimmingCharacters(in: .whitespaces)

            if trimmed.isEmpty {
                flushPending()
                continue
            }

            if isListItem(trimmed) {
                flushPending()
                blocks.append(trimmed)
                continue
            }

            if let current = pending {
                if shouldMergeHardWrappedLine(previousLineContent: current, nextLine: trimmed) {
                    pending = current + " " + trimmed
                } else {
                    blocks.append(current)
                    pending = trimmed
                }
            } else {
                pending = trimmed
            }
        }
        flushPending()
        return blocks
    }

    /// `true` when `nextLine` is likely the same paragraph continued from a column wrap (not a new markdown line).
    private static func shouldMergeHardWrappedLine(previousLineContent: String, nextLine: String) -> Bool {
        !endsWithSentenceBreak(previousLineContent) && startsWithLowercaseLetter(nextLine)
    }

    private static func endsWithSentenceBreak(_ line: String) -> Bool {
        let t = line.trimmingCharacters(in: .whitespaces)
        guard let last = t.last else { return false }
        return ".?!…".contains(last)
    }

    private static func startsWithLowercaseLetter(_ line: String) -> Bool {
        let t = line.trimmingCharacters(in: .whitespaces)
        guard let first = t.first else { return false }
        return first.isLetter && first.isLowercase
    }

    private static func isListItem(_ line: String) -> Bool {
        // Unordered: - item, * item, + item
        if line.range(of: #"^[-*+]\s+"#, options: .regularExpression) != nil { return true }
        // Bullet (common when newlines are stripped from rich text)
        if line.range(of: #"^•\s+"#, options: .regularExpression) != nil { return true }
        // Ordered: 1. item, 2. item
        if line.range(of: #"^\d+\.\s+"#, options: .regularExpression) != nil { return true }
        return false
    }

    /// Sentence fragments in document order (English, Portuguese, etc.).
    private static func linguisticSentences(in text: String) -> [String] {
        let tokenizer = NLTokenizer(unit: .sentence)
        tokenizer.string = text
        var sentences: [String] = []
        tokenizer.enumerateTokens(in: text.startIndex..<text.endIndex) { range, _ in
            let piece = String(text[range]).trimmingCharacters(in: .whitespacesAndNewlines)
            if !piece.isEmpty { sentences.append(piece) }
            return true
        }
        if sentences.isEmpty, !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return [text.trimmingCharacters(in: .whitespacesAndNewlines)]
        }
        return sentences
    }

    /// Pack sentences into chunks at or below `maxCharacters`, splitting oversized sentences at spaces.
    private static func packSentencesIntoChunks(_ text: String, maxCharacters: Int) -> [String] {
        var chunks: [String] = []
        var buffer = ""

        func flushBuffer() {
            let trimmed = buffer.trimmingCharacters(in: .whitespacesAndNewlines)
            if !trimmed.isEmpty { chunks.append(trimmed) }
            buffer = ""
        }

        for sentence in linguisticSentences(in: text) {
            for fragment in splitOversizedClause(sentence, maxCharacters: maxCharacters) {
                if buffer.isEmpty {
                    buffer = fragment
                    continue
                }
                if buffer.count + 1 + fragment.count <= maxCharacters {
                    buffer += " " + fragment
                } else {
                    flushBuffer()
                    buffer = fragment
                }
            }
        }
        flushBuffer()
        return chunks
    }

    /// When a single sentence exceeds the limit, break at spaces (words stay intact when possible).
    private static func splitOversizedClause(_ text: String, maxCharacters: Int) -> [String] {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmed.count > maxCharacters else { return [trimmed] }

        var parts: [String] = []
        var remainder = trimmed[...]
        while !remainder.isEmpty {
            if remainder.count <= maxCharacters {
                parts.append(String(remainder))
                break
            }
            let endIdx = remainder.index(remainder.startIndex, offsetBy: maxCharacters, limitedBy: remainder.endIndex)
                ?? remainder.endIndex
            var window = remainder[..<endIdx]
            if let lastSpace = window.lastIndex(of: " "), lastSpace > remainder.startIndex {
                window = remainder[..<lastSpace]
            }
            let piece = window.trimmingCharacters(in: .whitespacesAndNewlines)
            if !piece.isEmpty { parts.append(piece) }
            remainder = remainder[window.endIndex...].drop(while: { $0 == " " })
        }
        return parts.isEmpty ? [trimmed] : parts
    }

    /// Merge very short segments with the next, except isolated tiny fragments (e.g. em-dash clauses) that should keep a boundary.
    private static func mergeShortSegments(_ segments: [String], minLength: Int) -> [String] {
        guard !segments.isEmpty else { return [] }
        var result: [String] = []
        var carry = ""

        for segment in segments {
            if carry.isEmpty {
                if segment.count < minLength {
                    carry = segment
                } else {
                    result.append(segment)
                }
                continue
            }

            if segment.count >= minLength {
                result.append("\(carry) \(segment)")
                carry = ""
                continue
            }

            let bothShort = carry.count < minLength && segment.count < minLength
            let noSentencePunctAnywhere = !carry.contains(where: { ".?!…".contains($0) })
                && !segment.contains(where: { ".?!…".contains($0) })
            let carryEndsBreak = carry.last.map { ".?!…".contains($0) } ?? false
            let segmentEndsBreak = segment.last.map { ".?!…".contains($0) } ?? false

            if bothShort {
                if noSentencePunctAnywhere {
                    result.append(carry)
                    carry = segment
                } else if carryEndsBreak && segmentEndsBreak {
                    result.append("\(carry) \(segment)")
                    carry = ""
                } else {
                    result.append(carry)
                    carry = segment
                }
                continue
            }

            result.append("\(carry) \(segment)")
            carry = ""
        }

        if !carry.isEmpty {
            if let last = result.last, last.count >= minLength {
                result[result.count - 1] = "\(last) \(carry)"
            } else {
                result.append(carry)
            }
        }

        return result
    }

    // MARK: - Text Cleaning

    /// Full cleaning pipeline: strip markup → strip symbols → normalize.
    package static func clean(_ text: String) -> String {
        var t = recoverSpacingWhenSourceStripsNewlines(text)
        // Clause break: speak as end of sentence (pause) without requiring SSML.
        t = t.replacingOccurrences(of: #"\s*[—–]\s*"#, with: ". ", options: .regularExpression)
        t = stripCodeBlocks(t)
        t = stripInlineCode(t)
        t = stripMarkdown(t)
        t = stripLinks(t)
        t = stripLists(t)
        t = stripSpecial(t)
        t = normalize(t)
        return t
    }

    // MARK: - Pipeline Steps

    private static func stripCodeBlocks(_ text: String) -> String {
        text.replacingOccurrences(
            of: #"```[\s\S]*?```"#, with: " code block omitted. ",
            options: .regularExpression
        )
    }

    private static func stripInlineCode(_ text: String) -> String {
        text.replacingOccurrences(
            of: #"`([^`]+)`"#, with: "$1",
            options: .regularExpression
        )
    }

    private static func stripMarkdown(_ text: String) -> String {
        var t = text
        // Headers → plain text with period
        t = t.replacingOccurrences(
            of: #"(?m)^#{1,6}\s+(.+)$"#,
            with: "$1.",
            options: .regularExpression
        )
        // Bold
        t = t.replacingOccurrences(of: #"\*\*(.+?)\*\*"#, with: "$1", options: .regularExpression)
        t = t.replacingOccurrences(of: #"__(.+?)__"#, with: "$1", options: .regularExpression)
        // Italic
        t = t.replacingOccurrences(of: #"[*_](.+?)[*_]"#, with: "$1", options: .regularExpression)
        // Strikethrough
        t = t.replacingOccurrences(of: #"~~(.+?)~~"#, with: "$1", options: .regularExpression)
        return t
    }

    private static func stripLinks(_ text: String) -> String {
        var t = text
        // Images
        t = t.replacingOccurrences(of: #"!\[([^\]]*)\]\([^)]+\)"#, with: "$1", options: .regularExpression)
        // Markdown links
        t = t.replacingOccurrences(of: #"\[([^\]]+)\]\([^)]+\)"#, with: "$1", options: .regularExpression)
        // Bare URLs
        t = t.replacingOccurrences(of: #"https?://\S+"#, with: "link", options: .regularExpression)
        return t
    }

    private static func stripLists(_ text: String) -> String {
        var t = text
        // Unordered lists: - item, * item, + item
        t = t.replacingOccurrences(
            of: #"(?m)^\s*[-*+]\s+(.+)$"#, with: "$1.",
            options: .regularExpression
        )
        // Bullet character lists
        t = t.replacingOccurrences(
            of: #"(?m)^\s*•\s+(.+)$"#, with: "$1.",
            options: .regularExpression
        )
        // Ordered lists: 1. item
        t = t.replacingOccurrences(
            of: #"(?m)^\s*\d+\.\s+(.+)$"#, with: "$1.",
            options: .regularExpression
        )
        return t
    }

    private static func stripSpecial(_ text: String) -> String {
        var t = text
        // Arrows
        t = t.replacingOccurrences(of: #"[→⟶⟹➡►▸]"#, with: " to ", options: .regularExpression)
        t = t.replacingOccurrences(of: #"[←⟵⟸⬅◄◂]"#, with: " from ", options: .regularExpression)
        // macOS keyboard symbols
        t = t.replacingOccurrences(of: "⌥", with: "Option ")
        t = t.replacingOccurrences(of: "⌘", with: "Command ")
        t = t.replacingOccurrences(of: "⇧", with: "Shift ")
        t = t.replacingOccurrences(of: "⌃", with: "Control ")
        // Currency
        t = t.replacingOccurrences(of: #"\$(\d+(?:\.\d+)?)"#, with: "$1 dollars", options: .regularExpression)
        // Percentage
        t = t.replacingOccurrences(of: #"(\d)%"#, with: "$1 percent", options: .regularExpression)
        // Hashtag
        t = t.replacingOccurrences(of: #"#(\d+)"#, with: "number $1", options: .regularExpression)
        t = t.replacingOccurrences(of: #"#([a-zA-Z]\w*)"#, with: "$1", options: .regularExpression)
        // Ampersand
        t = t.replacingOccurrences(of: "&", with: " and ")
        // Horizontal rules
        t = t.replacingOccurrences(of: #"[-=]{3,}"#, with: "", options: .regularExpression)
        // Pipes, blockquotes
        t = t.replacingOccurrences(of: #"[|>]"#, with: " ", options: .regularExpression)
        // Braces content
        t = t.replacingOccurrences(of: #"\{[^}]*\}"#, with: "", options: .regularExpression)
        // Brackets → keep content
        t = t.replacingOccurrences(of: #"\[([^\]]*)\]"#, with: "$1", options: .regularExpression)
        // Remaining special chars
        t = t.replacingOccurrences(of: #"[~+=@#$€£%]"#, with: " ", options: .regularExpression)
        return t
    }

    private static func normalize(_ text: String) -> String {
        var t = text
        // Lines not ending in punctuation get a period
        t = t.replacingOccurrences(of: #"([^\s.!?:;,])\s*\n"#, with: "$1. ", options: .regularExpression)
        // Remaining newlines → space
        t = t.replacingOccurrences(of: "\n", with: " ")
        // Collapse whitespace
        t = t.replacingOccurrences(of: #"[ \t]+"#, with: " ", options: .regularExpression)
        return t.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
