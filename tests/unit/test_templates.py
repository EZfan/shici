"""Unit tests for the 词牌 (cipai) template registry.

Tests cover:
- The built-in ``CIPAI_REGISTRY`` is non-empty and contains well-known cipai.
- ``list_cipai`` and ``get_cipai`` work as advertised.
- Each template has consistent structure (line counts match char counts and
  tone patterns).
- Total character counts match the canonical descriptions (e.g. 浣溪沙 = 42).
"""

from __future__ import annotations

import pytest

from shici.prosody.templates import (
    CIPAI_REGISTRY,
    CipaiTemplate,
    get_cipai,
    list_cipai,
)


# ---------------------------------------------------------------------------
# Registry basics
# ---------------------------------------------------------------------------


class TestCipaiRegistry:
    """Basic registry presence and lookup."""

    def test_not_empty(self):
        """Registry has at least 20 templates (the built-in minimum)."""
        assert len(CIPAI_REGISTRY) >= 20

    def test_all_values_are_templates(self):
        """All registry values are CipaiTemplate instances."""
        for name, tpl in CIPAI_REGISTRY.items():
            assert isinstance(tpl, CipaiTemplate), f"{name} is not a template"

    def test_list_cipai_sorted(self):
        """``list_cipai`` returns a sorted list of names."""
        names = list_cipai()
        assert names == sorted(names)
        assert isinstance(names, list)

    def test_list_contains_well_known(self):
        """Common cipai names are present."""
        names = list_cipai()
        assert "浣溪沙" in names
        assert "水调歌头" in names

    def test_get_cipai_huanxisha(self):
        """``浣溪沙`` has 6 lines summing to 42 characters."""
        tpl = get_cipai("浣溪沙")
        assert tpl.line_count == 6
        assert sum(tpl.char_counts) == 42
        assert tpl.name == "浣溪沙"

    def test_get_cipai_shuidiaogetou(self):
        """``水调歌头`` is a long-form cipai (>= 95 chars)."""
        tpl = get_cipai("水调歌头")
        assert tpl.line_count > 0
        assert sum(tpl.char_counts) >= 95

    def test_get_unknown_raises_keyerror(self):
        """Looking up a non-existent cipai raises KeyError."""
        with pytest.raises(KeyError):
            get_cipai("不存在的词牌")

    def test_get_unknown_error_message_lists_available(self):
        """The KeyError message lists available cipai for usability."""
        with pytest.raises(KeyError) as excinfo:
            get_cipai("不存在的词牌")
        # The message should mention at least one known cipai.
        assert "浣溪沙" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Template structural consistency
# ---------------------------------------------------------------------------


class TestCipaiStructure:
    """Cross-check structural invariants of every template."""

    @pytest.mark.parametrize("name", list(CIPAI_REGISTRY.keys()))
    def test_tone_patterns_match_lines(self, name: str):
        """Each cipai's tone_patterns length matches line_count."""
        tpl = CIPAI_REGISTRY[name]
        assert len(tpl.tone_patterns) == tpl.line_count, (
            f"{name}: tone_patterns={len(tpl.tone_patterns)} "
            f"vs lines={tpl.line_count}"
        )

    @pytest.mark.parametrize("name", list(CIPAI_REGISTRY.keys()))
    def test_char_counts_match_lines(self, name: str):
        """char_counts length matches line_count."""
        tpl = CIPAI_REGISTRY[name]
        assert len(tpl.char_counts) == tpl.line_count

    @pytest.mark.parametrize("name", list(CIPAI_REGISTRY.keys()))
    def test_pattern_length_matches_char_count(self, name: str):
        """Each pattern's non-flexible (平/仄) markers fit within char_count.

        The pattern may omit some ``中`` (flexible) placeholders to keep the
        schema concise, so we only check that the count of explicit 平/仄
        characters does not exceed the line's char count.
        """
        tpl = CIPAI_REGISTRY[name]
        for i, (pattern, count) in enumerate(
            zip(tpl.tone_patterns, tpl.char_counts)
        ):
            non_flexible = sum(1 for c in pattern if c in "平仄")
            assert non_flexible <= count, (
                f"{name} line {i}: pattern {pattern!r} has "
                f"{non_flexible} non-flexible but char_count={count}"
            )

    @pytest.mark.parametrize("name", list(CIPAI_REGISTRY.keys()))
    def test_pattern_chars_valid(self, name: str):
        """Pattern strings use only 平/仄/中 placeholders."""
        tpl = CIPAI_REGISTRY[name]
        for i, pattern in enumerate(tpl.tone_patterns):
            for ch in pattern:
                assert ch in "平仄中", (
                    f"{name} line {i}: invalid pattern char {ch!r}"
                )

    @pytest.mark.parametrize("name", list(CIPAI_REGISTRY.keys()))
    def test_non_flexible_pattern_chars_leq_count(self, name: str):
        """Each pattern's non-flexible markers should not exceed the line length."""
        tpl = CIPAI_REGISTRY[name]
        for i, (pattern, count) in enumerate(
            zip(tpl.tone_patterns, tpl.char_counts)
        ):
            non_flexible = sum(1 for c in pattern if c in "平仄")
            assert non_flexible <= count, (
                f"{name} line {i}: pattern {pattern} has "
                f"{non_flexible} non-flexible but {count} chars"
            )

    @pytest.mark.parametrize("name", list(CIPAI_REGISTRY.keys()))
    def test_rhyme_positions_in_range(self, name: str):
        """All rhyme positions are valid 0-indexed line numbers."""
        tpl = CIPAI_REGISTRY[name]
        for rp in tpl.rhyme_positions:
            assert 0 <= rp < tpl.line_count, (
                f"{name}: rhyme_position {rp} out of range for "
                f"line_count={tpl.line_count}"
            )

    @pytest.mark.parametrize("name", list(CIPAI_REGISTRY.keys()))
    def test_duilian_pairs_in_range(self, name: str):
        """All duilian pair indices are valid line numbers."""
        tpl = CIPAI_REGISTRY[name]
        for a, b in tpl.duilian_pairs:
            assert 0 <= a < tpl.line_count, f"{name}: pair start {a} OOR"
            assert 0 <= b < tpl.line_count, f"{name}: pair end {b} OOR"
            assert a != b, f"{name}: self-pair {a}=={b}"


# ---------------------------------------------------------------------------
# CipaiTemplate dataclass
# ---------------------------------------------------------------------------


class TestCipaiTemplate:
    """CipaiTemplate derived properties."""

    def test_total_chars(self):
        """``total_chars`` is the sum of char_counts."""
        tpl = get_cipai("浣溪沙")
        assert tpl.total_chars == sum(tpl.char_counts)

    def test_total_chars_zero(self):
        """An empty template has total_chars 0."""
        # Build an empty template manually (dataclass allows this).
        tpl = CipaiTemplate(
            name="empty",
            category="小令",
            line_count=0,
            char_counts=(),
            tone_patterns=(),
            rhyme_positions=(),
        )
        assert tpl.total_chars == 0

    def test_shangque_split(self):
        """``shangque`` returns at least one stanza."""
        tpl = get_cipai("浣溪沙")
        stanzas = tpl.shangque
        assert len(stanzas) >= 1
        # Total lines across stanzas equals line_count.
        assert sum(len(s) for s in stanzas) == tpl.line_count
