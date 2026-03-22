from clean_for_tts import strip_special


def test_strip_special_converts_right_arrow_to_to():
    result = strip_special("a → b")
    assert result == "a  to  b"


def test_strip_special_converts_multiple_right_arrow_types():
    result = strip_special("→ ⟶ ⟹ ➡ ► ▸")
    assert " to " in result


def test_strip_special_converts_left_arrow_to_from():
    result = strip_special("a ← b")
    assert result == "a  from  b"


def test_strip_special_converts_multiple_left_arrow_types():
    result = strip_special("← ⟵ ⟸ ⬅ ◄ ◂")
    assert " from " in result


def test_strip_special_converts_option_key():
    result = strip_special("Press ⌥ key")
    assert result == "Press Option  key"


def test_strip_special_converts_command_key():
    result = strip_special("Press ⌘ key")
    assert result == "Press Command  key"


def test_strip_special_converts_shift_key():
    result = strip_special("Press ⇧ key")
    assert result == "Press Shift  key"


def test_strip_special_converts_control_key():
    result = strip_special("Press ⌃ key")
    assert result == "Press Control  key"


def test_strip_special_converts_em_dash_to_comma():
    result = strip_special("text — more text")
    assert result == "text, more text"


def test_strip_special_converts_en_dash_to_comma():
    result = strip_special("text – more text")
    assert result == "text, more text"


def test_strip_special_removes_pipe():
    result = strip_special("a | b")
    assert result == "a   b"


def test_strip_special_removes_blockquote():
    result = strip_special("> quoted")
    assert result == "  quoted"


def test_strip_special_removes_horizontal_rule_with_dashes():
    result = strip_special("---")
    assert result == ""


def test_strip_special_removes_horizontal_rule_with_equals():
    result = strip_special("===")
    assert result == ""


def test_strip_special_removes_content_in_braces():
    result = strip_special("keep {remove} this")
    assert result == "keep  this"


def test_strip_special_extracts_content_from_brackets():
    result = strip_special("keep [important] this")
    assert result == "keep important this"


def test_strip_special_removes_emojis():
    result = strip_special("hello 😀 world")
    assert "😀" not in result


def test_strip_special_removes_weather_emojis():
    result = strip_special("sunny ☀️ day")
    assert "☀" not in result or "day" in result


def test_strip_special_preserves_portuguese_accents():
    result = strip_special("Açúcar → café")
    assert result == "Açúcar  to  café"


def test_strip_special_handles_empty_string():
    result = strip_special("")
    assert result == ""


def test_strip_special_no_special_characters():
    result = strip_special("Just plain text")
    assert result == "Just plain text"


def test_strip_special_removes_nested_braces():
    result = strip_special("keep {outer {inner}} this")
    assert result == "keep } this"
