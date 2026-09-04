"""Home screen — welcome banner and main menu.

Displays the project banner, version subtitle, and four navigation
buttons that switch to the other screens. Also reachable via the
``h`` global binding.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from ..app import BANNER
from .. import __version__

__all__ = ["HomeScreen"]


class HomeScreen(Screen):
    """Welcome screen with the main menu."""

    BINDINGS = [
        Binding("1", "go_generate", "生成"),
        Binding("2", "go_check", "校验"),
        Binding("3", "go_browse", "浏览"),
        Binding("4", "quit_app", "退出"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the home screen."""
        with Vertical(id="home-root"):
            yield Static(BANNER, id="banner")
            yield Static(
                f"shici v{__version__}  ·  古典诗词格律引擎",
                id="subtitle",
            )
            with Container(id="menu"):
                    yield Button("生成诗词  (g)", id="btn-generate", classes="menu-button")
                    yield Button("检查诗作  (c)", id="btn-check", classes="menu-button")
                    yield Button("浏览词牌  (b)", id="btn-browse", classes="menu-button")
                    yield Button("退出      (q)", id="btn-quit", classes="menu-button")
            yield Static(
                "键盘提示:  g 生成  ·  c 校验  ·  b 浏览  ·  h 首页  ·  q 退出",
                id="status-bar",
                classes="status-bar",
            )

    # -- Button handlers ---------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Route button presses to the matching screen action."""
        bid = event.button.id or ""
        if bid == "btn-generate":
            self.action_show_generate()
        elif bid == "btn-check":
            self.action_show_check()
        elif bid == "btn-browse":
            self.action_show_browse()
        elif bid == "btn-quit":
            self.app.exit()

    # -- Key-binding actions -----------------------------------------------------

    def action_go_generate(self) -> None:
        """Switch to the generate screen."""
        self.action_show_generate()

    def action_go_check(self) -> None:
        """Switch to the check screen."""
        self.action_show_check()

    def action_go_browse(self) -> None:
        """Switch to the browse screen."""
        self.action_show_browse()

    def action_quit_app(self) -> None:
        """Quit the application."""
        self.app.exit()

    # -- App-level wrappers (defined on ShiciApp) --------------------------------

    def action_show_generate(self) -> None:
        self.app.action_show_generate()

    def action_show_check(self) -> None:
        self.app.action_show_check()

    def action_show_browse(self) -> None:
        self.app.action_show_browse()