"""Prosody (格律) engine — tone classification, rhyme grouping, structure checking.

This package vendors code from gelv-poetry (https://github.com/chenmisss/gelv-poetry)
under MIT License. See data/LICENSE-gelv-poetry.txt for the full text.
"""

from __future__ import annotations

from .classifier import Tone, ToneClassifier, classify_character, classify_line
from .rhyme import RhymeBook, RhymeGroup, classify_rhyme, lookup_rhyme
from .checker import (
    CheckResult,
    Issue,
    IssueLevel,
    PoetryForm,
    check_jueju,
    check_lushi,
    check_poem,
    check_duilian,
)
from .templates import (
    CIPAI_REGISTRY,
    CipaiTemplate,
    get_cipai,
    list_cipai,
)
from .duilian import (
    check_antithesis,
    antithesis_score,
)

__all__ = [
    "Tone",
    "ToneClassifier",
    "classify_character",
    "classify_line",
    "RhymeBook",
    "RhymeGroup",
    "classify_rhyme",
    "lookup_rhyme",
    "CheckResult",
    "Issue",
    "IssueLevel",
    "PoetryForm",
    "check_jueju",
    "check_lushi",
    "check_poem",
    "check_duilian",
    "CIPAI_REGISTRY",
    "CipaiTemplate",
    "get_cipai",
    "list_cipai",
    "check_antithesis",
    "antithesis_score",
]