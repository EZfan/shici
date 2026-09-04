# CLI Reference

Complete reference for every `shici` command, flag, and option.

## Global options

```
shici --version       # show version
shici --help          # show help
```

## `shici check` — prosody validation

```bash
shici check FILE                       # auto-detect form
shici check FILE --form 七言绝句       # explicit form
shici check FILE --form 五言律诗
shici check FILE --duilian             # parallel couplet mode
shici check FILE --json                # machine-readable output
```

`FILE` is a UTF-8 text file with one line per sentence (4 lines for 绝句,
8 lines for 律诗, 2 lines for 对联).

Exits non-zero if any errors are found.

## `shici lint` — single-line tone analysis

```bash
shici lint "床前明月光"
```

Prints each character with its tone marker (平/仄/中).

## `shici rhyme` — rhyme group lookup

```bash
shici rhyme 光
# 光 → 韵部: 下平七阳 · 平/仄: 平
```

## `shici cipai` — list 词牌

```bash
shici cipai
```

Prints a table of all supported 词牌 with category, 字数, 句数, and 代表作者.

## `shici duilian` — antithesis scoring

```bash
shici duilian "天增岁月人增寿" "春满乾坤福满门"
```

Scores 0–1 and reports issues with parallelism, tone opposition, length, etc.

## `shici search` — RAG over 全唐诗

```bash
shici search "明月几时有"
shici search "床前明月光" --top 10
shici search "黄河之水天上来" --json
```

Requires the `rag` extra (`uv add shici --extra rag`) and a built index
(`shici index`).

## `shici generate` — LLM-powered composition

```bash
shici generate jueju --theme 思乡
shici generate jueju --theme 思乡 --chars 5          # 五言绝句
shici generate jueju --theme 思乡 --chars 7          # 七言绝句
shici generate jueju --theme 思乡 --rhyme 上平一东
shici generate jueju --theme 思乡 --revisions 3
shici generate jueju --theme 思乡 --model openai
shici generate ci --cipai 浣溪沙 --theme 思乡
```

Requires the `llm` extra and an API key environment variable.

## `shici critique` — AI critique

```bash
shici critique FILE
shici critique FILE --model deepseek
```

Returns a 0–10 score breakdown across prosody, imagery, originality, plus
highlights and detected allusions.

## `shici annotate` — line-by-line annotation

```bash
shici annotate FILE
```

Returns 字词释义, 典故, and 意境 for each line.

## `shici index` — build RAG index

```bash
shici index                       # default: data/poetry/*.jsonl → ~/.cache/shici/vectors
shici index -s data/poetry -o /tmp/vectors
shici index --model BAAI/bge-m3
```

## `shici fetch` — corpus download hint

```bash
shici fetch
```

Prints instructions for downloading chinese-poetry corpora.

## `shici tui` — launch interactive TUI

```bash
shici tui
```

Opens a full-screen Textual app with 4 screens: Home, Generate, Check, Browse.
Use `h/g/c/b` to navigate, `q` to quit.