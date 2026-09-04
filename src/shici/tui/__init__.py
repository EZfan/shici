"""shici TUI — Textual interactive interface for classical Chinese poetry.

The TUI provides four screens:
    - HomeScreen   — main menu and welcome banner.
    - GenerateScreen — form for poem generation (CLI-driven when LLM is required).
    - CheckScreen  — paste a poem, run prosody checks, view coloured tone output.
    - BrowseScreen — browse the cipai (词牌) registry.

Run via:

    python -m shici tui
    # or
    shici tui
"""

from __future__ import annotations

from .app import ShiciApp, run

__all__ = ["ShiciApp", "run"]