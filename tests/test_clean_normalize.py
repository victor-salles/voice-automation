from clean_for_tts import normalize


def test_normalize_adds_period_before_newline_when_line_lacks_punctuation():
    result = normalize("line1\nline2")
    assert result == "line1. line2"


def test_normalize_preserves_newline_when_line_ends_with_period():
    result = normalize("line1.\nline2")
    assert result == "line1. line2"


def test_normalize_flattens_multiple_paragraphs_to_single_line():
    result = normalize("para1\n\npara2")
    assert "\n" not in result
    assert "para1" in result and "para2" in result


def test_normalize_handles_line_ending_with_exclamation():
    result = normalize("exciting!\nmore text")
    assert result == "exciting! more text"


def test_normalize_handles_line_ending_with_question():
    result = normalize("question?\nmore text")
    assert result == "question? more text"


def test_normalize_handles_line_ending_with_colon():
    result = normalize("introduction:\nmore text")
    assert result == "introduction: more text"


def test_normalize_handles_line_ending_with_semicolon():
    result = normalize("clause;\nmore text")
    assert result == "clause; more text"


def test_normalize_handles_line_ending_with_comma():
    result = normalize("item,\nmore text")
    assert result == "item, more text"


def test_normalize_collapses_multiple_spaces():
    result = normalize("text  with   many    spaces")
    assert result == "text with many spaces"


def test_normalize_collapses_tabs_to_space():
    result = normalize("text\twith\ttabs")
    assert result == "text with tabs"


def test_normalize_strips_leading_and_trailing_whitespace():
    result = normalize("  text  \n")
    assert result == "text."


def test_normalize_handles_single_character_lines():
    result = normalize("a\nb")
    assert result == "a. b"


def test_normalize_handles_empty_lines():
    result = normalize("text\n\nmore")
    assert result == "text. more"


def test_normalize_handles_multiple_newlines():
    result = normalize("line1\n\n\n\nline2")
    assert "\n" not in result


def test_normalize_preserves_portuguese_accents():
    result = normalize("Açúcar\ncafé")
    assert result == "Açúcar. café"


def test_normalize_preserves_portuguese_sentence_with_accents():
    result = normalize("Aqui está uma sentença\ncom mais texto")
    assert "Aqui" in result and "sentença." in result


def test_normalize_handles_empty_string():
    result = normalize("")
    assert result == ""


def test_normalize_single_line_no_newline():
    result = normalize("just one line")
    assert result == "just one line"


def test_normalize_line_with_only_whitespace():
    result = normalize("text\n   \nmore")
    assert "text." in result and "more" in result
