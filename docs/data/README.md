# 数据集 (datasets)

本目录包含 shici 使用的本地数据。

## pingshui.json

来自 [gelv-poetry](https://github.com/chenmisss/gelv-poetry) 的平水韵字典 (MIT 协议)。
8232 字符,涵盖平水韵 105 个韵部 + 中华新韵 14 个韵部 + 1105 个多音字 + 1653 个入声字。

vendored 到 `src/shici/prosody/data/`,license 保留在 `LICENSE-gelv-poetry.txt`。

## samples.jsonl

来自 [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) 的语料 (MIT 协议),
经过预处理,每行一条 `{author, title, line, dynasty, source}` 记录。

共 47,809 条记录,涵盖:
- 唐诗: 28,971 行 (1000+1000+1001 首)
- 宋词: 15,430 行 (1000+280 首)
- 诗经: 3,408 行 (305 首)

由 `shijing` 和 `tang`/`song` 三个 corpus 合并而成,用作 RAG 索引的源。

## 如何下载完整数据集

本目录只包含精简样本 (约 5MB)。

要构建完整的 ~1GB RAG 索引:

```bash
git clone --depth 1 https://github.com/chinese-poetry/chinese-poetry
cd chinese-poetry
# 上述目录已包含 全唐诗/, 宋词/, 诗经/ 等子目录

# 用 scripts/build_corpora.py 把所有 JSON 转成 JSONL
cd <path-to-shici>
uv run python scripts/build_corpora.py \
    --source /path/to/chinese-poetry \
    --output data/poetry

# 建立 RAG 索引
uv run shici index -s data/poetry
```

## License

- pingshui.json: MIT (gelv-poetry)
- samples.jsonl: MIT (chinese-poetry)