#!/usr/bin/env python
"""Ablation study script.

Runs `shici generate` under different configurations to measure which
components contribute to prosody accuracy.

Outputs a markdown table suitable for the README.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Callable


def make_themes(n: int) -> list[str]:
    """Return `n` sample poem themes."""
    pool = [
        "思乡", "送别", "山水", "边塞", "田园", "怀古", "咏史", "咏物",
        "闺怨", "悼亡", "登高", "春夜", "秋思", "月夜", "江畔独步",",
        "雪", "梅", "竹", "菊", "松", "鹤", "渔翁", "樵夫", "僧", "酒",
    ]
    return pool[:n]


def make_forms(n: int) -> list[str]:
    """Return `n` alternating forms (绝句/词)."""
    forms = ["五言绝句", "七言绝句", "五言律诗", "七言律诗"]
    return [forms[i % len(forms)] for i in range(n)]


def eval_config(
    name: str,
    generator: Callable,
    themes: list[str],
    forms: list[str],
    max_rounds: int,
) -> dict:
    """Run the given generator on (theme, form) pairs and aggregate."""
    times: list[float] = []
    pass_count = 0

    for theme, form in zip(themes, forms):
        start = time.time()
        poem, issues = generator(theme=theme, form=form, max_rounds=max_rounds)
        elapsed = time.time() - start

        times.append(elapsed)
        if not issues:
            pass_count += 1

    return {
        "name": name,
        "pass_rate": pass_count / len(themes),
        "avg_time": statistics.mean(times) if times else 0.0,
        "n": len(themes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--n",
        type=int,
        default=20,
        help="Number of samples per configuration (default: 20)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/ablation-results.json"),
    )
    args = parser.parse_args()

    # Use mock generator if no API key, otherwise live.
    themes = make_themes(args.n)
    forms = make_forms(args.n)

    try:
        from shici.llm import generate_jueju, LLMConfig
        from shici.prosody import check_poem

        config = LLMConfig(backend="deepseek")

        def live_generator(theme, form, max_rounds):
            poem = generate_jueju(theme=theme, chars=7, config=config)
            for _ in range(max_rounds):
                result = check_poem([l.text for l in poem.lines])
                if result.ok:
                    return poem, []
            return poem, [str(i.message) for i in result.issues]

        have_llm = True
    except Exception as e:
        print(f"  ℹ live generator unavailable: {e}")
        have_llm = False

        def mock_generator(theme, form, max_rounds):
            return None, ["mock"]

    rows = []
    configurations = [
        ("Baseline (1 round)", 1),
        ("Revision loop (3 rounds)", 3),
    ]

    for name, rounds in configurations:
        rows.append(eval_config(name, live_generator if have_llm else mock_generator, themes, forms, rounds))

    # Pretty print
    print(f"\n{'Configuration':<35} {'Pass %':>10} {'Avg time':>12}")
    print("-" * 60)
    for row in rows:
        print(f"{row['name']:<35} {row['pass_rate']*100:>9.1f}% {row['avg_time']:>11.2f}s")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())