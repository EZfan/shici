# shici/data/poetry

Classical Chinese poetry corpus for the **shici** CLI, sourced from
[chinese-poetry/chinese-poetry](https://github.com/chinese-poetry/chinese-poetry)
(53.3k stars, MIT).

The upstream repo is hundreds of MB; this directory ships only a
**curated subset (~5 MB)** suitable for development, unit tests, and a
local retrieval index. See "Downloading the full dataset" below if you
need everything.

## Layout

```
data/poetry/
├── README.md                     <- this file
├── LICENSE-chinese-poetry.txt    <- upstream MIT license
├── preprocess.js                 <- JSON -> samples.jsonl converter
├── samples.jsonl                 <- generated, one record per poem line
├── tang/
│   ├── poet.tang.0.json          <- first 1000 Tang poems
│   ├── poet.tang.1000.json       <- poems 1000-2000
│   ├── poet.tang.3000.json       <- poems 3000-4000
│   └── authors.tang.json         <- Tang author metadata (3675 authors)
├── song/
│   ├── ci.song.0.json            <- first 1000 Song ci
│   ├── songci-300.json           <- 宋词三百首 (curated 280 ci)
│   └── author.song.json          <- Song author metadata (1563 authors)
└── shijing/
    └── shijing.json              <- 诗经 (Book of Songs, 305 poems)
```

## Schema

Each source uses a slightly different JSON shape. The preprocessor
unifies them.

| Source        | Poem record keys                                       |
|---------------|--------------------------------------------------------|
| `poet.tang.*` | `author`, `title`, `paragraphs[]`, `id`                |
| `ci.song.*`   | `author`, `paragraphs[]`, `rhythmic` (词牌)            |
| `songci-300`  | `author`, `paragraphs[]`, `rhythmic`, `tags[]`         |
| `shijing`     | `title`, `chapter`, `section`, `content[]`             |

`paragraphs[]` (or `content[]` for shijing) holds couplets / lines as
single strings like `"秦川雄帝宅，函谷壯皇居。"`. The preprocessor splits
each paragraph on the Chinese comma `，` so each sample record is one
half-couplet (one sentence).

## Regenerating samples.jsonl

```bash
cd data/poetry
node preprocess.js          # writes samples.jsonl
node preprocess.js --check  # stats only, no file write
```

Output schema (one JSON object per line):

```json
{ "author": "太宗皇帝", "title": "帝京篇十首 一", "line": "秦川雄帝宅", "dynasty": "唐", "source": "tang" }
```

Current stats: **47809 lines, 4586 poems, 495 authors** across
唐 (28,971 lines), 宋 (15,430 lines), 先秦 (3,408 lines).

## Downloading the full dataset

Only a small subset is committed here. To pull everything (hundreds of
MB, ~55k Tang poems, ~21k Song ci, plus 诗经/楚辞/元曲/纳兰词 etc.):

```bash
# Whole repo, ~1 GB unpacked
git clone --depth 1 https://github.com/chinese-poetry/chinese-poetry.git

# Or, the data subsets only, via sparse checkout (recommended)
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/chinese-poetry/chinese-poetry.git
cd chinese-poetry
git sparse-checkout set 全唐诗 宋词 诗经
```

After cloning, copy the files you need into the `tang/`, `song/`,
`shijing/` folders and re-run `node preprocess.js` to regenerate
`samples.jsonl` against the larger corpus. The preprocessor already
knows the file naming convention `poet.tang.<N>.json` / `ci.song.<N>.json`
— just add new entries to the `sources` array in `preprocess.js`.

## Attribution

All poetry text in this directory is from
[chinese-poetry/chinese-poetry](https://github.com/chinese-poetry/chinese-poetry)
by JackeyGao and contributors, used under the MIT License
(see `LICENSE-chinese-poetry.txt`). The poems themselves are classical
Chinese works in the public domain; the MIT license covers the
digitization and curation work.

## License

- Poetry text: public domain (classical Chinese works).
- Curation, JSON packaging, and any code in this directory: MIT, as
  inherited from the upstream project.
