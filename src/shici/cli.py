"""shici CLI — generate and validate classical Chinese poetry.

Usage examples:

    shici check poem.txt
    shici generate --form 七言绝句 --theme 思乡
    shici search "明月几时有"
    shici critique poem.txt
    shici --help
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__
from .prosody import (
    PoetryForm,
    Tone,
    antithesis_score,
    check_duilian,
    check_poem,
    classify_character,
    get_cipai,
    list_cipai,
    lookup_rhyme,
)
from .utils import (
    console,
    render_issues,
    render_poem_panel,
)

app = typer.Typer(
    name="shici",
    help="Generate classical Chinese poetry under strict tonal & rhyme rules.",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

generate_app = typer.Typer(
    name="generate",
    help="Generate poetry with an LLM (requires API key).",
    add_completion=False,
)
app.add_typer(generate_app, name="generate")


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]shici[/bold cyan] [dim]v{__version__}[/dim]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """shici — AI 古典诗词生成器"""


@app.command()
def check(
    file: Path = typer.Argument(..., exists=True, readable=True, help="诗作文件,每行一句"),
    form: str | None = typer.Option(
        None,
        "--form",
        "-f",
        help="显式指定体裁: 五言绝句 / 七言绝句 / 五言律诗 / 七言律诗 / 对联",
    ),
    duilian: bool = typer.Option(
        False,
        "--duilian",
        "-d",
        help="按对联检查(两行)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="以 JSON 格式输出",
    ),
) -> None:
    """检查诗作是否合乎格律。"""
    text = file.read_text(encoding="utf-8").strip()
    if duilian:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) != 2:
            console.print("[red]对联检查需要正好两行 (上联/下联)[/red]")
            raise typer.Exit(code=1)
        result = check_duilian(lines[0], lines[1])
    else:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) not in (4, 8):
            console.print(f"[red]诗作应为 4 句 (绝句) 或 8 句 (律诗),当前 {len(lines)} 句[/red]")
            raise typer.Exit(code=1)
        explicit_form = None
        if form:
            try:
                explicit_form = PoetryForm(form)
            except ValueError:
                console.print(f"[red]未知的体裁: {form}[/red]")
                raise typer.Exit(code=1) from None
        result = check_poem(lines, form=explicit_form)

    if json_output:
        payload = {
            "form": result.form.value,
            "ok": result.ok,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "issues": [
                {
                    "level": i.level.value,
                    "line": i.line,
                    "column": i.column,
                    "code": i.code,
                    "message": i.message,
                    "suggestion": i.suggestion,
                }
                for i in result.issues
            ],
        }
        console.print_json(data=payload)
    else:
        render_poem_panel(result)
        render_issues(result)

    if not result.ok:
        raise typer.Exit(code=1)


@app.command()
def search(
    line: str = typer.Argument(..., help="要查找的诗句片段"),
    top_k: int = typer.Option(5, "--top", "-k", help="返回几条相似诗句"),
    json_output: bool = typer.Option(False, "--json", "-j"),
) -> None:
    """在全唐诗中检索相似诗句。"""
    try:
        from .rag import CorpusSearcher
    except ImportError:
        console.print(
            "[yellow]RAG 功能需要安装 rag 扩展:[/yellow] [cyan]uv add shici --extra rag[/cyan]"
        )
        raise typer.Exit(code=1) from None

    try:
        searcher = CorpusSearcher()
    except Exception as e:
        console.print(f"[red]语料库未初始化: {e}[/red]")
        console.print("[dim]提示: 运行 [cyan]shici index[/cyan] 先建立索引。[/dim]")
        raise typer.Exit(code=1) from None

    results = searcher.search(line, top_k=top_k)
    if not results:
        console.print("[yellow]未找到相似诗句[/yellow]")
        return

    if json_output:
        console.print_json(data=results)
    else:
        table = Table(
            title=f'与 "{line}" 相似的诗句',
            box=box.ROUNDED,
            title_style="bold cyan",
        )
        table.add_column("诗句", style="white")
        table.add_column("作者", style="green")
        table.add_column("出处", style="dim")
        table.add_column("相似度", justify="right", style="magenta")
        for r in results:
            table.add_row(
                r["line"],
                r["author"],
                r["source"],
                f"{r['score']:.2f}",
            )
        console.print(table)


@app.command()
def critique(
    file: Path = typer.Argument(..., exists=True, readable=True),
    model: str = typer.Option("deepseek", "--model", "-m"),
) -> None:
    """AI 鉴赏诗作 (需要 API key)。"""
    try:
        from .llm import critique_poem
    except ImportError:
        console.print(
            "[yellow]鉴赏功能需要 llm 扩展:[/yellow] [cyan]uv add shici --extra llm[/cyan]"
        )
        raise typer.Exit(code=1) from None

    text = file.read_text(encoding="utf-8").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        console.print("[red]空文件[/red]")
        raise typer.Exit(code=1)

    with console.status("[cyan]AI 正在鉴赏...[/cyan]"):
        critique_obj = critique_poem(lines, model=model)

    console.print(
        Panel(
            Text(f"总分: {critique_obj.overall_score:.1f} / 10"),
            title="[bold cyan]AI 鉴赏结果[/bold cyan]",
            border_style="cyan",
        )
    )

    table = Table(box=box.SIMPLE)
    table.add_column("维度", style="bold")
    table.add_column("分数", justify="right")
    for name, score in [
        ("格律", critique_obj.prosody_score),
        ("意象", critique_obj.imagery_score),
        ("创意", critique_obj.originality_score),
    ]:
        table.add_row(name, f"{score:.1f} / 10")
    console.print(table)

    if critique_obj.highlights:
        console.print("\n[bold green]佳句[/bold green]")
        for h in critique_obj.highlights:
            console.print(f"  • {h}")
    if critique_obj.allusions:
        console.print("\n[bold magenta]用典[/bold magenta]")
        for a in critique_obj.allusions:
            console.print(f"  • {a}")
    if critique_obj.comments:
        console.print("\n[bold yellow]点评[/bold yellow]")
        for c in critique_obj.comments:
            console.print(f"  • {c}")


@app.command()
def annotate(
    file: Path = typer.Argument(..., exists=True, readable=True),
) -> None:
    """逐句注释 (需要 API key)。"""
    try:
        from .llm import annotate_poem
    except ImportError:
        console.print("[yellow]注疏功能需要 llm 扩展[/yellow]")
        raise typer.Exit(code=1) from None

    text = file.read_text(encoding="utf-8").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    with console.status("[cyan]生成注释...[/cyan]"):
        annotations = annotate_poem(lines)
    for i, (line, ann) in enumerate(zip(lines, annotations), 1):
        console.print(
            Panel(
                ann.get("text", ""),
                title=f"[bold cyan]第 {i} 句: {line}[/bold cyan]",
                border_style="cyan",
            )
        )


@app.command()
def lint(
    line: str = typer.Argument(..., help="任意诗句"),
) -> None:
    """查看单行的逐字平仄。"""
    tones = []
    for c in line:
        if not _is_chinese(c):
            tones.append((" ", " "))
            continue
        tone = classify_character(c)
        marker = "平" if tone == Tone.PING else ("仄" if tone == Tone.ZE else "中")
        tones.append((c, marker))

    console.print(
        Panel(
            _format_tone_table(tones),
            title=f"[bold cyan]平仄分析: {line}[/bold cyan]",
            border_style="cyan",
        )
    )


@app.command()
def rhyme(
    char: str = typer.Argument(..., help="单个汉字"),
) -> None:
    """查询单字所属的平水韵部。"""
    if len(char) != 1:
        console.print("[red]请输入单个汉字[/red]")
        raise typer.Exit(code=1)
    rg = lookup_rhyme(char)
    if rg is None:
        console.print(f"[yellow]未找到 '{char}' 的韵部[/yellow]")
        raise typer.Exit(code=1)
    tone = classify_character(char)
    console.print(f"[cyan]{char}[/cyan] → [bold]韵部: {rg.value}[/bold] · 平/仄: {tone.value}")


@app.command()
def cipai() -> None:
    """列出所有支持的词牌。"""
    table = Table(title="[bold cyan]词牌 (cipai) 列表[/bold cyan]", box=box.ROUNDED)
    table.add_column("词牌", style="bold cyan")
    table.add_column("类型", style="green")
    table.add_column("字数", justify="right")
    table.add_column("句数", justify="right")
    table.add_column("代表作者", style="dim")
    for name in list_cipai():
        tpl = get_cipai(name)
        table.add_row(
            name,
            tpl.category,
            str(tpl.total_chars),
            str(tpl.line_count),
            tpl.example_author or "-",
        )
    console.print(table)


@app.command(name="duilian")
def duilian(
    upper: str = typer.Argument(..., help="上联"),
    lower: str | None = typer.Argument(None, help="下联 (留空则只评估上联)"),
) -> None:
    """对仗检查。"""
    if lower is None:
        console.print("[yellow]未提供下联,只能计算字符信息。[/yellow]")
        console.print(f"上联长度: {len(upper)} 字")
        return

    score = antithesis_score(upper, lower)
    result = check_duilian(upper, lower)
    console.print(
        Panel(
            f"[bold]对仗得分: {score:.2f} / 1.00[/bold]\n"
            f"格律问题: {result.error_count} 处错误, {result.warning_count} 处警告",
            title="[bold cyan]对仗分析[/bold cyan]",
            border_style="cyan",
        )
    )
    render_issues(result)


@app.command()
def version() -> None:
    """显示版本。"""
    console.print(f"shici v{__version__}")


@app.command()
def index(
    source: Path = typer.Option("data/poetry", "--source", "-s"),
    output: Path = typer.Option(None, "--output", "-o"),
    model: str = typer.Option("BAAI/bge-small-zh-v1.5", "--model", "-m"),
) -> None:
    """建立 RAG 向量索引 (从 data/poetry/*.jsonl)。"""
    from .rag.indexer import index_command

    index_command(source=source, output=output, model=model)


@app.command()
def fetch(
    output: Path = typer.Option("data/poetry", "--output", "-o"),
    source: str = typer.Option("tang", "--corpus", "-c"),
) -> None:
    """下载 chinese-poetry 语料库 (按 chinese-poetry 仓库 README 操作)。"""
    from .rag.indexer import fetch_command

    fetch_command(output=output, source=source)


@app.command()
def tui() -> None:
    """启动交互式 TUI 界面。"""
    try:
        from .app import run
    except ImportError as e:
        console.print(f"[red]TUI 不可用: {e}[/red]")
        console.print("[dim]提示:[/dim] 安装 textual 扩展: [cyan]uv add shici --extra tui[/cyan]")
        raise typer.Exit(code=1) from None
    run()


@generate_app.command("jueju")
def generate_jueju(
    theme: str = typer.Option(..., "--theme", "-t", help="主题,如 思乡/送别/山水"),
    chars: int = typer.Option(7, "--chars", "-c", help="每句字数 (5 或 7)"),
    rhyme: str | None = typer.Option(None, "--rhyme", "-r", help="韵部,如 上平一东"),
    model: str = typer.Option("deepseek", "--model", "-m"),
    revise: int = typer.Option(2, "--revisions", help="修订轮数"),
) -> None:
    """生成绝句 (4 句)。"""
    try:
        from .llm import LLMConfig, get_client
        from .llm import generate_jueju as _gen
    except ImportError:
        console.print("[yellow]请先安装 llm 扩展: uv add shici --extra llm[/yellow]")
        raise typer.Exit(code=1) from None

    form = PoetryForm.JUEJU_5 if chars == 5 else PoetryForm.JUEJU_7
    config = LLMConfig(backend=model)

    with console.status(f"[cyan]生成 {form.value} (主题: {theme})...[/cyan]"):
        poem = _gen(theme=theme, chars=chars, rhyme_group=rhyme, config=config)

    # Revise loop
    lines = [line.text for line in poem.lines]
    for round_num in range(revise):
        result = check_poem(lines, form=form)
        if result.ok:
            break
        from .llm import generate_revision

        with console.status(f"[cyan]第 {round_num + 1} 轮修订...[/cyan]"):
            revised = generate_revision(poem, result.issues, config=config)
            poem = revised
            lines = [line.text for line in poem.lines]

    # Final check + render
    final_result = check_poem(lines, form=form)
    console.print(
        Panel(
            "\n".join(lines),
            title=f"[bold cyan]{poem.title or form.value}[/bold cyan]",
            subtitle=f"[dim]主题: {poem.theme}[/dim]",
            border_style="cyan",
        )
    )
    render_issues(final_result)
    if poem.notes:
        console.print(f"\n[dim]创作意图: {poem.notes}[/dim]")


@generate_app.command("ci")
def generate_ci(
    cipai_name: str = typer.Option(..., "--cipai", "-c", help="词牌名,如 浣溪沙"),
    theme: str = typer.Option(..., "--theme", "-t", help="主题"),
    model: str = typer.Option("deepseek", "--model", "-m"),
) -> None:
    """生成词。"""
    try:
        from .llm import LLMConfig
        from .llm import generate_ci as _gen_ci
    except ImportError:
        console.print("[yellow]请先安装 llm 扩展[/yellow]")
        raise typer.Exit(code=1) from None

    config = LLMConfig(backend=model)
    with console.status(f"[cyan]生成 {cipai_name}...[/cyan]"):
        ci = _gen_ci(cipai_name=cipai_name, theme=theme, config=config)
    lines = [line.text for line in ci.lines]
    console.print(
        Panel(
            "\n".join(lines),
            title=f"[bold cyan]{ci.title or cipai_name}[/bold cyan]",
            subtitle=f"[dim]{ci.cipai} · 主题: {ci.theme}[/dim]",
            border_style="cyan",
        )
    )


def _is_chinese(c: str) -> bool:
    if not c:
        return False
    code = ord(c)
    return 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF


def _format_tone_table(tones: list[tuple[str, str]]) -> str:
    """Format a (char, tone) list as aligned columns."""
    chars = " ".join(c for c, _ in tones)
    markers = " ".join(m for _, m in tones)
    return f"{chars}\n{markers}"


if __name__ == "__main__":
    app()
