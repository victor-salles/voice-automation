import AppKit
import ApplicationServices
import CoreFoundation
import CoreGraphics

/// Reads selected text from the focused app via macOS Accessibility API.
/// Stateless — no dependencies, no side effects beyond AX queries.
package struct TextExtractor {

    package init() {}

    /// Get the currently selected text in any app.
    /// Returns nil if no text is selected or AX is unavailable.
    package func selectedText() -> String? {
        guard let element = focusedElement() else { return nil }

        if let selected = attribute(element, kAXSelectedTextAttribute) as? String,
           !selected.isEmpty {
            return selected
        }

        return nil
    }

    /// Focused element and a **screen-space** rect for overlay placement.
    /// WebKit (Apple Notes) often exposes `AXFrame` in non-screen coordinates; we prefer
    /// `AXBoundsForRange` at the paragraph start, which is usually correct on screen.
    package func focusedTextArea() -> (element: AXUIElement, frame: CGRect)? {
        guard let element = focusedElement() else { return nil }
        guard let role = attribute(element, kAXRoleAttribute) as? String,
              role == (kAXTextAreaRole as String) else { return nil }
        guard let axFrame = cgRect(fromFrameAttributeOf: element) else { return nil }

        guard let fullText = attribute(element, kAXValueAttribute) as? String,
              let sel = cfRange(fromSelectedTextRangeAttributeOf: element),
              sel.location != kCFNotFound else {
            return (element, axFrame)
        }

        let nsFull = fullText as NSString
        let utf16Len = nsFull.length
        guard sel.location >= 0, sel.location <= utf16Len else { return (element, axFrame) }

        let paragraphStart = Self.paragraphStartUTF16(in: fullText, cursorUTF16Index: sel.location)
        let rangeLen = paragraphStart < utf16Len ? 1 : 0
        let boundsRange = CFRange(location: paragraphStart, length: rangeLen)

        if let bounds = boundsForRange(boundsRange, in: element), bounds.isReasonableAXBounds {
            return (element, bounds)
        }
        return (element, axFrame)
    }

    /// Full text from the start of the paragraph containing the caret to the end of the field.
    package func textFromCurrentParagraph(in element: AXUIElement) -> String? {
        guard let fullText = attribute(element, kAXValueAttribute) as? String else { return nil }
        guard let range = cfRange(fromSelectedTextRangeAttributeOf: element) else { return nil }
        guard range.location != kCFNotFound else { return nil }
        return Self.textFromParagraphStart(fullText: fullText, cursorUTF16Index: range.location)
    }

    /// Shared paragraph-boundary logic (UTF-16 indices, matching AX ranges).
    package static func textFromParagraphStart(fullText: String, cursorUTF16Index: Int) -> String? {
        let nsFull = fullText as NSString
        let length = nsFull.length
        guard cursorUTF16Index >= 0, cursorUTF16Index <= length else { return nil }
        let paragraphStart = paragraphStartUTF16(in: fullText, cursorUTF16Index: cursorUTF16Index)
        let slice = nsFull.substring(from: paragraphStart)
        return slice.isEmpty ? nil : slice
    }

    package static func paragraphStartUTF16(in fullText: String, cursorUTF16Index: Int) -> Int {
        let nsFull = fullText as NSString
        let length = nsFull.length
        guard cursorUTF16Index >= 0, cursorUTF16Index <= length else { return 0 }
        var paragraphStart = 0
        if cursorUTF16Index > 0 {
            let searchRange = NSRange(location: 0, length: cursorUTF16Index)
            let newlineRange = nsFull.rangeOfCharacter(from: .newlines, options: .backwards, range: searchRange)
            if newlineRange.location != NSNotFound {
                paragraphStart = NSMaxRange(newlineRange)
            }
        }
        return paragraphStart
    }

    // MARK: - Private

    private func focusedElement() -> AXUIElement? {
        let systemWide = AXUIElementCreateSystemWide()
        var element: AnyObject?
        let result = AXUIElementCopyAttributeValue(
            systemWide,
            kAXFocusedUIElementAttribute as CFString,
            &element
        )
        guard result == .success else { return nil }
        return (element as! AXUIElement)
    }

    private func attribute(_ element: AXUIElement, _ attr: String) -> AnyObject? {
        var value: AnyObject?
        let result = AXUIElementCopyAttributeValue(element, attr as CFString, &value)
        return result == .success ? value : nil
    }

    private func cgRect(fromFrameAttributeOf element: AXUIElement) -> CGRect? {
        guard let value = attribute(element, "AXFrame") else { return nil }
        guard CFGetTypeID(value as CFTypeRef) == AXValueGetTypeID() else { return nil }
        let axValue = value as! AXValue
        var rect = CGRect.zero
        guard AXValueGetValue(axValue, .cgRect, &rect) else { return nil }
        return rect
    }

    private func cfRange(fromSelectedTextRangeAttributeOf element: AXUIElement) -> CFRange? {
        guard let value = attribute(element, kAXSelectedTextRangeAttribute) else { return nil }
        guard CFGetTypeID(value as CFTypeRef) == AXValueGetTypeID() else { return nil }
        let axValue = value as! AXValue
        var range = CFRange()
        guard AXValueGetValue(axValue, .cfRange, &range) else { return nil }
        return range
    }

    private func boundsForRange(_ range: CFRange, in element: AXUIElement) -> CGRect? {
        var mutable = range
        guard let axRange = AXValueCreate(.cfRange, &mutable) else { return nil }
        var out: AnyObject?
        let result = AXUIElementCopyParameterizedAttributeValue(
            element,
            kAXBoundsForRangeParameterizedAttribute as CFString,
            axRange,
            &out
        )
        guard result == .success, let out else { return nil }
        guard CFGetTypeID(out as CFTypeRef) == AXValueGetTypeID() else { return nil }
        var rect = CGRect.zero
        guard AXValueGetValue(out as! AXValue, .cgRect, &rect) else { return nil }
        return rect
    }
}

private extension CGRect {
    /// Filters out empty / garbage rects from AX so we keep the `AXFrame` fallback.
    var isReasonableAXBounds: Bool {
        guard !isNull, !isInfinite else { return false }
        guard width > 0.25 || height > 0.25 else { return false }
        guard width < 50_000, height < 50_000 else { return false }
        return true
    }
}
