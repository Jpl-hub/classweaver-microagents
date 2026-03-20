from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config.celery import app  # noqa: E402

__all__ = ("app",)
