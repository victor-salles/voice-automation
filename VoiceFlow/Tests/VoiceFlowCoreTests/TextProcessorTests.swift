import Testing
@testable import VoiceFlowCore

// MARK: - clean()

@Suite("TextProcessor.clean")
struct CleanTests {

    // MARK: Code blocks

    @Test("fenced code block is replaced with placeholder")
    func fencedCodeBlock() {
        let result = TextProcessor.clean("```swift\nlet x = 1\n```")
        #expect(result == "code block omitted.")
    }

    @Test("inline code backticks are stripped, content kept")
    func inlineCode() {
        #expect(TextProcessor.clean("`myFunc()`") == "myFunc()")
    }

    @Test("multiple inline code spans in one string")
    func multipleInlineCode() {
        #expect(TextProcessor.clean("Call `foo()` and `bar()`") == "Call foo() and bar()")
    }

    // MARK: Markdown

    @Test("all header levels become plain text with trailing period",
          arguments: zip(
              ["# H1", "## H2", "### H3", "#### H4", "##### H5", "###### H6"],
              ["H1.", "H2.", "H3.", "H4.", "H5.", "H6."]
          ))
    func headerLevels(input: String, expected: String) {
        #expect(TextProcessor.clean(input) == expected)
    }

    @Test("bold markers stripped",
          arguments: zip(["**bold**", "__bold__"], ["bold", "bold"]))
    func bold(input: String, expected: String) {
        #expect(TextProcessor.clean(input) == expected)
    }

    @Test("italic markers stripped",
          arguments: zip(["*italic*", "_italic_"], ["italic", "italic"]))
    func italic(input: String, expected: String) {
        #expect(TextProcessor.clean(input) == expected)
    }

    @Test("strikethrough markers stripped")
    func strikethrough() {
        #expect(TextProcessor.clean("~~deleted~~") == "deleted")
    }

    // MARK: Links

    @Test("markdown image becomes alt text")
    func imageLink() {
        #expect(TextProcessor.clean("![alt text](https://example.com/img.png)") == "alt text")
    }

    @Test("empty alt image becomes empty string")
    func imageLinkEmptyAlt() {
        #expect(TextProcessor.clean("![](https://example.com/img.png)") == "")
    }

    @Test("markdown link becomes link text")
    func markdownLink() {
        #expect(TextProcessor.clean("[click here](https://example.com)") == "click here")
    }

    @Test("bare https URL becomes 'link'")
    func bareHttpsURL() {
        #expect(TextProcessor.clean("https://example.com/path?q=1") == "link")
    }

    @Test("bare http URL becomes 'link'")
    func bareHttpURL() {
        #expect(TextProcessor.clean("http://example.com") == "link")
    }

    // MARK: Lists

    @Test("unordered list markers stripped",
          arguments: zip(["- item", "* item", "+ item"], ["item.", "item.", "item."]))
    func unorderedListMarkers(input: String, expected: String) {
        #expect(TextProcessor.clean(input) == expected)
    }

    @Test("ordered list marker stripped")
    func orderedListMarker() {
        #expect(TextProcessor.clean("1. First step") == "First step.")
    }

    // MARK: Special symbols

    @Test("right arrows become 'to'",
          arguments: zip(["→", "⟶", "⟹", "➡", "►", "▸"],
                         ["to", "to", "to", "to", "to", "to"]))
    func rightArrows(input: String, expected: String) {
        #expect(TextProcessor.clean(input) == expected)
    }

    @Test("left arrows become 'from'",
          arguments: zip(["←", "⟵", "⟸", "⬅", "◄", "◂"],
                         ["from", "from", "from", "from", "from", "from"]))
    func leftArrows(input: String, expected: String) {
        #expect(TextProcessor.clean(input) == expected)
    }

    @Test("macOS keyboard symbols expanded",
          arguments: zip(
              ["⌥S", "⌘C", "⇧K", "⌃X"],
              ["Option S", "Command C", "Shift K", "Control X"]
          ))
    func keyboardSymbols(input: String, expected: String) {
        #expect(TextProcessor.clean(input) == expected)
    }

    @Test("em dash with spaces becomes comma-space")
    func emDashWithSpaces() {
        #expect(TextProcessor.clean("foo — bar") == "foo, bar")
    }

    @Test("em dash without spaces becomes comma-space")
    func emDashNoSpaces() {
        #expect(TextProcessor.clean("foo—bar") == "foo, bar")
    }

    @Test("en dash becomes comma-space")
    func enDash() {
        #expect(TextProcessor.clean("foo–bar") == "foo, bar")
    }

    @Test("dollar amount expanded")
    func dollarAmount() {
        #expect(TextProcessor.clean("$100") == "100 dollars")
    }

    @Test("decimal dollar amount expanded")
    func dollarDecimal() {
        #expect(TextProcessor.clean("$9.99") == "9.99 dollars")
    }

    @Test("percentage expanded")
    func percentage() {
        #expect(TextProcessor.clean("50%") == "50 percent")
    }

    @Test("numeric hashtag becomes 'number N'")
    func numericHashtag() {
        #expect(TextProcessor.clean("#42") == "number 42")
    }

    @Test("text hashtag strips the hash")
    func textHashtag() {
        #expect(TextProcessor.clean("#feature") == "feature")
    }

    @Test("ampersand becomes 'and'")
    func ampersand() {
        #expect(TextProcessor.clean("a & b") == "a and b")
    }

    @Test("horizontal rule stripped entirely",
          arguments: ["---", "===", "-----", "====="])
    func horizontalRule(input: String) {
        #expect(TextProcessor.clean(input) == "")
    }

    @Test("pipe character stripped")
    func pipe() {
        #expect(TextProcessor.clean("a | b") == "a b")
    }

    @Test("blockquote marker stripped")
    func blockquote() {
        #expect(TextProcessor.clean("> quoted text") == "quoted text")
    }

    @Test("brace content stripped entirely")
    func braces() {
        #expect(TextProcessor.clean("{config: value}") == "")
    }

    @Test("bracket content kept, brackets removed")
    func brackets() {
        #expect(TextProcessor.clean("[item]") == "item")
    }

    // MARK: Normalization

    @Test("multiple spaces collapsed to single space")
    func collapseSpaces() {
        #expect(TextProcessor.clean("too   many   spaces") == "too many spaces")
    }

    @Test("line without trailing punctuation gets a period before newline")
    func periodInsertedBeforeNewline() {
        let result = TextProcessor.clean("first line\nsecond line")
        #expect(result == "first line. second line")
    }

    @Test("line ending with punctuation does not get extra period")
    func noDuplicatePeriod() {
        let result = TextProcessor.clean("first line.\nsecond line")
        #expect(result == "first line. second line")
    }

    @Test("leading and trailing whitespace trimmed")
    func trimming() {
        #expect(TextProcessor.clean("  hello  ") == "hello")
    }

    @Test("empty string returns empty string")
    func emptyString() {
        #expect(TextProcessor.clean("") == "")
    }

    @Test("whitespace-only string returns empty string")
    func whitespaceOnly() {
        #expect(TextProcessor.clean("   \t  ") == "")
    }
}

// MARK: - segment()

@Suite("TextProcessor.segment")
struct SegmentTests {

    @Test("empty string returns no segments")
    func emptyInput() {
        #expect(TextProcessor.segment("") == [])
    }

    @Test("whitespace-only string returns no segments")
    func whitespaceOnly() {
        #expect(TextProcessor.segment("   \n   ") == [])
    }

    @Test("single paragraph returns one segment")
    func singleParagraph() {
        let text = "This is a single paragraph with enough characters to be kept."
        let segments = TextProcessor.segment(text)
        #expect(segments.count == 1)
        #expect(segments[0].contains("single paragraph"))
    }

    @Test("blank line separates two paragraphs into two segments")
    func twoParagraphs() {
        let text = "First paragraph with sufficient length here.\n\nSecond paragraph with sufficient length here."
        let segments = TextProcessor.segment(text)
        #expect(segments.count == 2)
        #expect(segments[0].contains("First paragraph"))
        #expect(segments[1].contains("Second paragraph"))
    }

    @Test("list items each become their own segment")
    func listItemsAreIndividualSegments() {
        let text = "- This is a sufficiently long first list item\n- This is a sufficiently long second list item"
        let segments = TextProcessor.segment(text)
        #expect(segments.count == 2)
        #expect(segments[0].contains("first list item"))
        #expect(segments[1].contains("second list item"))
    }

    @Test("paragraph before list is flushed as its own segment")
    func paragraphBeforeList() {
        let text = "Intro paragraph with enough text to be kept here.\n- Sufficiently long list item follows it"
        let segments = TextProcessor.segment(text)
        #expect(segments.count == 2)
        #expect(segments[0].contains("Intro paragraph"))
        #expect(segments[1].contains("list item"))
    }

    @Test("all list marker styles are detected",
          arguments: [
              "- dash item with enough characters to pass",
              "* star item with enough characters to pass",
              "+ plus item with enough characters to pass",
              "1. ordered item with enough characters to pass",
          ])
    func listMarkerStyles(line: String) {
        let segments = TextProcessor.segment(line)
        #expect(segments.count == 1)
        let first = segments[0]
        #expect(!first.hasPrefix("- "))
        #expect(!first.hasPrefix("* "))
        #expect(!first.hasPrefix("+ "))
        // Ordered marker "1. " should also be gone
        let startsWithOrderedMarker = first.first?.isNumber == true && first.dropFirst().hasPrefix(". ")
        #expect(!startsWithOrderedMarker)
    }

    @Test("block longer than 500 chars is split at sentence boundaries")
    func longBlockSplitsAtSentences() {
        let sentence = "This sentence contains enough words to contribute meaningfully to the total character count."
        let longText = (1...7).map { "Sentence \($0): \(sentence)" }.joined(separator: " ")
        #expect(longText.count > 500)

        let segments = TextProcessor.segment(longText)
        #expect(segments.count > 1)
        for segment in segments {
            #expect(segment.count <= 500)
        }
    }

    @Test("segment shorter than 20 chars merges with the following segment")
    func shortSegmentMergesWithNext() {
        let text = "Short.\n\nThis is a long enough following paragraph to pass the threshold."
        let segments = TextProcessor.segment(text)
        #expect(segments.count == 1)
        #expect(segments[0].contains("Short"))
        #expect(segments[0].contains("following paragraph"))
    }

    @Test("trailing short segment is appended to the last segment")
    func trailingShortSegmentAppendsToLast() {
        let text = "This is a long enough opening paragraph to stay.\n\nShort."
        let segments = TextProcessor.segment(text)
        #expect(segments.count == 1)
        #expect(segments[0].contains("opening paragraph"))
        #expect(segments[0].contains("Short"))
    }

    @Test("segment containing only cleaned-away content is dropped")
    func emptyAfterCleaningIsDropped() {
        let text = "---\n\nThis paragraph has real content to keep here."
        let segments = TextProcessor.segment(text)
        #expect(segments.count == 1)
        #expect(segments[0].contains("real content"))
    }
}
