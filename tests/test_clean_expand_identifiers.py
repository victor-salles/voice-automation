from clean_for_tts import expand_identifiers


def test_expand_identifiers_kokoro_debug():
    result = expand_identifiers("KOKORO_DEBUG")
    assert result == "Kokoro Debug"


def test_expand_identifiers_pt_voice():
    result = expand_identifiers("PT_VOICE")
    assert result == "P T Voice"


def test_expand_identifiers_kokoro_url():
    result = expand_identifiers("KOKORO_URL")
    assert result == "Kokoro U R L"


def test_expand_identifiers_en_voice():
    result = expand_identifiers("EN_VOICE")
    assert result == "E N Voice"


def test_expand_identifiers_max_history():
    result = expand_identifiers("MAX_HISTORY")
    assert result == "Max History"


def test_expand_identifiers_wav_file():
    result = expand_identifiers("WAV_FILE")
    assert result == "W A V File"


def test_expand_identifiers_http_code():
    result = expand_identifiers("HTTP_CODE")
    assert result == "H T T P Code"


def test_expand_identifiers_kokoro_pt_voice():
    result = expand_identifiers("KOKORO_PT_VOICE")
    assert result == "Kokoro P T Voice"


def test_expand_identifiers_mixed_text_set_kokoro_debug():
    result = expand_identifiers("Set KOKORO_DEBUG to 1")
    assert result == "Set Kokoro Debug to 1"


def test_expand_identifiers_should_not_affect_regular_words():
    result = expand_identifiers("Hello")
    assert result == "Hello"


def test_expand_identifiers_should_not_affect_camelcase():
    result = expand_identifiers("debugMode")
    assert result == "debugMode"


def test_expand_identifiers_should_not_affect_lowercase():
    result = expand_identifiers("debug")
    assert result == "debug"


def test_expand_identifiers_multiple_identifiers_in_sentence():
    result = expand_identifiers("Set KOKORO_DEBUG and MAX_HISTORY values")
    assert "Kokoro Debug" in result
    assert "Max History" in result


def test_expand_identifiers_portuguese_context():
    result = expand_identifiers("Configure KOKORO_DEBUG em português")
    assert "Kokoro Debug" in result
    assert "português" in result


def test_expand_identifiers_empty_string():
    result = expand_identifiers("")
    assert result == ""


def test_expand_identifiers_no_identifiers():
    result = expand_identifiers("Just plain text")
    assert result == "Just plain text"


def test_expand_identifiers_url_alone():
    result = expand_identifiers("URL")
    # URL alone is 3 chars and no vowel, so stays as "U R L"
    assert result == "U R L" or result == "URL"


def test_expand_identifiers_api_acronym():
    result = expand_identifiers("API_KEY")
    # API has vowel but 3 chars, may be treated as acronym
    assert "A P I" in result or "Api" in result
    assert "Key" in result


def test_expand_identifiers_three_char_acronym_http():
    result = expand_identifiers("HTTP")
    assert result == "H T T P"


def test_expand_identifiers_three_char_word_max():
    result = expand_identifiers("MAX")
    assert result == "Max"


def test_expand_identifiers_env_constant():
    result = expand_identifiers("ENV_PATH")
    # ENV has no vowel, PATH does
    assert "E N V" in result or "Env" in result
    assert "Path" in result


def test_expand_identifiers_should_not_affect_mixed_case_identifiers():
    result = expand_identifiers("myVariable")
    assert result == "myVariable"


def test_expand_identifiers_two_char_segment():
    result = expand_identifiers("EN_US")
    # EN and US both have 2 chars or no standard vowels
    assert "E N" in result
    assert "U S" in result


def test_expand_identifiers_preserves_surrounding_punctuation():
    result = expand_identifiers("Set KOKORO_DEBUG.")
    assert "Kokoro Debug" in result
    assert result.endswith(".")


def test_expand_identifiers_multiple_underscores():
    result = expand_identifiers("THIS_IS_A_TEST")
    # Should handle multiple segments
    assert "This" in result or "T H I S" in result
