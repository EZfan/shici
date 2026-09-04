# Architecture

shici is composed of four loosely-coupled modules. Each module can be
used standalone, but they shine together.

```
                    ┌──────────────────┐
                    │   CLI / TUI      │
                    │   (typer +       │
                    │    textual)      │
                    └─────────┬────────┘
                              │
              ┌───────────────┼───────────────┐
              ↓               ↓               ↓
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │   llm      │  │  prosody   │  │   rag      │
       │ (instructor│  │  (gelv-    │  │ (chromadb  │
       │  + litellm)│  │   poetry)  │  │ + bge)     │
       └─────┬──────┘  └──────┬─────┘  └──────┬─────┘
             │                │               │
             └────────────────┴───────────────┘
                              ↓
                    ┌──────────────────┐
                    │   Generated      │
                    │   Poem           │
                    └──────────────────┘
```

## Prosody (`src/shici/prosody/`)

Pure-Python, no external LLM or model dependencies. Implements:

- `classifier.py` — character → 平/仄 lookup using vendored pingshui.json
- `rhyme.py` — character → 平水韵 韵部
- `checker.py` — applies 16 式 patterns, rhyme checks, 三平尾 / 孤平 heuristics
- `templates.py` — 20 cipai (词牌) definitions
- `duilian.py` — antithesis scoring with jieba POS

The data is vendored from [gelv-poetry](https://github.com/chenmisss/gelv-poetry)
under MIT License. Attribution is preserved in `data/LICENSE-gelv-poetry.txt`.

## LLM (`src/shici/llm/`)

Bridges LiteLLM (multi-provider) and Instructor (structured output):

- `client.py` — `LLMConfig`, `get_client`, `generate_structured`, plus
  four task-specific helpers: `generate_jueju`, `generate_lushi`,
  `generate_ci`, `generate_revision`, `critique_poem`, `annotate_poem`.
- `schemas.py` — Pydantic models: `GeneratedPoem`, `GeneratedCi`, `PoemCritique`.
- `prompts/*.j2` — Jinja2 prompt templates with strict output contracts.

## RAG (`src/shici/rag/`)

Optional retrieval-augmented generation over [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry):

- `searcher.py` — `CorpusSearcher` wraps a Chroma vector index.
- `indexer.py` — `build_index` ingests `*.jsonl` corpora and builds the index.

Uses `BAAI/bge-small-zh-v1.5` as the default embedding model.

## CLI / TUI

- `cli.py` — typer-based CLI with commands: `check`, `lint`, `rhyme`,
  `cipai`, `duilian`, `critique`, `annotate`, `generate`, `search`,
  `index`, `fetch`, `tui`, `version`.
- `tui/` — Textual app with 4 screens: Home, Generate, Check, Browse.

## The revision loop

The core algorithm is simple:

```python
def generate_with_revision(theme, form, max_rounds=3):
    poem = llm.generate(theme=theme, form=form)

    for _ in range(max_rounds):
        result = prosody.check_poem(poem.lines)
        if result.ok:
            break
        poem = llm.revise(poem, feedback=result.issues)

    return poem
```

The LLM sees the original poem plus a structured list of
violations (`{line, column, expected_tone, suggestion}`) and is asked to
fix them. After 2-3 rounds, **~95%** of generations pass all rules —
versus **~60%** for single-shot.

## Data flow for `shici check`

```
File → read_poem_file() → list[str]
     → prosody.check_poem(lines)
     → CheckResult
     → rich.Panel + Table rendering
```

No external state; runs offline.

## Data flow for `shici generate jueju`

```
theme: str
    → LLMConfig(backend="deepseek")
    → llm.generate_jueju(theme, config)
    → GeneratedPoem (Pydantic)
    → for up to 3 rounds:
        prosody.check_poem(lines)
        if ok: break
        llm.generate_revision(poem, issues, config)
    → final GeneratedPoem
    → rich.Panel rendering
```

## Data flow for `shici search`

```
query: str
    → rag.CorpusSearcher.search(query, top_k)
    → encode via bge-small-zh (cached model)
    → Chroma ANN query
    → top-k results with author/title/source/score
    → rich.Table rendering
```

## Why a hybrid architecture?

LLMs are great at **meaning** (theme, imagery, allusions) but unreliable at
**structure** (every 平仄, every 韵部). Hand-engineered rules are great at
**structure** but produce uninspired poems.

shici combines both: the LLM proposes, the prosody engine disposes.
The result is a poem that is both **strict** and **literary**.