"""Pure Markdown skill loading, intentionally independent of agent packages."""
from pathlib import Path


def load_skill(path: Path | str = "SKILL.md") -> str:
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("Skill file is empty.")
    return text
