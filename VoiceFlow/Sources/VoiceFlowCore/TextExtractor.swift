import AppKit
import ApplicationServices

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
}
