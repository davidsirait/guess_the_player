"""
Custom rate limit error handler
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors
    Returns user-friendly message
    """
    return JSONResponse(
        status_code=429,
        content={
            "detail": "⏱️ Slow down! You're guessing too fast. You can submit up to 10 guesses per minute. Please wait a moment and try again.",
            "retry_after": 60  # Seconds until rate limit resets
        }
    )