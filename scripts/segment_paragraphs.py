#!/usr/bin/env python3
"""Segment text into paragraphs and locate cursor position.

Usage:
    echo "text" | python3 segment_paragraphs.py --cursor-offset 42

Returns JSON:
    {"paragraphs": ["...", "..."], "currentIndex": 0, "total": 5}
"""
import json
import re
import sys
from argparse import ArgumentParser

MAX_CHARS = 600
MIN_CHARS = 20


def split_at_sentences(text: str) -> list[str]:
    """Break a long paragraph into sentence-boundary chunks."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    buf = ""
    for s in sentences:
        if buf and len(buf) + len(s) > MAX_CHARS:
            chunks.append(buf.strip())
            buf = s
        else:
            buf = f"{buf} {s}".strip()
    if buf:
        chunks.append(buf.strip())
    return [c for c in chunks if len(c) >= MIN_CHARS]


def segment(text: str, cursor_offset: int = 0) -> dict:
    """Return paragraphs list and the index containing cursor_offset."""
    blocks = re.split(r"\n{2,}", text)
    paragraphs: list[str] = []
    offsets: list[int] = []
    pos = 0

    for block in blocks:
        cleaned = block.strip()
        block_len = len(block)

        if len(cleaned) >= MIN_CHARS:
            if len(cleaned) > MAX_CHARS:
                for chunk in split_at_sentences(cleaned):
                    paragraphs.append(chunk)
                    offsets.append(pos)
            else:
                paragraphs.append(cleaned)
                offsets.append(pos)

        pos += block_len + 2  # +2 for the \n\n separator

    # Find which paragraph the cursor falls in
    current = 0
    for i, off in enumerate(offsets):
        if cursor_offset >= off:
            current = i

    return {
        "paragraphs": paragraphs,
        "currentIndex": current,
        "total": len(paragraphs),
    }


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--cursor-offset", type=int, default=0)
    args = parser.parse_args()

    text = sys.stdin.read()
    if not text.strip():
        json.dump({"paragraphs": [], "currentIndex": 0, "total": 0}, sys.stdout)
        return

    json.dump(segment(text, args.cursor_offset), sys.stdout)


if __name__ == "__main__":
    main()
