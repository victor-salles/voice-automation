from clean_for_tts import clean


def test_clean_simple_markdown_text():
    result = clean("# Hello **world**")
    assert result == "Hello world."


def test_clean_removes_code_blocks_and_markdown():
    result = clean("# Title\n```python\ncode\n```\nText")
    assert "python" not in result
    assert "code block omitted" in result
    assert "Title" in result


def test_clean_processes_list_with_headers():
    result = clean("## Items\n- item1\n- item2")
    assert "Items." in result
    assert "item1." in result
    assert "item2." in result


def test_clean_removes_links_and_markdown():
    result = clean("Read [this](https://example.com) **article**")
    assert result == "Read this article"


def test_clean_converts_keyboard_symbols():
    result = clean("Press ⌘ key")
    assert result == "Press Command key"


def test_clean_preserves_portuguese_accents_through_pipeline():
    result = clean("# Açúcar **e** café")
    assert "Açúcar" in result
    assert "café" in result
    assert result == "Açúcar e café."


def test_clean_preserves_portuguese_accents_with_list():
    result = clean("- Açúcar\n- Café\n- Pão")
    assert "Açúcar" in result
    assert "Café" in result
    assert "Pão" in result
    assert "Açúcar." in result
    assert "Café." in result
    assert "Pão." in result


def test_clean_preserves_portuguese_accents_with_links():
    result = clean("[Clique aqui com ação](https://example.com)")
    assert "Clique aqui com ação" in result
    assert "https" not in result


def test_clean_handles_mixed_content():
    result = clean("# Header\n\n**Bold** and *italic*\n\n- list item\n\n`code` text")
    assert "Header." in result
    assert "Bold" in result
    assert "italic" in result
    assert "list item." in result
    assert "code" in result


def test_clean_handles_multiple_paragraphs():
    result = clean("Para 1\n\nPara 2\n\nPara 3")
    assert result == "Para 1. Para 2. Para 3"


def test_clean_strips_inline_code_with_special_chars():
    result = clean("`@var#name` text")
    # @ and # are converted by strip_special for TTS readability
    assert "@" not in result
    assert "#" not in result
    assert "text" in result


def test_clean_removes_emojis():
    result = clean("hello 😀 world")
    assert "😀" not in result
    assert "hello" in result


def test_clean_converts_arrows():
    result = clean("input → output → result")
    assert "to" in result
    assert "→" not in result


def test_clean_removes_horizontal_rules():
    result = clean("text\n---\nmore")
    assert "---" not in result
    assert "text." in result


def test_clean_removes_braces_content():
    result = clean("Keep {remove this} this")
    assert "remove" not in result
    assert "Keep" in result
    assert "this" in result


def test_clean_handles_numbered_list():
    result = clean("1. first item\n2. second item\n3. third item")
    assert "first item." in result
    assert "second item." in result
    assert "third item." in result


def test_clean_handles_bare_urls():
    result = clean("Visit https://example.com for info")
    assert "link" in result
    assert "https" not in result


def test_clean_markdown_link_with_url():
    result = clean("[visit](https://example.com)")
    assert result == "visit"


def test_clean_preserves_sentence_punctuation():
    result = clean("Is this a question?")
    assert result == "Is this a question?"


def test_clean_handles_complex_document():
    text = """# Welcome to our guide

This is **important** content.

- First point
- Second point: with colon
- Third point!

See [our website](https://example.com) for more → details.

```
def code():
    pass
```

Final paragraph with `inline` code and emoji 🎉"""

    result = clean(text)
    assert "code block omitted" in result
    assert "Welcome to our guide." in result
    assert "important" in result
    assert "First point." in result
    assert "Second point: with colon" in result
    assert "Third point!" in result
    assert "our website" in result
    assert "https" not in result
    assert "to" in result
    assert "🎉" not in result
    assert "inline" in result
    assert "Final paragraph" in result


def test_clean_empty_string():
    result = clean("")
    assert result == ""


def test_clean_whitespace_only():
    result = clean("   \n   \n   ")
    assert result == ""


def test_clean_single_word():
    result = clean("hello")
    assert result == "hello"


def test_clean_markdown_with_em_dash():
    result = clean("text — more text")
    assert "text, more text" in result
    assert "—" not in result
