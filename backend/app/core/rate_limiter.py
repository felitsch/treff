"""Rate limiter for AI generation endpoints.

Implements a per-user, sliding-window rate limiter to prevent abuse
of expensive AI generation endpoints (text + image).

Uses in-memory storage which is appropriate for single-server deployments.
Rate limit state resets on server restart, which is acceptable since
this is a protective measure, not a billing system.
"""

import time
import logging
from collections import defaultdict
from typing import NamedTuple

from fastapi import HTTPException

logger = logging.getLogger(__name__)


class RateLimitConfig(NamedTuple):
    """Configuration for a rate limit window."""
    max_requests: int  # Maximum requests allowed in the window
    window_seconds: int  # Duration of the sliding window


# Per-user rate limits for AI endpoints
# Conservative limits to protect against rapid-fire requests
AI_RATE_LIMITS = {
    "generate-text": RateLimitConfig(max_requests=10, window_seconds=60),
    "regenerate-field": RateLimitConfig(max_requests=15, window_seconds=60),
    "generate-image": RateLimitConfig(max_requests=5, window_seconds=60),
}

# Default rate limit for any AI endpoint not explicitly configured
DEFAULT_AI_RATE_LIMIT = RateLimitConfig(max_requests=10, window_seconds=60)


class RateLimiter:
    """Sliding-window rate limiter using in-memory storage.

    Tracks request timestamps per (user_id, endpoint) pair and
    enforces configurable limits per endpoint.
    """

    def __init__(self):
        # {(user_id, endpoint): [timestamp1, timestamp2, ...]}
        self._requests: dict[tuple[int, str], list[float]] = defaultdict(list)

    def _cleanup_old(self, key: tuple[int, str], window_seconds: int) -> None:
        """Remove timestamps older than the sliding window."""
        now = time.monotonic()
        cutoff = now - window_seconds
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > cutoff
        ]

    def check_rate_limit(self, user_id: int, endpoint: str) -> None:
        """Check if the user is within rate limits.

        Args:
            user_id: The authenticated user's ID
            endpoint: The AI endpoint name (e.g. "generate-text")

        Raises:
            HTTPException: 429 Too Many Requests if rate limit exceeded
        """
        config = AI_RATE_LIMITS.get(endpoint, DEFAULT_AI_RATE_LIMIT)
        key = (user_id, endpoint)

        # Clean up expired timestamps
        self._cleanup_old(key, config.window_seconds)

        current_count = len(self._requests[key])

        if current_count >= config.max_requests:
            # Calculate how long until the oldest request expires
            oldest = self._requests[key][0]
            retry_after = int(config.window_seconds - (time.monotonic() - oldest)) + 1
            retry_after = max(1, retry_after)

            logger.warning(
                f"Rate limit exceeded for user {user_id} on {endpoint}: "
                f"{current_count}/{config.max_requests} in {config.window_seconds}s"
            )

            raise HTTPException(
                status_code=429,
                detail=f"Zu viele Anfragen. Bitte warte {retry_after} Sekunden und versuche es erneut.",
                headers={"Retry-After": str(retry_after)},
            )

        # Record this request
        self._requests[key].append(time.monotonic())

    def get_remaining(self, user_id: int, endpoint: str) -> dict:
        """Get remaining rate limit info for a user/endpoint.

        Returns dict with remaining requests and reset time.
        """
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


# Singleton instance used across the application
ai_rate_limiter = RateLimiter()
