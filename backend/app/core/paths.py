"""Centralized path utilities for Vercel + local compatibility."""

import base64
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


def save_and_encode(data: bytes, file_path: Path) -> str | None:
    """Write bytes to disk. On Vercel, also return base64 for DB storage."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(data)
    if IS_VERCEL:
        return base64.b64encode(data).decode("ascii")
    return None
