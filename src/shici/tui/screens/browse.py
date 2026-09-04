"""Browse screen — cipai (词牌) registry browser.

A two-pane layout:

    +----------------------------------+---------------------------+
    | cipai list (ListView)            | selected cipai details    |
    |                                  |  - 字数 / 句数            |
    |                                  |  - 平仄模式                |
    |                                  |  - 韵位                    |
    |                                  |  - 代表作品                |
    +----------------------------------+---------------------------+

If the prosody engine (or its data files) are unavailable the screen
falls back to an explanatory notice instead of crashing.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

__all__ = ["BrowseScreen"]


class BrowseScreen(Screen):
    """Browse the cipai registry."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "返回"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the browse screen."""
        with Vertical(id="browse-root"):
            yield Static("词牌浏览", id="title")
            yield Static(
                "在左侧选择词牌,右侧查看平仄、字数、代表作品等详情。",
                classes="form-label",
            )
            with Horizontal(id="browse-body"):
                yield ListView(id="cipai-list")
                yield Static("", id="cipai-detail", classes="detail-panel")
            yield Static(
                "就绪。",
                id="status-bar",
                classes="status-bar",
            )

    def on_mount(self) -> None:
        """Populate the cipai list."""
        try:
            from ...prosody import get_cipai, list_cipai  # type: ignore
        except Exception as exc:
            self._render_unavailable(exc)
            return

        names = list_cipai()
        lv = self.query_one("#cipai-list", ListView)
        for name in names:
            lv.append(ListItem(Static(name), id=f"cipai-{name}"))

        if not names:
            self._set_detail("[!] 未发现任何词牌模板。")
            return

        # Default selection
        lv.index = 0
        self._show_cipai(names[0], get_cipai)

    # -- Selection handler -------------------------------------------------------

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Update the detail panel when the highlight changes."""
        if event.item is None:
            return
        # Recover the cipai name from the ListItem id ("cipai-<name>").
        item_id = event.item.id or ""
        if not item_id.startswith("cipai-"):
            return
        name = item_id[len("cipai-") :]
        try:
            from ...prosody import get_cipai  # type: ignore
        except Exception as exc:
            self._render_unavailable(exc)
            return
        self._show_cipai(name, get_cipai)

    # -- Rendering ---------------------------------------------------------------

    def _show_cipai(self, name: str, get_cipai) -> None:
        """Render the detail panel for the named cipai."""
        try:
            tpl = get_cipai(name)
        except KeyError as exc:
            self._set_detail(f"[!] {exc}")
            return
        except Exception as exc:
            self._set_detail(f"[!] 加载词牌失败: {exc}")
            return

        lines: list[str] = []
        lines.append(f"[b]{tpl.name}[/b]  ·  [dim]{tpl.category}[/dim]")
        lines.append("")
        lines.append(f"[b]句数:[/b] {tpl.line_count}")
        lines.append(
            f"[b]字数:[/b] {tpl.total_chars}  ([i]{', '.join(str(n) for n in tpl.char_counts)}[/i])"
        )
        lines.append(f"[b]韵位:[/b] {', '.join(str(p) for p in tpl.rhyme_positions) or '—'}")
        if tpl.rhyme_groups_allowed:
            rg = ", ".join(g.value for g in tpl.rhyme_groups_allowed)
            lines.append(f"[b]允许韵部:[/b] {rg}")
        lines.append("")
        lines.append("[b]平仄模式[/b]")
        for i, (pat, count) in enumerate(zip(tpl.tone_patterns, tpl.char_counts)):
            lines.append(
                f"  L{i + 1:>2} ({count} 字): [tone-ping]平[/tone-ping]/"
                f"[tone-ze]仄[/tone-ze] = {pat}"
            )

        if tpl.example_title or tpl.example_author:
            lines.append("")
            lines.append(
                f"[b]代表作品:[/b] 《{tpl.example_title or '—'}》 {tpl.example_author or ''}"
            )
            for i, ln in enumerate(tpl.example_lines):
                lines.append(f"  [b]L{i + 1:>2}[/b]  [poem-line]{ln}[/poem-line]")

        self._set_detail("\n".join(lines))
        self._set_status(f"已选择: {tpl.name}")

    # -- Helpers ---------------------------------------------------------------

    def _set_detail(self, content: str) -> None:
        try:
            self.query_one("#cipai-detail", Static).update(content)
        except Exception:
            pass

    def _set_status(self, text: str) -> None:
        try:
            self.query_one("#status-bar", Static).update(text)
        except Exception:
            pass

    def _render_unavailable(self, exc: BaseException) -> None:
        """Render a fallback notice when the prosody engine is missing."""
        msg = (
            f"[!] 词牌注册表不可用[/i]\n  [b]{exc}[/b]\n\n请安装项目依赖:  [b]pip install -e .[/b]"
        )
        self._set_detail(msg)
        try:
            self.query_one("#cipai-list", ListView).display = False
        except Exception:
            pass
        self._set_status("[!] 词牌注册表不可用")
