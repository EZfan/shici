"""Generate screen — interactive form for poem generation.

The TUI deliberately does **not** invoke the LLM directly. Generation
needs API credentials and can take seconds to minutes; the TUI is a
keyboard-first interface where long-running, network-bound work should
be driven from the CLI (``shici generate``). Instead this screen
captures the user's intent (form + theme + optional rhyme book) and
displays a helpful notice pointing them at the CLI command, while
still echoing their input so they can copy/paste it into the CLI.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Select, Static

__all__ = ["GenerateScreen"]


_FORM_OPTIONS: list[tuple[str, str]] = [
    ("五言绝句 (4×5)",  "五言绝句"),
    ("七言绝句 (4×7)",  "七言绝句"),
    ("五言律诗 (8×5)",  "五言律诗"),
    ("七言律诗 (8×7)",  "七言律诗"),
    ("词牌  (cipai)",   "词牌"),
]


class GenerateScreen(Screen):
    """Interactive poem-generation form.

    The form captures:
        * 体裁  (Select)
        * 主题  (Input)
        * 韵部  (Input, optional — for 律诗/绝句; or 词牌名 for 词)
        * CIPAI (Input, optional — shown when 体裁 = 词牌)

    Submitting the form renders a notice that generation requires the
    CLI (``shici generate``) along with a literal command line the
    user can copy.
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "返回"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the generate form."""
        with Vertical(id="generate-root"):
            yield Static("生成诗词", id="title")
            yield Static("填写以下字段,然后按 [生成] 提交。", classes="form-label")

            with Container(id="form"):
                yield Static("体裁", classes="form-label")
                yield Select(
                    options=_FORM_OPTIONS,
                    value="五言绝句",
                    id="select-form",
                    allow_blank=False,
                )

                yield Static("主题 / 意象 / 情感", classes="form-label")
                yield Input(
                    placeholder="例如:秋夜思乡、月下独酌、登高怀远…",
                    id="input-theme",
                )

                yield Static("韵部 (可选,如: 东韵 / 平水韵 · 上平四支)", classes="form-label")
                yield Input(
                    placeholder="留空则随机选择",
                    id="input-rhyme",
                )

                yield Static("词牌名 (仅当体裁=词牌)", classes="form-label")
                yield Input(
                    placeholder="例如: 浣溪沙、菩萨蛮、西江月…",
                    id="input-cipai",
                )

                yield Button("生成", id="btn-go", classes="menu-button")

            yield Static("", id="result", classes="poem-panel")

            yield Static(
                "提示: 生成完成后会自动跳到「检查」屏幕查看格律。",
                id="status-bar",
                classes="status-bar",
            )

    def on_mount(self) -> None:
        """Focus the theme input on entry."""
        self.query_one("#input-theme", Input).focus()

    # -- Helpers -----------------------------------------------------------------

    def _toggle_cipai_visibility(self, form_value: str) -> None:
        """Show / hide the 词牌 input depending on the selected form."""
        try:
            cipai_input = self.query_one("#input-cipai", Input)
        except Exception:
            return
        cipai_input.display = form_value == "词牌"

    def on_select_changed(self, event: Select.Changed) -> None:
        """React to form changes — toggle the 词牌 input visibility."""
        if event.select.id != "select-form":
            return
        # ``Select.Changed.value`` is the option value (a string in our case).
        self._toggle_cipai_visibility(str(event.value))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the [生成] button."""
        if event.button.id != "btn-go":
            return
        self._run_generate()

    def _run_generate(self) -> None:
        """Render the CLI hint notice.

        We deliberately avoid touching the LLM client — see the module
        docstring. Any error here should never reach the user.
        """
        try:
            form_value = str(self.query_one("#select-form", Select).value)
            theme = self.query_one("#input-theme", Input).value.strip()
            rhyme = self.query_one("#input-rhyme", Input).value.strip()
            cipai = self.query_one("#input-cipai", Input).value.strip()
        except Exception as exc:
            self._render_notice(f"[!] 表单读取失败: {exc}")
            return

        if not theme:
            self._render_notice("[!] 请先填写「主题」。")
            return

        parts: list[str] = ["shici", "generate"]
        if form_value == "词牌":
            parts += ["--form", "cipai"]
            if cipai:
                parts += ["--cipai", cipai]
            else:
                self._render_notice("[!] 体裁为「词牌」时,请填写词牌名。")
                return
        else:
            parts += ["--form", form_value]
        if rhyme:
            parts += ["--rhyme", rhyme]
        parts += ["--theme", theme]

        cmd = " ".join(parts)
        notice = (
            "[i]TUI 中生成需 LLM API,请使用 CLI:[/i]\n\n"
            f"  [b]{cmd}[/b]\n\n"
            "复制并粘贴到终端运行。生成后可回到「检查」屏幕粘贴诗作校验。"
        )
        self._render_notice(notice)

    def _render_notice(self, text: str) -> None:
        """Update the result panel with a notice (Rich markup allowed)."""
        try:
            self.query_one("#result", Static).update(text)
        except Exception:
            self.app.log(f"render failed: {text}")