# Contributing

Thanks for your interest in making shici better! This document covers how
to set up a development environment, run tests, and submit a PR.

## Development setup

shici uses [uv](https://github.com/astral-sh/uv) for dependency management
and [Hatchling](https://hatch.pypa.io/) as the build backend.

```bash
# Clone the repo
git clone https://github.com/EZfan/shici
cd shici

# Install all extras (dev, llm, tui, rag)
uv sync --all-extras --dev

# Verify the install
uv run shici --version
uv run pytest
```

## Running tests

```bash
# Run the full test suite
uv run pytest

# Run only fast unit tests
uv run pytest -m "not slow and not integration and not eval"

# Run a specific test file
uv run pytest tests/unit/test_checker.py -v

# Run with coverage
uv run pytest --cov=shici --cov-report=term-missing
```

Test layout:

- `tests/unit/` — pure unit tests, no network or model downloads
- `tests/integration/` — tests that hit real services (LLM APIs, RAG index)
- `tests/eval/` — LLM-as-judge evaluation (requires API key)
- `tests/cassettes/` — recorded HTTP interactions for `vcrpy`

## Project layout

```
src/shici/
├── __init__.py           # package metadata
├── cli.py                # typer CLI entry
├── app.py                # Textual TUI entry
├── utils.py              # Rich display helpers
├── prosody/              # ← the prosody engine (no LLM deps)
│   ├── classifier.py
│   ├── rhyme.py
│   ├── checker.py
│   ├── templates.py
│   ├── duilian.py
│   └── data/             # vendored from gelv-poetry (MIT)
├── llm/                  # ← the LLM client
│   ├── client.py
│   ├── schemas.py
│   └── prompts/*.j2
├── rag/                  # ← the RAG indexer (optional)
│   ├── searcher.py
│   └── indexer.py
└── tui/                  # ← the Textual TUI (optional)
    ├── app.py
    ├── theme.tcss
    └── screens/
```

## Coding conventions

- **Python 3.11+** syntax (`X | None`, `tuple[int, ...]`, etc.)
- **Line length**: 100 chars (configured in `pyproject.toml`)
- **Linter**: ruff with `E F W I UP B SIM RUF` rules
- **Formatter**: ruff format (drop-in for black)
- **Type hints**: encouraged but not required (mypy is permissive)

Before opening a PR, ensure:

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest
```

All three must pass.

## Adding a new 词牌 (cipai)

1. Open `src/shici/prosody/templates.py`.
2. Append a `_T(...)` call with the cipai name, char counts per line,
   tone patterns, rhyme positions, and an example.
3. Add a JSON file under `data/cipai/` if you want it shippable separately.
4. Add a unit test in `tests/unit/test_templates.py` — the parametrized
   `test_pattern_chars_match_counts` will pick it up automatically.

## Adding a new LLM backend

1. Open `src/shici/llm/client.py`.
2. Add an entry to `_DEFAULT_MODEL` / `_DEFAULT_KEY` / `_DEFAULT_URL`.
3. Document it in `docs/llm-backends.md`.
4. Update the comparison table in `README.md`.

## Vendored data policy

shici vendors data only from projects whose licenses are MIT or compatible.
Current vendored data:

- gelv-poetry (MIT) — `src/shici/prosody/data/`
- chinese-poetry (MIT, optional) — `data/poetry/`

When vendoring new data:

1. Keep the upstream LICENSE file in the same directory.
2. Add a copyright header to any local file that derives from upstream.
3. Update the "Acknowledgements" section of the README.

## Submitting a PR

1. Fork the repo and create a feature branch.
2. Make your changes + add tests.
3. Ensure CI passes (ruff, mypy, pytest on 3 OS × 3 Python versions).
4. Submit a PR with a clear description.

## Code of conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/).
See [CODE_OF_CONDUCT.md](https://github.com/EZfan/shici/blob/main/CODE_OF_CONDUCT.md).

## Questions?

Open an [issue](https://github.com/EZfan/shici/issues) — happy to help.