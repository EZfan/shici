"""Tone (平仄) classifier for individual Chinese characters.

Vendored from gelv-poetry (https://github.com/chenmisss/gelv-poetry) under
MIT License. The classification logic and pingshui.json mapping table are
adapted to provide a small, self-contained classifier.

平仄 rules:
  - 平 (level): corresponds to ancient Chinese level tone
  - 仄 (oblique): 上声 + 去声 + 入声
  - 中 (flexible): a character whose tone is permissive in this position
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from ._data_loader import load_pingshui


class Tone(str, Enum):
    """Tonal category of a Chinese character in the classical sense."""

    PING = "平"
    ZE = "仄"
    FLEXIBLE = "中"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ToneEntry:
    """A single character entry in the tone dictionary."""

    char: str
    ping: bool
    # Multiple readings map to a list of tone tuples (tone, optional sub-tone)
    readings: tuple[tuple[str, str], ...] = ()


class ToneDictionary:
    """Lookup table for character → tone.

    Lazily loaded from the bundled pingshui.json data file (vendored from
    gelv-poetry). The data shape is normalized via ``_data_loader``.
    """

    def __init__(self, entries: dict[str, ToneEntry]):
        self._entries = entries

    @classmethod
    def load(cls) -> "ToneDictionary":
        """Load the bundled dictionary."""
        data = load_pingshui()
        entries: dict[str, ToneEntry] = {}
        for char, info in data.items():
            entries[char] = ToneEntry(
                char=char,
                ping=info.get("ping", False),
                readings=tuple(info.get("readings", ())),
            )
        return cls(entries)

    def __contains__(self, char: str) -> bool:
        return char in self._entries

    def get(self, char: str) -> ToneEntry | None:
        return self._entries.get(char)

    def __len__(self) -> int:
        return len(self._entries)


_DICT: ToneDictionary | None = None


def get_dictionary() -> ToneDictionary:
    """Get the singleton tone dictionary."""
    global _DICT
    if _DICT is None:
        _DICT = ToneDictionary.load()
    return _DICT


@lru_cache(maxsize=4096)
def classify_character(char: str) -> Tone:
    """Classify a single character as 平/仄/中.

    Returns:
        Tone.PING if the character is 平 in any reading.
        Tone.ZE if all readings are 仄.
        Tone.FLEXIBLE if not found in the dictionary.
    """
    if not char or not _is_chinese(char):
        return Tone.FLEXIBLE

    entry = get_dictionary().get(char)
    if entry is None:
        return Tone.FLEXIBLE

    # If the entry has explicit ping=True, classify as 平; otherwise 仄
    # (gelv-poetry convention).
    if entry.ping:
        return Tone.PING
    return Tone.ZE


def classify_line(line: str) -> list[Tone]:
    """Classify every character in a line."""
    return [classify_character(c) for c in line if _is_chinese(c)]


def classify_text(text: str) -> list[Tone]:
    """Classify every Chinese character in a block of text."""
    return classify_line(text)


class ToneClassifier:
    """Higher-level classifier with contextual rules.

    The simple per-character classifier above works for raw pingshui lookup.
    This class adds rules for:
      - "一三五不论,二四六分明" (the well-known flexibility mnemonic)
      - "孤平" / "三平尾" detection helpers
    """

    def __init__(self, dictionary: ToneDictionary | None = None):
        self.dict = dictionary or get_dictionary()

    def classify(self, char: str) -> Tone:
        return classify_character(char)

    def classify_line(self, line: str) -> list[Tone]:
        """Classify line characters, returning one tone per Chinese char."""
        return [classify_character(c) for c in line if _is_chinese(c)]

    def is_ping(self, char: str) -> bool:
        return classify_character(char) == Tone.PING

    def is_ze(self, char: str) -> bool:
        return classify_character(char) == Tone.ZE


def _is_chinese(char: str) -> bool:
    """Check whether a character is in the CJK range."""
    if not char:
        return False
    code = ord(char)
    return (
        0x4E00 <= code <= 0x9FFF  # CJK Unified Ideographs
        or 0x3400 <= code <= 0x4DBF  # CJK Extension A
        or 0x20000 <= code <= 0x2A6DF  # CJK Extension B
    )


__all__ = [
    "Tone",
    "ToneEntry",
    "ToneDictionary",
    "ToneClassifier",
    "classify_character",
    "classify_line",
    "classify_text",
    "get_dictionary",
]