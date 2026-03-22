from clean_for_tts import strip_links


def test_strip_links_converts_markdown_link_to_text():
    result = strip_links("[click here](https://example.com)")
    assert result == "click here"


def test_strip_links_preserves_text_outside_markdown_link():
    result = strip_links("Before [link](https://example.com) after")
    assert result == "Before link after"


def test_strip_links_handles_multiple_markdown_links():
    result = strip_links("[first](https://a.com) and [second](https://b.com)")
    assert result == "first and second"


def test_strip_links_replaces_http_url_with_link():
    result = strip_links("Visit https://example.com now")
    assert result == "Visit link now"


def test_strip_links_replaces_https_url_with_link():
    result = strip_links("Visit http://example.com now")
    assert result == "Visit link now"


def test_strip_links_handles_multiple_bare_urls():
    result = strip_links("Go to https://a.com or https://b.com")
    assert result == "Go to link or link"


def test_strip_links_handles_mixed_markdown_and_bare_urls():
    result = strip_links("See [this](https://a.com) and https://b.com")
    assert result == "See this and link"


def test_strip_links_preserves_text_without_links():
    result = strip_links("Just plain text")
    assert result == "Just plain text"


def test_strip_links_handles_markdown_link_with_complex_url():
    result = strip_links("[go there](https://example.com/path?query=value&other=123)")
    assert result == "go there"


def test_strip_links_handles_url_with_trailing_punctuation():
    result = strip_links("Visit https://example.com.")
    assert result == "Visit link"


def test_strip_links_handles_url_in_parentheses():
    result = strip_links("(https://example.com)")
    assert result == "(link"


def test_strip_links_preserves_portuguese_accents_in_link_text():
    result = strip_links("[clique aqui com ç ã õ](https://example.com)")
    assert result == "clique aqui com ç ã õ"


def test_strip_links_handles_empty_string():
    result = strip_links("")
    assert result == ""


def test_strip_links_markdown_link_with_empty_text():
    result = strip_links("[](https://example.com)")
    assert result == "[](link"


def test_strip_links_consecutive_urls():
    result = strip_links("https://a.com https://b.com")
    assert result == "link link"
