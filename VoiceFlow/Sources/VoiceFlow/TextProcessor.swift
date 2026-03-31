import Foundation

/// Pure text processing: clean markup, segment into speakable chunks.
/// No I/O, no side effects — fully testable.
enum TextProcessor {

    // MARK: - Segmentation

    /// Split text into speakable segments: paragraphs, list items, sentences.
    /// Each segment is cleaned and ready for TTS.
    static func segment(_ text: String) -> [String] {
        // First, separate structural blocks (paragraphs, list items)
        let blocks = splitIntoBlocks(text)

        // Clean each block, split long ones at sentence boundaries
        var segments: [String] = []
        for block in blocks {
            let cleaned = clean(block)
            guard !cleaned.isEmpty else { continue }

            if cleaned.count > 500 {
                segments.append(contentsOf: splitAtSentences(cleaned))
            } else {
                segments.append(cleaned)
            }
        }

        // Merge very short segments with the next one
        return mergeShortSegments(segments, minLength: 20)
    }

    /// Split text into structural blocks: paragraphs and individual list items.
    private static func splitIntoBlocks(_ text: String) -> [String] {
        var blocks: [String] = []
        var currentBlock: [String] = []

        for line in text.components(separatedBy: "\n") {
            let trimmed = line.trimmingCharacters(in: .whitespaces)

            // Empty line → flush current block, start new paragraph
            if trimmed.isEmpty {
                if !currentBlock.isEmpty {
                    blocks.append(currentBlock.joined(separator: "\n"))
                    currentBlock = []
                }
                continue
            }

            // List item → flush current block, add item as its own block
            if isListItem(trimmed) {
                if !currentBlock.isEmpty {
                    blocks.append(currentBlock.joined(separator: "\n"))
                    currentBlock = []
                }
                blocks.append(trimmed)
                continue
            }

            // Regular line → accumulate into current block
            currentBlock.append(trimmed)
        }

        if !currentBlock.isEmpty {
            blocks.append(currentBlock.joined(separator: "\n"))
        }

        return blocks
    }

    private static func isListItem(_ line: String) -> Bool {
        // Unordered: - item, * item, + item
        if line.range(of: #"^[-*+]\s+"#, options: .regularExpression) != nil { return true }
        // Ordered: 1. item, 2. item
        if line.range(of: #"^\d+\.\s+"#, options: .regularExpression) != nil { return true }
        return false
    }

    /// Split long text at sentence boundaries, each chunk <= 500 chars.
    private static func splitAtSentences(_ text: String) -> [String] {
        let sentences = text.components(separatedBy: ". ")
        var chunks: [String] = []
        var buffer = ""

        for part in sentences {
            let sentence = part.hasSuffix(".") ? part : part + "."
            if !buffer.isEmpty && buffer.count + sentence.count + 1 > 500 {
                chunks.append(buffer.trimmingCharacters(in: .whitespaces))
                buffer = sentence
            } else {
                buffer = buffer.isEmpty ? sentence : "\(buffer) \(sentence)"
            }
        }
        if !buffer.isEmpty {
            chunks.append(buffer.trimmingCharacters(in: .whitespaces))
        }

        return chunks
    }

    /// Merge segments shorter than minLength with the following segment.
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
            } else {
                // Merge carry with this segment
                result.append("\(carry) \(segment)")
                carry = ""
            }
        }

        // If there's a trailing short segment, append it to the last result or add standalone
        if !carry.isEmpty {
            if let last = result.last {
                result[result.count - 1] = "\(last) \(carry)"
            } else {
                result.append(carry)
            }
        }

        return result
    }

    // MARK: - Text Cleaning

    /// Full cleaning pipeline: strip markup → strip symbols → normalize.
    static func clean(_ text: String) -> String {
        var t = text
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
        // Em/en dashes → comma
        t = t.replacingOccurrences(of: #"\s*[—–]\s*"#, with: ", ", options: .regularExpression)
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
