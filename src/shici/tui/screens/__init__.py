"""shici TUI screens.

Each screen is a Textual ``Screen`` subclass that is pushed onto the
app's screen stack. Screens are registered in :class:`shici.tui.app.ShiciApp`
through the ``SCREENS`` mapping.

Modules:
    home       — main menu and welcome banner.
    generate   — interactive generate form (delegates to CLI for LLM).
    check      — paste-a-poem prosody checker with colourised output.
    browse     — cipai (词牌) registry browser.
"""

from __future__ import annotations

from .home import HomeScreen
from .generate import GenerateScreen
from .check import CheckScreen
from .browse import BrowseScreen

__all__ = ["HomeScreen", "GenerateScreen", "CheckScreen", "BrowseScreen"]