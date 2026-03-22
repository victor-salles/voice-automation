"""Tests for Portuguese language detection."""
from detect_lang import detect


def test_detect_returns_pt_for_text_with_cedilla():
    assert detect("açúcar") == "pt"


def test_detect_returns_pt_for_text_with_tilde():
    assert detect("não") == "pt"


def test_detect_returns_pt_for_text_with_circumflex():
    assert detect("você") == "pt"


def test_detect_returns_pt_for_single_cedilla():
    assert detect("ç") == "pt"


def test_detect_returns_pt_for_single_tilde_a():
    assert detect("ã") == "pt"


def test_detect_returns_pt_for_single_tilde_o():
    assert detect("õ") == "pt"


def test_detect_returns_pt_for_text_with_acute_accent():
    assert detect("café") == "pt"


def test_detect_returns_pt_for_text_with_grave_accent():
    assert detect("à") == "pt"


def test_detect_returns_pt_for_portuguese_specific_word_da():
    assert detect("da da") == "pt"


def test_detect_returns_pt_for_portuguese_specific_word_do():
    assert detect("do do") == "pt"


def test_detect_returns_pt_for_portuguese_specific_word_não():
    assert detect("não não") == "pt"


def test_detect_returns_pt_for_portuguese_specific_word_são():
    assert detect("são são") == "pt"


def test_detect_returns_pt_for_portuguese_specific_word_está():
    assert detect("está está") == "pt"


def test_detect_returns_pt_for_portuguese_specific_word_você():
    assert detect("você você") == "pt"


def test_detect_returns_pt_for_simple_portuguese_sentence():
    assert detect("O gato está na casa") == "pt"


def test_detect_returns_pt_for_portuguese_phrase_with_ã():
    assert detect("Não sei onde estão") == "pt"


def test_detect_returns_pt_for_portuguese_phrase_with_ç():
    assert detect("Ele usa uma camiseta") == "pt"


def test_detect_returns_pt_for_portuguese_phrase_with_multiple_accents():
    assert detect("Você é um amigo fiel") == "pt"


def test_detect_returns_pt_for_real_portuguese_sentence_1():
    assert detect("Olá, como você está hoje?") == "pt"


def test_detect_returns_pt_for_real_portuguese_sentence_2():
    assert detect("Muito bom, obrigado. Tudo bem com você?") == "pt"


def test_detect_returns_pt_for_real_portuguese_sentence_3():
    assert detect("Ela foi à praia e encontrou seus amigos lá.") == "pt"


def test_detect_returns_pt_for_uppercase_cedilla():
    assert detect("AÇÚCAR") == "pt"


def test_detect_returns_pt_for_uppercase_tilde_a():
    assert detect("NÃO") == "pt"


def test_detect_returns_pt_for_uppercase_tilde_o():
    assert detect("SÃO") == "pt"


def test_detect_returns_pt_for_uppercase_accents():
    assert detect("CAFÉ") == "pt"


def test_detect_returns_pt_for_mixed_case_portuguese_text():
    assert detect("Você Não Pode Ir à Festa") == "pt"


def test_detect_returns_pt_for_portuguese_word_isso():
    assert detect("isso isso") == "pt"


def test_detect_returns_pt_for_portuguese_word_também():
    assert detect("também também") == "pt"


def test_detect_returns_pt_for_portuguese_word_ele():
    assert detect("ele ele") == "pt"


def test_detect_returns_pt_for_portuguese_word_ela():
    assert detect("ela ela") == "pt"


def test_detect_returns_pt_for_portuguese_word_muito():
    assert detect("muito muito") == "pt"


def test_detect_returns_pt_for_portuguese_word_pode():
    assert detect("pode pode") == "pt"


def test_detect_returns_pt_for_portuguese_word_seu():
    assert detect("seu seu") == "pt"


def test_detect_returns_pt_for_portuguese_word_sua():
    assert detect("sua sua") == "pt"


def test_detect_returns_pt_for_portuguese_word_ter():
    assert detect("ter ter") == "pt"


def test_detect_returns_pt_for_portuguese_word_foi():
    assert detect("foi foi") == "pt"


def test_detect_returns_pt_for_portuguese_word_havia():
    assert detect("havia havia") == "pt"


def test_detect_returns_pt_for_portuguese_word_mas():
    assert detect("mas mas") == "pt"


def test_detect_returns_pt_for_portuguese_word_ao():
    assert detect("ao ao") == "pt"


def test_detect_returns_pt_for_portuguese_word_até():
    assert detect("até até") == "pt"


def test_detect_returns_pt_for_portuguese_word_pelo():
    assert detect("pelo pelo") == "pt"


def test_detect_returns_pt_for_portuguese_word_pela():
    assert detect("pela pela") == "pt"
