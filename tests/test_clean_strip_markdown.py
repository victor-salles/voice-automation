from clean_for_tts import strip_markdown


def test_strip_markdown_removes_h1_header():
    result = strip_markdown("# Header")
    assert result == "Header."


def test_strip_markdown_removes_h2_header():
    result = strip_markdown("## Header")
    assert result == "Header."


def test_strip_markdown_removes_h6_header():
    result = strip_markdown("###### Header")
    assert result == "Header."


def test_strip_markdown_adds_period_to_header_without_punctuation():
    result = strip_markdown("# My Header")
    assert result == "My Header."


def test_strip_markdown_preserves_header_with_ending_punctuation():
    result = strip_markdown("# Header!")
    assert result == "Header!"


def test_strip_markdown_removes_bold_double_asterisk():
    result = strip_markdown("**bold text**")
    assert result == "bold text"


def test_strip_markdown_removes_bold_double_underscore():
    result = strip_markdown("__bold text__")
    assert result == "bold text"


def test_strip_markdown_removes_italic_single_asterisk():
    result = strip_markdown("*italic text*")
    assert result == "italic text"


def test_strip_markdown_removes_italic_single_underscore():
    result = strip_markdown("_italic text_")
    assert result == "italic text"


def test_strip_markdown_removes_strikethrough():
    result = strip_markdown("~~strikethrough~~")
    assert result == "strikethrough"


def test_strip_markdown_handles_mixed_formatting():
    result = strip_markdown("**bold** *italic* ~~strike~~")
    assert result == "bold italic strike"


def test_strip_markdown_preserves_text_outside_formatting():
    result = strip_markdown("Before **bold** after")
    assert result == "Before bold after"


def test_strip_markdown_handles_nested_formatting():
    result = strip_markdown("**bold with *italic* inside**")
    assert result == "bold with italic inside"


def test_strip_markdown_preserves_portuguese_accents_in_headers():
    result = strip_markdown("# Cabeçalho com ç ã õ")
    assert result == "Cabeçalho com ç ã õ."


def test_strip_markdown_preserves_portuguese_accents_in_bold():
    result = strip_markdown("**Açúcar e café**")
    assert result == "Açúcar e café"


def test_strip_markdown_handles_empty_string():
    result = strip_markdown("")
    assert result == ""


def test_strip_markdown_no_markdown_content():
    result = strip_markdown("Plain text")
    assert result == "Plain text"


def test_strip_markdown_multiple_headers_on_separate_lines():
    result = strip_markdown("# Header 1\n## Header 2")
    assert result == "Header 1.\nHeader 2."


def test_strip_markdown_header_with_colon_punctuation():
    result = strip_markdown("# Header:")
    assert result == "Header:"
