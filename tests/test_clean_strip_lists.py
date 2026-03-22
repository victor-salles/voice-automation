from clean_for_tts import strip_lists


def test_strip_lists_removes_dash_marker():
    result = strip_lists("- item")
    assert result == "item."


def test_strip_lists_removes_asterisk_marker():
    result = strip_lists("* item")
    assert result == "item."


def test_strip_lists_removes_plus_marker():
    result = strip_lists("+ item")
    assert result == "item."


def test_strip_lists_removes_numbered_list_marker():
    result = strip_lists("1. item")
    assert result == "item."


def test_strip_lists_removes_multiple_numbered_items():
    result = strip_lists("1. first\n2. second\n3. third")
    assert result == "first.\nsecond.\nthird."


def test_strip_lists_handles_list_with_existing_punctuation():
    result = strip_lists("- item!")
    assert result == "item!"


def test_strip_lists_handles_list_with_colon():
    result = strip_lists("- item:")
    assert result == "item:"


def test_strip_lists_preserves_text_outside_lists():
    result = strip_lists("Before\n- item\nAfter")
    assert result == "Before\nitem.\nAfter"


def test_strip_lists_handles_indented_list_items():
    result = strip_lists("  - indented item")
    assert result == "indented item."


def test_strip_lists_handles_heavily_indented_list():
    result = strip_lists("    * deeply indented")
    assert result == "deeply indented."


def test_strip_lists_handles_multiple_list_items_with_dash():
    result = strip_lists("- first\n- second\n- third")
    assert result == "first.\nsecond.\nthird."


def test_strip_lists_handles_mixed_list_markers():
    result = strip_lists("- item1\n* item2\n+ item3")
    assert result == "item1.\nitem2.\nitem3."


def test_strip_lists_preserves_portuguese_accents():
    result = strip_lists("- Açúcar, café e pão")
    assert result == "Açúcar, café e pão."


def test_strip_lists_handles_list_item_with_comma():
    result = strip_lists("- item with comma,")
    assert result == "item with comma,"


def test_strip_lists_handles_list_item_with_question_mark():
    result = strip_lists("- what is this?")
    assert result == "what is this?"


def test_strip_lists_handles_empty_string():
    result = strip_lists("")
    assert result == ""


def test_strip_lists_no_list_items():
    result = strip_lists("Just plain text")
    assert result == "Just plain text"


def test_strip_lists_handles_list_item_ending_with_semicolon():
    result = strip_lists("- item;")
    assert result == "item;"
