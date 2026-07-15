"""Pure Markdown skill loading, intentionally independent of agent packages."""

from __future__ import annotations

from pathlib import Path


def load_skill(path: Path | str) -> str:
    """Load a non-empty Markdown skill from an explicit path."""
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("Skill file is empty.")
    return text
