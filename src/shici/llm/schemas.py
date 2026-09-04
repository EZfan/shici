"""Pydantic schemas for structured LLM outputs in shici.

This module defines all the structured data types used to communicate
between the shici application and LLM backends. Every model is derived
from :class:`pydantic.BaseModel` so that ``instructor`` can validate
and re-parse model outputs against the schema.

The schemas cover three primary concerns:

1. **Generation** -- ``GeneratedPoem`` (shi forms), ``GeneratedCi``
   (ci forms), and individual ``PoemLine`` objects carrying tonal
   patterns and rhyme groups.
2. **Evaluation** -- ``PoemCritique`` carrying multi-axis scores plus
   qualitative commentary, highlights, and allusions.
3. **Encyclopaedic metadata** -- enums for ``PoemForm``, ``CipaiName``,
   ``ToneLevel`` and ``RhymeGroup`` (a subset of the 106 pingshui rhyme
   groups that covers the most common cases).
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PoemForm(str, Enum):
    """Classical poetry forms (诗体).

    Each value carries the Chinese name of the form so that it round-trips
    through prompts and UI display unchanged. The length requirements
    documented in the docstrings are enforced by callers and by the
    prosody engine, not by this enum itself.
    """

    JUEJU_5 = "五言绝句"  # 4 lines, 5 characters each
    JUEJU_7 = "七言绝句"  # 4 lines, 7 characters each
    LUSHI_5 = "五言律诗"  # 8 lines, 5 characters each
    LUSHI_7 = "七言律诗"  # 8 lines, 7 characters each
    CI = "词"  # ci (lyric) form, governed by a cipai template
    DUILIAN = "对联"  # antithetical couplet


class ToneLevel(str, Enum):
    """Tonal category of a single character.

    Following the traditional ping-ze (平仄) classification:

    * ``PING``       -- level tone (平)
    * ``ZE``         -- deflected tone (仄)
    * ``FLEXIBLE``   -- either tone permissible (中 / 韵)
    """

    PING = "平"
    ZE = "仄"
    FLEXIBLE = "中"


class RhymeGroup(str, Enum):
    """A subset of the 106 Pingshui rhyme groups (平水韵).

    This list is intentionally curated to cover the most frequently used
    rhyme groups across classical shi and ci. Extend as needed; the full
    106-group table lives in the prosody module.
    """

    # 上平声 (level tone group 1)
    DONG = "上平一东"
    DONG_2 = "上平二冬"
    JIANG = "上平三江"
    XIE = "上平四支"
    WEI = "上平五微"
    YU = "上平六鱼"
    HU = "上平七虞"
    QI = "上平八齐"
    JIA = "上平九佳"
    GAI = "上平十灰"

    # 下平声 (level tone group 2)
    XIAN = "下平一先"
    SHAO = "下平二萧"
    YOU = "下平三肴"
    MOU = "下平四豪"
    GENG = "下平五庚"
    MING = "下平六青"
    TONG = "下平七蒸"
    WANG = "下平八尤"
    QIU = "下平九覃"
    YUAN = "下平十盐"

    # 上声 (rising tone group -- sample)
    SONG = "上三肿"
    HAI = "上九蟹"
    YOU_2 = "上二十五有"

    # 去声 (departing tone group -- sample)
    SONG_2 = "去一送"
    HAN = "去十四旱"
    JIAN_2 = "去十六谏"


class CipaiName(str, Enum):
    """Names of the most commonly encountered ci (词) tune patterns.

    Each ci form has its own line-length pattern and rhyme scheme.
    The prosody engine enforces these constraints; the LLM is informed
    of the choice via the prompt template.
    """

    HUANXISHA = "浣溪沙"
    RUMLING = "如梦令"
    SHUIDIAOGETOU = "水调歌头"
    YUANXIA = "鹧鸪天"  # commonly romanised as "Zhe Gu Tian"
    QINGPINGYUE = "清平乐"
    DIANJIANGCHUN = "点绛唇"
    MANJINHONG = "满江红"
    YIJIANGNAN = "忆江南"  # commonly romanised as "Yi Jiang Nan"


# ---------------------------------------------------------------------------
# Core building blocks
# ---------------------------------------------------------------------------


class PoemLine(BaseModel):
    """A single line of a classical poem or lyric.

    Attributes:
        text:           The line text, one Chinese character per cell.
                        Must be the exact length required by the form
                        (e.g. 5 or 7 characters for jueju/lushi).
        tone_pattern:   The ping/ze tonal pattern of every character
                        in ``text``. Must have the same length as
                        ``text``. ``ToneLevel.FLEXIBLE`` denotes that
                        the character may be classified as either
                        ping or ze (a "中" tone).
        rhyme_group:    The rhyme group of the final character if the
                        line ends on a rhyme, otherwise ``None``. For
                        ci forms each line carries its own rhyme
                        status and is recorded in ``GeneratedCi``'s
                        ``rhyme_groups`` list.
    """

    text: str = Field(
        ...,
        min_length=1,
        description="Line text. Each Chinese character occupies one cell.",
    )
    tone_pattern: list[ToneLevel] = Field(
        default_factory=list,
        description="Tonal pattern aligned to each character in ``text``.",
    )
    rhyme_group: RhymeGroup | None = Field(
        default=None,
        description="Rhyme group of the final character, if any.",
    )


# ---------------------------------------------------------------------------
# Generation outputs
# ---------------------------------------------------------------------------


class GeneratedPoem(BaseModel):
    """A fully generated classical poem (shi, jueju, or lushi).

    The ``lines`` list must satisfy the constraints implied by ``form``:

    * ``JUEJU_*`` -- exactly 4 lines, each of length 5 or 7.
    * ``LUSHI_*`` -- exactly 8 lines, each of length 5 or 7.
    * ``CI`` / ``DUILIAN`` -- not used directly; use ``GeneratedCi``
      or construct a poem manually for those forms.

    The prosody engine performs the hard structural checks. This model
    only captures the data shape.
    """

    form: PoemForm = Field(..., description="The poem's literary form.")
    title: str | None = Field(
        default=None,
        description="Optional title. Most jueju/lushi are untitled.",
    )
    lines: list[PoemLine] = Field(
        default_factory=list,
        description="Ordered list of poem lines.",
    )
    theme: str = Field(
        ...,
        min_length=1,
        description="The thematic intent described in natural language.",
    )
    notes: str | None = Field(
        default=None,
        description="Optional creative intent / commentary from the LLM.",
    )


class GeneratedCi(BaseModel):
    """A generated ci (词) following a specific cipai tune pattern.

    ``rhyme_groups`` aligns one-to-one with ``lines`` -- set the entry
    to the rhyme group if the line ends on a rhyme, or ``None`` if it
    does not. The prosody engine exposes the canonical rhyme scheme
    of each cipai for validation.
    """

    cipai: CipaiName = Field(..., description="The tune pattern used.")
    title: str | None = Field(default=None, description="Optional title.")
    lines: list[PoemLine] = Field(
        default_factory=list,
        description="Ordered list of ci lines.",
    )
    rhyme_groups: list[RhymeGroup | None] = Field(
        default_factory=list,
        description="Per-line rhyme group; matches ``lines`` index-for-index.",
    )
    theme: str = Field(..., min_length=1, description="Thematic intent.")
    notes: str | None = Field(default=None, description="Optional notes.")


# ---------------------------------------------------------------------------
# Evaluation outputs
# ---------------------------------------------------------------------------


class PoemCritique(BaseModel):
    """Multi-axis critique of a generated poem.

    All four numeric scores are constrained to ``[0, 10]`` to keep the
    output comparable across runs. ``comments`` carries prose feedback
    per axis; ``highlights`` and ``allusions`` are surfaced separately
    so the UI can present them in dedicated panels.
    """

    overall_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Composite judgement, 0-10.",
    )
    prosody_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Adherence to tonal and rhyming patterns.",
    )
    imagery_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Quality and coherence of imagery.",
    )
    originality_score: float = Field(
        ...,
        ge=0,
        le=10,
        description="Freshness and inventiveness.",
    )
    comments: list[str] = Field(
        default_factory=list,
        description="Free-form critique, one bullet per item.",
    )
    highlights: list[str] = Field(
        default_factory=list,
        description="Standout lines worth quoting.",
    )
    allusions: list[str] = Field(
        default_factory=list,
        description="Allusions to canonical works identified in the poem.",
    )


# ---------------------------------------------------------------------------
# Literal aliases for prompt authors
# ---------------------------------------------------------------------------

# Convenient literal aliases. Use these in ``Literal[...]`` annotations
# where an Enum would be over-engineered.

PoemFormLiteral = Literal[
    "五言绝句",
    "七言绝句",
    "五言律诗",
    "七言律诗",
    "词",
    "对联",
]

ToneLevelLiteral = Literal["平", "仄", "中"]


__all__ = [
    "CipaiName",
    "GeneratedCi",
    "GeneratedPoem",
    "PoemCritique",
    "PoemForm",
    "PoemFormLiteral",
    "PoemLine",
    "RhymeGroup",
    "ToneLevel",
    "ToneLevelLiteral",
]
