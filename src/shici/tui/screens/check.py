"""Check screen — paste-a-poem prosody checker.

The user pastes one line per row into the ``TextArea`` (4 lines for
绝句, 8 lines for 律诗) and presses [检查]. We invoke
:func:`shici.prosody.check_poem` (with a graceful fallback when the
prosody engine is not installed) and render:

    * the detected form;
    * each poem line annotated with [blue]平[/blue] / [red]仄[/red]
      colouring for the strict positions (2 / 4 / 6);
    * a summary of errors and warnings with markers ``✗`` / ``!``.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static, TextArea

__all__ = ["CheckScreen"]


# Default sample — 杜甫「登高」, a 七言律诗 — useful as a quick demo.
DEFAULT_POEM = (
    "风急天高猿啸哀，渚清沙白鸟飞回。\n"
    "无边落木萧萧下，不尽长江滚滚来。\n"
    "万里悲秋常作客，百年多病独登台。\n"
    "艰难苦恨繁霜鬓，潦倒新停浊酒杯。"
)


class CheckScreen(Screen):
    """Prosody-check screen with a TextArea input and a result panel."""

    BINDINGS = [
        Binding("ctrl+enter", "run_check", "检查"),
        Binding("escape", "app.pop_screen", "返回"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the check form."""
        with Vertical(id="check-root"):
            yield Static("格律检查", id="title")
            yield Static(
                "每行一句古诗(4 行绝句 / 8 行律诗),按 [检查] 或 Ctrl+Enter 运行。",
                classes="form-label",
            )

            with Container(id="input-area"):
                yield TextArea.code_editor(
                    DEFAULT_POEM,
                    id="poem-input",
                    language=None,
                )

            with Container(id="actions"):
                yield Button("检查  (Ctrl+Enter)", id="btn-check", classes="menu-button")
                yield Button("清空", id="btn-clear", classes="menu-button")

            yield Static("", id="result", classes="poem-panel")

            yield Static(
                "就绪。",
                id="status-bar",
                classes="status-bar",
            )

    def on_mount(self) -> None:
        """Focus the input area on entry."""
        try:
            self.query_one("#poem-input", TextArea).focus()
        except Exception:
            pass

    # -- Button handlers ---------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Route button presses."""
        bid = event.button.id or ""
        if bid == "btn-check":
            self.action_run_check()
        elif bid == "btn-clear":
            self._clear_input()

    # -- Bindings ----------------------------------------------------------------

    def action_run_check(self) -> None:
        """Run the prosody check on the current input."""
        try:
            text = self.query_one("#poem-input", TextArea).text
        except Exception as exc:
            self._set_status(f"[!] 无法读取输入: {exc}")
            return

        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        if not lines:
            self._set_status("[!] 请先粘贴诗作。")
            return

        try:
            from ...prosody import (
                IssueLevel,
                Tone,
                check_poem,
                classify_character,
            )
        except Exception as exc:
            # Graceful degradation — prosody engine not available.
            self._render_unavailable(exc)
            return

        try:
            result = check_poem(lines)
        except ValueError as exc:
            self._render_parse_error(exc)
            return
        except Exception as exc:  # pragma: no cover - defensive
            self._render_parse_error(exc)
            return

        self._render_result(result, IssueLevel, Tone, classify_character)

    # -- Rendering ---------------------------------------------------------------

    def _clear_input(self) -> None:
        """Clear the TextArea and the result panel."""
        try:
            ta = self.query_one("#poem-input", TextArea)
            ta.clear()
            ta.focus()
        except Exception:
            pass
        self._set_result_panel("")

    def _set_status(self, text: str) -> None:
        """Update the status bar with a short message."""
        try:
            self.query_one("#status-bar", Static).update(text)
        except Exception:
            pass

    def _set_result_panel(self, content: str) -> None:
        """Replace the contents of the result panel."""
        try:
            self.query_one("#result", Static).update(content)
        except Exception:
            pass

    def _render_unavailable(self, exc: BaseException) -> None:
        """Render a fallback notice when prosody is not importable."""
        msg = (
            f"[!] 格律引擎未安装或导入失败:[/i]\n"
            f"  [b]{exc}[/b]\n\n"
            "请安装项目依赖:  [b]pip install -e .[/b]"
        )
        self._set_result_panel(msg)
        self._set_status("[!] 格律引擎不可用")

    def _render_parse_error(self, exc: BaseException) -> None:
        """Render a parse error gracefully."""
        self._set_result_panel(f"[!] 无法解析诗作: {exc}")
        self._set_status("[!] 解析失败")

    def _render_result(self, result, IssueLevel, Tone, classify_character) -> None:
        """Render a successful :class:`CheckResult` to Rich markup.

        Each line is rendered with one character per cell, tagged by the
        ``tone-ping`` / ``tone-ze`` / ``tone-flexible`` CSS classes. A
        list of issues follows.
        """
        from ...prosody import IssueLevel as _IL  # noqa: F401  (re-bind guard)

        buf: list[str] = []

        form_name = result.form.value
        n_lines = len(result.lines)
        buf.append(f"[b]体裁:[/b] {form_name}  ·  [b]行数:[/b] {n_lines}")
        buf.append("")

        # Per-line tone rendering. Even positions (1-based: 2,4,6...) are
        # strict; odd positions are flexible. We colour every char.
        for i, line in enumerate(result.lines):
            chars = [c for c in line if not _is_punct(c)]
            tones = [classify_character(c) for c in chars]
            cells: list[str] = []
            for j, (ch, tone) in enumerate(zip(chars, tones)):
                pos = j + 1  # 1-based
                if tone == Tone.PING:
                    cells.append(f"[tone-ping]{ch}[/tone-ping]")
                elif tone == Tone.ZE:
                    cells.append(f"[tone-ze]{ch}[/tone-ze]")
                else:
                    cells.append(f"[tone-flexible]{ch}[/tone-flexible]")
            # Compact line number annotation
            buf.append(f"  [b]L{i + 1:>2}[/b]  " + "".join(cells))

        buf.append("")

        # Issue list
        if not result.issues:
            buf.append("[b][green]✓ 格律无违。[/green][/b]")
        else:
            errs = [i for i in result.issues if i.level == IssueLevel.ERROR]
            warns = [i for i in result.issues if i.level == IssueLevel.WARNING]
            infos = [i for i in result.issues if i.level == IssueLevel.INFO]
            buf.append(
                f"[b]问题汇总:[/b] "
                f"[issue-error]{len(errs)} 错[/issue-error]  "
                f"[issue-warning]{len(warns)} 警[/issue-warning]  "
                f"[issue-info]{len(infos)} 提示[/issue-info]"
            )
            for issue in result.issues:
                cls = (
                    "issue-error"
                    if issue.level == IssueLevel.ERROR
                    else "issue-warning"
                    if issue.level == IssueLevel.WARNING
                    else "issue-info"
                )
                marker = "✗" if issue.level == IssueLevel.ERROR else "!"
                loc = f"L{issue.line + 1}" if issue.line >= 0 else "全局"
                buf.append(f"  [{cls}]{marker} {loc}: {issue.message}[/{cls}]")
                if issue.suggestion:
                    buf.append(f"     [dim]建议: {issue.suggestion}[/dim]")

        # Rhyme summary
        if result.rhyme_groups:
            buf.append("")
            buf.append("[b]韵部:[/b]")
            for line_idx, grp in zip(_rhyme_indices(result.form), result.rhyme_groups):
                if grp is None:
                    buf.append(f"  L{line_idx + 1}: [dim]未能识别韵脚[/dim]")
                else:
                    buf.append(f"  L{line_idx + 1}: {grp.value}")

        self._set_result_panel("\n".join(buf))
        verdict = "通过" if result.ok else f"{result.error_count} 处违律"
        self._set_status(f"检查完成 · {verdict}")


# -- Local helpers ----------------------------------------------------------------


def _is_punct(c: str) -> bool:
    """Cheap punctuation test — mirrors the prosody checker rule."""
    code = ord(c)
    return (
        0x3000 <= code <= 0x303F
        or 0xFF00 <= code <= 0xFFEF
        or 0x0021 <= code <= 0x002F
        or 0x003A <= code <= 0x0040
    )


def _rhyme_indices(form) -> list[int]:
    """Best-effort rhyme positions for display (绝句 1/3, 律诗 1/3/5/7)."""
    name = getattr(form, "value", str(form))
    if name in {"五言绝句", "七言绝句"}:
        return [1, 3]
    if name in {"五言律诗", "七言律诗"}:
        return [1, 3, 5, 7]
    return []