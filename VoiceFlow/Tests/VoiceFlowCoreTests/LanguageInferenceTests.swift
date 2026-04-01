import Testing
@testable import VoiceFlowCore

@Suite("LanguageInference")
struct LanguageInferenceTests {

    @Test("American English prose")
    func englishArticle() {
        let text = """
            OpenAI has closed a deal to raise one hundred twenty billion dollars. \
            The round will add to the company’s budget for chips and data centers.
            """
        #expect(LanguageInference.infer(from: text) == .americanEnglish)
    }

    @Test("Brazilian Portuguese prose")
    func portugueseArticle() {
        let text = """
            A empresa anunciou hoje um novo investimento de vários bilhões de reais. \
            O valor reflete a confiança dos acionistas no mercado brasileiro.
            """
        #expect(LanguageInference.infer(from: text) == .brazilianPortuguese)
    }

    @Test("Portuguese with typical diacritics")
    func portugueseDiacritics() {
        let text = "Não há ninguém aqui; você está certo sobre ações e corações."
        #expect(LanguageInference.infer(from: text) == .brazilianPortuguese)
    }

    @Test("Very short ambiguous string defaults to English")
    func shortDefaultsToEnglish() {
        #expect(LanguageInference.infer(from: "OK") == .americanEnglish)
        #expect(LanguageInference.infer(from: "sim") == .americanEnglish)
    }
}
