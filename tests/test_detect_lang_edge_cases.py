"""Tests for edge cases and ambiguous text in language detection."""
from detect_lang import detect


def test_detect_returns_en_for_empty_string():
    assert detect("") == "en"


def test_detect_returns_en_for_single_space():
    assert detect(" ") == "en"


def test_detect_returns_en_for_numbers_only():
    assert detect("12345") == "en"


def test_detect_returns_en_for_special_characters_only():
    assert detect("!@#$%") == "en"


def test_detect_returns_en_for_ambiguous_word_no():
    assert detect("no") == "en"


def test_detect_returns_en_for_ambiguous_word_com():
    assert detect("com") == "en"


def test_detect_returns_en_for_ambiguous_word_a():
    assert detect("a") == "en"


def test_detect_returns_en_for_ambiguous_word_ou():
    assert detect("ou") == "en"


def test_detect_returns_en_for_ambiguous_word_em():
    assert detect("em") == "en"


def test_detect_returns_en_for_ambiguous_word_para():
    assert detect("para") == "en"


def test_detect_returns_en_for_text_with_only_ambiguous_words():
    assert detect("no com a ou em para") == "en"


def test_detect_returns_en_for_single_portuguese_word_with_score_one():
    assert detect("da") == "en"


def test_detect_returns_en_for_two_ambiguous_words():
    assert detect("no ou") == "en"


def test_detect_returns_pt_when_pt_score_equals_en_score_but_exceeds_en():
    assert detect("café the") == "pt"


def test_detect_returns_pt_when_pt_score_significantly_exceeds_en_score():
    assert detect("café café the") == "pt"


def test_detect_returns_en_for_single_letter():
    assert detect("a") == "en"


def test_detect_returns_en_for_two_letter_word_english():
    assert detect("is") == "en"


def test_detect_returns_en_for_single_word_english_the():
    assert detect("the") == "en"


def test_detect_returns_en_for_very_short_english_phrase():
    assert detect("is it") == "en"


def test_detect_returns_pt_for_very_short_portuguese_phrase():
    assert detect("não não") == "pt"


def test_detect_returns_en_for_mixed_language_where_english_dominant():
    assert detect("O gato the the the") == "en"


def test_detect_returns_pt_for_mixed_language_where_portuguese_dominant():
    assert detect("The cat está está está") == "pt"


def test_detect_returns_en_when_text_is_all_spaces():
    assert detect("     ") == "en"


def test_detect_returns_en_for_single_english_specific_word():
    assert detect("hello") == "en"


def test_detect_returns_pt_for_single_portuguese_accent_a():
    assert detect("á") == "pt"


def test_detect_returns_pt_for_single_portuguese_accent_e():
    assert detect("é") == "pt"


def test_detect_returns_pt_for_single_portuguese_accent_i():
    assert detect("í") == "pt"


def test_detect_returns_pt_for_single_portuguese_accent_o():
    assert detect("ó") == "pt"


def test_detect_returns_pt_for_single_portuguese_accent_u():
    assert detect("ú") == "pt"


def test_detect_returns_pt_for_single_portuguese_accent_circumflex_a():
    assert detect("â") == "pt"


def test_detect_returns_pt_for_single_portuguese_accent_circumflex_e():
    assert detect("ê") == "pt"


def test_detect_returns_pt_for_single_portuguese_accent_circumflex_o():
    assert detect("ô") == "pt"


def test_detect_returns_pt_for_single_portuguese_accent_grave():
    assert detect("à") == "pt"


def test_detect_returns_en_for_english_text_with_no_portuguese_chars():
    assert detect("programming software database algorithm") == "en"


def test_detect_returns_pt_for_portuguese_text_with_no_english_words():
    assert detect("não está você também há") == "pt"


def test_detect_returns_en_for_text_with_contractions():
    assert detect("I'm happy you're here") == "en"


def test_detect_returns_en_for_text_with_hyphenated_words():
    assert detect("well-known state-of-the-art") == "en"


def test_detect_returns_en_for_portuguese_word_once():
    assert detect("da") == "en"


def test_detect_returns_pt_for_portuguese_words_twice():
    assert detect("da da") == "pt"


def test_detect_returns_pt_for_exactly_two_pt_score():
    assert detect("é é") == "pt"


def test_detect_returns_pt_for_pt_score_of_two():
    assert detect("é") == "pt"


def test_detect_returns_en_for_pt_score_exactly_one():
    assert detect("da") == "en"


def test_detect_returns_en_for_portuguese_words_not_in_only_list():
    assert detect("muito bem obrigado") == "en"


def test_detect_returns_en_for_english_phrase_without_portuguese_chars():
    assert detect("very good thank you") == "en"


def test_detect_returns_en_for_text_with_only_portuguese_articles():
    assert detect("da do na nos") == "pt"


def test_detect_returns_en_for_mixed_case_ambiguous_words():
    assert detect("NO COM PARA OU EM") == "en"


def test_detect_returns_pt_for_mixed_case_portuguese_with_accents():
    assert detect("VOCÊ ESTÁ NÃO") == "pt"


def test_detect_returns_en_for_random_consonants_and_vowels():
    assert detect("bcd fgh jkl") == "en"


def test_detect_returns_pt_for_portuguese_word_dos():
    assert detect("dos dos") == "pt"


def test_detect_returns_pt_for_portuguese_word_das():
    assert detect("das das") == "pt"


def test_detect_returns_pt_for_portuguese_word_nas():
    assert detect("nas nas") == "pt"


def test_detect_returns_pt_for_portuguese_word_uma():
    assert detect("uma uma") == "pt"


def test_detect_returns_pt_for_portuguese_word_uns():
    assert detect("uns uns") == "pt"


def test_detect_returns_pt_for_portuguese_word_umas():
    assert detect("umas umas") == "pt"


def test_detect_returns_pt_for_portuguese_word_esse():
    assert detect("esse esse") == "pt"


def test_detect_returns_pt_for_portuguese_word_essa():
    assert detect("essa essa") == "pt"


def test_detect_returns_pt_for_portuguese_word_este():
    assert detect("este este") == "pt"


def test_detect_returns_pt_for_portuguese_word_esta():
    assert detect("esta esta") == "pt"


def test_detect_returns_pt_for_portuguese_word_ja():
    assert detect("já já") == "pt"


def test_detect_returns_pt_for_portuguese_word_aos():
    assert detect("aos aos") == "pt"


def test_detect_returns_pt_for_portuguese_word_pelos():
    assert detect("pelos pelos") == "pt"


def test_detect_returns_pt_for_portuguese_word_pelas():
    assert detect("pelas pelas") == "pt"
