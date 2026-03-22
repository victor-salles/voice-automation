from clean_for_tts import strip_links, clean


def test_strip_links_replaces_image_with_alt_text_as_caption():
    result = strip_links("![A cat sitting](https://example.com/cat.jpg)")
    assert result == "A cat sitting"


def test_strip_links_replaces_image_without_alt_text_with_empty_string():
    result = strip_links("![](https://example.com/cat.jpg)")
    assert result == ""


def test_strip_links_replaces_image_in_surrounding_text():
    result = strip_links("Check this ![screenshot](https://img.com/s.png) out")
    assert result == "Check this screenshot out"


def test_strip_links_leaves_no_exclamation_mark_from_image_syntax():
    result = strip_links("![alt](url)")
    assert "!" not in result


def test_strip_links_handles_image_and_regular_link_in_same_text():
    result = strip_links("![logo](img.png) and [click here](http://example.com)")
    assert result == "logo and click here"


def test_strip_links_handles_multiple_images():
    result = strip_links("![first](a.png) then ![second](b.png)")
    assert result == "first then second"


def test_strip_links_preserves_regular_exclamation_marks():
    result = strip_links("Hello! This is great!")
    assert result == "Hello! This is great!"


def test_clean_pipeline_reads_image_caption_naturally():
    result = clean("# Gallery\n![A beautiful sunset](https://example.com/sunset.jpg)\nMore text")
    assert "beautiful sunset" in result
    assert "!" not in result
    assert "example.com" not in result


def test_clean_pipeline_skips_image_with_no_caption():
    result = clean("Before\n![](https://example.com/img.png)\nAfter")
    assert "Before" in result
    assert "After" in result
    assert "example.com" not in result
    assert "!" not in result


def test_strip_links_handles_image_with_portuguese_alt_text():
    result = strip_links("![Programação em ação](https://example.com/code.png)")
    assert result == "Programação em ação"
    assert "ã" in result
    assert "ç" in result
