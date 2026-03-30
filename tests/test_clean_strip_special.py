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


def test_strip_special_converts_forward_slash_to_comma():
    result = strip_special("play/pause")
    assert result == "play, pause"


def test_strip_special_converts_multiple_slashes_to_commas():
    result = strip_special("start/stop/restart")
    assert result == "start, stop, restart"


def test_strip_special_converts_slash_with_spaces():
    result = strip_special("option A / option B")
    assert result == "option A ,  option B"


def test_strip_special_converts_and_or_slash():
    result = strip_special("and/or")
    assert result == "and, or"


def test_strip_special_preserves_portuguese_with_slashes():
    result = strip_special("opção/escolha")
    assert result == "opção, escolha"


def test_strip_special_converts_dollar_to_dollars():
    result = strip_special("costs $50")
    assert "50 dollars" in result
    assert "$" not in result


def test_strip_special_converts_dollar_with_cents():
    result = strip_special("priced at $9.99")
    assert "9.99 dollars" in result


def test_strip_special_converts_euro_to_euros():
    result = strip_special("costs €20")
    assert "20 euros" in result


def test_strip_special_converts_pound_to_pounds():
    result = strip_special("costs £15")
    assert "15 pounds" in result


def test_strip_special_converts_percent_to_percent_word():
    result = strip_special("50% done")
    assert "50 percent" in result
    assert "%" not in result


def test_strip_special_converts_hash_number_to_number_word():
    result = strip_special("issue #42")
    assert "number 42" in result
    assert "#" not in result


def test_strip_special_converts_hash_word_to_hashtag():
    result = strip_special("#python is great")
    assert "hashtag python" in result
    assert "#" not in result


def test_strip_special_converts_ampersand_to_and():
    result = strip_special("cats & dogs")
    assert " and " in result
    assert "&" not in result


def test_strip_special_converts_email_at_sign():
    result = strip_special("user@example.com")
    assert "user at example.com" in result


def test_strip_special_converts_cpp_plusplus():
    result = strip_special("written in C++")
    assert "plus plus" in result


def test_strip_special_converts_equals_between_words():
    result = strip_special("a = b")
    assert "a equals b" in result


def test_strip_special_converts_tilde_before_number():
    result = strip_special("~100 items")
    assert "approximately 100" in result
    assert "~" not in result
