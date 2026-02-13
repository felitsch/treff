"""Centralized path utilities for Vercel + local compatibility."""

import os
from pathlib import Path

IS_VERCEL = os.environ.get("VERCEL") == "1"
APP_DIR = Path(__file__).resolve().parent.parent


def get_upload_dir(subdir: str = "") -> Path:
    """Return the upload directory, using /tmp on Vercel."""
    base = Path("/tmp/uploads") if IS_VERCEL else APP_DIR / "static" / "uploads"
    path = base / subdir if subdir else base
    path.mkdir(parents=True, exist_ok=True)
    return path
