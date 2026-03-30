from segment_paragraphs import segment, split_at_sentences

MAX_CHARS = 600
MIN_CHARS = 20


def test_segment_empty_text_returns_empty():
    result = segment("")
    assert result == {"paragraphs": [], "currentIndex": 0, "total": 0}


def test_segment_single_paragraph():
    text = "This is a single paragraph with enough content to be included."
    result = segment(text)
    assert result["total"] == 1
    assert result["paragraphs"][0] == text
    assert result["currentIndex"] == 0


def test_segment_two_paragraphs_separated_by_double_newline():
    p1 = "First paragraph with enough content here."
    p2 = "Second paragraph with enough content too."
    result = segment(f"{p1}\n\n{p2}")
    assert result["total"] == 2
    assert result["paragraphs"][0] == p1
    assert result["paragraphs"][1] == p2


def test_segment_skips_blocks_shorter_than_min_chars():
    text = "Short.\n\nThis is a proper paragraph with enough content to be included."
    result = segment(text)
    assert result["total"] == 1
    assert "proper paragraph" in result["paragraphs"][0]


def test_segment_cursor_at_start_gives_index_zero():
    p1 = "First paragraph with enough content here."
    p2 = "Second paragraph with enough content too."
    result = segment(f"{p1}\n\n{p2}", cursor_offset=0)
    assert result["currentIndex"] == 0


def test_segment_cursor_in_second_paragraph_gives_index_one():
    p1 = "First paragraph with enough content here."
    p2 = "Second paragraph with enough content too."
    offset = len(p1) + 3  # past the \n\n separator
    result = segment(f"{p1}\n\n{p2}", cursor_offset=offset)
    assert result["currentIndex"] == 1


def test_segment_three_paragraphs_returns_correct_total():
    p = "Paragraph with enough words to be included here."
    text = f"{p}\n\n{p}\n\n{p}"
    result = segment(text)
    assert result["total"] == 3
    assert len(result["paragraphs"]) == 3


def test_segment_multiple_newlines_treated_as_single_separator():
    p1 = "Paragraph one is long enough to be included here."
    p2 = "Paragraph two is also long enough to be included."
    result = segment(f"{p1}\n\n\n\n{p2}")
    assert result["total"] == 2


def test_segment_strips_whitespace_from_paragraphs():
    text = "  Paragraph with leading and trailing spaces and enough content.  \n\nAnother paragraph here."
    result = segment(text)
    assert not result["paragraphs"][0].startswith(" ")
    assert not result["paragraphs"][0].endswith(" ")


def test_segment_long_paragraph_split_into_chunks():
    sentence = "This is a sentence that takes up some space in the buffer. "
    long_para = sentence * 12  # ~720 chars, exceeds MAX_CHARS
    result = segment(long_para)
    assert result["total"] > 1
    for para in result["paragraphs"]:
        assert len(para) <= MAX_CHARS


def test_split_at_sentences_short_text_returns_single_chunk():
    text = "This is a short sentence."
    result = split_at_sentences(text)
    assert result == [text]


def test_split_at_sentences_multiple_short_sentences_kept_together():
    text = "First sentence. Second sentence. Third sentence."
    result = split_at_sentences(text)
    assert len(result) == 1
    assert "First sentence" in result[0]
    assert "Third sentence" in result[0]


def test_split_at_sentences_splits_when_combined_length_exceeds_max():
    sentence = "This is a longer sentence that occupies a chunk of the buffer. "
    long_text = sentence * 12  # ~744 chars
    result = split_at_sentences(long_text)
    assert len(result) > 1
    for chunk in result:
        assert len(chunk) <= MAX_CHARS


def test_split_at_sentences_filters_chunks_shorter_than_min():
    sentence = "This is a sentence that takes up some space in the buffer. "
    long_text = sentence * 12
    result = split_at_sentences(long_text)
    for chunk in result:
        assert len(chunk) >= MIN_CHARS
