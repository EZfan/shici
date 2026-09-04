"""Pytest configuration for the shici test suite.

Ensures ``src/`` is on ``sys.path`` so the suite can import the
``shici`` package without requiring an editable install. This is the
recommended pattern when ``pyproject.toml`` is not yet defined.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
