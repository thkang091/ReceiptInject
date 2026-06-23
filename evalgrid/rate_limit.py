"""Simple async rate limiting utilities."""

from __future__ import annotations

import asyncio


class AsyncRateLimiter:
    """Limit concurrency and optionally sleep before requests."""

    def __init__(self, max_concurrency: int = 1, sleep_between_requests: float = 0.0) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        if sleep_between_requests < 0:
            raise ValueError("sleep_between_requests must be non-negative")
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.sleep_between_requests = sleep_between_requests

    async def __aenter__(self) -> None:
        """Enter the concurrency limiter."""

        await self.semaphore.acquire()
        if self.sleep_between_requests > 0:
            await asyncio.sleep(self.sleep_between_requests)

    async def __aexit__(self, exc_type, exc, tb) -> None:
        """Release concurrency limiter."""

        self.semaphore.release()
