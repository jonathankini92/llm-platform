"""
Gateway Middleware.

Handles authentication and rate limiting.
"""

import time
from collections import defaultdict
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from config import settings

# =============================================================================
# AUTHENTICATION
# =============================================================================

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the API key from the Authorization header.

    Expected format: "Bearer sk-xxx" or just "sk-xxx"
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Use 'Authorization: Bearer sk-xxx' header."
        )

    # Remove "Bearer " prefix if present
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]

    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key."
        )

    return api_key


# =============================================================================
# RATE LIMITING
# =============================================================================


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window.

    In production, use Redis for distributed rate limiting.
    """

    def __init__(self, requests_per_minute: int):
        self.rpm = requests_per_minute
        self.window_size = 60  # seconds
        # client_id -> list of timestamps
        self.requests: dict[str, list[float]] = defaultdict(list)

    def allow(self, client_id: str) -> bool:
        """
        Check if a request from client_id is allowed.

        Returns True if allowed, False if rate limited.
        """
        now = time.time()
        window_start = now - self.window_size

        # Get requests in current window
        client_requests = self.requests[client_id]

        # Remove old requests outside the window
        client_requests = [ts for ts in client_requests if ts > window_start]
        self.requests[client_id] = client_requests

        # Check if under limit
        if len(client_requests) >= self.rpm:
            return False

        # Record this request
        client_requests.append(now)
        return True

    def reset(self, client_id: str):
        """Reset rate limit for a client (for testing)."""
        self.requests[client_id] = []
