from clean_for_tts import strip_code_blocks


def test_strip_code_blocks_replaces_fenced_block_with_omitted_message():
    result = strip_code_blocks("```python\nprint('hello')\n```")
    assert result == " code block omitted. "


def test_strip_code_blocks_preserves_text_outside_code_blocks():
    result = strip_code_blocks("Before ```code``` after")
    assert result == "Before  code block omitted.  after"


def test_strip_code_blocks_handles_multiple_blocks():
    result = strip_code_blocks("```a```\ntext\n```b```")
    assert result == " code block omitted. \ntext\n code block omitted. "


def test_strip_code_blocks_handles_empty_code_block():
    result = strip_code_blocks("```\n\n```")
    assert result == " code block omitted. "


def test_strip_code_blocks_handles_code_block_with_backticks_inside():
    result = strip_code_blocks("```\nsome ` code\n```")
    assert result == " code block omitted. "


def test_strip_code_blocks_handles_multiline_code_with_newlines():
    result = strip_code_blocks("```\nline1\nline2\nline3\n```")
    assert result == " code block omitted. "


def test_strip_code_blocks_preserves_portuguese_accents():
    result = strip_code_blocks("Aqui ```código com ç ã õ``` está limpo")
    assert result == "Aqui  code block omitted.  está limpo"


def test_strip_code_blocks_handles_empty_string():
    result = strip_code_blocks("")
    assert result == ""


def test_strip_code_blocks_no_code_blocks():
    result = strip_code_blocks("Just plain text")
    assert result == "Just plain text"


def test_strip_code_blocks_nested_fence_markers():
    result = strip_code_blocks("Start ```outer ``` inner ``` end```")
    assert result == "Start  code block omitted.  inner  code block omitted. "
