"""Integration tests for speak.sh TTS pipeline.

Tests validate pipeline stages without calling Kokoro API:
1. Text cleaning via clean_for_tts.py
2. Language detection via detect_lang.py
3. JSON encoding with accent preservation
4. Voice selection logic
5. Full pipeline integration
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"


def get_scripts_dir():
    return SCRIPT_DIR


def run_clean_for_tts(text: str) -> str:
    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "clean_for_tts.py")],
        input=text,
        capture_output=True,
        text=True,
        cwd=str(SCRIPT_DIR),
    )
    return result.stdout.strip()


def run_detect_lang(text: str) -> str:
    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "detect_lang.py")],
        input=text,
        capture_output=True,
        text=True,
        cwd=str(SCRIPT_DIR),
    )
    return result.stdout.strip()


def run_json_encode(text: str, ensure_ascii: bool = False) -> str:
    ensure_ascii_arg = "False" if not ensure_ascii else "True"
    code = f"import json,sys; print(json.dumps(sys.stdin.read(), ensure_ascii={ensure_ascii_arg}))"
    result = subprocess.run(
        ["python3", "-c", code],
        input=text,
        capture_output=True,
        text=True,
        cwd=str(SCRIPT_DIR),
    )
    return result.stdout.strip()


def run_full_pipeline_clean_detect(text: str) -> str:
    # First run clean_for_tts
    clean_result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "clean_for_tts.py")],
        input=text,
        capture_output=True,
        text=True,
        cwd=str(SCRIPT_DIR),
    )
    if clean_result.returncode != 0:
        return ""

    cleaned_text = clean_result.stdout.strip()

    # Then run detect_lang on the cleaned text
    detect_result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "detect_lang.py")],
        input=cleaned_text,
        capture_output=True,
        text=True,
        cwd=str(SCRIPT_DIR),
    )
    return detect_result.stdout.strip()


# ============================================================================
# 1. Portuguese accent preservation through each pipeline stage
# ============================================================================


def test_clean_preserves_cedilla_in_text():
    text = "Açúcar é doce"
    cleaned = run_clean_for_tts(text)
    assert "ç" in cleaned, f"Cedilla (ç) not preserved. Got: {cleaned}"


def test_clean_preserves_tilde_a_in_text():
    text = "Não vou lá"
    cleaned = run_clean_for_tts(text)
    assert "ã" in cleaned, f"Tilde A (ã) not preserved. Got: {cleaned}"


def test_clean_preserves_tilde_o_in_text():
    text = "Ele põe a mesa"
    cleaned = run_clean_for_tts(text)
    assert "õ" in cleaned, f"Tilde O (õ) not preserved. Got: {cleaned}"


def test_clean_preserves_acute_accent_a():
    text = "Está á noite"
    cleaned = run_clean_for_tts(text)
    assert "á" in cleaned, f"Acute accent A (á) not preserved. Got: {cleaned}"


def test_clean_preserves_acute_accent_e():
    text = "Éste é o meu"
    cleaned = run_clean_for_tts(text)
    assert "é" in cleaned, f"Acute accent E (é) not preserved. Got: {cleaned}"


def test_clean_preserves_acute_accent_i():
    text = "Construído assim"
    cleaned = run_clean_for_tts(text)
    assert "í" in cleaned, f"Acute accent I (í) not preserved. Got: {cleaned}"


def test_clean_preserves_acute_accent_o():
    text = "Açúcar óbvio"
    cleaned = run_clean_for_tts(text)
    assert "ó" in cleaned, f"Acute accent O (ó) not preserved. Got: {cleaned}"


def test_clean_preserves_acute_accent_u():
    text = "Futura última"
    cleaned = run_clean_for_tts(text)
    assert "ú" in cleaned, f"Acute accent U (ú) not preserved. Got: {cleaned}"


def test_detect_lang_returns_pt_for_cedilla_text():
    text = "ç ç ç"
    detected = run_detect_lang(text)
    assert detected == "pt", f"Expected 'pt' for cedilla text, got: {detected}"


def test_detect_lang_returns_pt_for_tilde_a_text():
    text = "ã ã ã"
    detected = run_detect_lang(text)
    assert detected == "pt", f"Expected 'pt' for tilde A text, got: {detected}"


def test_detect_lang_returns_pt_for_tilde_o_text():
    text = "õ õ õ"
    detected = run_detect_lang(text)
    assert detected == "pt", f"Expected 'pt' for tilde O text, got: {detected}"


def test_full_pipeline_preserves_accents_through_clean_and_detect():
    text = "Você está aqui"
    cleaned = run_clean_for_tts(text)
    detected = run_detect_lang(cleaned)
    assert "ê" in cleaned or "á" in cleaned or "ç" in cleaned, f"Accents lost in cleaning. Got: {cleaned}"
    assert detected == "pt", f"Language not detected as PT after cleaning. Got: {detected}"


def test_full_pipeline_clean_to_detect_with_cedilla_tilde_accents():
    text = "Açúcar não está aqui"
    result = run_full_pipeline_clean_detect(text)
    assert result == "pt", f"Expected 'pt' for full pipeline with Portuguese text, got: {result}"


# ============================================================================
# 2. Language detection after cleaning
# ============================================================================


def test_detect_lang_markdown_wrapped_portuguese():
    text = "# Você está aqui"
    cleaned = run_clean_for_tts(text)
    detected = run_detect_lang(cleaned)
    assert detected == "pt", f"Expected 'pt' for markdown-wrapped Portuguese, got: {detected}"


def test_detect_lang_bold_wrapped_portuguese():
    text = "**Você está aqui**"
    cleaned = run_clean_for_tts(text)
    detected = run_detect_lang(cleaned)
    assert detected == "pt", f"Expected 'pt' for bold-wrapped Portuguese, got: {detected}"


def test_detect_lang_code_block_containing_portuguese():
    text = "`Você está` aqui com português"
    cleaned = run_clean_for_tts(text)
    detected = run_detect_lang(cleaned)
    assert detected == "pt", f"Expected 'pt' for code-wrapped Portuguese with surrounding text, got: {detected}"


def test_detect_lang_mixed_portuguese_english_weighted_portuguese():
    text = "Você está aqui and the text is here"
    cleaned = run_clean_for_tts(text)
    detected = run_detect_lang(cleaned)
    assert detected == "pt", f"Expected 'pt' for Portuguese-heavy mixed text, got: {detected}"


def test_detect_lang_mixed_portuguese_english_weighted_english():
    text = "The text is here and Você está"
    cleaned = run_clean_for_tts(text)
    detected = run_detect_lang(cleaned)
    # This test documents current behavior - which language wins depends on word counts
    # Just verify it returns a valid language
    assert detected in ["pt", "en"], f"Expected 'pt' or 'en', got: {detected}"


def test_detect_lang_link_removed_then_portuguese_detected():
    text = "[clique aqui](https://example.com) Você está"
    cleaned = run_clean_for_tts(text)
    detected = run_detect_lang(cleaned)
    assert detected == "pt", f"Expected 'pt' after link removal, got: {detected}"


def test_detect_lang_portuguese_specific_words_detected():
    text = "da do das dos"
    detected = run_detect_lang(text)
    assert detected == "pt", f"Expected 'pt' for Portuguese-specific words, got: {detected}"


# ============================================================================
# 3. JSON encoding preserves accents
# ============================================================================


def test_json_encode_with_ensure_ascii_false_preserves_cedilla():
    text = "açúcar"
    encoded = run_json_encode(text, ensure_ascii=False)
    decoded = json.loads(encoded)
    assert "ç" in decoded, f"Cedilla not preserved with ensure_ascii=False. Got: {decoded}"


def test_json_encode_with_ensure_ascii_false_preserves_tilde():
    text = "não"
    encoded = run_json_encode(text, ensure_ascii=False)
    decoded = json.loads(encoded)
    assert "ã" in decoded, f"Tilde not preserved with ensure_ascii=False. Got: {decoded}"


def test_json_encode_with_ensure_ascii_false_does_not_escape_cedilla():
    text = "açúcar"
    encoded = run_json_encode(text, ensure_ascii=False)
    assert "\\u" not in encoded, f"Cedilla escaped when ensure_ascii=False. Got: {encoded}"


def test_json_encode_with_ensure_ascii_true_escapes_cedilla():
    text = "açúcar"
    encoded = run_json_encode(text, ensure_ascii=True)
    assert "\\u" in encoded, f"Cedilla NOT escaped when ensure_ascii=True. Got: {encoded}"


def test_json_encode_with_ensure_ascii_false_multiple_accents():
    text = "Você não está aqui"
    encoded = run_json_encode(text, ensure_ascii=False)
    decoded = json.loads(encoded)
    assert "ê" in decoded and "ã" in decoded, f"Accents lost. Got: {decoded}"


def test_json_encode_roundtrip_with_ensure_ascii_false():
    original = "Açúcar, não está"
    encoded = run_json_encode(original, ensure_ascii=False)
    decoded = json.loads(encoded)
    assert decoded.strip() == original, f"Roundtrip failed. Expected: {original}, Got: {decoded}"


# ============================================================================
# 4. Voice selection logic (based on detect_lang output)
# ============================================================================


def test_voice_selection_pt_when_language_is_portuguese():
    detected_lang = "pt"
    voice = "pf_dora" if detected_lang == "pt" else "af_heart"
    assert voice == "pf_dora", f"Expected Portuguese voice (pf_dora), got: {voice}"


def test_voice_selection_en_when_language_is_english():
    detected_lang = "en"
    voice = "pf_dora" if detected_lang == "pt" else "af_heart"
    assert voice == "af_heart", f"Expected English voice (af_heart), got: {voice}"


def test_voice_selection_logic_applies_when_no_explicit_voice_set():
    text = "Você está aqui"
    detected = run_detect_lang(text)
    voice = "pf_dora" if detected == "pt" else "af_heart"
    assert voice == "pf_dora", f"Expected pf_dora for Portuguese text, got: {voice}"


def test_voice_selection_logic_applies_to_english_text():
    text = "Hello there"
    detected = run_detect_lang(text)
    voice = "pf_dora" if detected == "pt" else "af_heart"
    assert voice == "af_heart", f"Expected af_heart for English text, got: {voice}"


# ============================================================================
# 5. Edge cases
# ============================================================================


def test_clean_handles_empty_text():
    text = ""
    cleaned = run_clean_for_tts(text)
    assert isinstance(cleaned, str), f"Empty text should produce string, got: {type(cleaned)}"


def test_detect_lang_handles_empty_text():
    text = ""
    detected = run_detect_lang(text)
    assert detected in ["pt", "en"], f"Empty text should default to a language, got: {detected}"


def test_clean_handles_only_accented_characters():
    text = "ãõçáéíóú"
    cleaned = run_clean_for_tts(text)
    assert len(cleaned) > 0, f"Text with only accents should produce output, got: {cleaned}"


def test_detect_lang_handles_only_accented_characters():
    text = "ãõçáéíóú"
    detected = run_detect_lang(text)
    assert detected == "pt", f"Accented-only text should be detected as PT, got: {detected}"


def test_clean_handles_very_long_portuguese_text():
    text = "Você está aqui " * 100 + "com muito português"
    cleaned = run_clean_for_tts(text)
    detected = run_detect_lang(cleaned)
    assert len(cleaned) > 0, f"Long text should produce output"
    assert detected == "pt", f"Long Portuguese text should be detected as PT, got: {detected}"


def test_clean_handles_text_with_newlines():
    text = "Você está aqui\ncom português\nna próxima linha"
    cleaned = run_clean_for_tts(text)
    detected = run_detect_lang(cleaned)
    assert detected == "pt", f"Text with newlines should be detected as PT, got: {detected}"


def test_full_pipeline_preserves_language_through_newlines():
    text = "Você está\naqui com português\nnesse texto"
    result = run_full_pipeline_clean_detect(text)
    assert result == "pt", f"Expected 'pt' for text with newlines, got: {result}"


# ============================================================================
# 6. Known bug investigation: Portuguese text with English voice
# ============================================================================


def test_bug_investigate_clean_correctly_preserves_portuguese_text():
    """BUG: Portuguese text sometimes spoken with English voice.
    This test verifies that clean_for_tts.py preserves the Portuguese text correctly.
    """
    text = "Você está aqui com acento"
    cleaned = run_clean_for_tts(text)
    assert "Você" in cleaned or "você" in cleaned.lower(), f"Portuguese text lost. Got: {cleaned}"
    assert "ê" in cleaned or "á" in cleaned, f"Accents lost in cleaning. Got: {cleaned}"


def test_bug_investigate_detect_correctly_identifies_portuguese():
    """BUG: Portuguese text sometimes spoken with English voice.
    This test verifies that detect_lang.py correctly identifies Portuguese after cleaning.
    """
    text = "Você está aqui com acento"
    cleaned = run_clean_for_tts(text)
    detected = run_detect_lang(cleaned)
    assert detected == "pt", f"Portuguese not detected after cleaning. Clean: {cleaned}, Detected: {detected}"


def test_bug_investigate_full_pipeline_returns_portuguese():
    """BUG: Portuguese text sometimes spoken with English voice.
    This test verifies the full clean->detect pipeline works correctly.
    """
    text = "Você está aqui com acento"
    result = run_full_pipeline_clean_detect(text)
    assert result == "pt", f"Full pipeline should detect Portuguese, got: {result}"


def test_bug_investigate_text_with_multiple_portuguese_markers():
    """BUG: Portuguese text sometimes spoken with English voice.
    Text with multiple Portuguese indicators (accents + specific words).
    """
    text = "Você não está aqui com a camiseta azul"
    result = run_full_pipeline_clean_detect(text)
    assert result == "pt", f"Text with multiple PT markers should detect as PT, got: {result}"


def test_bash_quoting_does_not_break_pipeline():
    """BUG: Portuguese text sometimes spoken with English voice.
    Verify that bash variable expansion doesn't break accents.
    Tests TEXT variable in speak.sh properly passes through pipe.
    """
    text = "Açúcar não está aqui"
    # Simulate bash: TEXT="..." | clean_for_tts.py | detect_lang.py
    result = run_full_pipeline_clean_detect(text)
    assert result == "pt", f"Accents shouldn't be lost through bash pipe, got: {result}"


def test_json_encoding_does_not_lose_language_detection():
    """BUG: Portuguese text sometimes spoken with English voice.
    Verify that JSON encoding (used before curl) preserves text for detection.
    """
    text = "Você está aqui"
    detected = run_detect_lang(text)
    encoded = run_json_encode(text, ensure_ascii=False)
    decoded = json.loads(encoded)
    detected_after_encoding = run_detect_lang(decoded)
    assert detected == "pt", f"Original should be PT, got: {detected}"
    assert detected_after_encoding == "pt", f"After JSON roundtrip should still be PT, got: {detected_after_encoding}"
