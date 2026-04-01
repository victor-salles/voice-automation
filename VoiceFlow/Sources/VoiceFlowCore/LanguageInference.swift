import Foundation
import NaturalLanguage

/// Locale bucket used to pick a Kokoro voice (American English vs Brazilian Portuguese).
package enum InferredSpeakLanguage: String, Sendable {
    case americanEnglish
    case brazilianPortuguese
}

/// Infers read-aloud language from text using `NLLanguageRecognizer`.
package enum LanguageInference {

    /// Below this length, recognition is noisy; default to American English.
    private static let minimumMeaningfulLength = 12

    package static func infer(from text: String) -> InferredSpeakLanguage {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmed.count >= minimumMeaningfulLength else {
            return .americanEnglish
        }

        let recognizer = NLLanguageRecognizer()
        recognizer.processString(trimmed)

        if let dominant = recognizer.dominantLanguage {
            switch dominant {
            case .portuguese:
                return .brazilianPortuguese
            case .english:
                return .americanEnglish
            default:
                break
            }
        }

        let hypotheses = recognizer.languageHypotheses(withMaximum: 4)
        if let portugueseScore = hypotheses[.portuguese], portugueseScore >= 0.2 {
            return .brazilianPortuguese
        }
        if let englishScore = hypotheses[.english], englishScore >= 0.15 {
            return .americanEnglish
        }

        return .americanEnglish
    }
}
