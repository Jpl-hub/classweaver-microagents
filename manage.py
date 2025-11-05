#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main() -> None:
    """Run administrative tasks."""
    base_dir = Path(__file__).resolve().parent
    src_dir = base_dir / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django is not installed or could not be imported. "
            "Ensure dependencies are installed and PYTHONPATH is set correctly."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
