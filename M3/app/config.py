"""
Configuration for M3: Billing & Payments backend.
"""

from __future__ import annotations

import os
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("M3_DB_PATH", str(BASE_DIR / "billing.db"))
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
