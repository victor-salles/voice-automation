"""Tests to verify the scoring weights for language detection."""
from detect_lang import detect


def test_detect_scoring_single_cedilla_gives_pt_score_of_3():
    assert detect("ç") == "pt"


def test_detect_scoring_single_tilde_a_gives_pt_score_of_3():
    assert detect("ã") == "pt"


def test_detect_scoring_single_tilde_o_gives_pt_score_of_3():
    assert detect("õ") == "pt"


def test_detect_scoring_single_acute_accent_gives_pt_score_of_2():
    assert detect("é") == "pt"


def test_detect_scoring_single_grave_accent_gives_pt_score_of_2():
    assert detect("à") == "pt"


def test_detect_scoring_single_circumflex_a_gives_pt_score_of_2():
    assert detect("â") == "pt"


def test_detect_scoring_single_circumflex_e_gives_pt_score_of_2():
    assert detect("ê") == "pt"


def test_detect_scoring_single_circumflex_o_gives_pt_score_of_2():
    assert detect("ô") == "pt"


def test_detect_scoring_two_cedillas_give_pt_score_of_6():
    assert detect("ç ç") == "pt"


def test_detect_scoring_three_acute_accents_give_pt_score_of_6():
    assert detect("á á á") == "pt"


def test_detect_scoring_one_cedilla_and_one_acute_accent():
    assert detect("ç é") == "pt"


def test_detect_scoring_cedilla_worth_3_times_acute_accent():
    assert detect("ç ç ç é") == "pt"


def test_detect_scoring_pt_word_da_worth_1_point():
    assert detect("da") == "en"


def test_detect_scoring_two_pt_words_worth_2_points():
    assert detect("da da") == "pt"


def test_detect_scoring_three_pt_words_worth_3_points():
    assert detect("da da da") == "pt"


def test_detect_scoring_one_cedilla_plus_one_pt_word():
    assert detect("ç da") == "pt"


def test_detect_scoring_one_acute_accent_plus_one_pt_word():
    assert detect("é da") == "pt"


def test_detect_scoring_pt_score_minimum_threshold_is_2():
    assert detect("é") == "pt"


def test_detect_scoring_pt_score_below_minimum_threshold():
    assert detect("da") == "en"


def test_detect_scoring_one_en_word_beats_one_pt_word():
    assert detect("da the") == "en"


def test_detect_scoring_two_pt_words_beat_one_en_word():
    assert detect("da da the") == "pt"


def test_detect_scoring_cedilla_worth_3_beats_two_en_words():
    assert detect("ç the the") == "pt"


def test_detect_scoring_two_cedillas_beat_multiple_en_words():
    assert detect("ç ç the the") == "pt"


def test_detect_scoring_four_acute_accents_beat_one_en_word():
    assert detect("é é é é the") == "pt"


def test_detect_scoring_three_en_words_beat_one_cedilla():
    assert detect("ç the is are") == "en"


def test_detect_scoring_cedilla_3_beats_one_en_word():
    assert detect("ç the") == "pt"


def test_detect_scoring_pt_exceeding_en_by_one_returns_pt():
    assert detect("ç ç the") == "pt"


def test_detect_scoring_mixed_cedilla_and_acute():
    assert detect("ç é") == "pt"


def test_detect_scoring_mixed_pt_words_and_chars():
    assert detect("não da é") == "pt"


def test_detect_scoring_pt_with_many_en_words_defeated():
    assert detect("ç da was is are the been") == "en"


def test_detect_scoring_en_with_one_cedilla():
    assert detect("the is are ç") == "en"


def test_detect_scoring_cedilla_sufficient_despite_en_words():
    assert detect("the is ç") == "pt"


def test_detect_scoring_uppercase_cedilla_worth_3_points():
    assert detect("Ç") == "pt"


def test_detect_scoring_uppercase_tilde_a_worth_3_points():
    assert detect("Ã") == "pt"


def test_detect_scoring_uppercase_tilde_o_worth_3_points():
    assert detect("Õ") == "pt"


def test_detect_scoring_mixed_case_cedilla_and_acute():
    assert detect("Ç é") == "pt"


def test_detect_scoring_six_en_words_vs_cedilla():
    assert detect("the is are was were been ç") == "en"


def test_detect_scoring_cedilla_and_one_en_word():
    assert detect("ç ç the") == "pt"


def test_detect_scoring_acute_accent_2_beats_one_en_word():
    assert detect("é the") == "pt"


def test_detect_scoring_two_acute_accents_and_one_en_word():
    assert detect("é é the") == "pt"


def test_detect_scoring_pt_word_counted_once_per_word():
    assert detect("já já já") == "pt"


def test_detect_scoring_en_word_counted_once_per_word():
    assert detect("the the the") == "en"


def test_detect_scoring_repeated_cedilla_in_word():
    assert detect("çç") == "pt"


def test_detect_scoring_two_acute_accents_4_beats_one_en_word():
    assert detect("á á the") == "pt"


def test_detect_scoring_pt_score_exceeds_en_score_boundary():
    assert detect("á á á the") == "pt"


def test_detect_scoring_complex_mixed_scenario():
    assert detect("não é o café está the is") == "pt"
