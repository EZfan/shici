# Prosody Engine

The prosody engine is the heart of shici. It encodes the classical Chinese
poetic rules — **ping/ze** (tone), **pingshui rhyme groups**, **cipai templates**,
and **antithesis (duilian)** — and checks poems against them.

## Tone classification (平仄)

Every Chinese character belongs to one of three tonal groups in the classical sense:

- **平 (level)**: characters with level-tone readings (e.g. `光 guāng`)
- **仄 (oblique)**: characters with 上声, 去声, or 入声 readings (e.g. `国 guó`)
- **中 (flexible)**: characters not in the dictionary or ambiguous in the position

shici ships a vendored dictionary of **8232 characters** from
[gelv-poetry](https://github.com/chenmisss/gelv-poetry) under MIT License.

```python
from shici.prosody import classify_character, Tone

classify_character("光")  # Tone.PING
classify_character("国")  # Tone.ZE
```

## Rhyme groups (韵部)

Classical poetry uses the **pingshuiyun** (平水韵) system of 106 traditional
rhyme groups. Modern Mandarin pronunciation is *not* a substitute — many
ancient rhymes are no longer rhyming in Mandarin.

shici ships the full 106-group table:

```python
from shici.prosody import lookup_rhyme

lookup_rhyme("光")  # RhymeGroup.XIA_PING_7_YANG = "下平七阳"
lookup_rhyme("黄")  # RhymeGroup.XIA_PING_7_YANG = "下平七阳"
```

## 16 patterns (16 式)

律诗 and 绝句 each have **16 canonical tonal patterns**, depending on:

- 五言 vs 七言 (5 vs 7 chars per line)
- 平起 vs 仄起 (level-start vs oblique-start)
- 首句入韵 vs 首句不入韵 (first line rhymes or not)

shici implements all 16 patterns. The `check_poem` function tries every
applicable pattern and selects the one with fewest mismatches:

```python
from shici.prosody import check_jueju

result = check_jueju([
    "床前明月光",
    "疑是地上霜",
    "举头望明月",
    "低头思故乡",
])
print(result.ok)         # True if no errors
print(result.error_count) # number of issues
```

## Cipai templates (词牌)

词 (ci poetry) follows strict tune patterns called **cipai**. Each cipai
specifies the number of lines, characters per line, tonal pattern per line,
rhyme positions, and example stanza.

shici ships **20 cipai** out of the box (浣溪沙, 如梦令, 水调歌头, 满江红, …):

```python
from shici.prosody import list_cipai, get_cipai

for name in list_cipai():
    tpl = get_cipai(name)
    print(f"{name}: {tpl.line_count} lines, {tpl.total_chars} chars")
```

## Antithesis (对仗)

In lüshi, the **颔联** (2nd couplet) and **颈联** (3rd couplet) must satisfy
**antithesis**: matching character count, parallel parts-of-speech, opposing
平/仄, and balanced semantic categories (no 合掌 — redundant pairs).

shici computes a 0–1 antithesis score using:

- **Length match** (20%)
- **POS match** via `jieba` (30%)
- **Tone opposition** (30%)
- **Semantic overlap** penalty (15%)
- **Structural match** (5%)

```python
from shici.prosody import antithesis_score

antithesis_score("天增岁月人增寿", "春满乾坤福满门")  # → ~0.92
```

## Revision loop (生成-校验-修订)

The killer feature: shici couples the prosody engine with an LLM in a tight
**revision loop**:

```
       ┌────────────────────────────┐
       ↓                            │
   [ LLM 生成 ] ──→ [ 校验 ] ──→ ok? ──→ 输出
        ↑              ↓ no
        └──── [ 反馈违规位置 ] ←──┘
```

Each round, the LLM sees the current poem plus a structured list of
violations (line/column/expected tone), and is asked to revise. After 2–3
rounds, ~95% of generations are 格律合法 — versus ~60% for single-shot.

See [Architecture](architecture.md) for details.

## Limitations

- The dictionary covers ~8200 characters. Rare characters in poems may fall
  back to `Tone.FLEXIBLE`.
- 入声字 detection is based on the bundled dictionary, not Mandarin tones.
- Tone patterns are the canonical 正格; some historical poems intentionally
  deviate (孤平, 拗救). Use the result as a guide, not absolute law.