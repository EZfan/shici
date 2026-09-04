"""Rhyme (韵部) classification.

In pingshuiyun (平水韵) the 106 traditional rhyme groups classify final
characters. The exact mapping between characters and groups is part of
the bundled pingshui.json data file (vendored from gelv-poetry).

This module provides a small wrapper around that data to expose:
  - RhymeGroup enum
  - lookup_rhyme(char) -> RhymeGroup
  - classify_rhyme(line) -> list[RhymeGroup]
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from ._data_loader import load_pingshui


class RhymeGroup(str, Enum):
    """The 106 traditional Pingshui rhyme groups."""

    # 上平 (1-15)
    SHANG_PING_1_DONG = "上平一东"
    SHANG_PING_2_DONG = "上平二冬"
    SHANG_PING_3_JUN = "上平三江"
    SHANG_PING_4_XI = "上平四支"
    SHANG_PING_5_MI = "上平五微"
    SHANG_PING_6_YU = "上平六鱼"
    SHANG_PING_7_YU = "上平七虞"
    SHANG_PING_8_QI = "上平八齐"
    SHANG_PING_9_GAO = "上平九佳"
    SHANG_PING_10_HUI = "上平十灰"
    SHANG_PING_11_ZHEN = "上平十一真"
    SHANG_PING_12_WEN = "上平十二文"
    SHANG_PING_13_YUAN = "上平十三元"
    SHANG_PING_14_HAO = "上平十四寒"
    SHANG_PING_15_GE = "上平十五删"
    # 下平 (1-15)
    XIA_PING_1_XIAN = "下平一先"
    XIA_PING_2_XIAO = "下平二萧"
    XIA_PING_3_JAO = "下平三肴"
    XIA_PING_4_HAI = "下平四豪"
    XIA_PING_5_GENG = "下平五歌"
    XIA_PING_6_MA = "下平六麻"
    XIA_PING_7_YANG = "下平七阳"
    XIA_PING_8_GENG = "下平八庚"
    XIA_PING_9_QING = "下平九青"
    XIA_PING_10_DENG = "下平十蒸"
    XIA_PING_11_DANG = "下平十一尤"
    XIA_PING_12_SHEN = "下平十二侵"
    XIA_PING_13_TAN = "下平十三覃"
    XIA_PING_14_TAN_2 = "下平十四盐"
    XIA_PING_15_JIAN = "下平十五咸"
    # 上声 (29)
    SHANG_SHENG_1_DONG = "上声一董"
    SHANG_SHENG_2_DONG = "上声二肿"
    SHANG_SHENG_3_JIANG = "上声三讲"
    SHANG_SHENG_4_ZHI = "上声四纸"
    SHANG_SHENG_5_YI = "上声五尾"
    SHANG_SHENG_6_YU = "上声六语"
    SHANG_SHENG_7_QU = "上声七麌"
    SHANG_SHENG_8_JI = "上声八荠"
    SHANG_SHENG_9_JIA = "上声九蟹"
    SHANG_SHENG_10_HAI = "上声十贿"
    SHANG_SHENG_11_ZHEN = "上声十一轸"
    SHANG_SHENG_12_WEN = "上声十二吻"
    SHANG_SHENG_13_YUAN = "上声十三阮"
    SHANG_SHENG_14_HAN = "上声十四旱"
    SHANG_SHENG_15_SHAN = "上声十五潸"
    SHANG_SHENG_16_XIAN = "上声十六铣"
    SHANG_SHENG_17_XIAO = "上声十七筱"
    SHANG_SHENG_18_XIAO = "上声十八巧"
    SHANG_SHENG_19_HAO = "上声十九皓"
    SHANG_SHENG_20_GENG = "上声二十哿"
    SHANG_SHENG_21_MA = "上声二十一马"
    SHANG_SHENG_22_YANG = "上声二十二养"
    SHANG_SHENG_23_GENG = "上声二十三梗"
    SHANG_SHENG_24_JING = "上声二十四迥"
    SHANG_SHENG_25_DENG = "上声二十五有"
    SHANG_SHENG_26_QIN = "上声二十六寝"
    SHANG_SHENG_27_TAN = "上声二十七感"
    SHANG_SHENG_28_YAN = "上声二十八俭"
    SHANG_SHENG_29_JIAN = "上声二十九豏"
    # 去声 (30)
    QU_SHENG_1_SONG = "去声一送"
    QU_SHENG_2_SONG = "去声二宋"
    QU_SHENG_3_JIANG = "去声三绛"
    QU_SHENG_4_ZHI = "去声四寘"
    QU_SHENG_5_WEI = "去声五未"
    QU_SHENG_6_YU = "去声六御"
    QU_SHENG_7_QU = "去声七遇"
    QU_SHENG_8_JI = "去声八霁"
    QU_SHENG_9_XIE = "去声九泰"
    QU_SHENG_10_JIE = "去声十卦"
    QU_SHENG_11_TEAM = "去声十一队"
    QU_SHENG_12_ZHEN = "去声十二震"
    QU_SHENG_13_WEN = "去声十三问"
    QU_SHENG_14_YUAN = "去声十四愿"
    QU_SHENG_15_HAN = "去声十五翰"
    QU_SHENG_16_GE = "去声十六谏"
    QU_SHENG_17_XIAN = "去声十七霰"
    QU_SHENG_18_XIAO = "去声十八啸"
    QU_SHENG_19_XIAO = "去声十九效"
    QU_SHENG_20_HAO = "去声二十号"
    QU_SHENG_21_MA = "去声二十一箇"
    QU_SHENG_22_MA = "去声二十二祃"
    QU_SHENG_23_YANG = "去声二十三漾"
    QU_SHENG_24_GENG = "去声二十四敬"
    QU_SHENG_25_JING = "去声二十五径"
    QU_SHENG_26_DENG = "去声二十六宥"
    QU_SHENG_27_QIN = "去声二十七沁"
    QU_SHENG_28_TAN = "去声二十八勘"
    QU_SHENG_29_YAN = "去声二十九艳"
    QU_SHENG_30_JIAN = "去声三十陷"
    # 入声 (17)
    RU_SHENG_1_WU = "入声一屋"
    RU_SHENG_2_WU = "入声二沃"
    RU_SHENG_3_JUE = "入声三觉"
    RU_SHENG_4_ZHI = "入声四质"
    RU_SHENG_5_MI = "入声五物"
    RU_SHENG_6_YUE = "入声六月"
    RU_SHENG_7_XUE = "入声七曷"
    RU_SHENG_8_JIA = "入声八黠"
    RU_SHENG_9_GE = "入声九屑"
    RU_SHENG_10_XIE = "入声十叶"
    RU_SHENG_11_GE = "入声十一陌"
    RU_SHENG_12_MIE = "入声十二锡"
    RU_SHENG_13_GE = "入声十三职"
    RU_SHENG_14_WU = "入声十四缉"
    RU_SHENG_15_JIA = "入声十五合"
    RU_SHENG_16_TIE = "入声十六叶"
    RU_SHENG_17_YUE = "入声十七洽"

    @classmethod
    def from_string(cls, value: str) -> "RhymeGroup | None":
        """Best-effort lookup from any string. Returns None if no match."""
        for member in cls:
            if member.value == value:
                return member
        return None


@lru_cache(maxsize=1)
def _load_rhyme_map() -> dict[str, str]:
    """Load char -> rhyme_group mapping from bundled data.

    Vendored pingshui.json (gelv-poetry) is normalized by ``_data_loader``
    into per-character dicts with a ``rhyme_group`` key.
    """
    data = load_pingshui()
    mapping: dict[str, str] = {}
    for char, info in data.items():
        rg = info.get("rhyme_group")
        if rg:
            mapping[char] = rg
    return mapping


class RhymeBook:
    """Lazy rhyme lookup table."""

    def __init__(self, mapping: dict[str, str] | None = None):
        self._mapping = mapping if mapping is not None else _load_rhyme_map()

    def lookup(self, char: str) -> RhymeGroup | None:
        """Find the rhyme group of a single character."""
        return RhymeGroup.from_string(self._mapping.get(char, ""))

    def group_of(self, char: str) -> RhymeGroup | None:
        return self.lookup(char)

    def is_same_group(self, a: str, b: str) -> bool:
        ga = self.lookup(a)
        gb = self.lookup(b)
        return ga is not None and ga == gb

    def rhymes_with(self, char: str, candidates: list[str]) -> list[str]:
        """Return candidates that rhyme with the given character."""
        target = self.lookup(char)
        if target is None:
            return []
        return [c for c in candidates if self.lookup(c) == target]

    def __contains__(self, char: str) -> bool:
        return char in self._mapping


_BOOK: RhymeBook | None = None


def lookup_rhyme(char: str) -> RhymeGroup | None:
    """Classify a single character into a rhyme group."""
    global _BOOK
    if _BOOK is None:
        _BOOK = RhymeBook()
    return _BOOK.lookup(char)


def classify_rhyme(line: str) -> list[RhymeGroup | None]:
    """Classify each Chinese character in a line."""
    return [lookup_rhyme(c) for c in line if _is_chinese(c)]


def _is_chinese(char: str) -> bool:
    if not char:
        return False
    code = ord(char)
    return (
        0x4E00 <= code <= 0x9FFF
        or 0x3400 <= code <= 0x4DBF
        or 0x20000 <= code <= 0x2A6DF
    )


__all__ = [
    "RhymeGroup",
    "RhymeBook",
    "lookup_rhyme",
    "classify_rhyme",
]