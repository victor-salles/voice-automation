import AppKit
import VoiceFlowCore

/// Floating control using the same waveform / transport metaphor and accent colors as the menu bar.
@MainActor
final class OverlayPanel {

    /// Pause, resume, or full stop — wired from `AppModel` based on `StatusManager.current`.
    var onPrimaryAction: (@MainActor () -> Void)?

    private let forwarder = ButtonForwarder()
    private let buttonSize: CGFloat = 36
    private var panel: NSPanel?
    private var actionButton: NSButton?

    private let symbolConfig = NSImage.SymbolConfiguration(pointSize: 20, weight: .medium)

    init() {
        forwarder.handler = { [weak self] in
            self?.onPrimaryAction?()
        }
    }

    var hasVisiblePanel: Bool {
        panel?.isVisible == true
    }

    func show(at elementFrame: CGRect) {
        let p = panel ?? makePanel()
        panel = p

        guard NSScreen.screens.contains(where: { $0.frame.intersects(elementFrame) })
            || NSScreen.main != nil else { return }

        let inset: CGFloat = 4
        let origin = NSPoint(
            x: elementFrame.minX + inset,
            y: elementFrame.maxY - buttonSize - inset
        )

        p.setFrame(NSRect(origin: origin, size: NSSize(width: buttonSize, height: buttonSize)), display: false)
        p.orderFront(nil)
    }

    func hide() {
        panel?.orderOut(nil)
    }

    func sync(with playbackStatus: StatusManager.Status) {
        guard let button = actionButton else { return }
        let (symbolName, color, accessibilityLabel): (String, NSColor, String) = {
            switch playbackStatus {
            case .idle:
                return ("waveform.circle", .secondaryLabelColor, "VoiceFlow")
            case .processing:
                return ("waveform.circle.fill", .secondaryLabelColor, "Preparing audio")
            case .playing:
                return ("pause.circle.fill", .systemGreen, "Pause playback")
            case .paused:
                return ("play.circle.fill", .systemBlue, "Resume playback")
            case .error:
                return ("exclamationmark.circle.fill", .systemRed, "Error — dismiss")
            }
        }()

        let image = NSImage(systemSymbolName: symbolName, accessibilityDescription: accessibilityLabel)?
            .withSymbolConfiguration(symbolConfig)
        button.image = image
        button.contentTintColor = color
    }

    private func makePanel() -> NSPanel {
        let rect = NSRect(x: 0, y: 0, width: buttonSize, height: buttonSize)
        let p = NSPanel(
            contentRect: rect,
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        p.level = .floating
        p.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        p.isOpaque = false
        p.backgroundColor = .clear
        p.hasShadow = true
        p.hidesOnDeactivate = false
        p.isReleasedWhenClosed = false

        let button = NSButton(frame: NSRect(origin: .zero, size: rect.size))
        button.isBordered = false
        button.imageScaling = .scaleProportionallyDown
        button.target = forwarder
        button.action = #selector(ButtonForwarder.tapped(_:))
        actionButton = button

        p.contentView = NSView(frame: rect)
        p.contentView?.addSubview(button)

        sync(with: .idle)
        return p
    }
}

@MainActor
private final class ButtonForwarder: NSObject {
    var handler: (@MainActor () -> Void)?

    @objc func tapped(_ sender: Any?) {
        handler?()
    }
}
