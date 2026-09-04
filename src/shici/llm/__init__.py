"""LLM integration for the shici project.

This sub-package bundles three concerns:

1. ``schemas``   -- Pydantic models describing structured I/O
                     (GeneratedPoem, GeneratedCi, PoemCritique, ...).
2. ``prompts/``  -- Jinja2 templates that render system + per-task
                     user messages.
3. ``client``    -- The :func:`generate_structured` entrypoint, plus
                     :class:`LLMConfig` and high-level helpers for
                     jueju, lushi, revision, critique, and annotation.
"""

from __future__ import annotations

from .client import (
    LLMConfig,
    annotate_poem,
    critique_poem,
    generate_jueju,
    generate_lushi,
    generate_revision,
    generate_structured,
    get_client,
    render_prompt,
    reset_client_cache,
)
from .schemas import (
    CipaiName,
    GeneratedCi,
    GeneratedPoem,
    PoemCritique,
    PoemForm,
    PoemLine,
    RhymeGroup,
    ToneLevel,
)

__all__ = [
    "CipaiName",
    "GeneratedCi",
    "GeneratedPoem",
    "LLMConfig",
    "PoemCritique",
    "PoemForm",
    "PoemLine",
    "RhymeGroup",
    "ToneLevel",
    "annotate_poem",
    "critique_poem",
    "generate_jueju",
    "generate_lushi",
    "generate_revision",
    "generate_structured",
    "get_client",
    "render_prompt",
    "reset_client_cache",
]
