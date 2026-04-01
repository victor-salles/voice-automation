import Testing
@testable import VoiceFlowCore

// Smoke test — verifies the test target builds and links correctly.
// Real tests are added in subsequent steps.
@Suite("Infrastructure")
struct InfrastructureTests {
    @Test("test target compiles and imports VoiceFlowCore")
    func importSucceeds() {
        #expect(Bool(true))
    }
}
