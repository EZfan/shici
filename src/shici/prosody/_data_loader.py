"""Adapter between vendored pingshui/xinyun JSON and the local classifier/rhyme API.

Vendored data shape (gelv-poetry):
    pingshui.json = {char: [[yunbu, diao], ...], ...}      # diao ∈ {上平, 下平, 上, 去, 入}
    xinyun.json   = {char: [[yunbu, tone], ...], ...}      # tone ∈ {平, 仄}

Local shici API shape (classifier.py / rhyme.py) expects per-character dicts:
    {char: {"readings": [(yunbu, diao), ...],
            "ping": bool,
            "rhyme_group": "<上平x... / 下平x... / ...>" | None}}

The vendored yunbu names use the short form "一东", "二冬", "入声一屋".
The local RhymeGroup enum uses the long form "上平一东", "上平二冬",
"入声一屋". We normalize here so the rest of the shici package works
unchanged, while the JSON files on disk remain pristine copies of the
upstream MIT-licensed data.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources
from json import loads

# Tone -> 平? mapping. Matches gelv-poetry's conventions:
#   平水韵: 上平 / 下平 = 平 ;  上 / 去 / 入 = 仄
#   新韵 : 平 = 平 ; 仄 = 仄
_PING_TONES_PINGSHUI = {"上平", "下平"}
_PING_TONES_XINYUN = {"平"}

# 中文数字
_CN_DIGITS = "一二三四五六七八九十"


def _normalize_yunbu_pingshui(yunbu: str, diao: str) -> str:
    """Prefix 平声/上声/去声/入声 to a short yunbu name to match RhymeGroup.

    Vendored data uses bare "一东" / "二冬" / "入声一屋". The local enum
    wants "上平一东" / "上平二冬" / "入声一屋". We add the tone-class prefix
    derived from the diao label when it's a 平声 部.
    """
    if yunbu.startswith("入声"):
        return yunbu  # already prefixed
    if diao in ("上平", "下平"):
        return f"{diao}{yunbu}"
    if diao in ("上", "去"):
        return f"{diao}声{yunbu}"
    # 入 without 入声 prefix shouldn't normally appear, but be safe.
    return f"入声{yunbu}"


def _normalize_yunbu_xinyun(yunbu: str, tone: str) -> str:
    """新韵 yunbu is already short ("一麻", "二波"...). We keep it as-is,
    because RhymeBook doesn't validate against the 平水韵 enum — it stores
    the raw label. Callers that care about specific names can map separately."""
    return yunbu


@lru_cache(maxsize=1)
def load_pingshui() -> dict[str, dict]:
    """Load pingshui.json and adapt to shici's per-character dict schema."""
    raw = resources.files("shici.prosody.data").joinpath("pingshui.json").read_text(
        encoding="utf-8"
    )
    data = loads(raw)
    out: dict[str, dict] = {}
    for char, entries in data.items():
        readings = [
            (_normalize_yunbu_pingshui(yunbu, diao), diao)
            for yunbu, diao in entries
        ]
        ping = any(diao in _PING_TONES_PINGSHUI for _, diao in readings)
        # Prefer a 平声 韵部 for rhyme grouping; fall back to first reading.
        ping_group = next(
            (y for y, d in readings if d in _PING_TONES_PINGSHUI),
            readings[0][0] if readings else None,
        )
        out[char] = {
            "readings": tuple(readings),
            "ping": ping,
            "rhyme_group": ping_group,
        }
    return out


@lru_cache(maxsize=1)
def load_xinyun() -> dict[str, dict]:
    """Load xinyun.json and adapt to shici's per-character dict schema."""
    raw = resources.files("shici.prosody.data").joinpath("xinyun.json").read_text(
        encoding="utf-8"
    )
    data = loads(raw)
    out: dict[str, dict] = {}
    for char, entries in data.items():
        readings = [
            (_normalize_yunbu_xinyun(yunbu, tone), tone)
            for yunbu, tone in entries
        ]
        ping = any(tone in _PING_TONES_XINYUN for _, tone in readings)
        ping_group = next(
            (y for y, t in readings if t in _PING_TONES_XINYUN),
            readings[0][0] if readings else None,
        )
        out[char] = {
            "readings": tuple(readings),
            "ping": ping,
            "rhyme_group": ping_group,
        }
    return out


__all__ = ["load_pingshui", "load_xinyun"]
