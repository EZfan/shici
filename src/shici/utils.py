"""Display helpers for shici.

Wraps Rich console/panel/table rendering for poem output, issues,
and welcome banner.
"""

from __future__ import annotations

from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .prosody import (
    CheckResult,
    IssueLevel,
    Tone,
    classify_character,
    lookup_rhyme,
)

console = Console()


def render_welcome() -> None:
    """Print a stylized welcome banner."""
    ascii_art = """
   _____  _
  / ___|| |__   ___ _   _ _ __
  \\___ \\| '_ \\ / _ \\ | | | '_ \\
   ___) | | | |  __/ |_| | |_) |
  |____/|_| |_|\\___|\\__,_| .__/
                         |_|
"""
    console.print(f"[bold cyan]{ascii_art}[/bold cyan]")
    console.print("[dim]古典诗词格律引擎 · 让 AI 写出严谨的诗[/dim]\n")


def read_poem_file(path: Path) -> list[str]:
    """Read a poem file and split into non-empty lines."""
    text = path.read_text(encoding="utf-8").strip()
    return [line.strip() for line in text.splitlines() if line.strip()]


def render_poem_panel(result: CheckResult) -> None:
    """Render the poem lines in a styled panel with tone markers."""
    lines = []
    for i, line in enumerate(result.lines):
        char_styles = []
        for c in line:
            tone = classify_character(c)
            if tone == Tone.PING:
                char_styles.append(f"[cyan]{c}[/cyan]")
            elif tone == Tone.ZE:
                char_styles.append(f"[yellow]{c}[/yellow]")
            else:
                char_styles.append(f"[dim]{c}[/dim]")
        lines.append("".join(char_styles))

    body = "\n".join(lines)
    console.print(
        Panel(
            body,
            title=f"[bold cyan]{result.form.value}[/bold cyan]",
            subtitle=(
                f"[dim]{result.error_count} 处错误 · {result.warning_count} 处警告[/dim]"
                if result.issues
                else "[green]✓ 合乎格律[/green]"
            ),
            border_style="cyan" if not result.issues else "red",
            box=box.DOUBLE,
        )
    )


def render_issues(result: CheckResult) -> None:
    """Render issues as a table."""
    if not result.issues:
        return

    table = Table(
        title="格律检查",
        title_style="bold yellow",
        box=box.ROUNDED,
    )
    table.add_column("严重", justify="center", width=6)
    table.add_column("位置", justify="center", width=10)
    table.add_column("代码", style="dim")
    table.add_column("说明")
    table.add_column("建议", style="dim")

    for issue in result.issues:
        prefix = (
            "[red]✗ 错误[/red]" if issue.level == IssueLevel.ERROR else "[yellow]! 警告[/yellow]"
        )
        loc = f"L{issue.line + 1}" if issue.line >= 0 else "全局"
        if issue.column >= 0:
            loc = f"L{issue.line + 1}C{issue.column + 1}"
        table.add_row(
            prefix,
            loc,
            issue.code,
            issue.message,
            issue.suggestion or "-",
        )
    console.print(table)


def render_character_tone_table(line: str) -> str:
    """Return a (char, tone_marker) table as a string."""
    chars = " ".join(c for c in line)
    markers = " ".join(
        "平"
        if classify_character(c) == Tone.PING
        else "仄"
        if classify_character(c) == Tone.ZE
        else "·"
        for c in line
    )
    return f"{chars}\n{markers}"


def format_rhyme_table(char_to_check: str) -> None:
    """Print rhyme group info for a character."""
    rg = lookup_rhyme(char_to_check)
    if rg is None:
        console.print(f"[dim]未找到 '{char_to_check}' 的韵部[/dim]")
        return
    console.print(f"[bold cyan]{char_to_check}[/bold cyan] → {rg.value}")


__all__ = [
    "console",
    "format_rhyme_table",
    "read_poem_file",
    "render_character_tone_table",
    "render_issues",
    "render_poem_panel",
    "render_welcome",
]
