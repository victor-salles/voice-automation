from clean_for_tts import expand_file_extensions


def test_expand_file_extensions_basic_py_extension():
    result = expand_file_extensions(".py")
    assert result == "dot P Y"


def test_expand_file_extensions_basic_js_extension():
    result = expand_file_extensions(".js")
    assert result == "dot J S"


def test_expand_file_extensions_basic_lua_extension():
    result = expand_file_extensions(".lua")
    assert result == "dot L U A"


def test_expand_file_extensions_basic_tsx_extension():
    result = expand_file_extensions(".tsx")
    assert result == "dot T S X"


def test_expand_file_extensions_basic_md_extension():
    result = expand_file_extensions(".md")
    assert result == "dot M D"


def test_expand_file_extensions_basic_json_extension():
    result = expand_file_extensions(".json")
    assert result == "dot J S O N"


def test_expand_file_extensions_basic_sh_extension():
    result = expand_file_extensions(".sh")
    assert result == "dot S H"


def test_expand_file_extensions_basic_yaml_extension():
    result = expand_file_extensions(".yaml")
    assert result == "dot Y A M L"


def test_expand_file_extensions_basic_txt_extension():
    result = expand_file_extensions(".txt")
    assert result == "dot T X T"


def test_expand_file_extensions_basic_csv_extension():
    result = expand_file_extensions(".csv")
    assert result == "dot C S V"


def test_expand_file_extensions_filename_with_py():
    result = expand_file_extensions("file.py")
    assert result == "file dot P Y"


def test_expand_file_extensions_filename_clean_for_tts_py():
    result = expand_file_extensions("clean_for_tts.py")
    assert result == "clean_for_tts dot P Y"


def test_expand_file_extensions_filename_settings_json():
    result = expand_file_extensions("settings.json")
    assert result == "settings dot J S O N"


def test_expand_file_extensions_filename_config_yaml():
    result = expand_file_extensions("config.yaml")
    assert result == "config dot Y A M L"


def test_expand_file_extensions_multiple_extensions_in_sentence():
    result = expand_file_extensions("Use script.py and config.json files")
    assert "script dot P Y" in result
    assert "config dot J S O N" in result


def test_expand_file_extensions_path_like_text():
    result = expand_file_extensions("scripts/speak.sh")
    assert result == "scripts/speak dot S H"


def test_expand_file_extensions_should_not_expand_decimal_numbers():
    result = expand_file_extensions("Version 3.14")
    assert result == "Version 3.14"


def test_expand_file_extensions_should_not_expand_sentence_period():
    result = expand_file_extensions("Hello.")
    assert result == "Hello."


def test_expand_file_extensions_should_not_expand_ellipsis():
    result = expand_file_extensions("Wait...")
    assert result == "Wait..."


def test_expand_file_extensions_portuguese_filename():
    result = expand_file_extensions("arquivo.py")
    assert result == "arquivo dot P Y"


def test_expand_file_extensions_multiple_dots_in_filename():
    result = expand_file_extensions("my.file.name.py")
    assert "dot P Y" in result


def test_expand_file_extensions_empty_string():
    result = expand_file_extensions("")
    assert result == ""


def test_expand_file_extensions_no_extensions():
    result = expand_file_extensions("Just plain text")
    assert result == "Just plain text"


def test_expand_file_extensions_extension_at_end_of_sentence():
    result = expand_file_extensions("Edit your file.py.")
    assert "file dot P Y" in result


def test_expand_file_extensions_mixed_case_extension():
    result = expand_file_extensions("FILE.PY")
    assert "dot P Y" in result


def test_expand_file_extensions_single_letter_extension():
    result = expand_file_extensions("file.c")
    assert result == "file dot C"
