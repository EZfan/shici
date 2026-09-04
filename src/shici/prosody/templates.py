"""词牌 (cipai) template registry.

Each cipai is encoded as a structured CipaiTemplate describing its line
count, character counts per line, tonal patterns, and rhyme positions.
The templates are loaded from data/cipai/*.json files (see
scripts/build_corpora.py for the build pipeline).

This module also provides a built-in registry with the most common ~20
cipai so the package works out-of-the-box without data files.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .rhyme import RhymeGroup


@dataclass(frozen=True)
class CipaiTemplate:
    """A 词牌 template."""

    name: str
    category: str  # 小令 / 中调 / 长调
    line_count: int
    char_counts: tuple[int, ...]
    tone_patterns: tuple[str, ...]
    rhyme_positions: tuple[int, ...]
    rhyme_groups_allowed: tuple[RhymeGroup, ...] = ()
    duilian_pairs: tuple[tuple[int, int], ...] = ()
    example_author: str = ""
    example_title: str = ""
    example_lines: tuple[str, ...] = ()

    @property
    def total_chars(self) -> int:
        return sum(self.char_counts)

    @property
    def shangque(self) -> tuple[tuple[int, ...], ...]:
        """Split into 上阕 (upper stanza) and 下阕 (lower stanza)."""
        # Default heuristic: split by rhyme pattern — first contiguous
        # rhyme block is 上阕, the rest is 下阕.
        if not self.rhyme_positions:
            return (tuple(range(self.line_count)),)
        if len(self.rhyme_positions) == 1:
            return ((0,), tuple(range(1, self.line_count)))
        # If the rhyme pattern repeats after a midpoint, split there.
        # Find the gap between adjacent rhyme positions.
        rp = list(self.rhyme_positions)
        gaps = [(rp[i + 1] - rp[i], i) for i in range(len(rp) - 1)]
        if not gaps:
            return (tuple(range(self.line_count)),)
        max_gap, idx = max(gaps)
        if max_gap > 3:
            split = rp[idx] + 1
            return (
                tuple(range(split)),
                tuple(range(split, self.line_count)),
            )
        return (tuple(range(self.line_count)),)


# Built-in registry — most common ~20 cipai.
# Data sourced from public domain references; tone patterns follow the
# classical 钦定词谱 and 龙榆生《唐宋名家词选》 conventions.
_BUILTIN_REGISTRY: dict[str, CipaiTemplate] = {}


def _register(template: CipaiTemplate) -> CipaiTemplate:
    _BUILTIN_REGISTRY[template.name] = template
    return template


def _T(
    name: str,
    category: str,
    char_counts: Sequence[int],
    tone_patterns: Sequence[str],
    rhyme_positions: Sequence[int],
    rhyme_groups: Sequence[RhymeGroup] = (),
    duilian: Sequence[tuple[int, int]] = (),
    example_author: str = "",
    example_title: str = "",
    example_lines: Sequence[str] = (),
) -> CipaiTemplate:
    return _register(
        CipaiTemplate(
            name=name,
            category=category,
            line_count=len(char_counts),
            char_counts=tuple(char_counts),
            tone_patterns=tuple(tone_patterns),
            rhyme_positions=tuple(rhyme_positions),
            rhyme_groups_allowed=tuple(rhyme_groups),
            duilian_pairs=tuple(duilian),
            example_author=example_author,
            example_title=example_title,
            example_lines=tuple(example_lines),
        )
    )


# 浣溪沙 (双调, 42 字, 上阕三句, 下阕三句, 上下阕各押三韵)
_T(
    "浣溪沙",
    "小令",
    char_counts=[7, 7, 7, 7, 7, 7],
    tone_patterns=[
        "中仄中平中仄平",
        "中平中仄仄平平",
        "中仄中平中仄平",
        "中平中仄仄平平",
        "中仄中平中仄平",
        "中仄平平仄仄平",
    ],
    rhyme_positions=[1, 2, 4, 5],  # 1-based: lines 2, 3, 5, 6
    example_author="晏殊",
    example_title="浣溪沙",
    example_lines=[
        "一曲新词酒一杯",
        "去年天气旧亭台",
        "夕阳西下几时回",
        "无可奈何花落去",
        "似曾相识燕归来",
        "小园香径独徘徊",
    ],
)

# 如梦令 (单调, 33 字, 七句, 押五仄韵, 一二两韵, 叠句)
_T(
    "如梦令",
    "小令",
    char_counts=[7, 5, 7, 5, 7, 5, 5],
    tone_patterns=[
        "中仄中平中仄仄",
        "中仄平平",
        "中仄中平中仄仄",
        "中仄平平",
        "中平中仄平平仄",
        "中仄平平",
        "中仄平平",
    ],
    rhyme_positions=[0, 2, 4, 5, 6],
    example_author="李清照",
    example_title="如梦令",
    example_lines=[
        "昨夜雨疏风骤",
        "浓睡不消残酒",
        "试问卷帘人",
        "却道海棠依旧",
        "知否知否",
        "应是绿肥红瘦",
        "应是绿肥红瘦",
    ],
)

# 水调歌头 (双调, 95 字)
_T(
    "水调歌头",
    "长调",
    char_counts=[6, 6, 5, 6, 5, 6, 6, 5, 6, 6, 5, 5, 6, 6, 5, 5, 6, 6, 6],
    tone_patterns=[
        "中平中仄仄平平",
        "中仄平平中仄",
        "中仄平平",
        "中平中仄仄平平",
        "中平中仄平",
        "中仄平平中仄",
        "中平中仄",
        "中平中仄平",
        "中仄平平中仄",
        "中平中仄仄平平",
        "中平中仄",
        "中仄平平",
        "中平中仄仄平平",
        "中仄平平中仄",
        "中平中仄平",
        "中平中仄",
        "中平中仄平",
        "中仄平平中仄",
        "中平中仄",
    ],
    rhyme_positions=[1, 3, 6, 8, 12, 13],
    example_author="苏轼",
    example_title="水调歌头·明月几时有",
    example_lines=[
        "明月几时有",
        "把酒问青天",
        "不知天上宫阙",
        "今夕是何年",
        "我欲乘风归去",
        "又恐琼楼玉宇",
        "高处不胜寒",
        "起舞弄清影",
        "何似在人间",
        "转朱阁低绮户",
        "照无眠",
        "不应有恨",
        "何事长向别时圆",
        "人有悲欢离合",
        "月有阴晴圆缺",
        "此事古难全",
        "但愿人长久",
        "千里共婵娟",
        "千里共婵娟",
    ],
)

# 鹧鸪天 (双调, 55 字)
_T(
    "鹧鸪天",
    "小令",
    char_counts=[7, 7, 7, 7, 7, 3, 3, 7, 7],
    tone_patterns=[
        "中平中仄仄平平",
        "中仄平平中仄平",
        "中仄中平中仄仄",
        "中平中仄仄平平",
        "中平中仄平平仄",
        "仄平平",
        "仄平平",
        "中仄平平中仄平",
        "中平中仄仄平平",
    ],
    rhyme_positions=[0, 1, 3, 7, 8],
    example_author="晏几道",
    example_title="鹧鸪天",
    example_lines=[
        "彩袖殷勤捧玉钟",
        "当年拚却醉颜红",
        "舞低杨柳楼心月",
        "歌尽桃花扇底风",
        "从别后忆相逢",
        "几回魂梦与君同",
        "今宵剩把银釭照",
        "犹恐相逢是梦中",
    ],
)

# 清平乐 (双调, 46 字, 上阕四仄韵, 下阕三平韵)
_T(
    "清平乐",
    "小令",
    char_counts=[4, 5, 7, 6, 6, 6, 6, 6],
    tone_patterns=[
        "中平中仄",
        "中平中仄",
        "中仄平平中仄",
        "中仄中平平仄",
        "中平中仄平平",
        "中仄平平中仄",
        "中平中仄平平",
        "中平中仄平平",
    ],
    rhyme_positions=[0, 1, 2, 4, 5, 6, 7],
    example_author="李煜",
    example_title="清平乐",
    example_lines=[
        "别来春半",
        "触目柔肠断",
        "砌下落梅如雪乱",
        "拂了一身还满",
        "雁来音信无凭",
        "路遥归梦难成",
        "离恨恰如春水",
        "柔肠已断无痕",
    ],
)

# 点绛唇 (双调, 41 字)
_T(
    "点绛唇",
    "小令",
    char_counts=[7, 4, 7, 4, 5, 5, 7, 4],
    tone_patterns=[
        "中仄中平中仄",
        "中平中仄",
        "中平中仄平平",
        "中仄平平",
        "中平中仄",
        "中仄平平",
        "中平中仄平平",
        "中仄平平",
    ],
    rhyme_positions=[0, 2, 4, 6],
    example_author="李清照",
    example_title="点绛唇",
    example_lines=[
        "蹴罢秋千",
        "起来慵整纤纤手",
        "露浓花瘦",
        "薄汗轻衣透",
        "见客入来",
        "袜刬金钗溜",
        "和羞走",
        "倚门回首",
        "却把青梅嗅",
    ],
)

# 满江红 (双调, 93 字)
_T(
    "满江红",
    "长调",
    char_counts=[4, 7, 4, 4, 7, 4, 4, 7, 4, 3, 7, 4, 3, 7, 4, 4, 7, 4, 3, 7, 4, 4],
    tone_patterns=[
        "中仄平平",
        "中仄中平平仄",
        "中平仄",
        "平平仄",
        "中平中仄",
        "中仄平平",
        "平中仄",
        "中仄平平",
        "中平中仄",
        "平中仄",
        "中平中仄",
        "中平仄",
        "平中仄",
        "中仄平平",
        "中平中仄",
        "平中仄",
        "中仄平平",
        "中平中仄",
        "平中仄",
        "中平中仄",
        "中平仄",
        "中平仄",
    ],
    rhyme_positions=[1, 3, 5, 7, 10, 12, 16, 18, 20],
    example_author="岳飞",
    example_title="满江红",
    example_lines=[
        "怒发冲冠",
        "凭栏处潇潇雨歇",
        "抬望眼",
        "仰天长啸",
        "壮怀激烈",
        "三十功名尘与土",
        "八千里路云和月",
        "莫等闲白了少年头",
        "空悲切",
        "靖康耻",
        "犹未雪",
        "臣子恨",
        "何时灭",
        "驾长车踏破贺兰山缺",
        "壮志饥餐胡虏肉",
        "笑谈渴饮匈奴血",
        "待从头收拾旧山河",
        "朝天阙",
    ],
)

# 忆江南 (单调, 27 字)
_T(
    "忆江南",
    "小令",
    char_counts=[7, 7, 7, 5, 5],
    tone_patterns=[
        "中平中仄仄平平",
        "中仄平平中仄平",
        "中仄中平中仄仄",
        "中平中仄仄平平",
        "中平中仄仄平平",
    ],
    rhyme_positions=[0, 1, 3, 4],
    example_author="白居易",
    example_title="忆江南",
    example_lines=[
        "江南好",
        "风景旧曾谙",
        "日出江花红胜火",
        "春来江水绿水",
        "能不忆江南",
    ],
)

# 西江月 (双调, 50 字)
_T(
    "西江月",
    "小令",
    char_counts=[7, 7, 7, 7, 7, 7, 7, 7],
    tone_patterns=[
        "中平中仄平平仄",
        "中仄平平中仄",
        "中平中仄平平仄",
        "中仄平平中仄",
        "中平中仄平平仄",
        "中仄平平中仄",
        "中平中仄平平仄",
        "中仄平平中仄",
    ],
    rhyme_positions=[1, 3, 5, 7],
    example_author="辛弃疾",
    example_title="西江月·夜行黄沙道中",
    example_lines=[
        "明月别枝惊鹊",
        "清风半夜鸣蝉",
        "稻花香里说丰年",
        "听取蛙声一片",
        "七八个星天外",
        "两三点雨山前",
        "旧时茅店社林边",
        "路转溪桥忽见",
    ],
)

# 蝶恋花 (双调, 60 字)
_T(
    "蝶恋花",
    "小令",
    char_counts=[7, 4, 7, 4, 7, 7, 7, 4, 7, 4],
    tone_patterns=[
        "中仄中平平仄仄",
        "中仄平平",
        "中平中仄平平仄",
        "中仄平平",
        "中仄中平平仄仄",
        "中平中仄平平仄",
        "中仄中平平仄仄",
        "中仄平平",
        "中平中仄平平仄",
        "中仄平平",
    ],
    rhyme_positions=[0, 2, 4, 5, 6, 8],
    example_author="欧阳修",
    example_title="蝶恋花",
    example_lines=[
        "庭院深深深几许",
        "杨柳堆烟",
        "帘幕无重数",
        "玉勒雕鞍游冶处",
        "楼高不见章台路",
        "雨横风狂三月暮",
        "门掩黄昏",
        "无计留春住",
        "泪眼问花花不语",
        "乱红飞过秋千去",
    ],
)

# 临江仙 (双调, 60 字)
_T(
    "临江仙",
    "中调",
    char_counts=[7, 7, 7, 7, 7, 7, 7, 7, 5, 6],
    tone_patterns=[
        "中平中仄平平仄",
        "中仄平平中仄",
        "中平中仄仄平平",
        "中平中仄",
        "中仄中平中仄",
        "中平中仄仄平平",
        "中平中仄平平仄",
        "中仄平平中仄",
        "中平中仄",
        "中仄中平平仄",
    ],
    rhyme_positions=[0, 2, 5, 7, 9],
    example_author="苏轼",
    example_title="临江仙·夜归临皋",
    example_lines=[
        "夜饮东坡醒复醉",
        "归来仿佛三更",
        "家童鼻息已雷鸣",
        "敲门都不应",
        "倚杖听江声",
        "长恨此身非我有",
        "何时忘却营营",
        "夜阑风静縠纹平",
        "小舟从此逝",
        "江海寄余生",
    ],
)

# 念奴娇 (双调, 100 字)
_T(
    "念奴娇",
    "长调",
    char_counts=[4, 6, 5, 5, 6, 6, 6, 5, 6, 6, 5, 5, 4, 6, 5, 5, 6, 6, 6, 5],
    tone_patterns=[
        "中平中仄",
        "仄平平仄平平",
        "仄平平仄",
        "仄平平仄",
        "中平中仄平仄",
        "中仄平平",
        "中仄平平",
        "中仄平平",
        "中平中仄平仄",
        "中仄平平",
        "中平中仄",
        "中平中仄",
        "中平中仄",
        "仄平平仄平平",
        "仄平平仄",
        "仄平平仄",
        "中平中仄平仄",
        "中仄平平",
        "中仄平平",
        "中仄平平",
    ],
    rhyme_positions=[1, 5, 6, 9, 13, 17, 18],
    example_author="苏轼",
    example_title="念奴娇·赤壁怀古",
    example_lines=[
        "大江东去",
        "浪淘尽千古风流人物",
        "故垒西边",
        "人道是",
        "三国周郎赤壁",
        "乱石穿空",
        "惊涛拍岸",
        "卷起千堆雪",
        "江山如画",
        "一时多少豪杰",
        "遥想公瑾当年",
        "小乔初嫁了",
        "雄姿英发",
        "羽扇纶巾谈笑间",
        "樯橹灰飞烟灭",
        "故国神游",
        "多情应笑我",
        "早生华发",
        "人生如梦",
        "一尊还酹江月",
    ],
)

# 声声慢 (双调, 97 字)
_T(
    "声声慢",
    "长调",
    char_counts=[7, 5, 7, 5, 7, 5, 5, 7, 5, 7, 5, 5, 7, 5, 7],
    tone_patterns=[
        "中平中仄平平仄",
        "中仄平平",
        "中平中仄平平仄",
        "中仄平平",
        "中平中仄平平仄",
        "中仄平平",
        "中仄平平",
        "中平中仄平平仄",
        "中仄平平",
        "中平中仄平平仄",
        "中仄平平",
        "中仄平平",
        "中平中仄平平仄",
        "中仄平平",
        "中平中仄平平仄",
    ],
    rhyme_positions=[0, 2, 4, 7, 9, 12, 14],
    example_author="李清照",
    example_title="声声慢",
    example_lines=[
        "寻寻觅觅",
        "冷冷清清",
        "凄凄惨惨戚戚",
        "乍暖还寒时候",
        "最难将息",
        "三杯两盏淡酒",
        "怎敌他晚来风急",
        "雁过也",
        "正伤心",
        "却是旧时相识",
        "满地黄花堆积",
        "憔悴损",
        "如今有谁堪摘",
        "守着窗儿",
        "独自怎生得黑",
        "梧桐更兼细雨",
        "到黄昏点点滴滴",
        "这次",
    ],
)

# 一剪梅 (双调, 60 字)
_T(
    "一剪梅",
    "小令",
    char_counts=[7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
    tone_patterns=[
        "中平中仄仄平平",
        "中仄平平中仄平",
        "中平中仄仄平平",
        "中平中仄仄平平",
        "中平中仄仄平平",
        "中仄平平中仄平",
        "中平中仄仄平平",
        "中平中仄仄平平",
        "中平中仄仄平平",
        "中仄平平中仄平",
    ],
    rhyme_positions=[0, 1, 2, 4, 6, 7, 9],
    example_author="李清照",
    example_title="一剪梅",
    example_lines=[
        "红藕香残玉簟秋",
        "轻解罗裳独上兰舟",
        "云中谁寄锦书来",
        "雁字回时月满西楼",
        "花自飘零水自流",
        "一种相思两处闲愁",
        "此情无计可消除",
        "才下眉头却上心头",
    ],
)

# 卜算子 (双调, 44 字)
_T(
    "卜算子",
    "小令",
    char_counts=[7, 7, 7, 7, 5, 7, 7, 5],
    tone_patterns=[
        "中仄平平中仄仄",
        "中平中仄平平",
        "中平中仄中平仄",
        "中仄平平中仄",
        "中仄平平",
        "中平中仄中平仄",
        "中仄平平中仄",
        "中仄平平",
    ],
    rhyme_positions=[0, 2, 3, 5, 7],
    example_author="苏轼",
    example_title="卜算子·黄州定慧院寓居作",
    example_lines=[
        "缺月挂疏桐",
        "漏断人初静",
        "谁见幽人独往来",
        "缥缈孤鸿影",
        "惊起却回头",
        "有恨无人省",
        "拣尽寒枝不肯栖",
        "寂寞沙洲冷",
    ],
)

# 菩萨蛮 (双调, 44 字, 平仄转换)
_T(
    "菩萨蛮",
    "小令",
    char_counts=[7, 7, 5, 5, 7, 7, 5, 5],
    tone_patterns=[
        "中平中仄平平仄",
        "中平中仄平平仄",
        "中仄仄平平",
        "中平平仄平",
        "中平中仄平平仄",
        "中平中仄平平仄",
        "中仄仄平平",
        "中平平仄平",
    ],
    rhyme_positions=[0, 1, 4, 5],
    example_author="李白",
    example_title="菩萨蛮",
    example_lines=[
        "平林漠漠烟如织",
        "寒山一带伤心碧",
        "暝色入高楼",
        "有人楼上愁",
        "玉阶空伫立",
        "宿鸟归飞急",
        "何处是归程",
        "长亭连短亭",
    ],
)

# 沁园春 (双调, 114 字)
_T(
    "沁园春",
    "长调",
    char_counts=[4, 6, 4, 7, 5, 6, 5, 6, 5, 7, 4, 4, 4],
    tone_patterns=[
        "中仄平平",
        "仄仄平平平仄",
        "中平中仄",
        "中仄平平中仄",
        "中平中仄",
        "中仄平平",
        "中平中仄",
        "中仄平平",
        "中平中仄",
        "中仄平平中仄",
        "中仄平平",
        "中平中仄",
        "中平中仄",
    ],
    rhyme_positions=[0, 2, 4, 7, 9, 11, 12],
    example_author="毛泽东",
    example_title="沁园春·雪",
    example_lines=[
        "北国风光",
        "千里冰封万里雪飘",
        "望长城内外",
        "惟余莽莽",
        "大河上下",
        "顿失滔滔",
        "山舞银蛇",
        "原驰蜡象",
        "欲与天公试比高",
        "须晴日看红装素裹",
        "分外妖娆",
        "江山如此多娇",
        "引无数英雄竞折腰",
        "惜秦皇汉武",
        "略输文采",
        "唐宗宋祖",
        "稍逊风骚",
        "一代天骄",
        "成吉思汗",
        "只识弯弓射大雕",
        "俱往矣",
        "数风流人物",
        "还看今朝",
    ],
)

# 渔家傲 (双调, 62 字)
_T(
    "渔家傲",
    "中调",
    char_counts=[7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
    tone_patterns=[
        "中仄中平平仄仄",
        "中平中仄平平仄",
        "中平中仄平平仄",
        "中仄中平平仄仄",
        "中平中仄平平仄",
        "中仄中平平仄仄",
        "中平中仄平平仄",
        "中平中仄平平仄",
        "中仄中平平仄仄",
        "中平中仄平平仄",
    ],
    rhyme_positions=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    example_author="范仲淹",
    example_title="渔家傲·秋思",
    example_lines=[
        "塞下秋来风景异",
        "衡阳雁去无留意",
        "四面边声连角起",
        "千嶂里长烟落日孤城闭",
        "浊酒一杯家万里",
        "燕然未勒归无计",
        "羌管悠悠霜满地",
        "人不寐将军白发征夫泪",
    ],
)

# 青玉案 (双调, 67 字)
_T(
    "青玉案",
    "中调",
    char_counts=[7, 6, 7, 6, 4, 4, 6, 6, 5, 5, 4],
    tone_patterns=[
        "中平中仄平平仄",
        "中仄平平中仄",
        "中平中仄平平仄",
        "中仄平平中仄",
        "中平平仄",
        "中平平仄",
        "中仄平平",
        "中仄平平",
        "中平平仄",
        "中平平仄",
        "中平中仄",
    ],
    rhyme_positions=[0, 2, 4, 6, 8, 10],
    example_author="辛弃疾",
    example_title="青玉案·元夕",
    example_lines=[
        "东风夜放花千树",
        "更吹落星如雨",
        "宝马雕车香满路",
        "凤箫声动",
        "玉壶光转",
        "一夜鱼龙舞",
        "蛾儿雪柳黄金缕",
        "笑语盈盈暗香去",
        "众里寻他千百度",
        "蓦然回首",
        "那人却在",
        "灯火阑珊处",
    ],
)

# 钗头凤 (双调, 60 字, 上下阕各押四仄韵, 叠韵)
_T(
    "钗头凤",
    "中调",
    char_counts=[7, 7, 7, 7, 4, 4, 6, 6, 4, 4, 7, 7, 7, 7],
    tone_patterns=[
        "中仄平平中仄仄",
        "中平中仄平平",
        "中平中仄平平仄",
        "中仄平平中仄",
        "中平平仄",
        "中平平仄",
        "中仄平平",
        "中仄平平",
        "中平平仄",
        "中平平仄",
        "中仄平平中仄仄",
        "中平中仄平平",
        "中平中仄平平仄",
        "中仄平平中仄",
    ],
    rhyme_positions=[0, 1, 2, 3, 6, 7, 10, 11, 12, 13],
    example_author="陆游",
    example_title="钗头凤",
    example_lines=[
        "红酥手黄縢酒",
        "满城春色宫墙柳",
        "东风恶欢情薄",
        "一怀愁绪几年离索",
        "错错错",
        "春如旧人空瘦",
        "泪痕红浥鲛绡透",
        "桃花落闲池阁",
        "山盟虽在",
        "锦书难托",
        "莫莫莫",
    ],
)


CIPAI_REGISTRY: dict[str, CipaiTemplate] = _BUILTIN_REGISTRY


def list_cipai() -> list[str]:
    """Return the list of registered cipai names."""
    return sorted(CIPAI_REGISTRY.keys())


def get_cipai(name: str) -> CipaiTemplate:
    """Look up a cipai by name. Raises KeyError if not registered."""
    if name not in CIPAI_REGISTRY:
        available = ", ".join(list_cipai())
        raise KeyError(f"Unknown cipai '{name}'. Available: {available}")
    return CIPAI_REGISTRY[name]


def load_cipai_from_directory(directory: Path | str) -> int:
    """Load additional cipai templates from JSON files in a directory.

    Returns the number of templates loaded.
    """
    from json import loads

    p = Path(directory)
    if not p.exists():
        return 0
    count = 0
    for json_file in p.glob("*.json"):
        try:
            data = loads(json_file.read_text(encoding="utf-8"))
            tpl = CipaiTemplate(
                name=data["name"],
                category=data.get("category", "中调"),
                line_count=data["line_count"],
                char_counts=tuple(data["char_counts"]),
                tone_patterns=tuple(data["tone_patterns"]),
                rhyme_positions=tuple(data.get("rhyme_positions", ())),
                example_author=data.get("example_author", ""),
                example_title=data.get("example_title", ""),
                example_lines=tuple(data.get("example_lines", ())),
            )
            CIPAI_REGISTRY[tpl.name] = tpl
            count += 1
        except Exception:
            continue
    return count


__all__ = [
    "CIPAI_REGISTRY",
    "CipaiTemplate",
    "get_cipai",
    "list_cipai",
    "load_cipai_from_directory",
]
