from clean_for_tts import expand_parentheticals


def test_expand_parentheticals_eg_with_comma():
    result = expand_parentheticals("use a tool (e.g., Python)")
    assert "for example Python" in result
    assert "e.g." not in result


def test_expand_parentheticals_eg_without_comma():
    result = expand_parentheticals("use a tool (e.g. Python)")
    assert "for example Python" in result


def test_expand_parentheticals_ie_with_comma():
    result = expand_parentheticals("the main file (i.e., the config)")
    assert "that is the config" in result
    assert "i.e." not in result


def test_expand_parentheticals_ie_without_comma():
    result = expand_parentheticals("the main file (i.e. the config)")
    assert "that is the config" in result


def test_expand_parentheticals_etc_with_dot():
    result = expand_parentheticals("and so on (etc.)")
    assert "etcetera" in result
    assert "(etc.)" not in result


def test_expand_parentheticals_etc_without_dot():
    result = expand_parentheticals("and so on (etc)")
    assert "etcetera" in result


def test_expand_parentheticals_empty_parens_removed():
    result = expand_parentheticals("something () here")
    assert "()" not in result
    assert "something" in result
    assert "here" in result


def test_expand_parentheticals_general_aside_becomes_comma_delimited():
    result = expand_parentheticals("the tool (a wrapper)")
    assert "a wrapper" in result
    assert "(" not in result
    assert ")" not in result


def test_expand_parentheticals_preserves_text_outside_parens():
    result = expand_parentheticals("before (inside) after")
    assert "before" in result
    assert "inside" in result
    assert "after" in result


def test_expand_parentheticals_no_parens_unchanged():
    assert expand_parentheticals("plain text") == "plain text"


def test_expand_parentheticals_empty_string():
    assert expand_parentheticals("") == ""
