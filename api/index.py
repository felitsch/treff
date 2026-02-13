"""Vercel Serverless Function entry point.

Exposes the FastAPI app so Vercel routes /api/* requests here.
"""

import sys
from pathlib import Path

# Add backend/ to Python path so "from app.xxx" imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402, F401 — Vercel detects the `app` variable
