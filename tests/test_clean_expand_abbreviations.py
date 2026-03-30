from clean_for_tts import expand_abbreviations


def test_expand_abbreviations_api_spelled_out():
    assert expand_abbreviations("the API endpoint") == "the A P I endpoint"


def test_expand_abbreviations_url_spelled_out():
    assert expand_abbreviations("open the URL") == "open the U R L"


def test_expand_abbreviations_https_spelled_out():
    assert expand_abbreviations("use HTTPS") == "use H T T P S"


def test_expand_abbreviations_html_spelled_out():
    assert expand_abbreviations("write HTML") == "write H T M L"


def test_expand_abbreviations_cpu_spelled_out():
    assert expand_abbreviations("CPU usage") == "C P U usage"


def test_expand_abbreviations_llm_spelled_out():
    assert expand_abbreviations("an LLM model") == "an L L M model"


def test_expand_abbreviations_json_becomes_jason():
    assert expand_abbreviations("JSON response") == "Jason response"


def test_expand_abbreviations_sql_becomes_sequel():
    assert expand_abbreviations("SQL query") == "sequel query"


def test_expand_abbreviations_gui_becomes_gooey():
    assert expand_abbreviations("the GUI app") == "the gooey app"


def test_expand_abbreviations_case_insensitive():
    assert expand_abbreviations("the api endpoint") == "the A P I endpoint"


def test_expand_abbreviations_multiple_acronyms_in_sentence():
    result = expand_abbreviations("the API uses JSON")
    assert "A P I" in result
    assert "Jason" in result


def test_expand_abbreviations_https_matched_before_http():
    result = expand_abbreviations("HTTPS and HTTP")
    assert result == "H T T P S and H T T P"


def test_expand_abbreviations_word_boundary_prevents_partial_match():
    result = expand_abbreviations("APIS")
    assert result == "APIS"


def test_expand_abbreviations_plain_text_unchanged():
    assert expand_abbreviations("hello world") == "hello world"


def test_expand_abbreviations_empty_string():
    assert expand_abbreviations("") == ""
