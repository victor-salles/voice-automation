import Foundation
import Testing
@testable import VoiceFlowCore

@Suite("TextExtractor paragraph slice")
struct TextExtractorTests {
    @Test("cursor at start returns full text")
    func startOfDocument() {
        let full = "Hello\nWorld"
        let got = TextExtractor.textFromParagraphStart(fullText: full, cursorUTF16Index: 0)
        #expect(got == "Hello\nWorld")
    }

    @Test("cursor after newline starts from new paragraph")
    func secondParagraph() {
        let full = "Hello\nWorld"
        let idx = (full as NSString).range(of: "W").location
        let got = TextExtractor.textFromParagraphStart(fullText: full, cursorUTF16Index: idx)
        #expect(got == "World")
    }

    @Test("cursor mid-paragraph returns from paragraph start")
    func midParagraph() {
        let full = "Line one\nLine two tail"
        let idx = (full as NSString).range(of: "tail").location
        let got = TextExtractor.textFromParagraphStart(fullText: full, cursorUTF16Index: idx)
        #expect(got == "Line two tail")
    }

    @Test("out of range returns nil")
    func outOfRange() {
        let full = "ab"
        #expect(TextExtractor.textFromParagraphStart(fullText: full, cursorUTF16Index: -1) == nil)
        #expect(TextExtractor.textFromParagraphStart(fullText: full, cursorUTF16Index: 99) == nil)
    }
}
