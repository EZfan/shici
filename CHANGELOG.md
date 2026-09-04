# Changelog

All notable changes to shici are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial public release.

### Features
- `shici check` — prosody validation for jueju, lüshi, ci, duilian
- `shici lint` — per-character tone analysis
- `shici rhyme` — pingshui rhyme group lookup
- `shici cipai` — list 20 supported 词牌
- `shici duilian` — antithesis scoring
- `shici generate` — LLM-powered poem generation with revision loop
- `shici critique` — AI poem critique (0–10 across prosody/imagery/originality)
- `shici annotate` — line-by-line annotation
- `shici search` — semantic search over 全唐诗/宋词 via Chroma
- `shici index` — build RAG vector index from `*.jsonl` corpora
- `shici tui` — Textual TUI with 4 screens
- Optional extras: `llm`, `tui`, `rag`, `dev`, `all`

### Engineering
- Vendored 平水韵 dictionary (8232 characters) from gelv-poetry (MIT)
- 20 canonical cipai templates (浣溪沙, 如梦令, 水调歌头, 满江红, …)
- Pydantic schemas for structured LLM output
- Jinja2 prompt templates with strict tone/rhyme constraints
- CI across Ubuntu/macOS/Windows × Python 3.11/3.12/3.13
- PyPI Trusted Publishing via GitHub Actions

[Unreleased]: https://github.com/anthropics/shici/compare/main...HEAD