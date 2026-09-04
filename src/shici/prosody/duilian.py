"""对仗 (parallelism) check for 律诗 颔联/颈联 and 对联.

A good antithesis satisfies:
  1. 字数 相同
  2. 词性 相对 (noun↔noun, verb↔verb, adjective↔adjective, ...)
  3. 平仄 相对 (平对仄)
  4. 语义 类别 相当 (avoid "合掌" — same-meaning pairs)
  5. 句法结构 相当

We approximate parts-of-speech via jieba with a small classical-Chinese
POS table; semantic relatedness uses lightweight set comparison.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    import jieba.posseg as pseg  # type: ignore[import]

    _HAS_JIEBA = True
except ImportError:
    pseg = None  # type: ignore[assignment]
    _HAS_JIEBA = False


# Maps jieba POS tags to coarse classical grammar categories.
POS_CATEGORY: dict[str, str] = {
    "n": "名词",
    "nr": "名词",
    "ns": "名词",
    "nt": "名词",
    "nz": "名词",
    "v": "动词",
    "vd": "动词",
    "vn": "动词",
    "a": "形容词",
    "ad": "形容词",
    "an": "形容词",
    "d": "副词",
    "m": "数词",
    "q": "量词",
    "r": "代词",
    "c": "连词",
    "p": "介词",
    "u": "助词",
    "xc": "虚词",
}


@dataclass(frozen=True)
class AntithesisReport:
    """Result of an antithesis check."""

    score: float  # 0.0 - 1.0
    length_match: bool
    pos_match_ratio: float  # 0.0 - 1.0
    tone_match_ratio: float  # 0.0 - 1.0
    semantic_overlap: float  # 0.0 - 1.0 (lower is better)
    structural_match: bool
    notes: list[str]

    def __str__(self) -> str:
        return (
            f"AntithesisReport(score={self.score:.2f}, "
            f"length={self.length_match}, "
            f"pos={self.pos_match_ratio:.0%}, "
            f"tone={self.tone_match_ratio:.0%}, "
            f"semantic_overlap={self.semantic_overlap:.0%})"
        )


def _classify_word(word: str) -> str:
    """Return coarse POS category for a single word.

    Falls back to "未识别" if jieba isn't available.
    """
    if not _HAS_JIEBA:
        return "未识别"
    tokens = pseg.cut(word)
    for tok in tokens:
        tag = POS_CATEGORY.get(tok.flag, "其他")
        return tag
    return "其他"


def _line_categories(line: str) -> list[str]:
    """Classify each character/word in a line."""
    if _HAS_JIEBA:
        return [_classify_word(word) for word, _ in pseg.cut(line)]
    # Fallback: return per-character "未识别"
    return ["未识别"] * len(line)


def _tone_sequence(line: str):
    from .classifier import classify_line

    return classify_line(line)


def _semantic_overlap(a: str, b: str) -> float:
    """Jaccard-like overlap of two strings on characters. Lower is better."""
    set_a = set(a)
    set_b = set(b)
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    return len(intersection) / len(set_a | set_b)


def check_antithesis(upper: str, lower: str) -> AntithesisReport:
    """Evaluate antithesis quality of a pair of lines.

    Args:
        upper: 上联 / 颔联上句
        lower: 下联 / 颔联下句

    Returns:
        AntithesisReport with overall score and component metrics.
    """
    notes: list[str] = []

    # 1. Length match
    length_match = len(upper) == len(lower)
    if not length_match:
        notes.append(f"字数不等: 上 {len(upper)} 字 vs 下 {len(lower)} 字")

    if not length_match:
        return AntithesisReport(
            score=0.0,
            length_match=False,
            pos_match_ratio=0.0,
            tone_match_ratio=0.0,
            semantic_overlap=1.0,
            structural_match=False,
            notes=notes,
        )

    # 2. POS match (per position)
    upper_cats = _line_categories(upper)
    lower_cats = _line_categories(lower)
    pos_matches = sum(
        1 for u, l in zip(upper_cats, lower_cats) if u == l and u not in ("未识别", "其他")
    )
    pos_match_ratio = pos_matches / len(upper_cats)
    if pos_match_ratio < 0.5:
        notes.append(f"词性匹配率较低 ({pos_match_ratio:.0%})")

    # 3. Tone opposition (平 对 仄)
    upper_tones = _tone_sequence(upper)
    lower_tones = _tone_sequence(lower)
    tone_matches = sum(
        1
        for u, l in zip(upper_tones, lower_tones)
        if u.value == "中" or l.value == "中" or u.value != l.value
    )
    tone_match_ratio = tone_matches / len(upper_tones)
    if tone_match_ratio < 0.6:
        notes.append(f"平仄对立不足 ({tone_match_ratio:.0%})")

    # 4. Semantic overlap (lower is better)
    overlap = _semantic_overlap(upper, lower)
    if overlap > 0.4:
        notes.append(f"语义重复较高,可能合掌 ({overlap:.0%})")

    # 5. Structural match (length of segments is roughly equal)
    upper_seg = [len(w) for w, _ in (pseg.cut(upper) if _HAS_JIEBA else [])]
    lower_seg = [len(w) for w, _ in (pseg.cut(lower) if _HAS_JIEBA else [])]
    structural_match = upper_seg == lower_seg if upper_seg and lower_seg else True

    # Composite score
    score = (
        (1.0 if length_match else 0.0) * 0.2
        + pos_match_ratio * 0.3
        + tone_match_ratio * 0.3
        + (1.0 - overlap) * 0.15
        + (1.0 if structural_match else 0.5) * 0.05
    )

    return AntithesisReport(
        score=score,
        length_match=length_match,
        pos_match_ratio=pos_match_ratio,
        tone_match_ratio=tone_match_ratio,
        semantic_overlap=overlap,
        structural_match=structural_match,
        notes=notes,
    )


def antithesis_score(upper: str, lower: str) -> float:
    """Return a single scalar antithesis quality score in [0, 1]."""
    return check_antithesis(upper, lower).score


__all__ = [
    "AntithesisReport",
    "antithesis_score",
    "check_antithesis",
]
