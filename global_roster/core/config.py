"""Configuration module for Global Roster."""
from pathlib import Path

# Compute BASE_DIR as the project root (folder "Global Roster")
# This file is at global_roster/core/config.py
# So we go up 2 levels: global_roster/core -> global_roster -> project root
BASE_DIR = Path(__file__).parent.parent.parent.resolve()

# APP_DIR is the global_roster package directory
APP_DIR = BASE_DIR / "global_roster"

# Template and static directories
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

# Database path
DB_PATH = APP_DIR / "traders.db"

# Database URL (using synchronous SQLite for Phase 1)
# Convert Windows paths to use forward slashes for SQLite URLs
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

