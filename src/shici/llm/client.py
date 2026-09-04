"""LLM client for the shici project.

This module is a thin, opinionated wrapper around
``instructor`` + ``litellm`` that produces structured outputs for
classical Chinese poetry generation.

Why these libraries?

* ``litellm`` exposes a single uniform interface to many backends
  (OpenAI, Anthropic, DeepSeek, Qwen DashScope, local Ollama, ...)
  via standard environment variables -- exactly what a CLI tool like
  ``shici`` needs.
* ``instructor`` patches a chosen ``litellm`` mode to validate the
  model's response against a Pydantic model and to *re-ask* the
  model on validation failure, up to ``max_retries`` times.

The default backend is **DeepSeek** (``deepseek-chat``) -- it is an
OpenAI-compatible API, has generous Chinese-language quality, and
supports JSON-mode / function calling for structured output.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, TypeVar

import instructor
from jinja2 import Environment, FileSystemLoader, select_autoescape
from litellm import completion
from pydantic import BaseModel

from .schemas import (
    GeneratedCi,
    GeneratedPoem,
    PoemCritique,
    PoemForm,
    RhymeGroup,
)

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_PROMPTS_DIR = Path(__file__).parent / "prompts"


# ---------------------------------------------------------------------------
# Jinja environment
# ---------------------------------------------------------------------------


def _build_jinja_env() -> Environment:
    """Return a Jinja2 environment rooted at the ``prompts/`` directory."""
    return Environment(
        loader=FileSystemLoader(str(_PROMPTS_DIR)),
        autoescape=select_autoescape(disabled_extensions=("j2",), default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )


_JINJA = _build_jinja_env()


def render_prompt(template_name: str, **context: Any) -> str:
    """Render a prompt template by filename (e.g. ``system.j2``)."""
    template = _JINJA.get_template(template_name)
    return template.render(**context)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


# Map of supported backend identifiers to the litellm model name we use by
# default. litellm routes the request based on the model string prefix, so
# this is the *only* place that knows about vendor naming.
_BACKEND_DEFAULTS: dict[str, dict[str, str | None]] = {
    "deepseek": {
        "model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
    },
    "qwen": {
        "model": "qwen-plus",
        "env_key": "DASHSCOPE_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    },
    "openai": {
        "model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "base_url": None,
    },
    "anthropic": {
        "model": "claude-haiku-4-5",
        "env_key": "ANTHROPIC_API_KEY",
        "base_url": None,
    },
    "ollama": {
        "model": "ollama/qwen2.5:7b",
        "env_key": None,
        "base_url": "http://localhost:11434",
    },
}


class LLMConfig:
    """LLM backend configuration.

    All fields have sensible defaults that pull from environment
    variables when ``None`` is passed. Construct with a known
    ``backend`` and override whatever you need.
    """

    def __init__(
        self,
        backend: str = "deepseek",
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.8,
        max_tokens: int = 1024,
    ) -> None:
        defaults = _BACKEND_DEFAULTS.get(backend, _BACKEND_DEFAULTS["deepseek"])

        self.backend: str = backend
        self.model: str = model or defaults["model"]  # type: ignore[assignment]
        self.api_key: str | None = api_key or self._lookup_key(defaults["env_key"])  # type: ignore[arg-type]
        self.base_url: str | None = (
            base_url if base_url is not None else defaults["base_url"]  # type: ignore[assignment]
        )
        self.temperature: float = temperature
        self.max_tokens: int = max_tokens

    @staticmethod
    def _lookup_key(env_var: str | None) -> str:
        """Read an API key from the given environment variable name."""
        if env_var is None:
            return ""
        return os.environ.get(env_var, "")

    # -- dict-shaped helpers (litellm and instructor both expect dicts) -----

    def as_litellm_kwargs(self) -> dict[str, Any]:
        """Return the kwargs dict ready to splat into ``litellm.completion``."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return kwargs

    def __repr__(self) -> str:  # pragma: no cover -- trivial
        return (
            f"LLMConfig(backend={self.backend!r}, model={self.model!r}, "
            f"temperature={self.temperature}, max_tokens={self.max_tokens})"
        )


# ---------------------------------------------------------------------------
# Instructor client factory
# ---------------------------------------------------------------------------


# Cache instructor clients per (model, base_url) tuple so we don't
# rebuild the wrapper for every call. The wrapper is essentially free
# to construct, but caching makes it cheap to use as a module singleton.
_CLIENT_CACHE: dict[tuple[str, str | None], instructor.Instructor] = {}


def get_client(config: LLMConfig | None = None) -> instructor.Instructor:
    """Return a configured :class:`instructor.Instructor` client.

    The returned client is patched against ``litellm`` and configured
    with the supplied (or default) backend credentials. The result is
    cached per ``(model, base_url)`` so repeated calls are cheap.
    """
    cfg = config or LLMConfig()
    cache_key = (cfg.model, cfg.base_url)
    cached = _CLIENT_CACHE.get(cache_key)
    if cached is not None:
        return cached

    client = instructor.from_litellm(completion)
    _CLIENT_CACHE[cache_key] = client
    return client


def reset_client_cache() -> None:
    """Clear the instructor-client cache (mainly for tests)."""
    _CLIENT_CACHE.clear()


# ---------------------------------------------------------------------------
# Core generation helpers
# ---------------------------------------------------------------------------


def _messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
    """Build the openai-style chat messages list."""
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def generate_structured(
    response_model: type[T],
    system_prompt: str,
    user_prompt: str,
    config: LLMConfig | None = None,
    max_retries: int = 3,
    **extra_overrides: Any,
) -> T:
    """Generate a structured object from the LLM with retry on validation failure.

    Args:
        response_model: The Pydantic model class describing the desired output.
        system_prompt:  The system message -- typically ``render_prompt("system.j2")``.
        user_prompt:    The user message -- typically a rendered template.
        config:         Optional :class:`LLMConfig`; defaults are used when ``None``.
        max_retries:    Maximum number of times ``instructor`` will re-prompt
                        the model when its response fails to validate against
                        ``response_model``. Defaults to 3.
        **extra_overrides: Forwarded to ``litellm.completion`` and override
                            matching fields from ``config``.

    Returns:
        A validated instance of ``response_model``.
    """
    cfg = config or LLMConfig()
    client = get_client(cfg)

    kwargs = cfg.as_litellm_kwargs()
    kwargs.update(extra_overrides)
    kwargs["messages"] = _messages(system_prompt, user_prompt)

    # instructor patches ``messages`` parsing & validation on top of litellm.
    return client.chat.completions.create(
        response_model=response_model,
        max_retries=max_retries,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# High-level poetry operations
# ---------------------------------------------------------------------------


# Per-form prompts and a few sensible defaults. ``line_length`` is
# derived from the form name ("JUEJU_5" -> 5, etc.). The default rhyme
# group is intentionally ``None`` -- letting the model pick is usually
# better than forcing a specific rhyme and producing awkward phrasing.
_FORM_LINE_LENGTH: dict[PoemForm, int | None] = {
    PoemForm.JUEJU_5: 5,
    PoemForm.JUEJU_7: 7,
    PoemForm.LUSHI_5: 5,
    PoemForm.LUSHI_7: 7,
    PoemForm.CI: None,
    PoemForm.DUILIAN: None,
}


def _form_to_text(form: PoemForm) -> str:
    """Return the Chinese display name for a :class:`PoemForm`."""
    return form.value


def generate_jueju(
    theme: str,
    form: PoemForm = PoemForm.JUEJU_5,
    *,
    title: str | None = None,
    rhyme_group: RhymeGroup | None = None,
    keywords: list[str] | None = None,
    reference: str | None = None,
    config: LLMConfig | None = None,
    max_retries: int = 3,
) -> GeneratedPoem:
    """Generate a jueju (绝句) with the LLM and return a :class:`GeneratedPoem`."""
    system_prompt = render_prompt("system.j2")
    user_prompt = render_prompt(
        "generate_jueju.j2",
        form=_form_to_text(form),
        theme=theme,
        title=title,
        rhyme_group=rhyme_group.value if rhyme_group else None,
        keywords=keywords,
        reference=reference,
    )
    return generate_structured(
        GeneratedPoem,
        system_prompt,
        user_prompt,
        config=config,
        max_retries=max_retries,
    )


def generate_lushi(
    theme: str,
    form: PoemForm = PoemForm.LUSHI_7,
    *,
    title: str | None = None,
    rhyme_group: RhymeGroup | None = None,
    keywords: list[str] | None = None,
    reference: str | None = None,
    config: LLMConfig | None = None,
    max_retries: int = 3,
) -> GeneratedPoem:
    """Generate a lushi (律诗) with the LLM and return a :class:`GeneratedPoem`."""
    system_prompt = render_prompt("system.j2")
    user_prompt = render_prompt(
        "generate_lushi.j2",
        form=_form_to_text(form),
        theme=theme,
        title=title,
        rhyme_group=rhyme_group.value if rhyme_group else None,
        keywords=keywords,
        reference=reference,
    )
    return generate_structured(
        GeneratedPoem,
        system_prompt,
        user_prompt,
        config=config,
        max_retries=max_retries,
    )


# ---------------------------------------------------------------------------
# Revision
# ---------------------------------------------------------------------------


def generate_revision(
    current_poem: GeneratedPoem,
    feedback: list[str],
    config: LLMConfig | None = None,
    max_retries: int = 3,
) -> GeneratedPoem:
    """Generate a revised poem that addresses ``feedback`` items.

    The prosody engine feeds back concrete rule violations; this
    function passes those messages verbatim to the LLM along with
    the current poem so it can address them in the next pass.
    """
    system_prompt = render_prompt("system.j2")
    user_prompt = render_prompt(
        "revise.j2",
        poem=current_poem,
        feedback=feedback,
    )
    return generate_structured(
        GeneratedPoem,
        system_prompt,
        user_prompt,
        config=config,
        max_retries=max_retries,
    )


# ---------------------------------------------------------------------------
# Critique & annotation
# ---------------------------------------------------------------------------


def critique_poem(
    poem: GeneratedPoem,
    config: LLMConfig | None = None,
    max_retries: int = 3,
) -> PoemCritique:
    """Return a multi-axis critique of ``poem`` from the LLM."""
    system_prompt = render_prompt("system.j2")
    user_prompt = render_prompt("critique.j2", poem=poem)
    return generate_structured(
        PoemCritique,
        system_prompt,
        user_prompt,
        config=config,
        max_retries=max_retries,
    )


def annotate_poem(
    poem: GeneratedPoem,
    config: LLMConfig | None = None,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Return a line-by-line annotation payload from the LLM.

    The annotation schema is intentionally returned as ``dict`` --
    the rich structure (per-line lexical / allusions / imagery
    blocks) does not yet warrant a dedicated Pydantic model. This
    keeps the iteration loop fast while still providing structured
    data for the TUI to display.
    """
    system_prompt = render_prompt("system.j2")
    user_prompt = render_prompt("annotate.j2", poem=poem)

    # We pin base temperature a little lower for annotation, which is
    # a more deterministic, factual task. Callers can override via
    # their own LLMConfig.
    cfg = config or LLMConfig()

    client = get_client(cfg)
    kwargs = cfg.as_litellm_kwargs()
    kwargs["messages"] = _messages(system_prompt, user_prompt)

    # ``client.chat.completions.create_raw`` returns the raw dict so we
    # can let the prompt specify a free-form structure. This is a
    # deliberate departure from the strict ``response_model`` path.
    response = client.chat.completions.create(
        response_model=None,  # type: ignore[arg-type]
        max_retries=max_retries,
        **kwargs,
    )

    # The library returns a pydantic model when ``response_model`` is
    # ``None`` -- normalise to a plain dict for ergonomic use.
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if isinstance(response, dict):
        return response
    return dict(response)  # pragma: no cover -- defensive fallback


# ---------------------------------------------------------------------------
# Re-exports
# ---------------------------------------------------------------------------


__all__ = [
    "LLMConfig",
    "annotate_poem",
    "completion",
    "critique_poem",
    "generate_jueju",
    "generate_lushi",
    "generate_revision",
    "generate_structured",
    "get_client",
    "render_prompt",
    "reset_client_cache",
    # Re-exported Pydantic models for convenience:
    "GeneratedCi",
    "GeneratedPoem",
    "PoemCritique",
    "PoemForm",
    "RhymeGroup",
]
