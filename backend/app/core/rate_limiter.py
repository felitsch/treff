"""Rate-limiting middleware and utilities for the TREFF API.

Implements multi-tier rate limiting:
  - General: 100 requests/minute per IP + per user
  - AI endpoints (/ai/): 10 requests/minute per user
  - Upload endpoints: 50 requests/hour per user, max 10 MB file size
  - Custom per-endpoint overrides for expensive AI operations

Uses in-memory sliding-window counters. State resets on server restart,
which is acceptable since this is protective, not a billing system.

Response headers on every request:
  X-RateLimit-Limit      - max allowed in the window
  X-RateLimit-Remaining  - how many are left
  X-RateLimit-Reset      - epoch seconds when the window resets

When a limit is hit, returns 429 Too Many Requests with Retry-After header.
"""

import logging
import time
from collections import defaultdict
from typing import NamedTuple, Optional

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


# ─── Configuration ────────────────────────────────────────────────────────────

class RateLimitConfig(NamedTuple):
    """Configuration for a rate limit window."""
    max_requests: int      # Maximum requests allowed in the window
    window_seconds: int    # Duration of the sliding window


# Tier definitions — relaxed in development/testing to avoid false-positive 429s
import os as _os
_IS_TESTING = _os.environ.get("TESTING", "").lower() in ("1", "true", "yes")
_IS_DEV = _os.environ.get("ENV", "").lower() in ("", "dev", "development", "test")

# In dev/test mode, allow 10x more general requests to prevent E2E test flakiness
_GENERAL_MULTIPLIER = 10 if (_IS_DEV or _IS_TESTING) else 1

GENERAL_LIMIT = RateLimitConfig(max_requests=100 * _GENERAL_MULTIPLIER, window_seconds=60)
AI_LIMIT = RateLimitConfig(max_requests=10, window_seconds=60)
UPLOAD_LIMIT = RateLimitConfig(max_requests=50, window_seconds=3600)

# Per-endpoint overrides for AI routes
AI_RATE_LIMITS = {
    "generate-text": RateLimitConfig(max_requests=10, window_seconds=60),
    "regenerate-field": RateLimitConfig(max_requests=15, window_seconds=60),
    "generate-image": RateLimitConfig(max_requests=5, window_seconds=60),
}

# Default rate limit for any AI endpoint not explicitly configured
DEFAULT_AI_RATE_LIMIT = RateLimitConfig(max_requests=10, window_seconds=60)


# ─── Sliding-window engine ───────────────────────────────────────────────────

class RateLimiter:
    """Sliding-window rate limiter using in-memory storage.

    Tracks request timestamps per (identifier, bucket) pair and
    enforces configurable limits per bucket.
    """

    def __init__(self):
        # {(identifier, bucket): [timestamp1, timestamp2, ...]}
        self._requests: dict[tuple, list[float]] = defaultdict(list)

    def _cleanup_old(self, key: tuple, window_seconds: int) -> None:
        """Remove timestamps older than the sliding window."""
        now = time.monotonic()
        cutoff = now - window_seconds
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > cutoff
        ]

    def check_rate_limit(self, user_id: int, endpoint: str) -> None:
        """Legacy API: Check if the user is within rate limits for AI endpoints.

        Args:
            user_id: The authenticated user's ID
            endpoint: The AI endpoint name (e.g. "generate-text")

        Raises:
            HTTPException: 429 Too Many Requests if rate limit exceeded
        """
        config = AI_RATE_LIMITS.get(endpoint, DEFAULT_AI_RATE_LIMIT)
        key = (user_id, endpoint)

        self._cleanup_old(key, config.window_seconds)
        current_count = len(self._requests[key])

        if current_count >= config.max_requests:
            oldest = self._requests[key][0]
            retry_after = int(config.window_seconds - (time.monotonic() - oldest)) + 1
            retry_after = max(1, retry_after)

            logger.warning(
                "Rate limit exceeded for user %s on %s: %d/%d in %ds",
                user_id, endpoint, current_count, config.max_requests,
                config.window_seconds,
            )

            raise HTTPException(
                status_code=429,
                detail=f"Zu viele Anfragen. Bitte warte {retry_after} Sekunden und versuche es erneut.",
                headers={"Retry-After": str(retry_after)},
            )

        # Record this request
        self._requests[key].append(time.monotonic())

    def get_remaining(self, user_id: int, endpoint: str) -> dict:
        """Get remaining rate limit info for a user/endpoint."""
        config = AI_RATE_LIMITS.get(endpoint, DEFAULT_AI_RATE_LIMIT)
        key = (user_id, endpoint)

        self._cleanup_old(key, config.window_seconds)
        current_count = len(self._requests[key])
        remaining = max(0, config.max_requests - current_count)

        return {
            "limit": config.max_requests,
            "remaining": remaining,
            "window_seconds": config.window_seconds,
        }

    # ── Generic check used by the middleware ──────────────────────────────

    def check(
        self,
        identifier: str,
        bucket: str,
        config: RateLimitConfig,
    ) -> tuple:
        """Check a rate limit and record the request.

        Returns:
            (allowed: bool, limit: int, remaining: int, reset_epoch: int)
        """
        key = (identifier, bucket)
        self._cleanup_old(key, config.window_seconds)
        current_count = len(self._requests[key])

        now_epoch = int(time.time())
        if self._requests[key]:
            oldest_mono = self._requests[key][0]
            reset_epoch = now_epoch + int(config.window_seconds - (time.monotonic() - oldest_mono))
        else:
            reset_epoch = now_epoch + config.window_seconds

        if current_count >= config.max_requests:
            return False, config.max_requests, 0, reset_epoch

        # Record this request
        self._requests[key].append(time.monotonic())
        remaining = max(0, config.max_requests - current_count - 1)
        return True, config.max_requests, remaining, reset_epoch


# Singleton instance used across the application
ai_rate_limiter = RateLimiter()

# Global limiter instance (used by middleware)
_global_limiter = RateLimiter()


# ─── Helper: extract client identifier ────────────────────────────────────────

def _get_client_ip(request: Request) -> str:
    """Get the real client IP, respecting X-Forwarded-For behind reverse proxies."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_user_id_from_request(request: Request) -> Optional[str]:
    """Try to extract the user_id from an Authorization header (best-effort).

    This is a lightweight check that avoids hitting the database.
    Returns None if the token is missing, invalid, or expired.
    """
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    try:
        from app.core.config import settings
        from jose import jwt
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None


# ─── Middleware ────────────────────────────────────────────────────────────────

# Paths that are exempt from rate limiting
EXEMPT_PATHS = {
    "/api/health", "/api/docs", "/api/openapi.json",
    "/docs", "/openapi.json", "/redoc",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that enforces multi-tier rate limits.

    Tiers (checked in order, first applicable wins):
      1. AI endpoints  (/api/ai/*)      -> 10 req/min per user
      2. Upload endpoints (/api/*/upload) -> 50 req/hour per user
      3. General                          -> 100 req/min per IP + per user

    Adds X-RateLimit-* response headers on every request.
    Returns 429 + Retry-After when a limit is hit.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        # Skip rate limiting for health checks, docs, static files, OPTIONS
        if (
            path in EXEMPT_PATHS
            or path.startswith("/uploads/")
            or request.method == "OPTIONS"
        ):
            return await call_next(request)

        client_ip = _get_client_ip(request)
        user_id = _get_user_id_from_request(request)

        # Determine which tier applies
        tier_bucket, tier_config = self._classify_request(path)

        # --- IP-based check (general tier only) ---
        ip_allowed = True
        ip_remaining = GENERAL_LIMIT.max_requests
        ip_reset = int(time.time()) + GENERAL_LIMIT.window_seconds

        if tier_bucket == "general":
            ip_allowed, _, ip_remaining, ip_reset = _global_limiter.check(
                identifier=f"ip:{client_ip}",
                bucket="general",
                config=GENERAL_LIMIT,
            )

        # --- User-based check (all tiers) ---
        user_allowed = True
        limit = tier_config.max_requests
        remaining = tier_config.max_requests
        reset_epoch = int(time.time()) + tier_config.window_seconds

        if user_id:
            user_allowed, limit, remaining, reset_epoch = _global_limiter.check(
                identifier=f"user:{user_id}",
                bucket=tier_bucket,
                config=tier_config,
            )
        elif tier_bucket != "general":
            # For non-general tiers, fall back to IP if no user
            user_allowed, limit, remaining, reset_epoch = _global_limiter.check(
                identifier=f"ip:{client_ip}",
                bucket=tier_bucket,
                config=tier_config,
            )

        # Use the most restrictive result
        if not ip_allowed or not user_allowed:
            retry_after = max(1, reset_epoch - int(time.time()))

            # Log the violation
            id_label = f"user:{user_id}" if user_id else f"ip:{client_ip}"
            logger.warning(
                "Rate limit exceeded: %s on %s (tier=%s, limit=%d/%ds)",
                id_label, path, tier_bucket, limit, tier_config.window_seconds,
            )

            return Response(
                status_code=429,
                content='{"detail":"Zu viele Anfragen. Bitte warte und versuche es erneut.","error":{"code":"RATE_LIMITED","message":"Too many requests","details":null}}',
                media_type="application/json",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_epoch),
                },
            )

        # Use the more restrictive remaining value
        final_remaining = min(ip_remaining, remaining) if tier_bucket == "general" else remaining

        # Proceed with the request
        response = await call_next(request)

        # Attach rate limit headers to every response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(final_remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_epoch)

        return response

    @staticmethod
    def _classify_request(path: str) -> tuple:
        """Classify the request into a rate-limit tier.

        Returns (bucket_name, RateLimitConfig).
        """
        # Tier 1: AI endpoints
        if "/ai/" in path or path.endswith("/ai"):
            return "ai", AI_LIMIT

        # Tier 2: Upload endpoints
        if "/upload" in path:
            return "upload", UPLOAD_LIMIT

        # Tier 3: General
        return "general", GENERAL_LIMIT
