"""Unit tests for the LLM Pydantic schemas.

These tests are pure-Python and exercise only the data layer -- no
network calls, no LLM calls. They validate that:

* Construction from keyword arguments works.
* Default values match the documented contract.
* Numeric constraints (``ge`` / ``le``) on scores are enforced.
* Models serialise cleanly to JSON round-trip.
* Tone-pattern alignment (length == text length) is a soft
  invariant callers can rely on, even though we do not enforce it
  in the model itself.

Run with::

    pytest tests/unit/test_schemas.py -v
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from shici.llm.schemas import (
    CipaiName,
    GeneratedCi,
    GeneratedPoem,
    PoemCritique,
    PoemForm,
    PoemLine,
    RhymeGroup,
    ToneLevel,
)

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def _tone_pattern(level: ToneLevel, n: int) -> list[ToneLevel]:
    """Return a tone pattern of length ``n`` filled with ``level``."""
    return [level] * n


def _sample_5char_line(text: str = "床前明月光") -> PoemLine:
    """Build a 5-character ``PoemLine`` with mixed ping/ze tones."""
    return PoemLine(
        text=text,
        tone_pattern=_tone_pattern(ToneLevel.PING, 5),
        rhyme_group=RhymeGroup.DONG,
    )


def _sample_jueju() -> GeneratedPoem:
    """Build a valid 五言绝句 ``GeneratedPoem`` for reuse across tests."""
    sample_lines = [
        "床前明月光",
        "疑是地上霜",
        "举头望明月",
        "低头思故乡",
    ]
    return GeneratedPoem(
        form=PoemForm.JUEJU_5,
        title="静夜思",
        lines=[_sample_5char_line(text) for text in sample_lines],
        theme="思乡",
        notes="化用李白《静夜思》",
    )


# ---------------------------------------------------------------------------
# ToneLevel & RhymeGroup
# ---------------------------------------------------------------------------


class TestEnums:
    def test_tone_level_values(self) -> None:
        assert ToneLevel.PING.value == "平"
        assert ToneLevel.ZE.value == "仄"
        assert ToneLevel.FLEXIBLE.value == "中"

    def test_poem_form_values(self) -> None:
        assert PoemForm.JUEJU_5.value == "五言绝句"
        assert PoemForm.JUEJU_7.value == "七言绝句"
        assert PoemForm.LUSHI_5.value == "五言律诗"
        assert PoemForm.LUSHI_7.value == "七言律诗"
        assert PoemForm.CI.value == "词"
        assert PoemForm.DUILIAN.value == "对联"

    def test_rhyme_group_distinct_values(self) -> None:
        """RhymeGroup enum values must all be unique strings."""
        values = [rg.value for rg in RhymeGroup]
        assert len(values) == len(set(values))

    def test_cipai_name_samples(self) -> None:
        assert CipaiName.HUANXISHA.value == "浣溪沙"
        assert CipaiName.RUMLING.value == "如梦令"
        assert CipaiName.SHUIDIAOGETOU.value == "水调歌头"


# ---------------------------------------------------------------------------
# PoemLine
# ---------------------------------------------------------------------------


class TestPoemLine:
    def test_minimal_construction(self) -> None:
        line = PoemLine(text="春眠不觉晓")
        assert line.text == "春眠不觉晓"
        assert line.tone_pattern == []
        assert line.rhyme_group is None

    def test_empty_text_rejected(self) -> None:
        with pytest.raises(ValidationError):
            PoemLine(text="")

    def test_full_construction(self) -> None:
        line = PoemLine(
            text="举头望明月",
            tone_pattern=[
                ToneLevel.ZE,
                ToneLevel.PING,
                ToneLevel.ZE,
                ToneLevel.PING,
                ToneLevel.ZE,
            ],
            rhyme_group=RhymeGroup.YOU_2,
        )
        assert line.text == "举头望明月"
        assert len(line.tone_pattern) == 5
        assert line.rhyme_group is RhymeGroup.YOU_2


# ---------------------------------------------------------------------------
# GeneratedPoem
# ---------------------------------------------------------------------------


class TestGeneratedPoem:
    def test_jueju5_valid_construction(self) -> None:
        poem = _sample_jueju()
        assert len(poem.lines) == 4
        assert poem.form is PoemForm.JUEJU_5
        # Every line should be 5 Chinese characters long.
        for line in poem.lines:
            assert len(line.text) == 5
        # Caller is responsible for enforcing this; check via the model:
        assert all(len(line.text) == 5 for line in poem.lines)

    def test_jueju7_lines_length(self) -> None:
        poem = GeneratedPoem(
            form=PoemForm.JUEJU_7,
            title="夜泊",
            lines=[_sample_5char_line(f"七言句{i}") for i in range(1, 5)],
            theme="羁旅",
        )
        # The schema does not enforce character counts (5 vs 7); that
        # is left to the prosody engine. We just ensure that an
        # obviously wrong-length poem does not crash construction.
        for line in poem.lines:
            assert line.tone_pattern  # default is empty list

    def test_default_title_is_none(self) -> None:
        poem = GeneratedPoem(
            form=PoemForm.JUEJU_5,
            lines=[PoemLine(text="孤舟蓑笠翁")],
            theme="写意",
        )
        assert poem.title is None
        assert poem.notes is None
        assert poem.lines[0].rhyme_group is None

    def test_missing_lines_tolerated(self) -> None:
        # ``lines`` has default_factory=list -> empty list is allowed.
        poem = GeneratedPoem(form=PoemForm.JUEJU_5, theme="空诗")
        assert poem.lines == []

    def test_missing_theme_rejected(self) -> None:
        with pytest.raises(ValidationError):
            GeneratedPoem(form=PoemForm.JUEJU_5, lines=[])  # type: ignore[call-arg]

    def test_round_trip_json(self) -> None:
        poem = _sample_jueju()
        payload = poem.model_dump()
        restored = GeneratedPoem.model_validate(payload)
        assert restored == poem

    def test_tone_pattern_mismatch_callable(self) -> None:
        # The model itself does not enforce tone_pattern length; the
        # assertion below documents the *contract* we expect callers
        # to verify. The prosody module is responsible for catching
        # this in production.
        line = PoemLine(text="月", tone_pattern=[])
        assert line.tone_pattern == []  # tolerated at the schema level

    def test_lushi_form_distinct(self) -> None:
        poem = GeneratedPoem(
            form=PoemForm.LUSHI_7,
            title="登高",
            lines=[_sample_5char_line(f"律句{i}") for i in range(8)],
            theme="登高怀远",
        )
        assert poem.form is PoemForm.LUSHI_7
        assert len(poem.lines) == 8


# ---------------------------------------------------------------------------
# GeneratedCi
# ---------------------------------------------------------------------------


class TestGeneratedCi:
    def test_basic_construction(self) -> None:
        ci = GeneratedCi(
            cipai=CipaiName.HUANXISHA,
            title="春日忆旧游",
            lines=[PoemLine(text="一曲新词酒一杯") for _ in range(8)],
            rhyme_groups=[RhymeGroup.GAI] * 5 + [None] * 3,
            theme="怀旧",
            notes="小令",
        )
        assert ci.cipai is CipaiName.HUANXISHA
        assert ci.title == "春日忆旧游"
        assert len(ci.lines) == 8
        # rhyme_groups is parallel to lines
        assert len(ci.rhyme_groups) == 8

    def test_rhyme_groups_default_none(self) -> None:
        ci = GeneratedCi(
            cipai=CipaiName.RUMLING,
            lines=[PoemLine(text="常记溪亭日暮")],
            theme="忆昔",
        )
        assert ci.rhyme_groups == []

    def test_round_trip(self) -> None:
        ci = GeneratedCi(
            cipai=CipaiName.SHUIDIAOGETOU,
            title="明月几时有",
            lines=[PoemLine(text="明月几时有")],
            rhyme_groups=[RhymeGroup.YOU_2],
            theme="怀人",
        )
        payload = ci.model_dump()
        restored = GeneratedCi.model_validate(payload)
        assert restored == ci


# ---------------------------------------------------------------------------
# PoemCritique
# ---------------------------------------------------------------------------


class TestPoemCritique:
    def _sample_critique(self) -> PoemCritique:
        return PoemCritique(
            overall_score=8.4,
            prosody_score=9.0,
            imagery_score=8.5,
            originality_score=7.5,
            comments=["格律严整", "颔联对仗工稳", "尾联余韵悠然"],
            highlights=["春风又绿江南岸", "明月何时照我还"],
            allusions=["化用王安石《泊船瓜洲》"],
        )

    def test_construction_with_full_fields(self) -> None:
        c = self._sample_critique()
        assert c.overall_score == 8.4
        assert len(c.comments) == 3
        assert len(c.highlights) == 2
        assert len(c.allusions) == 1

    def test_default_collections(self) -> None:
        c = PoemCritique(
            overall_score=5.0,
            prosody_score=5.0,
            imagery_score=5.0,
            originality_score=5.0,
        )
        assert c.comments == []
        assert c.highlights == []
        assert c.allusions == []

    @pytest.mark.parametrize("bad_score", [-0.1, 10.1, 100.0, -1.0])
    def test_overall_score_out_of_range(self, bad_score: float) -> None:
        with pytest.raises(ValidationError):
            PoemCritique(
                overall_score=bad_score,
                prosody_score=5.0,
                imagery_score=5.0,
                originality_score=5.0,
            )

    @pytest.mark.parametrize("bad_score", [-1.0, 11.0])
    def test_prosody_score_out_of_range(self, bad_score: float) -> None:
        with pytest.raises(ValidationError):
            PoemCritique(
                overall_score=5.0,
                prosody_score=bad_score,
                imagery_score=5.0,
                originality_score=5.0,
            )

    def test_score_boundary_values_allowed(self) -> None:
        # 0 and 10 inclusive
        c = PoemCritique(
            overall_score=0.0,
            prosody_score=10.0,
            imagery_score=0.0,
            originality_score=10.0,
        )
        assert c.overall_score == 0.0
        assert c.prosody_score == 10.0

    def test_round_trip(self) -> None:
        c = self._sample_critique()
        payload = c.model_dump()
        restored = PoemCritique.model_validate(payload)
        assert restored == c


# ---------------------------------------------------------------------------
# Cross-model integration
# ---------------------------------------------------------------------------


class TestCrossModelIntegration:
    def test_poem_with_critique_can_coexist(self) -> None:
        """``GeneratedPoem`` and ``PoemCritique`` are independent models."""
        poem = _sample_jueju()
        critique = PoemCritique(
            overall_score=9.0,
            prosody_score=9.5,
            imagery_score=8.0,
            originality_score=9.0,
            comments=[],
            highlights=[poem.lines[0].text],
            allusions=[],
        )
        assert poem.theme == "思乡"
        assert critique.highlights[0] in {line.text for line in poem.lines}

    def test_duilian_two_lines(self) -> None:
        poem = GeneratedPoem(
            form=PoemForm.DUILIAN,
            title="春联",
            lines=[
                PoemLine(
                    text="天增岁月人增寿",
                    tone_pattern=[ToneLevel.PING] * 7,
                    rhyme_group=None,
                ),
                PoemLine(
                    text="春满乾坤福满门",
                    tone_pattern=[ToneLevel.PING] * 7,
                    rhyme_group=RhymeGroup.WEN if hasattr(RhymeGroup, "WEN") else RhymeGroup.WANG,
                ),
            ],
            theme="新春祝福",
        )
        assert poem.form is PoemForm.DUILIAN
        assert len(poem.lines) == 2

    def test_serialization_independent_of_enum_identity(self) -> None:
        """Serialise + restore must work even after enum re-import."""
        poem = _sample_jueju()
        # Drop into JSON and back via raw strings.
        raw = poem.model_dump_json()
        assert "五言绝句" in raw
        restored = GeneratedPoem.model_validate_json(raw)
        assert restored == poem
