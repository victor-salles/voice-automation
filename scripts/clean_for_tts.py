#!/usr/bin/env python3
"""Clean text for TTS playback. Strips markdown, code, URLs, special chars.

Ensures proper punctuation at structural boundaries (lists, headers,
paragraphs) so TTS engines pause naturally.

Usage: echo "# Hello **world**" | python3 clean_for_tts.py
Output: Hello world.
"""
import re
import sys

# ── Acronym dictionaries ──

# Spelled out letter-by-letter
SPELLED_ACRONYMS = {
    "HTTPS": "H T T P S", "HTML": "H T M L", "HTTP": "H T T P",
    "STDOUT": "standard out", "STDERR": "standard error",
    "STDIN": "standard in",
    "API": "A P I", "URL": "U R L", "CSS": "C S S", "XML": "X M L",
    "SSH": "S S H", "TLS": "T L S", "SSL": "S S L", "TCP": "T C P",
    "UDP": "U D P", "DNS": "D N S", "CLI": "C L I", "SDK": "S D K",
    "IDE": "I D E", "JWT": "J W T", "AWS": "A W S", "GCP": "G C P",
    "LLM": "L L M", "TTS": "T T S", "STT": "S T T", "OCR": "O C R",
    "NLP": "N L P", "CPU": "C P U", "GPU": "G P U", "SSD": "S S D",
    "USB": "U S B", "PDF": "P D F", "PNG": "P N G", "CSV": "C S V",
    "EOF": "E O F",
    "AI": "A I", "OS": "O S", "UI": "U I", "UX": "U X",
    "PR": "P R", "CI": "C I", "CD": "C D", "VM": "V M", "IP": "I P",
}

# Pronounced as words
PRONOUNCED_ACRONYMS = {
    "JSON": "Jason", "SQL": "sequel", "GUI": "gooey",
    "YAML": "YAML", "RAM": "ram", "REST": "rest", "CRUD": "crud",
    "FIFO": "fifo", "LIFO": "lifo", "MIME": "mime", "REGEX": "regex",
    "NULL": "null", "BOOL": "boolean", "INT": "int", "ENV": "env",
}

# Combined and sorted by length (longest first) to avoid partial matches
_ALL_ACRONYMS = {**SPELLED_ACRONYMS, **PRONOUNCED_ACRONYMS}
_ACRONYM_PATTERNS = [
    (re.compile(r'\b' + re.escape(k) + r'\b', re.IGNORECASE), v)
    for k, v in sorted(_ALL_ACRONYMS.items(), key=lambda x: -len(x[0]))
]

# Software names that precede version numbers
_VERSION_SOFTWARE = (
    "Python", "Node", "Ruby", "Java", "Go", "Rust", "Swift", "PHP",
    "macOS", "iOS", "Android", "Chrome", "Firefox", "Safari",
    "Docker", "Kubernetes",
)


def strip_code_blocks(text: str) -> str:
    return re.sub(r'```[\s\S]*?```', " code block omitted. ", text)


def strip_inline_code(text: str) -> str:
    return re.sub(r'`([^`]+)`', r'\1', text)


def strip_markdown(text: str) -> str:
    text = re.sub(
        r'^#{1,6}\s+(.+)$',
        lambda m: _ensure_period(m.group(1)),
        text, flags=re.MULTILINE,
    )
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'[*_](.+?)[*_]', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    return text


def strip_links(text: str) -> str:
    # Images: ![alt text](url) → alt text (or nothing if no alt)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Regular links: [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'https?://\S+', 'link', text)
    return text


def strip_lists(text: str) -> str:
    """Remove list markers and ensure each item ends with punctuation."""
    text = re.sub(
        r'^\s*[-*+]\s+(.+)$',
        lambda m: _ensure_period(m.group(1)),
        text, flags=re.MULTILINE,
    )
    text = re.sub(
        r'^\s*\d+\.\s+(.+)$',
        lambda m: _ensure_period(m.group(1)),
        text, flags=re.MULTILINE,
    )
    return text


def strip_special(text: str) -> str:
    # Arrows → natural language
    text = re.sub(r'[→⟶⟹➡►▸]', ' to ', text)
    text = re.sub(r'[←⟵⟸⬅◄◂]', ' from ', text)
    # macOS keyboard symbols
    text = re.sub(r'[⌥]', 'Option ', text)
    text = re.sub(r'[⌘]', 'Command ', text)
    text = re.sub(r'[⇧]', 'Shift ', text)
    text = re.sub(r'[⌃]', 'Control ', text)
    # Em/en dashes → comma for natural pause
    text = re.sub(r'\s*[—–]\s*', ', ', text)
    # Forward slashes → comma for pause
    text = re.sub(r'/', ', ', text)
    # Currency before numbers: $50 → 50 dollars
    text = re.sub(r'\$(\d+(?:\.\d+)?)', r'\1 dollars', text)
    text = re.sub(r'€(\d+(?:\.\d+)?)', r'\1 euros', text)
    text = re.sub(r'£(\d+(?:\.\d+)?)', r'\1 pounds', text)
    # Percentage after numbers: 50% → 50 percent
    text = re.sub(r'(\d)%', r'\1 percent', text)
    # Hashtag: #42 → number 42, #python → hashtag python
    text = re.sub(r'#(\d+)', r'number \1', text)
    text = re.sub(r'#([a-zA-Z]\w*)', r'hashtag \1', text)
    text = re.sub(r'#', '', text)
    # Ampersand
    text = re.sub(r'&', ' and ', text)
    # @ sign (not in emails)
    text = re.sub(r'(\w)@(\w+\.\w+)', r'\1 at \2', text)
    text = re.sub(r'@', ' at ', text)
    # C++ style: plus plus
    text = re.sub(r'(\w)\+\+', r'\1 plus plus', text)
    # Equals between words: a = b
    text = re.sub(r'(\w)\s*=\s*(\w)', r'\1 equals \2', text)
    # Tilde before number: ~100 → approximately 100
    text = re.sub(r'~(\d)', r'approximately \1', text)
    # Horizontal rules must be removed before the general = cleanup
    text = re.sub(r'[-=]{3,}', '', text)
    # Clean remaining symbols
    text = re.sub(r'[~+=]', ' ', text)
    text = re.sub(r'\$', '', text)
    text = re.sub(r'[€£%]', '', text)
    # Pipes, blockquotes
    text = re.sub(r'[|>]', ' ', text)
    # Braces and brackets
    text = re.sub(r'\{[^}]*\}', '', text)
    text = re.sub(r'\[([^\]]*)\]', r'\1', text)
    # Emojis (Unicode blocks for symbols/emoticons/etc.)
    text = re.sub(r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FA6F]', '', text)
    return text


def expand_parentheticals(text: str) -> str:
    """Convert parenthetical expressions to comma-delimited phrases."""
    text = re.sub(r'\(e\.g\.,?\s*([^)]*)\)', r', for example \1,', text)
    text = re.sub(r'\(i\.e\.,?\s*([^)]*)\)', r', that is \1,', text)
    text = re.sub(r'\(etc\.?\)', ', etcetera,', text)
    text = re.sub(r'\(\s*\)', '', text)  # empty parens
    text = re.sub(r'\(([^)]+)\)', r', \1,', text)
    return text


def expand_abbreviations(text: str) -> str:
    """Replace standalone acronyms with TTS-friendly forms."""
    for pattern, replacement in _ACRONYM_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def expand_versions(text: str) -> str:
    """Convert version numbers to spoken form.

    v3.12 → version 3 point 12
    3.12.1 → 3 point 12 point 1
    Python 3.9 → Python 3 point 9

    Does NOT affect plain decimals like 3.14 or 0.5.
    """
    # v-prefixed: v3.12 → version 3 point 12
    text = re.sub(
        r'\bv(\d+(?:\.\d+)+)\b',
        lambda m: "version " + m.group(1).replace(".", " point "),
        text,
    )
    # Three-part+ versions: 3.12.1 → 3 point 12 point 1
    text = re.sub(
        r'\b(\d+\.\d+\.\d+(?:\.\d+)*)\b',
        lambda m: m.group(1).replace(".", " point "),
        text,
    )
    # Software-prefixed two-part versions: Python 3.9 → Python 3 point 9
    sw_pattern = "|".join(re.escape(s) for s in _VERSION_SOFTWARE)
    text = re.sub(
        r'(' + sw_pattern + r')\s+(\d+\.\d+)\b',
        lambda m: m.group(1) + " " + m.group(2).replace(".", " point "),
        text,
    )
    return text


def expand_file_extensions(text: str) -> str:
    """Replace file extensions with spelled-out letters for TTS.

    Examples:
        .py → dot P Y
        file.py → file dot P Y
        config.json → config dot J S O N

    Does NOT expand:
        - Sentence-ending periods (followed by space or EOL)
        - Decimal numbers (3.14)
        - Ellipsis (...)
    """
    def is_decimal_number(text: str, dot_pos: int) -> bool:
        """Check if dot at dot_pos is part of a decimal number like 3.14."""
        if dot_pos == 0 or dot_pos >= len(text) - 1:
            return False
        return text[dot_pos - 1].isdigit() and text[dot_pos + 1].isdigit()

    result = []
    i = 0

    while i < len(text):
        # Look for the next dot followed by 1-5 letters at word boundary
        match = re.search(r'\.([a-zA-Z]{1,5})\b', text[i:])
        if not match:
            result.append(text[i:])
            break

        dot_pos_in_text = i + match.start()

        # Check if it's a decimal (dot between two digits) or ellipsis
        if is_decimal_number(text, dot_pos_in_text):
            # It's a decimal like "3.14" - don't expand
            result.append(text[i:dot_pos_in_text + 2])
            i = dot_pos_in_text + 2
            continue

        if dot_pos_in_text + 1 < len(text) and text[dot_pos_in_text + 1] == '.':
            # It's an ellipsis - don't expand
            result.append(text[i:dot_pos_in_text + 2])
            i = dot_pos_in_text + 2
            continue

        # Check what comes before the dot
        if dot_pos_in_text == 0:
            # Dot at start like ".py"
            result.append(text[i:dot_pos_in_text])
            prefix = ""
        else:
            prev_char = text[dot_pos_in_text - 1]
            if prev_char.isalnum() or prev_char == '_':
                # Word character before dot like "file.py"
                result.append(text[i:dot_pos_in_text])
                prefix = " "
            else:
                # Non-word char before dot
                result.append(text[i:dot_pos_in_text])
                prefix = ""

        # Add the expansion
        extension = match.group(1).upper()
        spaced_letters = " ".join(extension)
        result.append(f"{prefix}dot {spaced_letters}")

        i = dot_pos_in_text + len(match.group(0))

    return "".join(result)


def expand_identifiers(text: str) -> str:
    """Convert UPPER_SNAKE_CASE identifiers to readable form for TTS.

    Examples:
        KOKORO_DEBUG → Kokoro Debug
        MAX_HISTORY → Max History
        PT_VOICE → P T Voice
        HTTP_CODE → H T T P Code

    Heuristic:
        - Segments 3+ chars WITH vowels → Title Case (word-like)
        - Segments 1-2 chars OR known acronyms → space-separated uppercase
        - Known acronyms: URL, API, HTTP, HTTPS, HTML, CSS, JSON, XML, YAML, SQL,
          SSH, TLS, SSL, TCP, UDP, DNS, CLI, GUI, SDK, IDE, JWT, AWS, GCP, ENV,
          WAV, MP3, PDF, PNG, JPG, SVG, GIF, CSV, TSV, RAM, CPU, GPU, SSD, USB,
          LLM, TTS, STT, OCR, NLP, PT, EN, BR, US, UK
    """
    # List of known acronyms that should always be spelled out
    KNOWN_ACRONYMS = {
        "URL", "API", "HTTP", "HTTPS", "HTML", "CSS", "JSON", "XML", "YAML",
        "SQL", "SSH", "TLS", "SSL", "TCP", "UDP", "DNS", "CLI", "GUI", "SDK",
        "IDE", "JWT", "AWS", "GCP", "ENV", "WAV", "MP3", "PDF", "PNG", "JPG",
        "SVG", "GIF", "CSV", "TSV", "RAM", "CPU", "GPU", "SSD", "USB", "LLM",
        "TTS", "STT", "OCR", "NLP", "PT", "EN", "BR", "US", "UK"
    }

    def has_vowel(s: str) -> bool:
        return any(c in "AEIOUaeiou" for c in s)

    def is_word_like(segment: str) -> bool:
        """A segment looks like a word if 3+ chars AND has a vowel."""
        return len(segment) >= 3 and has_vowel(segment)

    def expand_identifier(match):
        identifier = match.group(0)
        segments = identifier.split("_")
        expanded_parts = []

        for segment in segments:
            if segment in KNOWN_ACRONYMS:
                # Known acronym: spell it out
                expanded_parts.append(" ".join(segment))
            elif is_word_like(segment):
                # Word-like: title case it
                expanded_parts.append(segment.capitalize())
            else:
                # Too short or no vowel: spell it out
                expanded_parts.append(" ".join(segment))

        return " ".join(expanded_parts)

    # Match all-caps identifiers with at least 3 characters (allowing underscores and digits)
    return re.sub(r'\b[A-Z][A-Z0-9_]{2,}\b', expand_identifier, text)


def normalize(text: str) -> str:
    """Flatten to single paragraph. All line breaks become sentence boundaries."""
    # Any line not ending in punctuation gets a period
    text = re.sub(r'([^\s.!?:;,])\s*\n', r'\1. ', text)
    # Lines already ending in punctuation: just add space
    text = re.sub(r'\n', ' ', text)
    # Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def _ensure_period(line: str) -> str:
    """Add a period if the line doesn't end with sentence punctuation."""
    stripped = line.rstrip()
    if stripped and stripped[-1] not in '.!?:;,':
        return stripped + '.'
    return stripped


def clean(text: str) -> str:
    for fn in (strip_code_blocks, strip_inline_code, strip_markdown,
               strip_links, strip_lists, strip_special,
               expand_file_extensions, expand_identifiers,
               normalize):
        text = fn(text)
    return text


if __name__ == "__main__":
    print(clean(sys.stdin.read()))
