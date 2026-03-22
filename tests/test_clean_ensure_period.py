from clean_for_tts import _ensure_period


def test_ensure_period_adds_period_to_text_without_punctuation():
    result = _ensure_period("no period")
    assert result == "no period."


def test_ensure_period_preserves_text_with_period():
    result = _ensure_period("has period.")
    assert result == "has period."


def test_ensure_period_preserves_text_with_exclamation():
    result = _ensure_period("exciting!")
    assert result == "exciting!"


def test_ensure_period_preserves_text_with_question():
    result = _ensure_period("question?")
    assert result == "question?"


def test_ensure_period_preserves_text_with_colon():
    result = _ensure_period("intro:")
    assert result == "intro:"


def test_ensure_period_preserves_text_with_semicolon():
    result = _ensure_period("clause;")
    assert result == "clause;"


def test_ensure_period_preserves_text_with_comma():
    result = _ensure_period("item,")
    assert result == "item,"


def test_ensure_period_handles_empty_string():
    result = _ensure_period("")
    assert result == ""


def test_ensure_period_handles_whitespace_only():
    result = _ensure_period("   ")
    assert result == ""


def test_ensure_period_strips_trailing_whitespace():
    result = _ensure_period("text  ")
    assert result == "text."


def test_ensure_period_handles_single_character():
    result = _ensure_period("a")
    assert result == "a."


def test_ensure_period_preserves_single_period():
    result = _ensure_period(".")
    assert result == "."


def test_ensure_period_preserves_portuguese_accents():
    result = _ensure_period("Açúcar e café")
    assert result == "Açúcar e café."


def test_ensure_period_preserves_portuguese_with_punctuation():
    result = _ensure_period("Café!")
    assert result == "Café!"


def test_ensure_period_handles_text_with_trailing_spaces_before_period():
    result = _ensure_period("text  .")
    assert result == "text  ."


def test_ensure_period_multiple_spaces_before_period():
    result = _ensure_period("text    ")
    assert result == "text."
