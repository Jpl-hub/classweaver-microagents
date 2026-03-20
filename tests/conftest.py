import os
import sys
from pathlib import Path

import django

ROOT_PATH = Path(__file__).resolve().parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))
SRC_PATH = ROOT_PATH / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# Force a lightweight DB for tests regardless of any local .env overrides.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
django.setup()
