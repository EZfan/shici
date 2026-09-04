# LLM Backends

shici supports multiple LLM providers through a unified interface built on
[LiteLLM](https://github.com/BerriAI/litellm) and
[Instructor](https://github.com/567-labs/instructor). This lets you choose the
best balance of **price**, **latency**, and **Chinese quality** for your needs.

## Backend comparison

| Backend   | Default model         | Cost / 1M tokens (in) | Chinese quality | Structured output |
|-----------|-----------------------|-----------------------|------------------|-------------------|
| DeepSeek  | `deepseek-chat`       | $0.14 (cached: $0.014) | ★★★★★           | ✓                  |
| Qwen      | `qwen-plus`           | $0.004                 | ★★★★★           | ✓                  |
| OpenAI    | `gpt-4o-mini`         | $0.15                 | ★★★★            | ✓ (native schema)  |
| Anthropic | `claude-haiku-4-5`    | $0.80                 | ★★★★            | ✓ (tool use)       |
| Ollama    | `qwen2.5` (local)     | free                  | ★★★★            | ✓                  |

**Recommendation**: DeepSeek for the best price/quality. Qwen if you want
to pay in RMB. OpenAI/Anthropic for premium quality. Ollama for offline.

## Configuration

Set the appropriate API key environment variable:

```bash
export DEEPSEEK_API_KEY="sk-..."
# or
export DASHSCOPE_API_KEY="sk-..."  # Qwen
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

Then select the backend via `--model`:

```bash
shici generate jueju --theme 思乡 --model deepseek   # default
shici generate jueju --theme 思乡 --model qwen
shici generate jueju --theme 思乡 --model openai
shici generate jueju --theme 思乡 --model anthropic
shici generate jueju --theme 思乡 --model ollama
```

## How shici uses the LLM

Three task templates, each with structured output via Pydantic:

1. **`generate_jueju`** / **`generate_lushi`** / **`generate_ci`**: produce a
   poem that satisfies specific tonal + rhyme constraints.
2. **`generate_revision`**: revise a poem given a list of prosody violations.
3. **`critique_poem`**: score and critique an existing poem (prosody, imagery, originality).
4. **`annotate_poem`**: line-by-line annotation (字词释义, 典故, 意境).

All tasks share the same Jinja2 prompt templates in
`src/shici/llm/prompts/`.

## Local inference (Ollama)

For fully offline generation:

```bash
# Install Ollama and pull a model
ollama pull qwen2.5:7b

# shici auto-detects Ollama at localhost:11434
shici generate jueju --theme 思乡 --model ollama
```

## Cost estimate

Generating one 7-char jueju with revision loop (2 rounds):

| Backend | Per generation |
|---------|----------------|
| DeepSeek | ~$0.001 |
| Qwen Plus | ~$0.0005 |
| GPT-4o-mini | ~$0.002 |
| Claude Haiku | ~$0.003 |

This means even 1000 generated poems cost less than a coffee.