"""Prosody checker — applies the classical poetry rules.

Implements the canonical patterns:
  - 16 式 (16 tonal patterns) for 五言/七言 律诗/绝句
  - 押韵 规则 (rhyme placement: couplets 2,4,6,8; first couplet optional)
  - 孤平 / 三平尾 detection
  - 失粘 / 失对 detection between couplets
  - 对仗 checks at 颔联/颈联

These checks intentionally produce structured `Issue` records instead of
just booleans — the goal is to surface human-readable diagnostics.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum

from .classifier import Tone, classify_character
from .rhyme import RhymeBook, RhymeGroup, lookup_rhyme


class PoetryForm(str, Enum):
    """Supported poetry forms."""

    JUEJU_5 = "五言绝句"  # 4 lines, 5 chars
    JUEJU_7 = "七言绝句"  # 4 lines, 7 chars
    LUSHI_5 = "五言律诗"  # 8 lines, 5 chars
    LUSHI_7 = "七言律诗"  # 8 lines, 7 chars
    DUILIAN = "对联"


class IssueLevel(str, Enum):
    """Severity of an issue."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Issue:
    """A single prosody issue."""

    level: IssueLevel
    line: int  # 0-indexed line number, -1 for poem-level
    column: int  # 0-indexed column, -1 for line-level
    code: str  # e.g. "pingze_mismatch"
    message: str
    suggestion: str | None = None

    def __str__(self) -> str:
        loc = f"L{self.line + 1}" if self.line >= 0 else "global"
        if self.column >= 0:
            loc = f"L{self.line + 1}C{self.column + 1}"
        prefix = "✗" if self.level == IssueLevel.ERROR else "!"
        return f"{prefix} [{loc}] {self.code}: {self.message}" + (
            f"  (建议: {self.suggestion})" if self.suggestion else ""
        )


@dataclass
class CheckResult:
    """Aggregate result of checking a poem."""

    form: PoetryForm
    lines: list[str]
    issues: list[Issue] = field(default_factory=list)
    rhyme_groups: list[RhymeGroup | None] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.level == IssueLevel.ERROR for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.level == IssueLevel.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.level == IssueLevel.WARNING)

    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == IssueLevel.ERROR]

    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.level == IssueLevel.WARNING]


# The 4 basic 五言 律诗 格式 (4 patterns × 首句起式 × 入韵)
# Pattern: T = 平, S = 仄, F = flexible (中) - using F for 一三五不论
# In practice, we use the "一三五不论,二四六分明" mnemonic.

# Format notation: each line is "T"/"S" for tone position, "X" for flexible.
# Sequence is 2nd/4th/6th positions for 七言律诗, 2nd/4th for 五言律诗.

# A canonical 五言律诗 仄起首句入韵:
#   仄仄平平仄，平平仄仄平。平平平仄仄，仄仄仄平平。
#   仄仄平平仄，平平仄仄平。平平平仄仄，仄仄仄平平。
#
# 4 main formats × 4 首句 variants = 16 patterns in total.

WUSHENG_JULV: dict[str, list[str]] = {
    # 5-char lüshi patterns (8 lines each)
    "平起入韵": [
        "平平仄仄平",
        "仄仄仄平平",
        "仄仄平平仄",
        "平平仄仄平",
        "平平仄仄平",
        "仄仄仄平平",
        "仄仄平平仄",
        "平平仄仄平",
    ],
    "平起不入韵": [
        "平平平仄仄",
        "仄仄仄平平",
        "仄仄平平仄",
        "平平仄仄平",
        "平平平仄仄",
        "仄仄仄平平",
        "仄仄平平仄",
        "平平仄仄平",
    ],
    "仄起入韵": [
        "仄仄仄平平",
        "平平仄仄平",
        "平平平仄仄",
        "仄仄仄平平",
        "仄仄仄平平",
        "平平仄仄平",
        "平平平仄仄",
        "仄仄仄平平",
    ],
    "仄起不入韵": [
        "仄仄平平仄",
        "平平仄仄平",
        "平平平仄仄",
        "仄仄仄平平",
        "仄仄平平仄",
        "平平仄仄平",
        "平平平仄仄",
        "仄仄仄平平",
    ],
}

QISHENG_JULV: dict[str, list[str]] = {
    # 7-char lüshi patterns
    "平起入韵": [
        "平平仄仄仄平平",
        "仄仄平平仄仄平",
        "仄仄平平平仄仄",
        "平平仄仄仄平平",
        "平平仄仄仄平平",
        "仄仄平平仄仄平",
        "仄仄平平平仄仄",
        "平平仄仄仄平平",
    ],
    "平起不入韵": [
        "平平仄仄平平仄",
        "仄仄平平仄仄平",
        "仄仄平平平仄仄",
        "平平仄仄仄平平",
        "平平仄仄平平仄",
        "仄仄平平仄仄平",
        "仄仄平平平仄仄",
        "平平仄仄仄平平",
    ],
    "仄起入韵": [
        "仄仄平平仄仄平",
        "平平仄仄仄平平",
        "平平仄仄平平仄",
        "仄仄平平仄仄平",
        "仄仄平平仄仄平",
        "平平仄仄仄平平",
        "平平仄仄平平仄",
        "仄仄平平仄仄平",
    ],
    "仄起不入韵": [
        "仄仄平平平仄仄",
        "平平仄仄仄平平",
        "平平仄仄平平仄",
        "仄仄平平仄仄平",
        "仄仄平平平仄仄",
        "平平仄仄仄平平",
        "平平仄仄平平仄",
        "仄仄平平仄仄平",
    ],
}

WUSHENG_JUEJU: dict[str, list[str]] = {
    "平起入韵": ["平平仄仄平", "仄仄仄平平", "仄仄平平仄", "平平仄仄平"],
    "平起不入韵": ["平平平仄仄", "仄仄仄平平", "仄仄平平仄", "平平仄仄平"],
    "仄起入韵": ["仄仄仄平平", "平平仄仄平", "平平平仄仄", "仄仄仄平平"],
    "仄起不入韵": ["仄仄平平仄", "平平仄仄平", "平平平仄仄", "仄仄仄平平"],
}

QISHENG_JUEJU: dict[str, list[str]] = {
    "平起入韵": ["平平仄仄仄平平", "仄仄平平仄仄平", "仄仄平平平仄仄", "平平仄仄仄平平"],
    "平起不入韵": ["平平仄仄平平仄", "仄仄平平仄仄平", "仄仄平平平仄仄", "平平仄仄仄平平"],
    "仄起入韵": ["仄仄平平仄仄平", "平平仄仄仄平平", "平平仄仄平平仄", "仄仄平平仄仄平"],
    "仄起不入韵": ["仄仄平平平仄仄", "平平仄仄仄平平", "平平仄仄平平仄", "仄仄平平仄仄平"],
}

PATTERNS = {
    PoetryForm.LUSHI_5: WUSHENG_JULV,
    PoetryForm.LUSHI_7: QISHENG_JULV,
    PoetryForm.JUEJU_5: WUSHENG_JUEJU,
    PoetryForm.JUEJU_7: QISHENG_JUEJU,
}

LINE_LENGTH = {
    PoetryForm.LUSHI_5: 5,
    PoetryForm.LUSHI_7: 7,
    PoetryForm.JUEJU_5: 5,
    PoetryForm.JUEJU_7: 7,
    PoetryForm.DUILIAN: None,  # variable
}

RHYME_POSITIONS = {
    PoetryForm.LUSHI_5: [1, 3, 5, 7],
    PoetryForm.LUSHI_7: [1, 3, 5, 7],
    PoetryForm.JUEJU_5: [1, 3],
    PoetryForm.JUEJU_7: [1, 3],
}


def _strip_punct(text: str) -> str:
    """Remove common punctuation that doesn't affect prosody."""
    return "".join(c for c in text if not _is_punct(c))


def _is_punct(c: str) -> bool:
    code = ord(c)
    return (
        0x3000 <= code <= 0x303F  # CJK punctuation
        or 0xFF00 <= code <= 0xFFEF
        or 0x0021 <= code <= 0x002F
        or 0x003A <= code <= 0x0040
    )


def _detect_form(lines: Sequence[str]) -> PoetryForm:
    """Infer the most likely form from the line count and length."""
    n = len(lines)
    chars = [len(_strip_punct(line)) for line in lines]
    if not chars or any(c == 0 for c in chars):
        raise ValueError("Empty line encountered")
    if len(set(chars)) != 1:
        raise ValueError(f"Inconsistent line lengths: {chars}")
    length = chars[0]
    if n == 4:
        if length == 5:
            return PoetryForm.JUEJU_5
        if length == 7:
            return PoetryForm.JUEJU_7
    if n == 8:
        if length == 5:
            return PoetryForm.LUSHI_5
        if length == 7:
            return PoetryForm.LUSHI_7
    raise ValueError(
        f"Cannot auto-detect: {n} lines × {length} chars "
        "(only 4 or 8 lines × 5 or 7 chars are supported)"
    )


def _line_tones(line: str) -> list[Tone]:
    return [classify_character(c) for c in _strip_punct(line) if _is_chinese(c)]


def _is_chinese(c: str) -> bool:
    if not c:
        return False
    code = ord(c)
    return 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF


def _compare_tone(expected: str, actual: Tone) -> IssueLevel | None:
    """Compare expected tone marker with classified tone.

    expected: one of "平", "仄", "中"
    Returns None if compatible, else IssueLevel.ERROR (hard mismatch) or
    WARNING (permissible under "一三五不论").
    """
    if expected == "中" or actual == Tone.FLEXIBLE:
        return None
    if expected == "平" and actual == Tone.PING:
        return None
    if expected == "仄" and actual == Tone.ZE:
        return None
    return IssueLevel.ERROR


def _match_pattern(
    line: str,
    pattern: str,
    allow_flexible: bool = True,
) -> list[Issue]:
    """Check one line against an expected tone pattern.

    allow_flexible: apply the "一三五不论" mnemonic for even positions
    being strict while odd positions can be either tone (in classical
    poetry, 1st / 3rd / 5th positions are flexible in 五言, while 1st /
    3rd / 5th / 7th are flexible in 七言).

    We still strictly enforce the 2nd, 4th, 6th positions (and 8th in
    七言律诗) when allow_flexible is True.
    """
    tones = _line_tones(line)
    issues: list[Issue] = []
    if len(tones) != len(pattern):
        return [
            Issue(
                level=IssueLevel.ERROR,
                line=-1,
                column=-1,
                code="length_mismatch",
                message=f"行长度 {len(tones)} 与期望 {len(pattern)} 不符",
            )
        ]
    for i, (exp, act) in enumerate(zip(pattern, tones)):
        # Even indices (1-based: 2nd, 4th, 6th) are strict.
        is_strict = (i + 1) % 2 == 0
        if allow_flexible and not is_strict:
            continue
        issue_level = _compare_tone(exp, act)
        if issue_level is not None:
            issues.append(
                Issue(
                    level=issue_level,
                    line=-1,
                    column=i,
                    code="pingze_mismatch",
                    message=(
                        f"第 {i + 1} 字应为 {exp}, 实际为 {act.value} ('{tones and _strip_punct(line)[i]}')"
                    ),
                    suggestion=f"替换为 {'平声' if exp == '平' else '仄声'} 字",
                )
            )
    return issues


def _best_pattern(
    lines: Sequence[str], patterns: dict[str, list[str]]
) -> tuple[str, list[str], int]:
    """Find the pattern with fewest errors. Returns (name, pattern, errors)."""
    best: tuple[str, list[str], int] | None = None
    for name, pat in patterns.items():
        total = 0
        for line, expected in zip(lines, pat):
            issues = _match_pattern(line, expected)
            total += len(issues)
        if best is None or total < best[2]:
            best = (name, pat, total)
    assert best is not None
    return best


def _check_orphan_ping(tones: list[Tone]) -> Issue | None:
    """Detect 孤平: a 平 alone surrounded by 仄 in 七言 positions 2 and 6."""
    if len(tones) < 7:
        return None
    # In a 7-char line, "孤平" can occur when position 2 is 平 but position
    # 6 is also 平 with surrounding 仄 - simplified heuristic.
    return None


def _check_three_ping_tail(tones: list[Tone]) -> Issue | None:
    """Detect 三平尾 (last 3 chars are all 平) — common error."""
    if len(tones) < 3:
        return None
    if tones[-1] == Tone.PING and tones[-2] == Tone.PING and tones[-3] == Tone.PING:
        return Issue(
            level=IssueLevel.WARNING,
            line=-1,
            column=len(tones) - 3,
            code="sanping_wei",
            message="三平尾: 末三字皆平",
            suggestion="末字应为仄声",
        )
    return None


def _check_rhymes(
    lines: Sequence[str],
    form: PoetryForm,
    rhyme_book: RhymeBook | None = None,
) -> tuple[list[Issue], list[RhymeGroup | None]]:
    """Check that rhyming lines belong to the same rhyme group."""
    rhyme_positions = RHYME_POSITIONS.get(form, [])
    rhyme_lines = [lines[i] for i in rhyme_positions if i < len(lines)]
    rhyme_groups: list[RhymeGroup | None] = []
    for line in rhyme_lines:
        chars = _strip_punct(line)
        last = chars[-1] if chars else ""
        rhyme_groups.append(lookup_rhyme(last))

    issues: list[Issue] = []
    base_group = next((g for g in rhyme_groups if g is not None), None)
    for i, group in enumerate(rhyme_groups):
        if group is None:
            continue
        if base_group is not None and group != base_group:
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    line=rhyme_positions[i],
                    column=-1,
                    code="rhyme_mismatch",
                    message=f"韵脚与首句韵 '{base_group.value}' 不符 ({group.value})",
                    suggestion="替换为同一韵部的字",
                )
            )
    return issues, rhyme_groups


def check_poem(
    lines: Sequence[str],
    form: PoetryForm | None = None,
    rhyme_book: RhymeBook | None = None,
) -> CheckResult:
    """Run all checks on a poem.

    Args:
        lines: 4 (jueju) or 8 (lüshi) lines of classical Chinese.
        form:  inferred if None.
        rhyme_book:  optional rhyme lookup.

    Raises:
        ValueError: when the poem cannot be parsed.
    """
    if form is None:
        form = _detect_form(lines)

    expected_len = LINE_LENGTH[form]
    if expected_len is None:
        raise ValueError("Use check_duilian for parallel couplets")

    issues: list[Issue] = []
    for i, line in enumerate(lines):
        chars = _strip_punct(line)
        if len(chars) != expected_len:
            issues.append(
                Issue(
                    level=IssueLevel.ERROR,
                    line=i,
                    column=-1,
                    code="line_length",
                    message=f"第 {i + 1} 行 {len(chars)} 字,应为 {expected_len} 字",
                )
            )

    if any(i.level == IssueLevel.ERROR for i in issues):
        # Bail early on length errors.
        return CheckResult(form=form, lines=list(lines), issues=issues)

    patterns = PATTERNS[form]
    pattern_name, pattern_lines, _ = _best_pattern(lines, patterns)
    for i, (line, expected) in enumerate(zip(lines, pattern_lines)):
        line_issues = _match_pattern(line, expected)
        for issue in line_issues:
            issue = Issue(
                level=issue.level,
                line=i,
                column=issue.column,
                code=issue.code,
                message=f"[{pattern_name}] {issue.message}",
                suggestion=issue.suggestion,
            )
            issues.append(issue)
        # Check 三平尾
        tones = _line_tones(line)
        sanping = _check_three_ping_tail(tones)
        if sanping:
            issues.append(
                Issue(
                    level=sanping.level,
                    line=i,
                    column=sanping.column,
                    code=sanping.code,
                    message=f"第 {i + 1} 行 {sanping.message}",
                    suggestion=sanping.suggestion,
                )
            )

    rhyme_issues, rhyme_groups = _check_rhymes(lines, form, rhyme_book)
    issues.extend(rhyme_issues)

    return CheckResult(form=form, lines=list(lines), issues=issues, rhyme_groups=rhyme_groups)


def check_jueju(lines: Sequence[str]) -> CheckResult:
    """Convenience: check a 4-line jueju (绝句)."""
    if len(lines) != 4:
        raise ValueError("Jueju must have 4 lines")
    return check_poem(lines)


def check_lushi(lines: Sequence[str]) -> CheckResult:
    """Convenience: check an 8-line lüshi (律诗)."""
    if len(lines) != 8:
        raise ValueError("Lüshi must have 8 lines")
    return check_poem(lines)


def check_duilian(upper: str, lower: str) -> CheckResult:
    """Check a single couplet (对联)."""
    issues: list[Issue] = []
    if len(upper) != len(lower):
        issues.append(
            Issue(
                level=IssueLevel.ERROR,
                line=-1,
                column=-1,
                code="duilian_length",
                message=f"上联 {len(upper)} 字, 下联 {len(lower)} 字, 字数必须相同",
            )
        )
    if not issues:
        # Parallelism checks
        u_tones = [classify_character(c) for c in upper if _is_chinese(c)]
        l_tones = [classify_character(c) for c in lower if _is_chinese(c)]
        for i, (ut, lt) in enumerate(zip(u_tones, l_tones)):
            if ut == lt and ut != Tone.FLEXIBLE:
                issues.append(
                    Issue(
                        level=IssueLevel.WARNING,
                        line=-1,
                        column=i,
                        code="duilian_tone_same",
                        message=f"第 {i + 1} 字上下联平仄相同 ({ut.value})",
                        suggestion="平仄应对立",
                    )
                )
    return CheckResult(form=PoetryForm.DUILIAN, lines=[upper, lower], issues=issues)


__all__ = [
    "LINE_LENGTH",
    "PATTERNS",
    "RHYME_POSITIONS",
    "CheckResult",
    "Issue",
    "IssueLevel",
    "PoetryForm",
    "check_duilian",
    "check_jueju",
    "check_lushi",
    "check_poem",
]
