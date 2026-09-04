"""Unit tests for the tone (平仄) classifier.

Tests cover:
- ``classify_character``: per-character tone lookup, including
  fallback to ``FLEXIBLE`` for unknown / non-Chinese / empty input.
- ``classify_line``: line-level classification of a famous Tang poem.
- ``ToneDictionary``: lazy loading and membership semantics.
"""

from __future__ import annotations

import pytest

from shici.prosody.classifier import (
    Tone,
    ToneClassifier,
    ToneDictionary,
    classify_character,
    classify_line,
    classify_text,
    get_dictionary,
)

# ---------------------------------------------------------------------------
# Character-level classification
# ---------------------------------------------------------------------------


class TestClassifyCharacter:
    """Single-character tone classification."""

    @pytest.mark.parametrize(
        "char",
        list("光山川天人"),
    )
    def test_ping_chars(self, char: str):
        """Known level-tone (平) characters are classified correctly."""
        assert classify_character(char) == Tone.PING

    @pytest.mark.parametrize(
        "char",
        list("白石日"),
    )
    def test_ze_chars(self, char: str):
        """Known oblique-tone (仄) characters are classified correctly."""
        assert classify_character(char) == Tone.ZE

    def test_unknown_char(self):
        """Uncommon characters fall back to FLEXIBLE."""
        # \u9fff is near the top of the BMP CJK range and unlikely to be in
        # the dictionary.
        assert classify_character("\u9fff") == Tone.FLEXIBLE

    @pytest.mark.parametrize(
        "punct",
        ["，", ".", "。", "！", "?", "；", " "],
    )
    def test_punct_skipped(self, punct: str):
        """Punctuation and non-Chinese chars do not crash and return FLEXIBLE."""
        assert classify_character(punct) == Tone.FLEXIBLE

    def test_empty(self):
        """Empty string returns FLEXIBLE."""
        assert classify_character("") == Tone.FLEXIBLE

    def test_latin_char(self):
        """Latin chars are not in the dictionary; return FLEXIBLE."""
        assert classify_character("A") == Tone.FLEXIBLE

    def test_returns_enum_member(self):
        """Result must be a ``Tone`` enum member."""
        result = classify_character("光")
        assert isinstance(result, Tone)


# ---------------------------------------------------------------------------
# Line-level classification
# ---------------------------------------------------------------------------


class TestClassifyLine:
    """Multi-character line classification."""

    def test_classic_line(self):
        """Classify a known poem line; all tones are valid enum members."""
        tones = classify_line("床前明月光")
        assert all(t in (Tone.PING, Tone.ZE, Tone.FLEXIBLE) for t in tones)
        # The line has 5 CJK characters.
        assert len(tones) == 5

    def test_line_skips_punctuation(self):
        """Punctuation is silently dropped from the tone sequence."""
        tones_clean = classify_line("床前明月光")
        tones_with_punct = classify_line("床前，明月光。")
        assert tones_clean == tones_with_punct

    def test_classify_text_alias(self):
        """``classify_text`` is an alias for ``classify_line``."""
        line = "举头望明月"
        assert classify_text(line) == classify_line(line)

    def test_empty_line(self):
        """Empty lines produce an empty list."""
        assert classify_line("") == []


# ---------------------------------------------------------------------------
# ToneDictionary
# ---------------------------------------------------------------------------


class TestDictionary:
    """Dictionary load / membership semantics."""

    def test_load(self):
        """Loaded dictionary has a reasonable number of characters."""
        d = ToneDictionary.load()
        assert len(d) > 100  # At least 100 characters (real data has >7000)

    def test_load_returns_fresh_instance(self):
        """Each ``load()`` call returns a new instance (cached separately)."""
        d1 = ToneDictionary.load()
        d2 = ToneDictionary.load()
        assert isinstance(d1, ToneDictionary)
        assert isinstance(d2, ToneDictionary)
        assert len(d1) == len(d2)

    def test_contains(self):
        """The dictionary exposes a ``__contains__`` method."""
        d = ToneDictionary.load()
        assert "光" in d
        assert "\u9fff" not in d

    def test_get_returns_entry(self):
        """``get`` returns a ToneEntry for known characters."""
        d = ToneDictionary.load()
        entry = d.get("光")
        assert entry is not None
        assert entry.char == "光"
        assert isinstance(entry.ping, bool)

    def test_get_returns_none_for_unknown(self):
        """Unknown characters return None from ``get``."""
        d = ToneDictionary.load()
        assert d.get("\u9fff") is None

    def test_singleton_get_dictionary(self):
        """``get_dictionary`` returns a singleton."""
        d1 = get_dictionary()
        d2 = get_dictionary()
        assert d1 is d2


# ---------------------------------------------------------------------------
# ToneClassifier (high-level API)
# ---------------------------------------------------------------------------


class TestToneClassifier:
    """High-level classifier with context-aware helpers."""

    def test_default_uses_singleton(self):
        cls = ToneClassifier()
        assert cls.dict is get_dictionary()

    def test_explicit_dictionary(self):
        d = ToneDictionary.load()
        cls = ToneClassifier(d)
        assert cls.dict is d

    def test_classify_delegates(self):
        cls = ToneClassifier()
        assert cls.classify("光") == classify_character("光")

    def test_is_ping_and_is_ze(self):
        cls = ToneClassifier()
        # Pick a known PING and ZE character (光=PING, 白=ZE per the data).
        assert cls.is_ping("光")
        assert cls.is_ze("白")

    def test_is_ping_negative(self):
        cls = ToneClassifier()
        # 白 is 仄, not 平.
        assert not cls.is_ping("白")
