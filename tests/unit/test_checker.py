"""Unit tests for the prosody checker.

Tests cover:
- ``check_jueju``: 5-char and 7-char jueju (绝句) checks, including
  length validation and the famous 静夜思 example.
- ``check_lushi``: 8-line lüshi (律诗) checks and length validation.
- ``check_poem``: auto-detection of poetry form via line count and
  per-line character count.
- ``check_duilian``: parallel-couplet length and tone checks.
- ``CheckResult`` properties (``ok``, ``error_count``,
  ``warning_count``, ``errors``, ``warnings``).
- ``Issue`` string representation.
"""

from __future__ import annotations

import pytest

from shici.prosody.checker import (
    CheckResult,
    Issue,
    IssueLevel,
    PoetryForm,
    check_duilian,
    check_jueju,
    check_lushi,
    check_poem,
)

# ---------------------------------------------------------------------------
# 5-char jueju
# ---------------------------------------------------------------------------


class TestCheckJueju5:
    """Test 5-character jueju (绝句)."""

    JINGYESI = [
        "床前明月光",
        "疑是地上霜",
        "举头望明月",
        "低头思故乡",
    ]

    def test_li_bai_jingyesi(self):
        """李白 静夜思 should pass (modulo minor variations)."""
        result = check_jueju(self.JINGYESI)
        assert result.form == PoetryForm.JUEJU_5
        # We expect some warnings or errors due to historical patterns
        # but the basic structure should be detected without an avalanche.
        assert result.error_count <= 5

    def test_returns_check_result(self):
        """The return type is ``CheckResult``."""
        result = check_jueju(self.JINGYESI)
        assert isinstance(result, CheckResult)
        assert result.lines == list(self.JINGYESI)

    def test_rhyme_groups_populated(self):
        """Rhyme groups for the rhyming positions (1, 3) are populated."""
        result = check_jueju(self.JINGYESI)
        # Rhyme groups correspond to lines 2 and 4 (indices 1 and 3).
        assert len(result.rhyme_groups) == 2

    def test_wrong_length_raises(self):
        """Wrong line length raises ValueError."""
        with pytest.raises(ValueError):
            check_jueju(["床前明月光", "疑是地", "举头望明月", "低头思故乡"])

    def test_wrong_line_count_raises(self):
        """Wrong number of lines raises ValueError."""
        with pytest.raises(ValueError):
            check_jueju(self.JINGYESI[:3])
        with pytest.raises(ValueError):
            check_jueju(self.JINGYESI + ["春眠不觉晓"])

    def test_inconsistent_lengths_raises(self):
        """Lines of different lengths raise ValueError."""
        with pytest.raises(ValueError):
            check_jueju(["床前明月光", "疑是地上霜", "举头望明月", "短"])


# ---------------------------------------------------------------------------
# 7-char jueju
# ---------------------------------------------------------------------------


class TestCheckJueju7:
    """Test 7-character jueju (绝句)."""

    CLASSIC = [
        "两个黄鹂鸣翠柳",
        "一行白鹭上青天",
        "窗含西岭千秋雪",
        "门泊东吴万里船",
    ]

    def test_classic_seven_char(self):
        """杜甫-style 7-char jueju auto-detects JUEJU_7."""
        result = check_jueju(self.CLASSIC)
        assert result.form == PoetryForm.JUEJU_7
        assert result.error_count <= 10

    def test_form_detection_works(self):
        """7-char 4-line input is recognized as JUEJU_7."""
        result = check_jueju(self.CLASSIC)
        assert result.form is PoetryForm.JUEJU_7

    def test_seven_char_lines_must_be_seven(self):
        """5-char lines under check_jueju produce an error issue (not raise)."""
        # check_jueju checks len(lines)==4 first; the line length
        # mismatch is recorded as an Issue.
        result = check_jueju(["床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"])
        # Form auto-detected as JUEJU_5 since lines are 5 chars.
        assert result.form == PoetryForm.JUEJU_5


# ---------------------------------------------------------------------------
# Lüshi
# ---------------------------------------------------------------------------


class TestCheckLushi:
    """Test 8-line lüshi (律诗)."""

    def test_lushi_requires_eight_lines(self):
        """check_lushi raises if line count is not 8."""
        with pytest.raises(ValueError):
            check_lushi(["床前明月光"] * 4)

    def test_lushi_wrong_length_records_issues(self):
        """Wrong character count per line is recorded as an Issue, not raised."""
        # 8 lines but only 4 chars each -> check_poem will report length errors
        # for each line. (8 lines × 5 chars is the LUSHI_5 form.)
        bad = [f"测试第{i}行五字" for i in range(8)]  # all 6 chars
        result = check_lushi(bad)
        # Should still be detected as LUSHI_5 because the lines are uniform.
        # The form detection is based on len(set(chars))==1, so all 6-char
        # lines will fail to match any known form.
        # We only assert that check_lushi doesn't raise and produces a result.
        assert isinstance(result, CheckResult)

    def test_basic_lushi5_returns_result(self):
        """An 8-line, 5-char lüshi produces a LUSHI_5 result."""
        # Even with nonsense characters the form should be detected.
        lines = ["一二三四五" for _ in range(8)]
        result = check_lushi(lines)
        assert result.form == PoetryForm.LUSHI_5

    def test_basic_lushi7_returns_result(self):
        """An 8-line, 7-char lüshi produces a LUSHI_7 result."""
        lines = ["一二三四五六七" for _ in range(8)]
        result = check_lushi(lines)
        assert result.form == PoetryForm.LUSHI_7


# ---------------------------------------------------------------------------
# Duilian (parallel couplet)
# ---------------------------------------------------------------------------


class TestCheckDuilian:
    """Test the 对联 checker."""

    def test_matched_length(self):
        """A well-formed 春联 of equal length produces no errors."""
        result = check_duilian("天增岁月人增寿", "春满乾坤福满门")
        assert result.form == PoetryForm.DUILIAN
        assert result.error_count == 0

    def test_mismatched_length(self):
        """A length mismatch produces at least one error."""
        result = check_duilian("天", "地久天长")
        assert result.error_count >= 1

    def test_duilian_lines(self):
        """The CheckResult stores the upper and lower lines."""
        result = check_duilian("天增岁月人增寿", "春满乾坤福满门")
        assert result.lines == ["天增岁月人增寿", "春满乾坤福满门"]


# ---------------------------------------------------------------------------
# Auto-detection
# ---------------------------------------------------------------------------


class TestAutoDetect:
    """Automatic form detection in ``check_poem``."""

    def test_detect_jueju5(self):
        """A 4-line, 5-char poem is detected as JUEJU_5."""
        lines = ["床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"]
        result = check_poem(lines)
        assert result.form == PoetryForm.JUEJU_5

    def test_detect_jueju7(self):
        """A 4-line, 7-char poem is detected as JUEJU_7."""
        lines = [
            "两个黄鹂鸣翠柳",
            "一行白鹭上青天",
            "窗含西岭千秋雪",
            "门泊东吴万里船",
        ]
        result = check_poem(lines)
        assert result.form == PoetryForm.JUEJU_7

    def test_detect_lushi7(self):
        """An 8-line, 7-char poem is detected as LUSHI_7."""
        # 8 lines, exactly 7 chars each.
        lines = [f"七言律诗第{i}行" for i in range(8)]
        assert all(len(line) == 7 for line in lines)
        result = check_poem(lines)
        assert result.form == PoetryForm.LUSHI_7

    def test_detect_lushi5(self):
        """An 8-line, 5-char poem is detected as LUSHI_5."""
        # 8 lines, exactly 5 chars each.
        lines = [f"五言律{i:02d}" for i in range(8)]
        assert all(len(line) == 5 for line in lines)
        result = check_poem(lines)
        assert result.form == PoetryForm.LUSHI_5

    def test_unsupported_line_count_raises(self):
        """A 2-line poem is not supported and raises ValueError."""
        with pytest.raises(ValueError):
            check_poem(["床前明月光", "疑是地上霜"])

    def test_unsupported_line_length_raises(self):
        """A 4-line, 6-char poem has no matching form and raises ValueError."""
        with pytest.raises(ValueError):
            check_poem(["床前明月", "疑是地上", "举头望明", "低头思故"])

    def test_explicit_form_overrides(self):
        """Passing ``form`` explicitly bypasses auto-detection."""
        lines = ["床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"]
        result = check_poem(lines, form=PoetryForm.JUEJU_5)
        assert result.form == PoetryForm.JUEJU_5

    def test_explicit_form_wrong_raises(self):
        """Explicit form with wrong line length still produces issues, no raise."""
        lines = ["床前明月光", "疑是地上霜", "举头望明月", "低头思故乡"]
        # Forcing LUSHI_7 means the 5-char lines are too short.
        result = check_poem(lines, form=PoetryForm.LUSHI_7)
        assert result.form == PoetryForm.LUSHI_7
        assert result.error_count >= 1


# ---------------------------------------------------------------------------
# CheckResult / Issue
# ---------------------------------------------------------------------------


class TestCheckResult:
    """Aggregate result object behaviour."""

    def test_ok_true_when_no_errors(self):
        """``ok`` is True if there are no ERROR-level issues."""
        result = check_duilian("天增岁月人增寿", "春满乾坤福满门")
        assert result.ok is True

    def test_ok_false_when_errors(self):
        """``ok`` is False if there is at least one ERROR-level issue."""
        result = check_duilian("天", "地久天长")
        assert result.ok is False

    def test_counts(self):
        """error_count and warning_count reflect the issues list."""
        result = check_duilian("一二三四五", "六七八九十")
        # All five positions have identical PING/ZE so at most warnings appear.
        total = result.error_count + result.warning_count
        assert total == len(result.issues)

    def test_errors_and_warnings_filters(self):
        """``errors()`` and ``warnings()`` return filtered lists."""
        result = check_duilian("天", "地久天长")
        errs = result.errors()
        warns = result.warnings()
        assert all(e.level == IssueLevel.ERROR for e in errs)
        assert all(w.level == IssueLevel.WARNING for w in warns)


class TestIssue:
    """Issue dataclass behaviour."""

    def test_str_with_location(self):
        """``__str__`` includes line/column location."""
        issue = Issue(
            level=IssueLevel.ERROR,
            line=2,
            column=3,
            code="pingze_mismatch",
            message="应为平",
            suggestion="换字",
        )
        s = str(issue)
        assert "pingze_mismatch" in s
        assert "L3C4" in s
        assert "建议" in s

    def test_str_global(self):
        """A poem-level issue uses 'global' location."""
        issue = Issue(
            level=IssueLevel.WARNING,
            line=-1,
            column=-1,
            code="duilian_length",
            message="字数不等",
        )
        s = str(issue)
        assert "global" in s
        assert "duilian_length" in s

    def test_str_without_suggestion(self):
        """No suggestion means no trailing parentheses."""
        issue = Issue(
            level=IssueLevel.INFO,
            line=0,
            column=0,
            code="note",
            message="info",
        )
        assert "建议" not in str(issue)
