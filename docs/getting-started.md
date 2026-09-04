# Getting Started

This guide walks you through installing shici, configuring your first LLM backend,
and running your first poem generation.

## Installation

shici is distributed via PyPI. Pick your preferred package manager:

=== "uv (recommended)"

    ```bash
    uv tool install shici
    ```

=== "pip"

    ```bash
    pip install shici
    ```

=== "pipx"

    ```bash
    pipx install shici
    ```

After installation, the `shici` command should be on your `$PATH`:

```bash
shici --version
# shici v0.1.0
```

## First steps without an LLM

Most diagnostic commands work **without an API key**. Try these first:

```bash
# Check a known poem against classical rules
shici check examples/jueju-5.txt

# Classify tones of each character in a line
shici lint "床前明月光"

# Look up the rhyme group of a character
shici rhyme 光

# Evaluate antithesis between two couplets
shici duilian "天增岁月人增寿" "春满乾坤福满门"

# List all supported 词牌
shici cipai
```

## Configure an LLM backend

To use `shici generate`, `shici critique`, or `shici annotate`, you need an API key.
Set one of the following environment variables:

| Backend   | Environment variable     | Notes                       |
|-----------|--------------------------|-----------------------------|
| DeepSeek  | `DEEPSEEK_API_KEY`       | Default. Best price/quality. |
| OpenAI    | `OPENAI_API_KEY`         | `gpt-4o-mini` is sufficient.|
| Qwen      | `DASHSCOPE_API_KEY`      | Strong Chinese.             |
| Anthropic | `ANTHROPIC_API_KEY`      | `claude-haiku-4-5`.         |
| Ollama    | (no key)                 | Local inference.            |

For example:

```bash
export DEEPSEEK_API_KEY="sk-..."
```

Then generate a poem:

```bash
shici generate jueju --theme 思乡 --chars 7 --revisions 3
```

## Optional: enable RAG over 全唐诗

```bash
uv add shici --extra rag

# Fetch corpora (manual step — see shici fetch for instructions)
# Then index them
shici index -s data/poetry

# Now find similar lines
shici search "明月几时有"
```

## What's next?

- Read the [CLI Reference](reference/cli.md) for every command and flag.
- Understand the [Prosody Engine](prosody.md) — how shici validates poems.
- See the [Architecture overview](architecture.md) for design rationale.