#!/usr/bin/env python
"""Build the RAG JSONL corpus from raw chinese-poetry data.

Run this after cloning https://github.com/chinese-poetry/chinese-poetry to
convert the raw JSON arrays into JSONL files, one record per poem line.

The output is consumed by `shici index`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterator


def parse_tang(raw: dict) -> Iterator[dict]:
    """Tang poetry: {author, title, paragraphs: [str], id}."""
    author = raw.get("author", "")
    title = raw.get("title", "")
    for para in raw.get("paragraphs", []):
        for line in _split_lines(para):
            yield {
                "author": author,
                "title": title,
                "line": line,
                "dynasty": "唐",
                "source": "tang",
            }


def parse_song(raw: dict) -> Iterator[dict]:
    """Song ci: {author, paragraphs: [str], rhythmic}."""
    author = raw.get("author", "")
    title = raw.get("rhythmic", "")
    for para in raw.get("paragraphs", []):
        for line in _split_lines(para):
            yield {
                "author": author,
                "title": title,
                "line": line,
                "dynasty": "宋",
                "source": "song",
            }


def parse_shijing(raw: dict) -> Iterator[dict]:
    """诗经: {title, chapter, section, content: [str]}."""
    title = raw.get("title", "")
    section = raw.get("section", "")
    chapter = raw.get("chapter", "")
    for para in raw.get("content", []):
        for line in _split_lines(para):
            yield {
                "author": f"{chapter}·{section}",
                "title": title,
                "line": line,
                "dynasty": "先秦",
                "source": "shijing",
            }


def _split_lines(paragraph: str) -> list[str]:
    """Split a paragraph into individual poem lines.

    Strips punctuation marks; keeps only Chinese-character-rich lines.
    """
    import re
    parts = re.split(r"[，。！？；\n]", paragraph)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) >= 2]


def convert_file(in_path: Path, out_path: Path, parser) -> int:
    """Convert one JSON file to JSONL."""
    raw = json.loads(in_path.read_text(encoding="utf-8"))
    count = 0
    with out_path.open("w", encoding="utf-8") as f:
        for record in parser(raw):
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/raw/chinese-poetry"),
        help="Path to the cloned chinese-poetry directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/poetry"),
        help="Output directory for *.jsonl files",
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    conversions = [
        ("全唐诗/poet.tang.0.json", "tang.jsonl", parse_tang),
        ("全唐诗/poet.tang.3000.json", "tang-3k.jsonl", parse_tang),
        ("全唐诗/poet.tang.1000.json", "tang-1k.jsonl", parse_tang),
        ("宋词/ci.song.0.json", "song.jsonl", parse_song),
        ("宋词/songci-300.json", "songci-300.jsonl", parse_song),
        ("诗经/shijing.json", "shijing.jsonl", parse_shijing),
    ]

    total = 0
    for rel_in, rel_out, parser_fn in conversions:
        in_path = args.source / rel_in
        out_path = args.output / rel_out
        if not in_path.exists():
            print(f"  - skip {rel_in} (not found)")
            continue
        try:
            count = convert_file(in_path, out_path, parser_fn)
            print(f"  ✓ {rel_in} → {rel_out}: {count} lines")
            total += count
        except Exception as e:
            print(f"  ✗ {rel_in}: {e}")

    print(f"\nTotal: {total} lines indexed across {len(conversions)} corpora")
    print(f"Next: shici index -s {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())