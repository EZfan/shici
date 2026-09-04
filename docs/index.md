# shici — 诗词格律引擎

> **Generate classical Chinese poetry under strict tonal & rhyme rules, powered by LLMs.**

shici 是一个面向终端的 AI 古典诗词生成工具。它把大语言模型的文学创造力
与确定性的格律校验引擎结合,生成严格遵守平水韵、平仄、词牌、对仗的古典诗词。

## 安装

```bash
uv tool install shici
# 或
pip install shici
```

## 快速开始

```bash
# 检查一首绝句
shici check examples/jueju-5.txt

# 校验对仗
shici duilian "天增岁月人增寿" "春满乾坤福满门"

# 查询单字韵部
shici rhyme 光

# 查看单句平仄
shici lint "床前明月光"

# 生成七言绝句 (需要 API key)
shici generate jueju --theme 思乡

# 启动 TUI
shici tui
```

## 工作原理

```
LLM (DeepSeek) → 候选诗作 → 格律校验引擎 → 修订循环 → 最终输出
                              ├ 平水韵 (105 韵部)
                              ├ 平仄 (16 式)
                              ├ 词牌 (20+)
                              └ 对仗 (词性 + 平仄 + 语义)
```

LLM 负责主题、意象、风格、典故 — 即"写什么"。格律引擎负责平仄、押韵、对仗 — 即"怎么写"。
两者结合,使 AI 生成的诗词既有意境又合乎格律。

## 进阶使用

- 配置 LLM API key: 设置环境变量 `DEEPSEEK_API_KEY` (默认), 或 `OPENAI_API_KEY` / `DASHSCOPE_API_KEY`
- 索引全唐诗: `shici index` (需要 rag 扩展: `uv add shici --extra rag`)
- RAG 检索相似诗句: `shici search "明月几时有"`
- AI 鉴赏: `shici critique examples/poem.txt`

## 致谢

shici 站在巨人的肩膀上:

- [gelv-poetry](https://github.com/chenmisss/gelv-poetry) — 平水韵数据 (MIT)
- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) — 全唐诗/宋词语料 (MIT)
- [Textual](https://github.com/Textualize/textual) — TUI framework (MIT)
- [Rich](https://github.com/Textualize/rich) — Terminal rendering (MIT)
- [Typer](https://github.com/tiangolo/typer) — CLI framework (MIT)
- [Instructor](https://github.com/567-labs/instructor) — LLM structured output (MIT)
- [LiteLLM](https://github.com/BerriAI/litellm) — Multi-provider LLM gateway (MIT)
- [Chroma](https://github.com/chroma-core/chroma) — Vector database (Apache 2.0)

诗词之道,源远流长。致敬所有古典文学研究者。

## License

MIT — see [LICENSE](https://github.com/anthropics/shici/blob/main/LICENSE).