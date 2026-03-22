from clean_for_tts import strip_inline_code


def test_strip_inline_code_removes_backticks_keeps_content():
    result = strip_inline_code("`code`")
    assert result == "code"


def test_strip_inline_code_preserves_text_outside_backticks():
    result = strip_inline_code("Before `inline` after")
    assert result == "Before inline after"


def test_strip_inline_code_handles_multiple_inline_codes():
    result = strip_inline_code("Use `var1` and `var2` together")
    assert result == "Use var1 and var2 together"


def test_strip_inline_code_handles_empty_backticks():
    result = strip_inline_code("Empty ``")
    assert result == "Empty ``"


def test_strip_inline_code_does_not_remove_single_backticks():
    result = strip_inline_code("Single ` backtick not closed")
    assert result == "Single ` backtick not closed"


def test_strip_inline_code_handles_inline_code_with_spaces():
    result = strip_inline_code("`some code here`")
    assert result == "some code here"


def test_strip_inline_code_preserves_portuguese_accents():
    result = strip_inline_code("Use `variável com ç ã õ` aqui")
    assert result == "Use variável com ç ã õ aqui"


def test_strip_inline_code_handles_empty_string():
    result = strip_inline_code("")
    assert result == ""


def test_strip_inline_code_no_inline_codes():
    result = strip_inline_code("Just plain text")
    assert result == "Just plain text"


def test_strip_inline_code_with_special_characters_inside():
    result = strip_inline_code("`@var#name$value`")
    assert result == "@var#name$value"
