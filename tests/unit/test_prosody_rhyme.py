"""Unit tests for the rhyme (韵部) classifier.

Tests cover:
- ``lookup_rhyme`` / ``classify_rhyme`` module-level helpers.
- ``RhymeBook`` instance-level lookups, ``is_same_group``,
  ``rhymes_with``, and membership checks.
- ``RhymeGroup`` enum value parsing via ``from_string``.
"""

from __future__ import annotations

import pytest

from shici.prosody.rhyme import (
    RhymeBook,
    RhymeGroup,
    classify_rhyme,
    lookup_rhyme,
)


# ---------------------------------------------------------------------------
# RhymeGroup enum
# ---------------------------------------------------------------------------


class TestRhymeGroup:
    """The 106 traditional Pingshui rhyme groups."""

    def test_total_count(self):
        """The enum exposes all 106 traditional groups."""
        assert len(list(RhymeGroup)) == 106

    def test_from_string_known(self):
        """Look up an enum member by its Chinese label."""
        rg = RhymeGroup.from_string("上平一东")
        assert rg == RhymeGroup.SHANG_PING_1_DONG

    def test_from_string_xia_ping_yang(self):
        """下平七阳 is a well-known rhyme (used by 床前明月光)."""
        rg = RhymeGroup.from_string("下平七阳")
        assert rg == RhymeGroup.XIA_PING_7_YANG

    def test_from_string_ru_sheng(self):
        """入声 (entering tone) groups are also present."""
        rg = RhymeGroup.from_string("入声一屋")
        assert rg == RhymeGroup.RU_SHENG_1_WU

    def test_invalid_string(self):
        """Unknown strings return None, never raise."""
        assert RhymeGroup.from_string("invalid") is None
        assert RhymeGroup.from_string("") is None

    def test_enum_members_are_unique(self):
        """All enum values are unique strings."""
        values = [m.value for m in RhymeGroup]
        assert len(values) == len(set(values))


# ---------------------------------------------------------------------------
# lookup_rhyme
# ---------------------------------------------------------------------------


class TestLookupRhyme:
    """Module-level rhyme lookup."""

    def test_known_char_light(self):
        """``光`` (moon-light) is in 下平七阳 per pingshui."""
        rg = lookup_rhyme("光")
        assert rg is not None
        # The exact label is "下平七阳" after normalization.
        assert "阳" in rg.value

    def test_known_char_yellow(self):
        """``黄`` should also be in 下平七阳."""
        rg = lookup_rhyme("黄")
        assert rg is not None
        assert "阳" in rg.value

    def test_unknown_char_returns_none(self):
        """A character outside the dictionary returns None."""
        assert lookup_rhyme("\u9fff") is None

    def test_empty_string_returns_none(self):
        """Empty input returns None."""
        assert lookup_rhyme("") is None

    def test_punct_returns_none(self):
        """Punctuation returns None (not in dictionary)."""
        assert lookup_rhyme("，") is None


class TestClassifyRhyme:
    """Line-level rhyme classification."""

    def test_classic_line(self):
        """Classify a line of known characters; result length matches CJK count."""
        result = classify_rhyme("床前明月光")
        assert len(result) == 5
        # Punctuation skipped
        result2 = classify_rhyme("床前，明月光。")
        assert result == result2

    def test_line_with_unknown(self):
        """Unknown characters become None in the result."""
        result = classify_rhyme("光\u9fff")
        assert result[0] is not None
        assert result[1] is None


# ---------------------------------------------------------------------------
# RhymeBook
# ---------------------------------------------------------------------------


class TestRhymeBook:
    """Instance-level rhyme lookup."""

    def test_construction(self):
        """Constructing without arguments loads the bundled data."""
        book = RhymeBook()
        # RhymeBook has many entries from the bundled pingshui data.
        assert len(book._mapping) > 100

    def test_lookup(self):
        """``lookup`` returns a RhymeGroup for known characters."""
        book = RhymeBook()
        rg = book.lookup("光")
        assert isinstance(rg, RhymeGroup)
        assert "阳" in rg.value

    def test_group_of_alias(self):
        """``group_of`` is an alias for ``lookup``."""
        book = RhymeBook()
        assert book.group_of("光") == book.lookup("光")

    def test_is_same_group(self):
        """Two characters in the same group are detected."""
        book = RhymeBook()
        # 光 and 黄 are both in 下平七阳 in the bundled data.
        if "光" in book and "黄" in book:
            assert book.is_same_group("光", "黄") is True

    def test_is_same_group_different(self):
        """Two characters in different groups are not the same."""
        book = RhymeBook()
        if "光" in book and "东" in book:
            assert book.is_same_group("光", "东") is False

    def test_is_same_group_with_unknown(self):
        """If either char is unknown, ``is_same_group`` returns False."""
        book = RhymeBook()
        assert book.is_same_group("光", "\u9fff") is False

    def test_rhymes_with_filters(self):
        """``rhymes_with`` returns only matching candidates."""
        book = RhymeBook()
        # Build a candidate list including a known rhyme and an unrelated char.
        candidates = ["黄", "东"] if "光" in book and "黄" in book and "东" in book else []
        if candidates:
            result = book.rhymes_with("光", candidates)
            # 黄 rhymes with 光; 东 does not.
            assert "黄" in result
            assert "东" not in result

    def test_rhymes_with_unknown_target(self):
        """If the target char is unknown, ``rhymes_with`` returns empty."""
        book = RhymeBook()
        assert book.rhymes_with("\u9fff", ["光", "黄"]) == []

    def test_contains(self):
        """``__contains__`` checks dictionary membership."""
        book = RhymeBook()
        assert "光" in book
        assert "\u9fff" not in book
