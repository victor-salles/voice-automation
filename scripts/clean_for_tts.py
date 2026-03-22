#!/usr/bin/env python3
"""Clean text for TTS playback. Strips markdown, code, URLs, special chars.

Ensures proper punctuation at structural boundaries (lists, headers,
paragraphs) so TTS engines pause naturally.

Usage: echo "# Hello **world**" | python3 clean_for_tts.py
Output: Hello world.
"""
import re
import sys


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
    # Em/en dashes → comma for pause
    text = re.sub(r'\s*[—–]\s*', ', ', text)
    # Pipes, blockquotes
    text = re.sub(r'[|>]', ' ', text)
    text = re.sub(r'[-=]{3,}', '', text)
    # Braces and brackets
    text = re.sub(r'\{[^}]*\}', '', text)
    text = re.sub(r'\[([^\]]*)\]', r'\1', text)
    # Emojis (Unicode blocks for symbols/emoticons/etc.)
    text = re.sub(r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FA6F]', '', text)
    return text


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
               strip_links, strip_lists, strip_special, normalize):
        text = fn(text)
    return text


if __name__ == "__main__":
    print(clean(sys.stdin.read()))
