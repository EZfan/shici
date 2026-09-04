"""Prosody (格律) engine — tone classification, rhyme grouping, structure checking.

This package vendors code from gelv-poetry (https://github.com/chenmisss/gelv-poetry)
under MIT License. See data/LICENSE-gelv-poetry.txt for the full text.
"""

from __future__ import annotations

from .checker import (
    CheckResult,
    Issue,
    IssueLevel,
    PoetryForm,
    check_duilian,
    check_jueju,
    check_lushi,
    check_poem,
)
from .classifier import Tone, ToneClassifier, classify_character, classify_line
from .duilian import (
    antithesis_score,
    check_antithesis,
)
from .rhyme import RhymeBook, RhymeGroup, classify_rhyme, lookup_rhyme
from .templates import (
    CIPAI_REGISTRY,
    CipaiTemplate,
    get_cipai,
    list_cipai,
)

__all__ = [
    "CIPAI_REGISTRY",
    "CheckResult",
    "CipaiTemplate",
    "Issue",
    "IssueLevel",
    "PoetryForm",
    "RhymeBook",
    "RhymeGroup",
    "Tone",
    "ToneClassifier",
    "antithesis_score",
    "check_antithesis",
    "check_duilian",
    "check_jueju",
    "check_lushi",
    "check_poem",
    "classify_character",
    "classify_line",
    "classify_rhyme",
    "get_cipai",
    "list_cipai",
    "lookup_rhyme",
]
