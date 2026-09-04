# Contributing

We welcome contributions to shici! Please read our
[contribution guide](https://anthropics.github.io/shici/contributing/) first.

## Quick start

```bash
git clone https://github.com/EZfan/shici
cd shici
uv sync --all-extras --dev
uv run pytest
```

## Issues

Found a bug or have a feature idea? Open an
[issue](https://github.com/EZfan/shici/issues) — please include:

- shici version (`shici --version`)
- Operating system
- Python version
- A minimal reproducible example

## Pull requests

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/cool-thing`)
3. Commit your changes with a descriptive message
4. Push and open a PR

Please ensure:

- `uv run ruff check src tests` passes
- `uv run pytest` passes
- New features include tests
- Public APIs are documented in the docstring

See [docs/contributing.md](docs/contributing.md) for more.