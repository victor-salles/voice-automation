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
    # Headers: strip marker, ensure trailing punctuation for pause
    text = re.sub(
        r'^#{1,6}\s+(.+)$',
        lambda m: _ensure_period(m.group(1)),
        text, flags=re.MULTILINE
    )
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'[*_](.+?)[*_]', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    return text


def strip_links(text: str) -> str:
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'https?://\S+', 'link', text)
    return text


def strip_lists(text: str) -> str:
    """Remove list markers and ensure each item ends with punctuation."""
    text = re.sub(
        r'^\s*[-*+]\s+(.+)$',
        lambda m: _ensure_period(m.group(1)),
        text, flags=re.MULTILINE
    )
    text = re.sub(
        r'^\s*\d+\.\s+(.+)$',
        lambda m: _ensure_period(m.group(1)),
        text, flags=re.MULTILINE
    )
    return text


def strip_special(text: str) -> str:
    text = re.sub(r'[|>]', ' ', text)
    text = re.sub(r'[-=]{3,}', '', text)
    text = re.sub(r'\{[^}]*\}', '', text)
    text = re.sub(r'\[([^\]]*)\]', r'\1', text)
    return text


def normalize(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
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
