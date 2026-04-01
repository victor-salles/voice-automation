// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "VoiceFlow",
    platforms: [.macOS(.v14)],
    dependencies: [
        .package(url: "https://github.com/swiftlang/swift-testing.git", branch: "release/6.2"),
    ],
    targets: [
        .target(
            name: "VoiceFlowCore",
            path: "Sources/VoiceFlowCore",
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
        .executableTarget(
            name: "VoiceFlow",
            dependencies: ["VoiceFlowCore"],
            path: "Sources/VoiceFlow",
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
        .testTarget(
            name: "VoiceFlowCoreTests",
            dependencies: [
                "VoiceFlowCore",
                .product(name: "Testing", package: "swift-testing"),
            ],
            path: "Tests/VoiceFlowCoreTests"
        ),
    ]
)
