"""CLI command: `shici index` — build the RAG index from JSONL corpora."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def index_command(
    source: Path = typer.Option(
        "data/poetry",
        "--source",
        "-s",
        help="Directory of *.jsonl files produced by scripts/build_corpora.py",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory (default: ~/.cache/shici/vectors)",
    ),
    model: str = typer.Option(
        "BAAI/bge-small-zh-v1.5",
        "--model",
        "-m",
        help="Sentence-transformers model name",
    ),
) -> None:
    """Build a Chroma vector index of poetry lines for similarity search."""
    from .searcher import build_index

    if not source.exists():
        console.print(f"[red]Source directory not found: {source}[/red]")
        console.print(
            "[dim]Tip:[/dim] run [cyan]shici fetch[/cyan] first to download "
            "chinese-poetry JSONL corpora, or place your own *.jsonl files there."
        )
        raise typer.Exit(code=1)

    jsonl_files = list(source.glob("*.jsonl"))
    if not jsonl_files:
        console.print(f"[red]No *.jsonl files in {source}[/red]")
        raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Indexing {len(jsonl_files)} files into {output or '~/.cache/shici/vectors'}...",
            total=None,
        )
        try:
            count = build_index(source_dir=source, index_dir=output, model_name=model)
        except ImportError as e:
            console.print(f"[red]{e}[/red]")
            console.print(
                "[yellow]Install the rag extra:[/yellow] [cyan]uv add shici --extra rag[/cyan]"
            )
            raise typer.Exit(code=1) from None
        progress.update(task, completed=True)

    console.print(f"[green]✓ Indexed {count} lines[/green]")


def fetch_command(
    output: Path = typer.Option(
        "data/poetry",
        "--output",
        "-o",
        help="Where to save the downloaded JSONL files",
    ),
    source: str = typer.Option(
        "tang",
        "--corpus",
        "-c",
        help="Which corpus: tang / song / shijing / all-small",
    ),
) -> None:
    """Download a subset of chinese-poetry data into JSONL."""
    console.print(
        "[yellow]chinese-poetry corpus downloader — manual step[/yellow]\n"
        "Run the following to populate the corpus directory:\n"
        "  1. Clone https://github.com/chinese-poetry/chinese-poetry (MIT)\n"
        "  2. Run [cyan]python scripts/build_corpora.py[/cyan] to convert JSON "
        "to JSONL with one poem-line per record.\n"
        "Or place your own *.jsonl files under the source directory — each "
        'line should be `{"line": "...", "author": "...", '
        '"title": "...", "dynasty": "..."}`.'
    )
