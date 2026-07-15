"""Shared configuration loader for this standalone lesson."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_model_name() -> str:
    """Load and validate the model selection from the project-root .env file."""
    load_dotenv(PROJECT_ROOT / ".env")
    model_name = os.getenv("MODEL_NAME")
    if not model_name:
        raise SystemExit("MODEL_NAME is missing. Configure the project-root .env file.")
    return model_name
