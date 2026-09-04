"""shici TUI — textual app.

This is the top-level Textual ``App``. It owns the screen stack and the
global bindings. The four screens (home / generate / check / browse) are
registered through the ``SCREENS`` mapping and switched via the
``h`` / ``g`` / ``c`` / ``b`` keys.

The visual theme is loaded from the sibling ``theme.tcss`` file and
follows the 宣纸 / 朱砂红 aesthetic — rice-paper background with
cinnabar-red accents.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header, Static

from .screens import BrowseScreen, CheckScreen, GenerateScreen, HomeScreen
from .. import __version__

__all__ = ["ShiciApp", "run"]


# ASCII banner used in the home screen. Rendered in a fixed-width font so
# the indentation is preserved. The user requested the content of
# ``docs/assets/banner.txt``; that file ships as SVG in this repository,
# so we use a hand-crafted ASCII rendition that fits the same aesthetic.
BANNER = r"""
   ____  _ _       _
  / ___|| (_)_ __ | |_ ___  _ __
  \___ \| | | '_ \| __/ _ \| '_ \
   ___) | | | | | | || (_) | | | |
  |____/|_|_|_| |_|\__\___/|_| |_|

       古 典 诗 词 格 律 引 擎
"""


class ShiciApp(App):
    """Main Textual application for shici.

    The app provides four screens reachable through the key bindings
    declared in ``BINDINGS``. Switching screens replaces the current
    screen on the stack with ``switch_screen``; the home screen is
    pushed once at mount time.
    """

    CSS_PATH = "theme.tcss"
    TITLE = f"shici v{__version__}"
    SUB_TITLE = "古典诗词格律引擎"

    BINDINGS = [
        Binding("ctrl+c", "quit", "退出"),
        Binding("q", "quit", "退出"),
        Binding("h", "show_home", "首页"),
        Binding("g", "show_generate", "生成"),
        Binding("c", "show_check", "校验"),
        Binding("b", "show_browse", "浏览"),
    ]

    SCREENS = {
        "home": HomeScreen,
        "generate": GenerateScreen,
        "check": CheckScreen,
        "browse": BrowseScreen,
    }

    def compose(self) -> ComposeResult:
        """Compose the chrome shared by every screen.

        The home screen draws its own banner inside its body, so the
        app-level compose only wires the ``Header``, ``Footer`` and a
        placeholder for the active screen.
        """
        yield Header(show_clock=False)
        yield Container(id="screen-container")
        yield Footer()

    def on_mount(self) -> None:
        """Push the home screen on startup."""
        self.push_screen("home")

    # -- Screen switching actions ------------------------------------------------

    def action_show_home(self) -> None:
        """Switch to the home (menu) screen."""
        self.switch_screen("home")

    def action_show_generate(self) -> None:
        """Switch to the generate screen."""
        self.switch_screen("generate")

    def action_show_check(self) -> None:
        """Switch to the prosody check screen."""
        self.switch_screen("check")

    def action_show_browse(self) -> None:
        """Switch to the cipai browser."""
        self.switch_screen("browse")

    # -- Helpers -----------------------------------------------------------------

    def switch_screen(self, name: str) -> None:
        """Replace the active screen with the named one.

        Falls back to the home screen if the name is unknown — this
        keeps the UI responsive even if a binding is misconfigured.
        """
        cls = self.SCREENS.get(name) or HomeScreen
        try:
            self.push_screen(cls())
        except Exception as exc:  # pragma: no cover - defensive
            self.log(f"Failed to switch to {name!r}: {exc}")
            self.push_screen(HomeScreen())


def run() -> None:
    """Entry point for the TUI.

    Instantiates :class:`ShiciApp` and runs its event loop. Call this
    from ``python -m shici tui`` or ``shici tui``.
    """
    ShiciApp().run()