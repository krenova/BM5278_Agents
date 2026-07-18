"""Lesson-local adapter for the shared trace implementation."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shared_trace import LiveTrace as SharedLiveTrace  # noqa: E402


class LiveTrace(SharedLiveTrace):
    """Configure the shared tracer for this tutorial's directory."""

    def __init__(self, enabled: bool = False, log_dir: Path | None = None) -> None:
        super().__init__(enabled, log_dir, tutorial_dir=Path(__file__).resolve().parent)
