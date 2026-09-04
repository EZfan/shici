#!/usr/bin/env python3
# Vendored from gelv-poetry (https://github.com/chenmisss/gelv-poetry) under MIT License.
# Original file: scripts/check.py  |  Original copyright (c) 2026 chenmisss.
# Local modifications: DATA path adjusted so this module loads the sibling data/ folder
# of prosody/ in the shici package (original gelv-poetry used scripts/..).
"""
近体诗格律校验器 — 五绝 / 五律 / 七绝 / 七律
双轨韵书：默认平水韵（含入声），--xin 切中华新韵（十四韵）。

子命令：
  tone   查字平仄与所属韵部（两套韵书都给）
  yun    列出某韵书一个韵部下的常用平声字（找韵脚备选）
  template  打印某体裁的平仄谱（中=可平可仄）
  check  校验一首诗：逐句标平仄、查押韵/重韵/粘对/特拗/孤平/三平尾/对仗

数据来源：charlesix59/chinese_word_rhyme （平水韵 / 中华新韵 / 平仄）。
设计要点：生成靠模型、判定靠本脚本；多音字「任一读音满足即过」。
"""

import argparse
import json
import os
import re
import sys

# Vendored path fix: original used ".." because scripts/ sits above data/.
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PING = json.load(open(os.path.join(DATA, "pingshui.json"), encoding="utf-8"))
XIN = json.load(open(os.path.join(DATA, "xinyun.json"), encoding="utf-8"))
# 字频排名（索引越小越常用）；缺文件则为空，yun 不排序也不报错
_FREQ_FILE = os.path.join(DATA, "charfreq.txt")
FREQ = (
    {ch: i for i, ch in enumerate(open(_FREQ_FILE, encoding="utf-8").read().strip())}
    if os.path.exists(_FREQ_FILE)
    else {}
)

PUNC = "，。！？、；：,.!?;:\n\r\t 　“”\"'《》（）()"


# ---------- 读音查询：返回 [(韵部, 声调标签, 平/仄), ...] ----------
def readings(ch, xin=False):
    out = []
    if xin:
        for yun, tone in XIN.get(ch, []):  # tone 已是 平/仄
            out.append((yun, tone, tone))
    else:
        for yun, diao in PING.get(ch, []):  # diao ∈ 上平/下平/上/去/入
            tone = "平" if diao in ("上平", "下平") else "仄"
            out.append((yun, diao, tone))
    return out


def tones(ch, xin=False):
    return set(r[2] for r in readings(ch, xin))


def can(ch, t, xin=False):  # 该字「可以」读成 t（平/仄）
    return t in tones(ch, xin)


def only(ch, t, xin=False):  # 该字「只能」读成 t（用于三平尾/孤平这类需保守判定处）
    ts = tones(ch, xin)
    return ts == {t}


def known(ch, xin=False):
    return len(readings(ch, xin)) > 0


# ---------- 平声韵部（押韵用） ----------
def ping_yunbu(ch, xin=False):
    return set(r[0] for r in readings(ch, xin) if r[2] == "平")


# =========================================================
#  平仄谱：四个基本句式 + 对/粘 状态机
# =========================================================
# 五言四式（A 仄起仄收 / B 平起平收·韵 / C 平起仄收 / D 仄起平收·韵）
BASE5 = {"A": "仄仄平平仄", "B": "平平仄仄平", "C": "平平平仄仄", "D": "仄仄仄平平"}


# 七言 = 五言前加两字、平仄相反
def to7(p5):
    head = "平平" if p5[0] == "仄" else "仄仄"
    return head + p5


BASE7 = {k: to7(v) for k, v in BASE5.items()}

# 展示用「可平可仄」掩码（保守：只放确实安全的活字位）
MASK5 = {"A": "中仄平平仄", "B": "平平中仄平", "C": "中平平仄仄", "D": "中仄仄平平"}
MASK7 = {"A": "中平中仄平平仄", "B": "中仄平平中仄平", "C": "中仄中平平仄仄", "D": "中平中仄仄平平"}

# 由首句字母推出整诗字母序列（对：A-B C-D D-B B-D；粘后转下一出句）
DUI = {"A": "B", "C": "D", "D": "B", "B": "D"}  # 出句 -> 对句
NEXT = {"B": "C", "D": "A"}  # 对句(平收) -> 粘后的下一出句


def letters(first, ju):
    seq = [first]
    while len(seq) < ju:
        last = seq[-1]
        if len(seq) % 2 == 1:  # 刚放的是出句 -> 补对句
            seq.append(DUI[last])
        else:  # 刚放的是对句 -> 粘转下一出句
            seq.append(NEXT[last])
    return seq[:ju]


def base_of(letter, yan):
    return (BASE5 if yan == 5 else BASE7)[letter]


def mask_of(letter, yan):
    return (MASK5 if yan == 5 else MASK7)[letter]


# 由「平起/仄起 + 首句是否入韵」定首句字母
def first_letter(qi, ru):
    # qi: '平'/'仄'（按首句第二字）；ru: 首句是否入韵
    if qi == "仄":
        return "D" if ru else "A"
    else:
        return "B" if ru else "C"


STRICT5 = {1, 3}  # 0-indexed 的强制位：第2、第4字
STRICT7 = {1, 3, 5}  # 第2、第4、第6字


# =========================================================
#  打印平仄谱
# =========================================================
def cmd_template(args):
    yan, ju = args.yan, args.ju
    name5 = {4: "五绝", 8: "五律"}
    name7 = {4: "七绝", 8: "七律"}
    tname = (name5 if yan == 5 else name7)[ju]
    rooms = []
    for ru in [True, False] if args.ru is None else [args.ru]:
        for qi in ["平", "仄"] if args.qi is None else [args.qi]:
            seq = letters(first_letter(qi, ru), ju)
            title = f"{tname}·{qi}起{'首句入韵' if ru else '首句不入韵'}"
            lines = []
            for i, L in enumerate(seq):
                m = mask_of(L, yan)
                tail = "（韵）" if base_of(L, yan)[-1] == "平" and (ru or i % 2 == 1) else ""
                lines.append("    " + " ".join(m) + tail)
            rooms.append(title + "\n" + "\n".join(lines))
    print(("\n\n").join(rooms))
    print(
        "\n注：中=可平可仄；末标（韵）处须押同一平声韵部。一三五位虽多可活，"
        "仍须避孤平、三平尾、三仄尾——交给 check 把关。"
    )


# =========================================================
#  查字 / 查韵
# =========================================================
def cmd_tone(args):
    for ch in args.chars:
        if ch in PUNC or not ch.strip():
            continue
        p = readings(ch, False)
        x = readings(ch, True)
        ps = "、".join(f"{y}({d}/{t})" for y, d, t in p) or "—（不在平水韵表）"
        xs = "、".join(f"{y}({t})" for y, d, t in x) or "—"
        flag = ""
        if any(d == "入" for y, d, t in p):
            flag += "  ⚠入声→仄(普通话易误判)"
        if len(tones(ch, False)) == 2:
            flag += "  ⚠可平可仄"
        print(f"{ch}  平水韵: {ps}   新韵: {xs}{flag}")


def cmd_yun(args):
    # 列出平水韵某平声韵部的字（帮挑韵脚）
    target = args.yunbu
    chars = []
    seen = set()
    if args.xin:
        for ch, lst in XIN.items():
            for yun, tone in lst:
                if yun == target and tone == "平" and ch not in seen:
                    seen.add(ch)
                    chars.append(ch)
    else:
        for ch, lst in PING.items():
            for yun, diao in lst:
                if yun == target and diao in ("上平", "下平") and ch not in seen:
                    seen.add(ch)
                    chars.append(ch)
    if not chars:
        print(
            f"未找到韵部「{target}」。平水韵平声部示例：一东 二冬 … 十五删 / 一先 … ；"
            f"新韵：一麻 二波 … 十四姑。"
        )
        return
    chars.sort(key=lambda c: FREQ.get(c, 10**9))  # 常用在前、生僻沉底
    common = [c for c in chars if c in FREQ]
    rare_n = len(chars) - len(common)
    head = "新韵" if args.xin else "平水韵"
    print(f"{head}「{target}」平声字（共{len(chars)}，常用在前）：")
    if getattr(args, "all", False):
        print("".join(chars))
    else:
        print("".join((common or chars)[:80]))
        if rare_n:
            print(f"（另有 {rare_n} 生僻字已略；--all 看全部）")


# =========================================================
#  校验一首诗
# =========================================================
def split_lines(text):
    # 按标点/换行切句，保留汉字
    raw = re.split(r"[，。！？、；：,.!?;:\n]+", text)
    return ["".join(c for c in s if c not in PUNC and c.strip()) for s in raw if s.strip()]


def line_tone_str(line, xin):
    # 返回每字的代表平仄串（多音以 '中' 表示），及详细
    s = ""
    for ch in line:
        ts = tones(ch, xin)
        if ts == {"平"}:
            s += "平"
        elif ts == {"仄"}:
            s += "仄"
        elif ts == {"平", "仄"}:
            s += "中"
        else:
            s += "?"
    return s


def fits(ch, want, xin):
    # 字能否落在 want（平/仄/中）位上
    if want == "中":
        return True
    return can(ch, want, xin) or not known(ch, xin)


def is_tewa(line, L, yan):
    # 特拗（特定拗句，公认合律变体）：
    #   五言 C 平平平仄仄 → 平平仄平仄；七言 仄仄平平平仄仄 → 仄仄平平仄平仄
    # 须第3字(七言第5字)转仄来补，否则只是无救之拗，不放行。
    if L != "C":
        return False
    if yan == 5 and len(line) >= 5:  # 平[平仄平仄]
        return (
            can(line[1], "平") and can(line[2], "仄") and can(line[3], "平") and can(line[4], "仄")
        )
    if yan == 7 and len(line) >= 7:  # 仄仄平[平仄平仄]
        return (
            can(line[3], "平") and can(line[4], "仄") and can(line[5], "平") and can(line[6], "仄")
        )
    return False


def cmd_check(args):
    text = args.text if args.text else sys.stdin.read()
    xin = args.xin
    lines = split_lines(text)
    n = len(lines)
    # 推断言数
    yan = args.yan or (7 if (lines and len(lines[0]) == 7) else 5)
    if n not in (4, 8):
        print(f"⚠ 句数={n}，近体诗应为 4 句（绝句）或 8 句（律诗）。仍按 {n} 句尽力校验。")
    bad_len = [i + 1 for i, l in enumerate(lines) if len(l) != yan]
    if bad_len:
        print(
            f"⚠ 第 {bad_len} 句字数不是 {yan}："
            + " | ".join(f"{i + 1}.{lines[i]}({len(lines[i])})" for i in bad_len)
        )

    strict = STRICT5 if yan == 5 else STRICT7
    sys_name = "中华新韵" if xin else "平水韵"
    print(f"== 格律体检（{ {4: '绝句', 8: '律诗'}.get(n, '?') } · {yan}言 · {sys_name}）==\n")

    # --- 推首句字母：枚举使「违规最少」的解释（应对多音/拗句） ---
    best = None
    for L0 in "ABCD":
        seq = letters(L0, n if n in (4, 8) else (8 if n > 4 else 4))
        viol = 0
        for i, line in enumerate(lines):
            if i >= len(seq):
                break
            patt = base_of(seq[i], yan)
            for j in strict | {yan - 1}:
                if j < len(line) and j < len(patt):
                    if not fits(line[j], patt[j], xin):
                        viol += 1
        if best is None or viol < best[0]:
            best = (viol, L0, seq)
    _, L0, seq = best

    rhyme_chars = []  # (句号, 字)
    issues = []
    for i, line in enumerate(lines):
        L = seq[i] if i < len(seq) else "?"
        patt = base_of(L, yan) if L != "?" else "?" * yan
        got = line_tone_str(line, xin)
        marks = []
        tewa = is_tewa(line, L, yan)
        # 强制位 + 收（特拗句合律，放行并标注）
        if not tewa:
            for j in strict | {yan - 1}:
                if j < len(line) and j < len(patt) and not fits(line[j], patt[j], xin):
                    kind = "失对/失粘" if j in strict else "句末"
                    marks.append(f"第{j + 1}字「{line[j]}」({got[j]})应{patt[j]}（{kind}）")
        # 押韵句（对句 + 首句入韵时的首句）
        is_rhyme = (patt[-1] == "平") and (
            i % 2 == 1 or (i == 0 and patt[-1] == "平" and L in ("B", "D"))
        )
        if is_rhyme and line:
            rhyme_chars.append((i + 1, line[-1]))
            if not ping_yunbu(line[-1], xin):
                marks.append(f"韵脚「{line[-1]}」非平声字")
        # 三平尾 / 三仄尾（保守：以「只能」判）
        if len(line) >= 3:
            t3 = [tones(c, xin) for c in line[-3:]]
            if all(t == {"平"} for t in t3):
                marks.append("三平尾(忌)")
            elif all(t == {"仄"} for t in t3):
                marks.append("三仄尾(慎)")
        # 孤平：仅 B 型平收句
        if L == "B":
            body = line[:-1]
            maybe = sum(1 for c in body if can(c, "平", xin))
            if maybe <= 1:
                marks.append("孤平(忌，可本句自救→倒数第三字改平)")
        tag = "✓" if not marks else "✗"
        rhyme_tag = "  ←韵" if is_rhyme else ""
        note = "  〔特拗·合律〕" if tewa else ""
        print(
            f"  {i + 1} {line}  [{got}]  谱{patt}({L}){rhyme_tag}{note}  {tag}{(' ' + '；'.join(marks)) if marks else ''}"
        )
        if marks:
            issues.append((i + 1, marks))

    # --- 押韵汇总 ---
    print()
    if rhyme_chars:
        sets = []
        for _, c in rhyme_chars:
            sets.append(ping_yunbu(c, xin))
        common = set.intersection(*sets) if all(sets) else set()
        names = " ".join(f"{i}{c}" for i, c in rhyme_chars)
        rc = [c for _, c in rhyme_chars]
        dup = sorted({c for c in rc if rc.count(c) > 1})
        if dup:
            print(f"⚠ 重韵：韵脚「{'、'.join(dup)}」重复作韵——近体诗忌重韵（同字不可重复押）")
            issues.append((-1, ["重韵"]))
        if common:
            print(f"押韵 ✓ 韵脚 [{names}] 同属平声韵部：{'、'.join(sorted(common))}")
        else:
            detail = "；".join(
                f"{c}={'/'.join(sorted(ping_yunbu(c, xin))) or '非平/未知'}" for _, c in rhyme_chars
            )
            print(f"押韵 ✗ 韵脚未落同一平声韵部 → {detail}")
            print("   （提示：平水韵里 山/间[删] 与 天/年[先] 不可同押；东[一东]≠冬[二冬]）")
    else:
        print("未识别到韵脚。")

    # --- 律诗对仗：颔联(3-4)、颈联(5-6) ---
    if n == 8:
        print()
        for cp, (a, b) in [("颔联", (2, 3)), ("颈联", (4, 5))]:
            la, lb = lines[a], lines[b]
            probs = []
            if len(la) == len(lb):
                same = [k for k in range(len(la)) if la[k] == lb[k]]
                if same:
                    probs.append("同位同字：" + "、".join(f"第{k + 1}字「{la[k]}」" for k in same))
            else:
                probs.append("两句字数不等")
            status = "需人工核词性" if not probs else "✗ " + "；".join(probs)
            print(f"对仗·{cp}（{la} / {lb}）：{status}")
        print("   （脚本只查字数/同字/平仄相对；词性相对、避合掌请据 reference/gelv.md 自检）")

    # --- 跨句重字提示（非硬伤，仅 warn）。同句叠字如「萧萧/滚滚」是修辞，豁免 ---
    line_of = {}
    for i, ln in enumerate(lines):
        for c in set(ln):  # set：同句重复只算一次，放过叠字
            line_of.setdefault(c, []).append(i + 1)
    rep = sorted([c for c, ls in line_of.items() if len(ls) >= 2], key=lambda c: -len(line_of[c]))
    if rep:
        parts = [f"「{c}」第{'、'.join(map(str, line_of[c]))}句" for c in rep]
        print()
        print("⚠ 跨句重字（非硬伤，留意是否有意呼应）：" + "；".join(parts))

    print()
    print(
        f"判定首句式：{ {'A': '仄起·首句不入韵', 'B': '平起·首句入韵', 'C': '平起·首句不入韵', 'D': '仄起·首句入韵'}.get(L0, '?') }"
        f"（标准谱字母序 {''.join(seq)}）"
    )
    nbad = len(issues)
    print(f"结论：{'格律基本合于谱 ✓' if nbad == 0 else f'有 {nbad} 处待核问题，见上方 ✗/⚠'}")


# =========================================================
def main():
    ap = argparse.ArgumentParser(description="近体诗格律校验器")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("tone")
    p.add_argument("chars")
    p.set_defaults(func=cmd_tone)
    p = sub.add_parser("yun")
    p.add_argument("yunbu")
    p.add_argument("--xin", action="store_true")
    p.add_argument("--all", action="store_true")
    p.set_defaults(func=cmd_yun)
    p = sub.add_parser("template")
    p.add_argument("--yan", type=int, choices=[5, 7], required=True)
    p.add_argument("--ju", type=int, choices=[4, 8], required=True)
    p.add_argument("--qi", choices=["平", "仄"], default=None)
    p.add_argument("--ru", type=lambda s: s in ("1", "true", "yes", "y"), default=None)
    p.set_defaults(func=cmd_template)
    p = sub.add_parser("check")
    p.add_argument("text", nargs="?", default=None)
    p.add_argument("--xin", action="store_true")
    p.add_argument("--yan", type=int, choices=[5, 7], default=None)
    p.set_defaults(func=cmd_check)

    a = ap.parse_args()
    if not getattr(a, "cmd", None):
        ap.print_help()
        return
    a.func(a)


if __name__ == "__main__":
    main()
