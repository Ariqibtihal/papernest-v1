from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _rate_limit_key(request: Request) -> str:
    """
    Key function for rate limiting.

    - Authenticated requests: keyed by user ID so limits are per-user,
      not per-IP. This prevents shared-IP environments (offices, NAT)
      from being unfairly throttled together, and stops IP-rotation bypass.
    - Unauthenticated requests: fall back to IP address.

    The user ID is extracted from request.state.user which is populated
    by FastAPI's dependency injection (get_current_user) before the
    rate-limit decorator runs on authenticated routes.
    """
    user = getattr(request.state, "user", None)
    if user is not None and hasattr(user, "id"):
        return f"user:{user.id}"
    return get_remote_address(request)


# Create limiter — authenticated routes use _rate_limit_key (user-aware),
# public routes (register, login, search) still use IP via get_remote_address.
limiter = Limiter(
    key_func=get_remote_address,   # default for public endpoints
    default_limits=["100/hour"],
)

# Separate limiter instance keyed by user ID for authenticated endpoints
user_limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=["100/hour"],
)

# Rate limit tiers for different endpoints
RATE_LIMITS = {
    "auth_register": "5/minute",
    "auth_login": "10/minute",
    "search": "30/minute",
    "export": "10/minute",
    "saved_papers": "60/minute",
    "alerts": "20/minute",
}
